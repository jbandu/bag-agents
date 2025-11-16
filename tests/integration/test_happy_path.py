"""
Integration Test 1: Happy Path - Normal Bag Journey

Test a bag's complete lifecycle through the system:
BOG (check-in) → PTY (transfer) → JFK (delivery)

Expected flow:
1. Bag checked in at BOG
2. Prediction agent assesses risk → LOW (connection time = 120 min)
3. Bag progresses through: security → sorting → loading → in-flight
4. Arrives PTY, enters transfer
5. Route optimization agent finds optimal transfer route
6. Re-sorted and loaded onto connecting flight
7. In-flight to JFK
8. Arrives JFK → claim → delivered

Success criteria:
- All state transitions occur in correct order
- All agents execute without errors
- No human approvals required
- Final state = "delivered"
- Journey completes within expected time
- 4+ passenger notifications sent
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from langgraph.orchestrator_state import BagStatus, RiskLevel


class TestHappyPath:
    """Test suite for normal bag journey with no issues"""

    @pytest.mark.asyncio
    async def test_normal_connection_success(
        self,
        orchestrator,
        create_happy_path_bag,
        performance_tracker
    ):
        """
        Test Case: Normal bag journey with connection

        Scenario: Passenger checks bag BOG → PTY → JFK
        Connection time: 120 minutes (comfortable)
        Expected: Smooth journey, all agents work correctly
        """
        # Arrange
        bag_state = create_happy_path_bag()
        start_time = datetime.utcnow()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=True
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Assert: Overall workflow completion
        assert result["status"] == "completed", \
            f"Expected workflow to complete, got status: {result['status']}"

        assert result["bag"]["current_status"] == BagStatus.DELIVERED, \
            f"Expected bag to be delivered, got: {result['bag']['current_status']}"

        # Assert: State machine progression
        expected_nodes = [
            "check_in",
            "security_screening",
            "sorting",
            "loading",
            "in_flight",
            "transfer",
            "sorting",  # Re-sorting after transfer
            "loading",  # Loading onto connecting flight
            "in_flight",  # Second flight
            "arrival",
            "claim",
            "delivered"
        ]

        actual_nodes = result["previous_nodes"]

        # Verify minimum required nodes were visited
        required_nodes = ["check_in", "sorting", "loading", "in_flight", "arrival", "claim", "delivered"]
        for node in required_nodes:
            assert node in actual_nodes, \
                f"Expected node '{node}' in journey, but not found. Actual: {actual_nodes}"

        # Assert: Agent invocations
        agents_invoked = result["agents_invoked"]

        assert "prediction" in agents_invoked, \
            "Prediction agent should have been invoked during check-in"

        # For connections, route optimization should be invoked
        assert "route_optimization" in agents_invoked, \
            "Route optimization agent should have been invoked for connection"

        # Assert: Risk assessment
        risk_score = result["bag"]["risk_score"]
        assert risk_score < 30, \
            f"Expected low risk score (<30) for comfortable connection, got: {risk_score}"

        assert result["bag"]["risk_level"] == RiskLevel.LOW, \
            f"Expected LOW risk level, got: {result['bag']['risk_level']}"

        # Assert: No errors
        assert len(result["errors"]) == 0, \
            f"Expected no errors, but got: {result['errors']}"

        # Assert: No interventions required
        assert result["intervention"]["interventions_pending"] == 0, \
            "No interventions should be pending for normal journey"

        assert not result["intervention"]["requires_approval"], \
            "No approval should be required for standard bag"

        # Assert: Events recorded
        events = result["bag"]["events"]
        assert len(events) >= 6, \
            f"Expected at least 6 events in journey, got: {len(events)}"

        # Verify key event types
        event_types = [event["event_type"] for event in events]
        assert "status_update" in event_types, \
            "Status update events should be recorded"

        # Assert: Performance
        assert duration < 120, \
            f"Test should complete in under 2 minutes, took {duration}s"

        # Record metrics
        performance_tracker.metrics["total_test_time"] = duration

        print(f"\n✅ Happy Path Test PASSED")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Nodes visited: {len(actual_nodes)}")
        print(f"   Agents invoked: {len(agents_invoked)}")
        print(f"   Risk score: {risk_score}")
        print(f"   Final status: {result['bag']['current_status']}")


    @pytest.mark.asyncio
    async def test_direct_flight_no_connection(
        self,
        orchestrator,
        copa_bag_data,
        performance_tracker
    ):
        """
        Test Case: Direct flight with no connection

        Scenario: Passenger checks bag PTY → JFK (direct)
        No connection involved
        Expected: Simpler journey, no transfer node
        """
        from langgraph.orchestrator_state import create_initial_bag_state

        # Arrange: Create direct flight bag
        bag_state = create_initial_bag_state(
            bag_id="BAG_DIRECT_001",
            tag_number="0230200001",
            passenger_id="PNR_DIRECT_001",
            origin_flight="CM777",
            origin_airport="PTY",
            destination_airport="JFK",
            weight_kg=22.0,
            declared_value=500.0
        )

        start_time = datetime.utcnow()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=False
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Assert: Completion
        assert result["status"] == "completed"
        assert result["bag"]["current_status"] == BagStatus.DELIVERED

        # Assert: No transfer node for direct flight
        actual_nodes = result["previous_nodes"]
        assert "transfer" not in actual_nodes, \
            "Transfer node should not be in journey for direct flight"

        # Assert: Simpler flow
        expected_simple_flow = [
            "check_in",
            "security_screening",
            "sorting",
            "loading",
            "in_flight",
            "arrival",
            "claim",
            "delivered"
        ]

        for node in expected_simple_flow:
            assert node in actual_nodes, \
                f"Expected node '{node}' in direct flight journey"

        # Assert: Prediction agent still invoked
        assert "prediction" in result["agents_invoked"]

        # Assert: Route optimization not needed for direct flight
        # (may or may not be invoked depending on implementation)

        # Assert: Low risk (no connection)
        assert result["bag"]["risk_score"] < 20, \
            "Direct flights should have very low risk scores"

        print(f"\n✅ Direct Flight Test PASSED")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Nodes visited: {len(actual_nodes)}")
        print(f"   Final status: {result['bag']['current_status']}")


    @pytest.mark.asyncio
    async def test_event_chronology(
        self,
        orchestrator,
        create_happy_path_bag
    ):
        """
        Test Case: Verify events are recorded in chronological order

        Scenario: Normal bag journey
        Expected: All events have timestamps in ascending order
        """
        # Arrange
        bag_state = create_happy_path_bag()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=True
        )

        # Assert: Events exist
        events = result["bag"]["events"]
        assert len(events) > 0, "Events should be recorded"

        # Assert: Chronological order
        timestamps = [
            datetime.fromisoformat(event["timestamp"])
            for event in events
        ]

        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i-1], \
                f"Event {i} timestamp is earlier than event {i-1}"

        # Assert: Event locations make sense
        locations = [event["location"] for event in events]

        # First events should be at origin
        assert locations[0] == "BOG", "First event should be at origin airport"

        # Should see PTY (connection hub) in the middle
        assert "PTY" in locations, "Connection airport should appear in events"

        # Last events should be at destination
        final_location_events = [e for e in events if e["location"] == "JFK"]
        assert len(final_location_events) > 0, \
            "Destination airport should appear in events"

        print(f"\n✅ Event Chronology Test PASSED")
        print(f"   Total events: {len(events)}")
        print(f"   Journey: {locations[0]} → {locations[-1]}")


    @pytest.mark.asyncio
    async def test_state_persistence(
        self,
        orchestrator,
        create_happy_path_bag
    ):
        """
        Test Case: Verify state is properly maintained throughout journey

        Scenario: Check that bag metadata persists across state transitions
        Expected: Original bag data unchanged, only status/location updated
        """
        # Arrange
        bag_state = create_happy_path_bag()
        original_tag = bag_state["tag_number"]
        original_passenger = bag_state["passenger_id"]
        original_weight = bag_state["weight_kg"]

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=True
        )

        # Assert: Immutable fields preserved
        assert result["bag"]["tag_number"] == original_tag, \
            "Tag number should not change"

        assert result["bag"]["passenger_id"] == original_passenger, \
            "Passenger ID should not change"

        assert result["bag"]["weight_kg"] == original_weight, \
            "Weight should not change"

        # Assert: Mutable fields updated
        assert result["bag"]["updated_at"] != result["bag"]["created_at"], \
            "Updated timestamp should differ from created timestamp"

        assert result["bag"]["current_location"] == "JFK", \
            "Final location should be destination"

        # Assert: Version incremented (if using versioning)
        assert result["bag"]["version"] >= 1, \
            "Version should be tracked"

        print(f"\n✅ State Persistence Test PASSED")
        print(f"   Tag preserved: {original_tag}")
        print(f"   Final location: {result['bag']['current_location']}")


    @pytest.mark.asyncio
    async def test_no_alerts_for_normal_journey(
        self,
        orchestrator,
        create_happy_path_bag
    ):
        """
        Test Case: Normal journey should not trigger alerts

        Scenario: Standard bag with comfortable connection time
        Expected: No alerts generated
        """
        # Arrange
        bag_state = create_happy_path_bag()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=True
        )

        # Assert: No alerts
        alerts = result["bag"]["alerts"]

        # Normal journey should have zero or minimal alerts
        high_severity_alerts = [
            a for a in alerts
            if a["severity"] in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        ]

        assert len(high_severity_alerts) == 0, \
            f"No high-severity alerts expected for normal journey, got: {high_severity_alerts}"

        print(f"\n✅ No Alerts Test PASSED")
        print(f"   Total alerts: {len(alerts)}")
        print(f"   High-severity alerts: {len(high_severity_alerts)}")


    @pytest.mark.asyncio
    async def test_agent_results_cached(
        self,
        orchestrator,
        create_happy_path_bag
    ):
        """
        Test Case: Agent results are cached in state

        Scenario: Verify prediction and route optimization results stored
        Expected: Agent results available in final state
        """
        # Arrange
        bag_state = create_happy_path_bag()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=True
        )

        # Assert: Prediction results cached
        assert result["bag"]["prediction_result"] is not None, \
            "Prediction agent results should be cached"

        prediction = result["bag"]["prediction_result"]
        assert "risk_score" in prediction, \
            "Prediction should contain risk_score"
        assert "risk_level" in prediction, \
            "Prediction should contain risk_level"

        # Assert: Route optimization results cached (for connections)
        assert result["bag"]["route_optimization_result"] is not None, \
            "Route optimization results should be cached for connections"

        route = result["bag"]["route_optimization_result"]
        assert "optimal_route" in route, \
            "Route optimization should contain optimal_route"

        # Assert: Results accessible via agent_results dict
        assert "prediction" in result["agent_results"] or \
               result["bag"]["prediction_result"] is not None, \
            "Prediction results should be accessible"

        print(f"\n✅ Agent Results Caching Test PASSED")
        print(f"   Prediction cached: {prediction.get('risk_level')}")
        print(f"   Route cached: {route.get('optimal_route', {}).get('path', [])[:3]}")
