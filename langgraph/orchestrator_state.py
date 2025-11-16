"""
LangGraph Orchestrator State Schemas

Defines comprehensive state schemas for baggage lifecycle management.
"""

from typing import TypedDict, Annotated, Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import operator


class BagStatus(str, Enum):
    """Possible bag statuses in the system."""
    CHECK_IN = "check_in"
    SECURITY_SCREENING = "security_screening"
    SORTING = "sorting"
    LOADING = "loading"
    IN_FLIGHT = "in_flight"
    ARRIVAL = "arrival"
    TRANSFER = "transfer"
    CLAIM = "claim"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    LOST = "lost"
    DAMAGED = "damaged"
    RESOLVED = "resolved"


class RiskLevel(str, Enum):
    """Risk levels for baggage handling."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(str, Enum):
    """Approval status for human-in-the-loop decisions."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class EventType(str, Enum):
    """Types of events in the baggage lifecycle."""
    RFID_SCAN = "rfid_scan"
    STATUS_UPDATE = "status_update"
    LOCATION_UPDATE = "location_update"
    FLIGHT_DELAY = "flight_delay"
    MISHANDLING_DETECTED = "mishandling_detected"
    APPROVAL_RECEIVED = "approval_received"
    AGENT_EXECUTED = "agent_executed"
    ALERT_TRIGGERED = "alert_triggered"


class BagEvent(TypedDict):
    """Individual event in the bag's history."""
    event_id: str
    event_type: EventType
    timestamp: str
    location: str
    details: Dict[str, Any]
    source: str  # RFID reader, agent, operator, etc.


class Alert(TypedDict):
    """Alert for baggage handling issues."""
    alert_id: str
    severity: RiskLevel
    message: str
    created_at: str
    resolved_at: Optional[str]
    assigned_to: Optional[str]


class Intervention(TypedDict):
    """Recommended or executed intervention."""
    intervention_id: str
    action: str
    reason: str
    priority: int
    requires_approval: bool
    approval_status: ApprovalStatus
    approved_by: Optional[str]
    approved_at: Optional[str]
    executed: bool
    executed_at: Optional[str]
    result: Optional[Dict[str, Any]]


class BagState(TypedDict):
    """
    Core state for a single bag's lifecycle.

    This represents all information about a bag as it moves through the system.
    """
    # Identity
    bag_id: str
    tag_number: str
    passenger_id: str

    # Current status
    current_status: BagStatus
    current_location: str
    last_scan_time: str

    # Flight information
    origin_flight: str
    destination_flight: Optional[str]  # For connections
    origin_airport: str
    destination_airport: str
    connection_airport: Optional[str]

    # Risk assessment
    risk_score: float  # 0-100
    risk_level: RiskLevel
    risk_factors: List[str]

    # Bag details
    weight_kg: float
    declared_value: float
    special_handling: Optional[str]  # fragile, priority, etc.

    # Events and history
    events: Annotated[List[BagEvent], operator.add]
    alerts: Annotated[List[Alert], operator.add]
    interventions: Annotated[List[Intervention], operator.add]

    # Agent results cache
    prediction_result: Optional[Dict[str, Any]]
    route_optimization_result: Optional[Dict[str, Any]]

    # Metadata
    created_at: str
    updated_at: str
    version: int  # For optimistic locking


class ConnectionState(TypedDict):
    """
    State for connection management.

    Tracks connection flights and timing information.
    """
    # Connection details
    has_connection: bool
    connection_time_minutes: Optional[int]
    minimum_connection_time: int

    # Flights
    inbound_flight: Dict[str, Any]
    outbound_flight: Optional[Dict[str, Any]]

    # Timing
    inbound_actual_arrival: Optional[str]
    outbound_scheduled_departure: str
    connection_buffer_minutes: Optional[int]

    # Risk
    connection_at_risk: bool
    contingency_plan: Optional[Dict[str, Any]]

    # Handler assignments
    handler_assigned: Optional[str]
    handler_notified: bool


class InterventionState(TypedDict):
    """
    State for managing interventions and approvals.

    Handles human-in-the-loop decision making.
    """
    # Pending interventions
    pending_interventions: List[Intervention]

    # Approval workflow
    requires_approval: bool
    approval_threshold_value: float
    approver_role: Optional[str]  # supervisor, manager, etc.
    approval_timeout_minutes: int

    # Execution status
    interventions_executed: int
    interventions_pending: int
    interventions_failed: int

    # Notifications
    notifications_sent: List[Dict[str, Any]]


class OrchestratorState(TypedDict):
    """
    Complete orchestrator state combining all sub-states.

    This is the main state that flows through the LangGraph.
    """
    # Core bag state
    bag: BagState

    # Connection state (if applicable)
    connection: Optional[ConnectionState]

    # Intervention state
    intervention: InterventionState

    # Workflow control
    current_node: str
    next_node: Optional[str]
    previous_nodes: Annotated[List[str], operator.add]

    # Error handling
    errors: Annotated[List[Dict[str, Any]], operator.add]
    retry_count: int
    max_retries: int

    # Agent execution tracking
    agents_invoked: Annotated[List[str], operator.add]
    agent_results: Dict[str, Any]

    # Decision tracking
    decisions_made: Annotated[List[Dict[str, Any]], operator.add]

    # Metadata
    workflow_id: str
    started_at: str
    completed_at: Optional[str]
    status: Literal["running", "completed", "failed", "paused"]


class MishandlingState(TypedDict):
    """
    State for mishandling sub-graph.

    Handles delayed, lost, or damaged baggage scenarios.
    """
    # Mishandling details
    mishandling_type: Literal["delayed", "lost", "damaged"]
    detected_at: str
    detection_method: str

    # Root cause analysis
    root_cause_analysis: Optional[Dict[str, Any]]
    contributing_factors: List[str]

    # Customer impact
    passenger_notified: bool
    notification_method: Optional[str]
    customer_response: Optional[str]

    # Compensation
    compensation_calculated: bool
    compensation_amount: Optional[float]
    compensation_approved: bool
    compensation_paid: bool

    # Resolution
    resolution_plan: Optional[Dict[str, Any]]
    estimated_resolution_time: Optional[str]
    actual_resolution_time: Optional[str]

    # Escalation
    escalated: bool
    escalation_level: int
    assigned_to: Optional[str]


class CheckpointState(TypedDict):
    """
    State checkpoint for persistence and replay.

    Stores snapshots of the orchestrator state for recovery.
    """
    checkpoint_id: str
    workflow_id: str
    bag_id: str
    node: str
    state: OrchestratorState
    timestamp: str
    version: int


def create_initial_bag_state(
    bag_id: str,
    tag_number: str,
    passenger_id: str,
    origin_flight: str,
    origin_airport: str,
    destination_airport: str,
    weight_kg: float,
    declared_value: float = 0.0,
    connection_flight: Optional[str] = None,
    connection_airport: Optional[str] = None
) -> BagState:
    """
    Create initial bag state for a new bag entering the system.

    Args:
        bag_id: Unique bag identifier
        tag_number: Baggage tag number
        passenger_id: Passenger identifier
        origin_flight: Origin flight number
        origin_airport: Origin airport code
        destination_airport: Destination airport code
        weight_kg: Bag weight in kilograms
        declared_value: Declared value in USD
        connection_flight: Connection flight number (if applicable)
        connection_airport: Connection airport code (if applicable)

    Returns:
        Initial BagState
    """
    now = datetime.utcnow().isoformat()

    return BagState(
        bag_id=bag_id,
        tag_number=tag_number,
        passenger_id=passenger_id,
        current_status=BagStatus.CHECK_IN,
        current_location=origin_airport,
        last_scan_time=now,
        origin_flight=origin_flight,
        destination_flight=connection_flight,
        origin_airport=origin_airport,
        destination_airport=destination_airport,
        connection_airport=connection_airport,
        risk_score=0.0,
        risk_level=RiskLevel.LOW,
        risk_factors=[],
        weight_kg=weight_kg,
        declared_value=declared_value,
        special_handling=None,
        events=[],
        alerts=[],
        interventions=[],
        prediction_result=None,
        route_optimization_result=None,
        created_at=now,
        updated_at=now,
        version=1
    )


def create_initial_orchestrator_state(
    bag_state: BagState,
    has_connection: bool = False
) -> OrchestratorState:
    """
    Create initial orchestrator state from bag state.

    Args:
        bag_state: Initial bag state
        has_connection: Whether bag has a connection

    Returns:
        Initial OrchestratorState
    """
    import uuid
    now = datetime.utcnow().isoformat()

    connection_state = None
    if has_connection:
        connection_state = ConnectionState(
            has_connection=True,
            connection_time_minutes=None,
            minimum_connection_time=45,
            inbound_flight={},
            outbound_flight=None,
            inbound_actual_arrival=None,
            outbound_scheduled_departure="",
            connection_buffer_minutes=None,
            connection_at_risk=False,
            contingency_plan=None,
            handler_assigned=None,
            handler_notified=False
        )

    return OrchestratorState(
        bag=bag_state,
        connection=connection_state,
        intervention=InterventionState(
            pending_interventions=[],
            requires_approval=False,
            approval_threshold_value=500.0,
            approver_role=None,
            approval_timeout_minutes=30,
            interventions_executed=0,
            interventions_pending=0,
            interventions_failed=0,
            notifications_sent=[]
        ),
        current_node="check_in",
        next_node=None,
        previous_nodes=[],
        errors=[],
        retry_count=0,
        max_retries=3,
        agents_invoked=[],
        agent_results={},
        decisions_made=[],
        workflow_id=str(uuid.uuid4()),
        started_at=now,
        completed_at=None,
        status="running"
    )
