"""
Orchestrator API Routes

API endpoints for baggage lifecycle orchestration.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from baggage_workflows.orchestrator_state import (
    create_initial_bag_state,
    EventType,
    BagStatus
)
from baggage_workflows.baggage_orchestrator import BaggageOrchestrator
from baggage_workflows.state_persistence import StatePersistenceManager
from baggage_workflows.event_system import EventProcessor, EventPriority


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


# =====================================================================
# REQUEST/RESPONSE MODELS
# =====================================================================

class InitializeBagRequest(BaseModel):
    """Request to initialize bag tracking."""
    tag_number: str = Field(..., description="Baggage tag number")
    passenger_id: str = Field(..., description="Passenger identifier")
    origin_flight: str = Field(..., description="Origin flight number")
    origin_airport: str = Field(..., description="Origin airport code (IATA)")
    destination_airport: str = Field(..., description="Destination airport code (IATA)")
    weight_kg: float = Field(..., description="Bag weight in kilograms", gt=0)
    declared_value: float = Field(default=0.0, description="Declared value in USD", ge=0)
    connection_flight: Optional[str] = Field(None, description="Connection flight number")
    connection_airport: Optional[str] = Field(None, description="Connection airport code")
    special_handling: Optional[str] = Field(None, description="Special handling requirements")


class ExternalEventRequest(BaseModel):
    """Request to send external event."""
    bag_id: str = Field(..., description="Bag identifier")
    event_type: str = Field(..., description="Event type")
    event_data: Dict[str, Any] = Field(..., description="Event details")
    priority: str = Field(default="medium", description="Event priority")


class ApprovalRequest(BaseModel):
    """Request to approve/reject pending action."""
    approval_id: str = Field(..., description="Approval request ID")
    status: str = Field(..., description="approved or rejected")
    approved_by: str = Field(..., description="Approver identifier")
    comments: Optional[str] = Field(None, description="Optional comments")


class BagStateResponse(BaseModel):
    """Response with current bag state."""
    bag_id: str
    tag_number: str
    current_status: str
    current_location: str
    risk_score: float
    risk_level: str
    alerts_count: int
    events_count: int
    last_updated: str


# =====================================================================
# DEPENDENCY INJECTION
# =====================================================================

# Global instances (initialized in main app)
orchestrator: Optional[BaggageOrchestrator] = None
state_persistence: Optional[StatePersistenceManager] = None
event_processor: Optional[EventProcessor] = None


def get_orchestrator() -> BaggageOrchestrator:
    """Get orchestrator instance."""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return orchestrator


def get_state_persistence() -> StatePersistenceManager:
    """Get state persistence instance."""
    if state_persistence is None:
        raise HTTPException(status_code=503, detail="State persistence not initialized")
    return state_persistence


def get_event_processor() -> EventProcessor:
    """Get event processor instance."""
    if event_processor is None:
        raise HTTPException(status_code=503, detail="Event processor not initialized")
    return event_processor


# =====================================================================
# API ENDPOINTS
# =====================================================================

@router.post("/initialize")
async def initialize_bag_tracking(
    request: InitializeBagRequest,
    orch: BaggageOrchestrator = Depends(get_orchestrator),
    persistence: StatePersistenceManager = Depends(get_state_persistence)
):
    """
    Initialize tracking for a new bag.

    Starts the bag lifecycle orchestration workflow.
    """
    import uuid

    try:
        logger.info(f"Initializing tracking for bag tag {request.tag_number}")

        # Generate bag ID
        bag_id = str(uuid.uuid4())

        # Create initial bag state
        bag_state = create_initial_bag_state(
            bag_id=bag_id,
            tag_number=request.tag_number,
            passenger_id=request.passenger_id,
            origin_flight=request.origin_flight,
            origin_airport=request.origin_airport,
            destination_airport=request.destination_airport,
            weight_kg=request.weight_kg,
            declared_value=request.declared_value,
            connection_flight=request.connection_flight,
            connection_airport=request.connection_airport
        )

        if request.special_handling:
            bag_state["special_handling"] = request.special_handling

        # Determine if has connection
        has_connection = bool(request.connection_flight)

        # Start orchestration workflow (async)
        # In production, would run in background task
        result = await orch.process_bag(bag_state, has_connection=has_connection)

        # Save initial checkpoint
        await persistence.save_checkpoint(
            workflow_id=result["workflow_id"],
            bag_id=bag_id,
            node="check_in",
            state=result
        )

        logger.info(f"Successfully initialized bag {bag_id}")

        return {
            "success": True,
            "bag_id": bag_id,
            "workflow_id": result["workflow_id"],
            "current_status": result["bag"]["current_status"],
            "risk_score": result["bag"]["risk_score"]
        }

    except Exception as e:
        logger.error(f"Error initializing bag tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/event")
async def send_external_event(
    request: ExternalEventRequest,
    processor: EventProcessor = Depends(get_event_processor)
):
    """
    Send an external event to update bag state.

    Examples:
    - RFID scan
    - Flight delay
    - Manual status update
    - Mishandling detected
    """
    try:
        logger.info(f"Processing {request.event_type} event for bag {request.bag_id}")

        # Convert event type string to enum
        try:
            event_type = EventType(request.event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: {request.event_type}"
            )

        # Convert priority
        try:
            priority = EventPriority(request.priority)
        except ValueError:
            priority = EventPriority.MEDIUM

        # Process event
        result = await processor.process_event(
            bag_id=request.bag_id,
            event_type=event_type,
            event_data=request.event_data,
            priority=priority
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/{bag_id}")
async def get_bag_state(
    bag_id: str,
    persistence: StatePersistenceManager = Depends(get_state_persistence)
):
    """
    Get current state for a bag.

    Returns the latest checkpoint state.
    """
    try:
        logger.info(f"Retrieving state for bag {bag_id}")

        # Load latest checkpoint
        state = await persistence.load_latest_checkpoint(bag_id)

        if not state:
            raise HTTPException(status_code=404, detail="Bag not found")

        # Build response
        bag = state["bag"]
        response = BagStateResponse(
            bag_id=bag["bag_id"],
            tag_number=bag["tag_number"],
            current_status=bag["current_status"],
            current_location=bag["current_location"],
            risk_score=bag["risk_score"],
            risk_level=bag["risk_level"],
            alerts_count=len(bag.get("alerts", [])),
            events_count=len(bag.get("events", [])),
            last_updated=bag["updated_at"]
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving bag state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/{bag_id}/full")
async def get_full_bag_state(
    bag_id: str,
    persistence: StatePersistenceManager = Depends(get_state_persistence)
):
    """
    Get complete state for a bag including all events and history.
    """
    try:
        # Load latest checkpoint
        state = await persistence.load_latest_checkpoint(bag_id)

        if not state:
            raise HTTPException(status_code=404, detail="Bag not found")

        # Get events
        events = await persistence.get_bag_events(bag_id)

        return {
            "state": state,
            "events": events
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving full bag state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{bag_id}")
async def get_bag_history(
    bag_id: str,
    limit: int = 100,
    persistence: StatePersistenceManager = Depends(get_state_persistence)
):
    """
    Get checkpoint history for a bag.

    Returns all state transitions.
    """
    try:
        history = await persistence.get_checkpoint_history(bag_id, limit=limit)

        return {
            "bag_id": bag_id,
            "checkpoints": history,
            "total": len(history)
        }

    except Exception as e:
        logger.error(f"Error retrieving bag history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
async def approve_action(
    request: ApprovalRequest,
    persistence: StatePersistenceManager = Depends(get_state_persistence),
    processor: EventProcessor = Depends(get_event_processor)
):
    """
    Approve or reject a pending action.

    Used for human-in-the-loop decision making.
    """
    try:
        logger.info(f"Processing approval {request.approval_id} by {request.approved_by}")

        # Update approval status
        success = await persistence.update_approval_status(
            approval_id=request.approval_id,
            status=request.status,
            approved_by=request.approved_by,
            comments=request.comments
        )

        if not success:
            raise HTTPException(status_code=404, detail="Approval request not found")

        # TODO: Trigger workflow resumption
        # Would need to get bag_id from approval and send approval_received event

        return {
            "success": True,
            "approval_id": request.approval_id,
            "status": request.status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing approval: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending-approvals")
async def get_pending_approvals(
    approver_role: Optional[str] = None,
    persistence: StatePersistenceManager = Depends(get_state_persistence)
):
    """
    Get all pending approval requests.

    Can filter by approver role.
    """
    try:
        approvals = await persistence.get_pending_approvals(approver_role=approver_role)

        return {
            "pending_approvals": approvals,
            "total": len(approvals)
        }

    except Exception as e:
        logger.error(f"Error retrieving pending approvals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_stats(
    persistence: StatePersistenceManager = Depends(get_state_persistence)
):
    """
    Get dashboard statistics.

    Provides overview of all bags in the system.
    """
    try:
        # In production, would query aggregated stats from database
        # For now, return placeholder

        return {
            "bags_by_status": {
                "check_in": 150,
                "in_flight": 320,
                "arrival": 85,
                "claim": 45,
                "delivered": 1250,
                "delayed": 12,
                "lost": 3
            },
            "total_bags": 1865,
            "pending_approvals": 7,
            "high_risk_bags": 23,
            "avg_risk_score": 15.5,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error retrieving dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# WEBSOCKET ENDPOINTS
# =====================================================================

@router.websocket("/ws/bags/{bag_id}")
async def websocket_bag_updates(websocket: WebSocket, bag_id: str):
    """
    WebSocket endpoint for real-time bag updates.

    Streams state changes for a specific bag.
    """
    await websocket.accept()

    try:
        logger.info(f"WebSocket connected for bag {bag_id}")

        # Send current state
        if state_persistence:
            current_state = await state_persistence.load_latest_checkpoint(bag_id)
            if current_state:
                await websocket.send_json({
                    "type": "current_state",
                    "data": current_state
                })

        # Keep connection alive and send updates
        while True:
            # In production, would subscribe to events and push updates
            # For now, just keep connection alive
            data = await websocket.receive_text()

            # Echo back (placeholder)
            await websocket.send_json({
                "type": "ack",
                "message": "received"
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for bag {bag_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    WebSocket endpoint for dashboard real-time updates.

    Streams system-wide statistics and alerts.
    """
    await websocket.accept()

    try:
        logger.info("Dashboard WebSocket connected")

        # Send initial dashboard data
        await websocket.send_json({
            "type": "dashboard_stats",
            "data": {
                "bags_by_status": {"in_flight": 320, "claim": 45},
                "timestamp": datetime.utcnow().isoformat()
            }
        })

        # Keep connection alive
        while True:
            data = await websocket.receive_text()

            # Echo (placeholder for real-time updates)
            await websocket.send_json({
                "type": "update",
                "timestamp": datetime.utcnow().isoformat()
            })

    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket disconnected")
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass
