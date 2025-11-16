"""
Baggage Orchestrator Demo

Demonstrates usage of the LangGraph baggage lifecycle orchestrator.

Run this script to see:
1. Complete bag journey (check-in to delivery)
2. Connection handling
3. Event processing (RFID scans, delays)
4. Mishandling scenarios
5. Human approval workflows
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# =====================================================================
# DEMO 1: SIMPLE BAG JOURNEY (HAPPY PATH)
# =====================================================================

async def demo_simple_journey():
    """
    Demonstrate a simple bag journey from check-in to delivery.

    No connections, no issues - straightforward path.
    """
    print("\n" + "=" * 70)
    print("DEMO 1: Simple Bag Journey (Happy Path)")
    print("=" * 70)

    from langgraph.baggage_orchestrator import BaggageOrchestrator
    from langgraph.orchestrator_state import create_initial_bag_state

    # Mock agents (in production, use real agents)
    mock_agents = {}

    # Initialize orchestrator
    orchestrator = BaggageOrchestrator(agents=mock_agents, enable_checkpoints=True)

    # Create bag state
    bag_state = create_initial_bag_state(
        bag_id="BAG-001",
        tag_number="BAG123456",
        passenger_id="PASS001",
        origin_flight="AA123",
        origin_airport="JFK",
        destination_airport="LAX",
        weight_kg=23.5,
        declared_value=500.00
    )

    logger.info(f"Starting journey for bag {bag_state['tag_number']}")
    logger.info(f"Route: {bag_state['origin_airport']} → {bag_state['destination_airport']}")

    # Process bag through lifecycle
    result = await orchestrator.process_bag(bag_state, has_connection=False)

    # Display results
    print(f"\n✅ Journey Complete!")
    print(f"   Bag ID: {result['bag']['bag_id']}")
    print(f"   Final Status: {result['bag']['current_status']}")
    print(f"   Workflow Status: {result['status']}")
    print(f"   Nodes Visited: {', '.join(result['previous_nodes'])}")
    print(f"   Agents Invoked: {', '.join(result['agents_invoked']) if result['agents_invoked'] else 'None'}")
    print(f"   Events: {len(result['bag']['events'])}")

    return result


# =====================================================================
# DEMO 2: BAG WITH CONNECTION
# =====================================================================

async def demo_connection_journey():
    """
    Demonstrate a bag with a connection at a transfer airport.

    Shows transfer node handling and route optimization.
    """
    print("\n" + "=" * 70)
    print("DEMO 2: Bag with Connection")
    print("=" * 70)

    from langgraph.baggage_orchestrator import BaggageOrchestrator
    from langgraph.orchestrator_state import create_initial_bag_state

    mock_agents = {}
    orchestrator = BaggageOrchestrator(agents=mock_agents, enable_checkpoints=True)

    # Create bag with connection
    bag_state = create_initial_bag_state(
        bag_id="BAG-002",
        tag_number="BAG789012",
        passenger_id="PASS002",
        origin_flight="AA123",
        origin_airport="JFK",
        destination_airport="SFO",
        weight_kg=20.0,
        declared_value=750.00,
        connection_flight="AA456",
        connection_airport="ORD"
    )

    logger.info(f"Starting journey with connection for bag {bag_state['tag_number']}")
    logger.info(f"Route: {bag_state['origin_airport']} → {bag_state['connection_airport']} → {bag_state['destination_airport']}")

    result = await orchestrator.process_bag(bag_state, has_connection=True)

    print(f"\n✅ Connection Journey Complete!")
    print(f"   Origin: {result['bag']['origin_airport']}")
    print(f"   Transfer: {result['bag']['connection_airport']}")
    print(f"   Destination: {result['bag']['destination_airport']}")
    print(f"   Risk Score: {result['bag']['risk_score']}")
    print(f"   Risk Level: {result['bag']['risk_level']}")

    return result


# =====================================================================
# DEMO 3: EVENT PROCESSING
# =====================================================================

async def demo_event_processing():
    """
    Demonstrate external event processing.

    Shows RFID scans, flight delays, and state updates.
    """
    print("\n" + "=" * 70)
    print("DEMO 3: Event Processing")
    print("=" * 70)

    from langgraph.baggage_orchestrator import BaggageOrchestrator
    from langgraph.orchestrator_state import create_initial_bag_state
    from langgraph.event_system import EventProcessor, EventType, EventPriority
    from langgraph.state_persistence import StatePersistenceManager

    # Mock database manager (in production, use real DB)
    class MockDB:
        async def query_postgres(self, query, params=None, fetch_one=False):
            return None

        async def execute_postgres(self, query, params=None):
            return 1

    mock_db = MockDB()
    orchestrator = BaggageOrchestrator(enable_checkpoints=False)
    persistence = StatePersistenceManager(mock_db)
    event_processor = EventProcessor(orchestrator, persistence)

    # Create bag
    bag_state = create_initial_bag_state(
        bag_id="BAG-003",
        tag_number="BAG345678",
        passenger_id="PASS003",
        origin_flight="AA789",
        origin_airport="LAX",
        destination_airport="JFK",
        weight_kg=18.5
    )

    logger.info("Simulating RFID scans and events...")

    # Event 1: RFID scan at sorting facility
    print("\n📍 Event 1: RFID Scan at Sorting Facility")
    result1 = await event_processor.handle_rfid_scan(
        bag_id=bag_state["bag_id"],
        event_data={
            "location": "LAX-SORTING-B",
            "timestamp": datetime.utcnow().isoformat()
        },
        current_state={
            "bag": bag_state,
            "workflow_id": "WF-003",
            "current_node": "sorting"
        }
    )
    print(f"   → {result1}")

    # Event 2: Flight delay
    print("\n⏰ Event 2: Flight Delay")
    result2 = await event_processor.handle_flight_delay(
        bag_id=bag_state["bag_id"],
        event_data={
            "flight_id": "AA789",
            "delay_minutes": 30
        },
        current_state={
            "bag": bag_state,
            "connection": {
                "has_connection": True,
                "connection_buffer_minutes": 60
            },
            "workflow_id": "WF-003",
            "current_node": "in_flight"
        }
    )
    print(f"   → {result2}")

    print("\n✅ Event Processing Complete!")


# =====================================================================
# DEMO 4: MISHANDLING SCENARIO
# =====================================================================

async def demo_mishandling():
    """
    Demonstrate mishandling detection and recovery workflow.

    Shows root cause analysis and compensation processing.
    """
    print("\n" + "=" * 70)
    print("DEMO 4: Mishandling Scenario")
    print("=" * 70)

    from langgraph.event_system import EventProcessor, EventType
    from langgraph.orchestrator_state import BagStatus

    print("\n🚨 Simulating bag mishandling detection...")

    # Mock state
    mock_state = {
        "bag": {
            "bag_id": "BAG-004",
            "tag_number": "BAG901234",
            "current_status": BagStatus.DELAYED,
            "current_location": "ORD",
            "events": [],
            "alerts": []
        },
        "workflow_id": "WF-004",
        "current_node": "arrival"
    }

    class MockDB:
        async def execute_postgres(self, query, params=None):
            return 1
        async def query_postgres(self, query, params=None, fetch_one=False):
            return None

    class MockOrch:
        agents = {}

    mock_db = MockDB()
    from langgraph.state_persistence import StatePersistenceManager
    persistence = StatePersistenceManager(mock_db)
    processor = EventProcessor(MockOrch(), persistence)

    # Trigger mishandling
    result = await processor.handle_mishandling_detected(
        bag_id="BAG-004",
        event_data={
            "type": "delayed",
            "reason": "missed_connection",
            "detected_at": "ORD-ARRIVAL"
        },
        current_state=mock_state
    )

    print(f"\n   Mishandling Type: {result.get('type', 'Unknown')}")
    print(f"   New Status: {result.get('new_status', 'Unknown')}")
    print(f"   Action: {result.get('action', 'Unknown')}")

    print("\n💰 Processing compensation...")
    print("   → Root cause analysis initiated")
    print("   → Customer notification sent")
    print("   → Compensation calculated: $350")

    print("\n✅ Mishandling Workflow Complete!")


# =====================================================================
# DEMO 5: HUMAN APPROVAL WORKFLOW
# =====================================================================

async def demo_approval_workflow():
    """
    Demonstrate human-in-the-loop approval for high-value bags.

    Shows approval request, waiting, and resolution.
    """
    print("\n" + "=" * 70)
    print("DEMO 5: Human Approval Workflow")
    print("=" * 70)

    from langgraph.orchestrator_state import Intervention, ApprovalStatus
    import uuid

    print("\n💎 High-value bag detected (value: $7,500)")
    print("   → Requires supervisor approval for delivery")

    # Create approval request
    intervention = Intervention(
        intervention_id=str(uuid.uuid4()),
        action="deliver_high_value_bag",
        reason="Declared value: $7,500",
        priority=1,
        requires_approval=True,
        approval_status=ApprovalStatus.PENDING,
        approved_by=None,
        approved_at=None,
        executed=False,
        executed_at=None,
        result=None
    )

    print(f"\n📋 Approval Request Created")
    print(f"   ID: {intervention['intervention_id']}")
    print(f"   Action: {intervention['action']}")
    print(f"   Reason: {intervention['reason']}")
    print(f"   Status: {intervention['approval_status']}")

    print(f"\n📧 Notification sent to: supervisor@airline.com")
    print(f"   Timeout: 30 minutes")

    print(f"\n⏳ Waiting for approval...")
    await asyncio.sleep(1)  # Simulate wait

    # Simulate approval
    intervention["approval_status"] = ApprovalStatus.APPROVED
    intervention["approved_by"] = "supervisor@airline.com"
    intervention["approved_at"] = datetime.utcnow().isoformat()

    print(f"\n✅ Approval Received!")
    print(f"   Approved by: {intervention['approved_by']}")
    print(f"   Decision: {intervention['approval_status']}")
    print(f"\n   → Proceeding with bag delivery")


# =====================================================================
# DEMO 6: COMPLETE SYSTEM SIMULATION
# =====================================================================

async def demo_complete_system():
    """
    Demonstrate complete system with multiple bags being processed.

    Simulates realistic airport operations.
    """
    print("\n" + "=" * 70)
    print("DEMO 6: Complete System Simulation")
    print("=" * 70)

    from langgraph.orchestrator_state import create_initial_bag_state

    # Simulate multiple bags
    bags = [
        {
            "tag": "BAG001",
            "route": "JFK → LAX",
            "value": 200,
            "connection": False
        },
        {
            "tag": "BAG002",
            "route": "LAX → ORD → JFK",
            "value": 1500,
            "connection": True
        },
        {
            "tag": "BAG003",
            "route": "ORD → SFO",
            "value": 8000,
            "connection": False
        },
        {
            "tag": "BAG004",
            "route": "SFO → LAX",
            "value": 500,
            "connection": False
        }
    ]

    print(f"\n🏢 Airport Operations Dashboard")
    print(f"   Active Bags: {len(bags)}")
    print(f"   Status Overview:")

    for i, bag in enumerate(bags, 1):
        status = "in_flight" if i % 2 == 0 else "check_in"
        risk = "HIGH" if bag["value"] > 5000 else "MEDIUM" if bag["connection"] else "LOW"

        print(f"   [{i}] {bag['tag']}: {bag['route']}")
        print(f"       Status: {status} | Risk: {risk} | Value: ${bag['value']}")

    print(f"\n📊 System Metrics:")
    print(f"   Total Bags Processed Today: 1,247")
    print(f"   Average Risk Score: 23.5")
    print(f"   Mishandling Rate: 0.8%")
    print(f"   Pending Approvals: 3")

    print(f"\n✅ System Running Smoothly!")


# =====================================================================
# MAIN EXECUTION
# =====================================================================

async def main():
    """
    Run all demos.

    Uncomment specific demos to run individually.
    """
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "BAGGAGE ORCHESTRATOR DEMO" + " " * 28 + "║")
    print("║" + " " * 16 + "LangGraph State Machine" + " " * 29 + "║")
    print("╚" + "=" * 68 + "╝")

    try:
        # Run all demos
        await demo_simple_journey()
        await asyncio.sleep(1)

        await demo_connection_journey()
        await asyncio.sleep(1)

        await demo_event_processing()
        await asyncio.sleep(1)

        await demo_mishandling()
        await asyncio.sleep(1)

        await demo_approval_workflow()
        await asyncio.sleep(1)

        await demo_complete_system()

        print("\n" + "=" * 70)
        print("✅ All Demos Complete!")
        print("=" * 70)

        print("\n📚 Next Steps:")
        print("   1. Review docs/ORCHESTRATOR.md for full documentation")
        print("   2. Test with real agents and database")
        print("   3. Integrate with production systems")
        print("   4. Deploy monitoring dashboards")

        print("\n🚀 Happy Orchestrating!\n")

    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)


if __name__ == "__main__":
    # Run demos
    asyncio.run(main())
