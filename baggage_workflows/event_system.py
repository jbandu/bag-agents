"""
Event-Driven Trigger System

Handles external events that trigger state transitions and agent invocations.
"""

import logging
import asyncio
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime
from enum import Enum

from .orchestrator_state import EventType, BagStatus


logger = logging.getLogger(__name__)


class EventPriority(str, Enum):
    """Event priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventProcessor:
    """
    Processes external events and triggers appropriate actions.

    Handles RFID scans, flight delays, manual updates, etc.
    """

    def __init__(
        self,
        orchestrator,
        state_persistence,
        notification_service=None
    ):
        """
        Initialize event processor.

        Args:
            orchestrator: BaggageOrchestrator instance
            state_persistence: StatePersistenceManager instance
            notification_service: Optional notification service
        """
        self.orchestrator = orchestrator
        self.state_persistence = state_persistence
        self.notification_service = notification_service
        self.logger = logging.getLogger(__name__)

        # Event handlers registry
        self.event_handlers: Dict[EventType, List[Callable]] = {}

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default event handlers."""
        self.register_handler(EventType.RFID_SCAN, self.handle_rfid_scan)
        self.register_handler(EventType.FLIGHT_DELAY, self.handle_flight_delay)
        self.register_handler(
            EventType.MISHANDLING_DETECTED,
            self.handle_mishandling_detected
        )
        self.register_handler(
            EventType.APPROVAL_RECEIVED,
            self.handle_approval_received
        )
        self.register_handler(
            EventType.STATUS_UPDATE,
            self.handle_status_update
        )

    def register_handler(
        self,
        event_type: EventType,
        handler: Callable
    ):
        """
        Register an event handler.

        Args:
            event_type: Type of event to handle
            handler: Async handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)
        self.logger.info(f"Registered handler for {event_type}")

    async def process_event(
        self,
        bag_id: str,
        event_type: EventType,
        event_data: Dict[str, Any],
        priority: EventPriority = EventPriority.MEDIUM
    ) -> Dict[str, Any]:
        """
        Process an external event.

        Args:
            bag_id: Bag identifier
            event_type: Type of event
            event_data: Event details
            priority: Event priority

        Returns:
            Processing result
        """
        self.logger.info(
            f"Processing {event_type} event for bag {bag_id} "
            f"(priority: {priority})"
        )

        try:
            # Save event to database
            event_id = await self.state_persistence.save_event(
                bag_id=bag_id,
                event_type=event_type,
                event_data=event_data,
                source="external"
            )

            # Get current state
            current_state = await self.state_persistence.load_latest_checkpoint(bag_id)

            if not current_state:
                self.logger.warning(f"No state found for bag {bag_id}")
                return {
                    "success": False,
                    "error": "Bag not found in system"
                }

            # Execute event handlers
            results = []
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        result = await handler(
                            bag_id=bag_id,
                            event_data=event_data,
                            current_state=current_state
                        )
                        results.append(result)
                    except Exception as e:
                        self.logger.error(
                            f"Error in handler {handler.__name__}: {e}"
                        )
                        results.append({"error": str(e)})

            # Send notifications if high priority
            if priority in [EventPriority.HIGH, EventPriority.CRITICAL]:
                await self._send_notification(
                    bag_id=bag_id,
                    event_type=event_type,
                    event_data=event_data
                )

            return {
                "success": True,
                "event_id": event_id,
                "handlers_executed": len(results),
                "results": results
            }

        except Exception as e:
            self.logger.error(f"Error processing event: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # =====================================================================
    # EVENT HANDLERS
    # =====================================================================

    async def handle_rfid_scan(
        self,
        bag_id: str,
        event_data: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle RFID scan event.

        Updates bag location and may trigger state transitions.
        """
        self.logger.info(f"Handling RFID scan for bag {bag_id}")

        location = event_data.get("location")
        scan_time = event_data.get("timestamp", datetime.utcnow().isoformat())

        if not location:
            return {"error": "Location not provided in event data"}

        # Update current state location
        current_state["bag"]["current_location"] = location
        current_state["bag"]["last_scan_time"] = scan_time

        # Determine if status should change based on location
        # Example: If scanned at claim area, update to CLAIM status
        if "CLAIM" in location.upper():
            current_state["bag"]["current_status"] = BagStatus.CLAIM
        elif "SORTING" in location.upper():
            current_state["bag"]["current_status"] = BagStatus.SORTING

        # Save updated checkpoint
        await self.state_persistence.save_checkpoint(
            workflow_id=current_state["workflow_id"],
            bag_id=bag_id,
            node=current_state["current_node"],
            state=current_state
        )

        return {
            "action": "location_updated",
            "new_location": location,
            "new_status": current_state["bag"]["current_status"]
        }

    async def handle_flight_delay(
        self,
        bag_id: str,
        event_data: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle flight delay event.

        Re-evaluates connections and may trigger interventions.
        """
        self.logger.warning(f"Handling flight delay for bag {bag_id}")

        delay_minutes = event_data.get("delay_minutes", 0)
        flight_id = event_data.get("flight_id")

        # If bag has connection, re-evaluate
        if current_state.get("connection"):
            connection = current_state["connection"]

            # Reduce connection buffer
            if connection.get("connection_buffer_minutes"):
                connection["connection_buffer_minutes"] -= delay_minutes

                # Check if connection is now at risk
                if connection["connection_buffer_minutes"] < 30:
                    connection["connection_at_risk"] = True

                    # Invoke prediction agent to re-assess
                    if "prediction" in self.orchestrator.agents:
                        try:
                            result = await self.orchestrator.agents["prediction"].run({
                                "flight_id": current_state["bag"]["origin_flight"],
                                "departure_airport": current_state["bag"]["origin_airport"],
                                "arrival_airport": current_state["bag"]["destination_airport"],
                                "connection_time": connection["connection_buffer_minutes"]
                            })

                            current_state["bag"]["risk_score"] = result.get("risk_score", 0)

                        except Exception as e:
                            self.logger.error(f"Error re-assessing risk: {e}")

        # Save updated state
        await self.state_persistence.save_checkpoint(
            workflow_id=current_state["workflow_id"],
            bag_id=bag_id,
            node=current_state["current_node"],
            state=current_state
        )

        return {
            "action": "connection_re_evaluated",
            "at_risk": current_state.get("connection", {}).get("connection_at_risk", False),
            "new_risk_score": current_state["bag"]["risk_score"]
        }

    async def handle_mishandling_detected(
        self,
        bag_id: str,
        event_data: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle mishandling detection event.

        Transitions bag to mishandled state and triggers response workflow.
        """
        self.logger.error(f"Mishandling detected for bag {bag_id}")

        mishandling_type = event_data.get("type", "delayed")

        # Update status
        if mishandling_type == "lost":
            current_state["bag"]["current_status"] = BagStatus.LOST
        elif mishandling_type == "damaged":
            current_state["bag"]["current_status"] = BagStatus.DAMAGED
        else:
            current_state["bag"]["current_status"] = BagStatus.DELAYED

        # Trigger customer service notification
        if "customer_service" in self.orchestrator.agents:
            try:
                await self.orchestrator.agents["customer_service"].run({
                    "customer_query": f"Baggage {mishandling_type}",
                    "bag_tag": current_state["bag"]["tag_number"]
                })
            except Exception as e:
                self.logger.error(f"Error notifying customer: {e}")

        # Save state
        await self.state_persistence.save_checkpoint(
            workflow_id=current_state["workflow_id"],
            bag_id=bag_id,
            node="mishandled",
            state=current_state
        )

        return {
            "action": "mishandling_workflow_triggered",
            "type": mishandling_type,
            "new_status": current_state["bag"]["current_status"]
        }

    async def handle_approval_received(
        self,
        bag_id: str,
        event_data: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle approval received event.

        Updates approval status and resumes workflow.
        """
        self.logger.info(f"Handling approval for bag {bag_id}")

        approval_id = event_data.get("approval_id")
        status = event_data.get("status", "approved")
        approved_by = event_data.get("approved_by")

        # Update approval in database
        await self.state_persistence.update_approval_status(
            approval_id=approval_id,
            status=status,
            approved_by=approved_by
        )

        # Update intervention state
        if current_state["intervention"]["pending_interventions"]:
            intervention = current_state["intervention"]["pending_interventions"][0]
            intervention["approval_status"] = status
            intervention["approved_by"] = approved_by
            intervention["approved_at"] = datetime.utcnow().isoformat()

        # Save state
        await self.state_persistence.save_checkpoint(
            workflow_id=current_state["workflow_id"],
            bag_id=bag_id,
            node=current_state["current_node"],
            state=current_state
        )

        return {
            "action": "approval_processed",
            "status": status,
            "approved_by": approved_by
        }

    async def handle_status_update(
        self,
        bag_id: str,
        event_data: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle manual status update."""
        new_status = event_data.get("status")

        if new_status:
            current_state["bag"]["current_status"] = BagStatus(new_status)

            await self.state_persistence.save_checkpoint(
                workflow_id=current_state["workflow_id"],
                bag_id=bag_id,
                node=current_state["current_node"],
                state=current_state
            )

        return {
            "action": "status_updated",
            "new_status": new_status
        }

    # =====================================================================
    # HELPER METHODS
    # =====================================================================

    async def _send_notification(
        self,
        bag_id: str,
        event_type: EventType,
        event_data: Dict[str, Any]
    ):
        """
        Send notification for high-priority event.

        In production, would integrate with notification service
        (email, SMS, WebSocket, etc.)
        """
        if self.notification_service:
            try:
                await self.notification_service.send({
                    "bag_id": bag_id,
                    "event_type": event_type,
                    "event_data": event_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Error sending notification: {e}")
        else:
            self.logger.info(
                f"Notification (no service configured): "
                f"{event_type} for bag {bag_id}"
            )


class EventQueue:
    """
    Asynchronous event queue for processing events.

    Provides buffering and ordered processing of events.
    """

    def __init__(self, event_processor: EventProcessor, max_size: int = 1000):
        """
        Initialize event queue.

        Args:
            event_processor: EventProcessor instance
            max_size: Maximum queue size
        """
        self.event_processor = event_processor
        self.queue = asyncio.Queue(maxsize=max_size)
        self.running = False
        self.logger = logging.getLogger(__name__)

    async def enqueue(
        self,
        bag_id: str,
        event_type: EventType,
        event_data: Dict[str, Any],
        priority: EventPriority = EventPriority.MEDIUM
    ):
        """
        Add event to queue.

        Args:
            bag_id: Bag identifier
            event_type: Type of event
            event_data: Event data
            priority: Event priority
        """
        try:
            await self.queue.put({
                "bag_id": bag_id,
                "event_type": event_type,
                "event_data": event_data,
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.logger.debug(f"Enqueued {event_type} event for bag {bag_id}")
        except asyncio.QueueFull:
            self.logger.error("Event queue is full, dropping event")

    async def process_queue(self):
        """
        Process events from queue.

        Runs continuously until stopped.
        """
        self.running = True
        self.logger.info("Event queue processor started")

        while self.running:
            try:
                # Get event from queue
                event = await self.queue.get()

                # Process event
                await self.event_processor.process_event(
                    bag_id=event["bag_id"],
                    event_type=event["event_type"],
                    event_data=event["event_data"],
                    priority=event["priority"]
                )

                self.queue.task_done()

            except Exception as e:
                self.logger.error(f"Error processing queued event: {e}")

    def stop(self):
        """Stop the queue processor."""
        self.running = False
        self.logger.info("Event queue processor stopped")
