# Baggage Lifecycle Orchestrator

Comprehensive documentation for the LangGraph-based baggage lifecycle orchestration system.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [State Machine](#state-machine)
4. [Nodes](#nodes)
5. [Agent Integration](#agent-integration)
6. [Human-in-the-Loop](#human-in-the-loop)
7. [Event System](#event-system)
8. [API Reference](#api-reference)
9. [Usage Examples](#usage-examples)

## Overview

The Baggage Lifecycle Orchestrator is a sophisticated state machine built with LangGraph that coordinates all 8 specialized agents to manage the complete journey of a bag from check-in to delivery. It handles:

- **State Management**: Tracks bag status, location, events, and risk
- **Agent Coordination**: Invokes appropriate agents at each stage
- **Human Approval**: Pause for human decisions on high-value actions
- **Event Processing**: Responds to external events (RFID scans, delays, etc.)
- **State Persistence**: Checkpoints for recovery and replay
- **Real-time Updates**: WebSocket streams for monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Baggage Orchestrator                       │
│                   (LangGraph StateGraph)                     │
└──────────────┬──────────────────────────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼────┐ ┌──▼───┐  ┌───▼────┐
│  State │ │Event │  │  Agent │
│Persist │ │Proc. │  │  Pool  │
└────┬───┘ └──┬───┘  └───┬────┘
     │        │          │
     ▼        ▼          ▼
┌──────────────────────────────┐
│      Neon PostgreSQL         │
│  - Checkpoints               │
│  - Events                    │
│  - Approvals                 │
└──────────────────────────────┘
```

## State Machine

### State Machine Diagram (Mermaid)

\`\`\`mermaid
graph TD
    START([START]) --> CHECK_IN[Check-In]
    CHECK_IN --> SECURITY[Security Screening]
    SECURITY --> SORTING[Sorting]

    SORTING -->|Normal| LOADING[Loading]
    SORTING -->|Issue| MISHANDLED[Mishandled]

    LOADING --> IN_FLIGHT[In-Flight]

    IN_FLIGHT -->|No Connection| ARRIVAL[Arrival]
    IN_FLIGHT -->|Has Connection| TRANSFER[Transfer]

    TRANSFER -->|Success| SORTING
    TRANSFER -->|Failed| MISHANDLED

    ARRIVAL -->|Found| CLAIM[Claim]
    ARRIVAL -->|Not Found| MISHANDLED

    CLAIM -->|Regular| DELIVERED[Delivered]
    CLAIM -->|High Value| REQUEST_APPROVAL{Request Approval}

    REQUEST_APPROVAL --> WAIT_APPROVAL[Wait for Approval]
    WAIT_APPROVAL -->|Approved| DELIVERED
    WAIT_APPROVAL -->|Rejected| MISHANDLED

    MISHANDLED --> ROOT_CAUSE[Root Cause Analysis]
    ROOT_CAUSE --> COMPENSATION[Compensation]

    COMPENSATION -->|Low Value| END([END])
    COMPENSATION -->|High Value| REQUEST_APPROVAL

    DELIVERED --> END

    style CHECK_IN fill:#90EE90
    style DELIVERED fill:#90EE90
    style MISHANDLED fill:#FFB6C1
    style REQUEST_APPROVAL fill:#FFD700
    style WAIT_APPROVAL fill:#FFD700
\`\`\`

### Normal Flow

1. **Check-In** → Bag enters system, risk assessment
2. **Security Screening** → Security clearance
3. **Sorting** → Route determination
4. **Loading** → Load onto aircraft
5. **In-Flight** → Transit to destination
6. **Arrival** → Arrive at destination
7. **Claim** → Ready for pickup
8. **Delivered** → Customer retrieval (terminal state)

### Connection Flow

1. Check-In → Security → Sorting → Loading → In-Flight
2. **Transfer** → Connection airport handling
3. Back to **Sorting** for connection flight
4. Continue normal flow

### Mishandling Flow

1. Detection at any stage
2. **Mishandled** → Classify type (delayed/lost/damaged)
3. **Root Cause Analysis** → Analyze contributing factors
4. **Compensation** → Calculate and process claim
5. End or request approval if high value

## Nodes

### 1. Check-In Node

**Purpose**: Initialize bag tracking and assess initial risk

**Agents Invoked**:
- Prediction Agent (risk assessment)

**Actions**:
- Create initial bag state
- Assess connection risk
- Generate alerts if high risk

**Code Location**: `langgraph/baggage_orchestrator.py:check_in_node`

### 2. Security Screening Node

**Purpose**: Track security processing

**Actions**:
- Update status to SECURITY_SCREENING
- Log security checkpoint pass

### 3. Sorting Node

**Purpose**: Route bag to correct destination

**Agents Invoked**:
- Infrastructure Health Agent (check sorting equipment)

**Actions**:
- Verify equipment health
- Determine routing
- Alert if equipment degraded

### 4. Loading Node

**Purpose**: Track bag loading onto aircraft

**Actions**:
- Update status to LOADING
- Record flight assignment

### 5. In-Flight Node

**Purpose**: Track transit status

**Actions**:
- Update to IN_FLIGHT
- Monitor for flight delays (via events)

### 6. Transfer Node

**Purpose**: Handle connection transfers

**Agents Invoked**:
- Route Optimization Agent (optimize connection path)
- Prediction Agent (re-assess risk)

**Actions**:
- Optimize transfer routing
- Check connection timing
- Assign handlers if at-risk

**Conditional Exit**:
- Success → Back to Sorting
- Failure → Mishandled

### 7. Arrival Node

**Purpose**: Track arrival at destination

**Actions**:
- Update location to destination airport
- Prepare for claim

### 8. Claim Node

**Purpose**: Ready for customer pickup

**Conditional Exit**:
- Regular bag → Delivered
- High-value bag (>$5000) → Request Approval

### 9. Delivered Node (Terminal)

**Purpose**: Final successful state

**Actions**:
- Mark workflow complete
- Close tracking

### 10. Mishandled Node

**Purpose**: Handle mishandling incidents

**Agents Invoked**:
- Customer Service Agent (notify passenger)

**Actions**:
- Classify mishandling type
- Create high-priority alert
- Trigger customer notification

### 11. Root Cause Analysis Node

**Purpose**: Determine why mishandling occurred

**Agents Invoked**:
- Root Cause Agent (analyze incident)

**Actions**:
- Identify contributing factors
- Generate recommendations
- Log insights for future prevention

### 12. Compensation Node

**Purpose**: Calculate and process compensation

**Agents Invoked**:
- Compensation Agent (calculate amount)

**Actions**:
- Determine eligibility
- Calculate compensation
- Check if approval needed (>$500)

**Conditional Exit**:
- Low value → End
- High value → Request Approval

### 13. Request Approval Node

**Purpose**: Request human approval for high-value actions

**Actions**:
- Create approval request
- Save to database
- Notify approver (email/SMS/dashboard)

**Triggers Approval When**:
- Bag value > $5000 (delivery approval)
- Compensation > $500 (payment approval)
- Flight hold request (ops approval)

### 14. Wait for Approval Node

**Purpose**: Pause execution until approval received

**Actions**:
- Check approval status
- Timeout after X minutes (default: 30)
- Auto-approve on timeout (configurable)

**Conditional Exit**:
- Approved/Timeout → Delivered
- Rejected → Mishandled

## Agent Integration

### Agent Invocation Strategy

Each node can invoke agents as needed:

| Node | Agents Used | Purpose |
|------|-------------|---------|
| Check-In | Prediction | Assess connection risk |
| Sorting | Infrastructure Health | Verify equipment |
| Transfer | Route Optimization, Prediction | Optimize path, re-assess risk |
| Mishandled | Customer Service | Notify passenger |
| Root Cause | Root Cause | Analyze incident |
| Compensation | Compensation | Calculate claim |

### Agent Coordination

```python
# Example: Check-in node invoking prediction agent
if "prediction" in self.agents:
    result = await self.agents["prediction"].run({
        "flight_id": state["bag"]["origin_flight"],
        "departure_airport": state["bag"]["origin_airport"],
        "arrival_airport": state["bag"]["destination_airport"]
    })

    state["bag"]["risk_score"] = result.get("risk_score", 0)
    state["agents_invoked"].append("prediction")
```

## Human-in-the-Loop

### Approval Workflow

1. **Trigger Condition Met**
   - High-value bag delivery (>$5000)
   - High compensation (>$500)
   - Custom business rules

2. **Create Approval Request**
   - Generate unique approval ID
   - Determine approver role (supervisor/manager)
   - Set timeout (default: 30 minutes)
   - Save to database

3. **Notify Approver**
   - Email notification
   - Dashboard alert
   - SMS (for critical)

4. **Wait for Response**
   - Pause workflow execution
   - Poll database for status
   - Auto-approve on timeout

5. **Resume Execution**
   - Apply decision
   - Continue workflow
   - Log approval trail

### Approval API

```python
# Request approval
POST /api/orchestrator/approve
{
    "approval_id": "APR-123",
    "status": "approved",
    "approved_by": "supervisor@airline.com",
    "comments": "Verified high-value item"
}

# Get pending approvals
GET /api/orchestrator/pending-approvals?approver_role=supervisor
```

## Event System

### Event Types

| Event Type | Trigger | Action |
|------------|---------|--------|
| RFID_SCAN | RFID reader scans tag | Update location |
| FLIGHT_DELAY | Flight delayed | Re-assess connections |
| STATUS_UPDATE | Manual update | Change status |
| MISHANDLING_DETECTED | Bag not found | Enter mishandling flow |
| APPROVAL_RECEIVED | Human approves | Resume workflow |

### Event Processing

```python
# Send event via API
POST /api/orchestrator/event
{
    "bag_id": "bag-123",
    "event_type": "rfid_scan",
    "event_data": {
        "location": "JFK-SORTING-A",
        "timestamp": "2024-11-15T10:30:00Z",
        "reader_id": "RFID-1234"
    },
    "priority": "medium"
}
```

### Event Handlers

Custom handlers can be registered:

```python
from langgraph.event_system import EventProcessor

processor = EventProcessor(orchestrator, state_persistence)

# Register custom handler
async def custom_handler(bag_id, event_data, current_state):
    # Custom logic
    return {"action": "processed"}

processor.register_handler(EventType.RFID_SCAN, custom_handler)
```

## API Reference

### Initialize Bag Tracking

```http
POST /api/orchestrator/initialize
Content-Type: application/json

{
    "tag_number": "BAG123456",
    "passenger_id": "PASS001",
    "origin_flight": "AA123",
    "origin_airport": "JFK",
    "destination_airport": "LAX",
    "weight_kg": 23.5,
    "declared_value": 1500.00,
    "connection_flight": "AA456",
    "connection_airport": "ORD"
}

Response:
{
    "success": true,
    "bag_id": "uuid-1234",
    "workflow_id": "uuid-5678",
    "current_status": "check_in",
    "risk_score": 35
}
```

### Get Bag State

```http
GET /api/orchestrator/state/{bag_id}

Response:
{
    "bag_id": "uuid-1234",
    "tag_number": "BAG123456",
    "current_status": "in_flight",
    "current_location": "IN_FLIGHT",
    "risk_score": 35,
    "risk_level": "medium",
    "alerts_count": 1,
    "events_count": 5,
    "last_updated": "2024-11-15T10:30:00Z"
}
```

### WebSocket - Real-time Updates

```javascript
// Connect to bag updates
const ws = new WebSocket('ws://localhost:8000/api/orchestrator/ws/bags/uuid-1234');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('State update:', data);
};
```

## Usage Examples

See [examples/orchestrator_demo.py](../examples/orchestrator_demo.py) for complete usage examples.

### Basic Usage

```python
from langgraph.baggage_orchestrator import BaggageOrchestrator
from langgraph.orchestrator_state import create_initial_bag_state

# Initialize orchestrator
orchestrator = BaggageOrchestrator(agents=agents, db_manager=db)

# Create bag state
bag_state = create_initial_bag_state(
    bag_id="bag-001",
    tag_number="BAG123456",
    passenger_id="PASS001",
    origin_flight="AA123",
    origin_airport="JFK",
    destination_airport="LAX",
    weight_kg=23.5
)

# Process bag through lifecycle
result = await orchestrator.process_bag(bag_state)

print(f"Final status: {result['bag']['current_status']}")
print(f"Agents invoked: {result['agents_invoked']}")
```

### Handling Events

```python
from langgraph.event_system import EventProcessor, EventType

processor = EventProcessor(orchestrator, state_persistence)

# RFID scan event
await processor.process_event(
    bag_id="bag-001",
    event_type=EventType.RFID_SCAN,
    event_data={
        "location": "JFK-SORTING-A",
        "timestamp": "2024-11-15T10:30:00Z"
    }
)

# Flight delay event
await processor.process_event(
    bag_id="bag-001",
    event_type=EventType.FLIGHT_DELAY,
    event_data={
        "flight_id": "AA123",
        "delay_minutes": 45
    },
    priority=EventPriority.HIGH
)
```

## State Persistence

All state transitions are checkpointed:

```python
from langgraph.state_persistence import StatePersistenceManager

persistence = StatePersistenceManager(db_manager)

# Save checkpoint
await persistence.save_checkpoint(
    workflow_id="uuid-1234",
    bag_id="bag-001",
    node="check_in",
    state=orchestrator_state
)

# Load latest
state = await persistence.load_latest_checkpoint("bag-001")

# Get history
history = await persistence.get_checkpoint_history("bag-001")
```

## Monitoring

### Dashboard Metrics

```http
GET /api/orchestrator/dashboard

Response:
{
    "bags_by_status": {
        "check_in": 150,
        "in_flight": 320,
        "arrival": 85,
        "delivered": 1250,
        "delayed": 12
    },
    "total_bags": 1865,
    "pending_approvals": 7,
    "high_risk_bags": 23,
    "avg_risk_score": 15.5
}
```

### WebSocket Dashboard

```javascript
const ws = new WebSocket('ws://localhost:8000/api/orchestrator/ws/dashboard');

ws.onmessage = (event) => {
    const stats = JSON.parse(event.data);
    updateDashboard(stats);
};
```

## Testing

See [tests/test_orchestrator.py](../tests/test_orchestrator.py) for comprehensive tests.

### Unit Tests

- Node execution
- Conditional edge routing
- State transitions
- Agent invocation

### Integration Tests

- Complete bag journey (happy path)
- Connection handling
- Mishandling scenarios
- Approval workflows

### Stress Tests

- 10,000 concurrent bags
- Event queue processing
- Database checkpoint performance

## Troubleshooting

### Common Issues

**Issue**: Workflow stuck at Wait for Approval
- **Solution**: Check approval timeout settings, verify notifications sent

**Issue**: State not persisting
- **Solution**: Verify database connection, check checkpoint tables exist

**Issue**: Events not triggering state changes
- **Solution**: Verify event handlers registered, check event type enum values

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

View workflow execution:

```python
# Get checkpoint history to see all state transitions
history = await persistence.get_checkpoint_history("bag-001")
for checkpoint in history:
    print(f"{checkpoint['timestamp']}: {checkpoint['node']}")
```

## Next Steps

- Implement Neo4j graph queries for route optimization
- Add machine learning model integration
- Build production notification service
- Create monitoring dashboards (Grafana)
- Implement workflow replay for debugging
