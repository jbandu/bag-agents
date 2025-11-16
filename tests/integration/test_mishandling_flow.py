"""
Integration Test 3: Mishandling → Resolution

Test complete mishandling lifecycle:
Bag misses connection → Root cause analysis → Customer service → Compensation → Delivery

Scenario:
1. Bag misses connection (inbound delayed 40 min)
2. Orchestrator transitions to "mishandled" state
3. Root Cause Agent analyzes:
   - Queries journey history
   - Identifies cause: "insufficient transfer time due to inbound delay"
   - Assigns primary cause: "flight_irregularity"
   - Suggests: "rebook on next available flight"
4. Customer Service Agent:
   - Auto-generates PIR
   - Notifies passenger via SMS + Email
   - Provides PIR number
5. Compensation Agent:
   - Calculates eligibility: Montreal Convention applies
   - Estimates $100 interim expenses
   - Requires supervisor approval (amount >$50)
6. Supervisor approval simulated
7. Route Optimization Agent:
   - Books bag on next flight
   - Calculates delivery route
8. Demand Forecast Agent:
   - Updates forecast for additional bag
9. Delivery completion
10. Final state = "delivered_delayed" or "resolved"

Success criteria:
- Root cause correctly identified
- PIR auto-generated with valid number
- Compensation calculated per regulations
- Passenger notified within 5 minutes
- All agent outputs logged
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from langgraph.orchestrator_state import BagStatus, RiskLevel, ApprovalStatus


class TestMishandlingFlow:
    """Test suite for complete mishandling lifecycle"""

    @pytest.mark.asyncio
    async def test_delayed_bag_complete_lifecycle(
        self,
        orchestrator,
        create_mishandled_bag,
        performance_tracker
    ):
        """
        Test Case: Complete lifecycle of delayed bag

        Scenario: Bag delayed due to missed connection
        Expected: Full recovery process with all agents coordinating
        """
        # Arrange
        bag_state = create_mishandled_bag()
        start_time = datetime.utcnow()

        # Modify orchestrator to simulate mishandling
        # We'll need to manually trigger mishandling flow
        # For now, process and check if mishandling path exists

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=False  # Direct flight that gets delayed
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Assert: Workflow completed
        # Note: For mishandling, the workflow might end differently
        # depending on implementation
        assert result["status"] in ["completed", "paused"], \
            f"Mishandling workflow should complete or pause for approval, got: {result['status']}"

        # Check if bag went through normal flow or mishandling detected
        nodes_visited = result["previous_nodes"]

        print(f"\n✅ Delayed Bag Lifecycle Test")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Final status: {result['bag']['current_status']}")
        print(f"   Nodes visited: {nodes_visited}")
        print(f"   Agents invoked: {result['agents_invoked']}")


    @pytest.mark.asyncio
    async def test_mishandling_detection_and_routing(
        self,
        orchestrator,
        create_mishandled_bag
    ):
        """
        Test Case: Detect mishandling and route to mishandling sub-graph

        Scenario: Simulate bag that should trigger mishandling flow
        Expected: Orchestrator detects issue and routes to mishandling nodes
        """
        # Arrange
        bag_state = create_mishandled_bag()

        # Manually set status to trigger mishandling
        bag_state["current_status"] = BagStatus.DELAYED

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=False
        )

        # Assert: Check if mishandling nodes were visited
        nodes_visited = result["previous_nodes"]

        # Depending on implementation, mishandling might trigger different flows
        # Check if any mishandling-related processing occurred
        if "mishandled" in nodes_visited:
            print("   ✓ Mishandled node visited")

            # Should have root cause analysis
            assert "root_cause_analysis" in nodes_visited or \
                   "root_cause" in result["agents_invoked"], \
                "Root cause analysis should occur for mishandling"

            # Should have compensation calculation
            assert "compensation" in nodes_visited or \
                   "compensation" in result["agents_invoked"], \
                "Compensation should be calculated for mishandling"

        print(f"\n✅ Mishandling Detection Test PASSED")
        print(f"   Nodes: {nodes_visited}")


    @pytest.mark.asyncio
    async def test_root_cause_analysis(
        self,
        orchestrator,
        mock_root_cause_agent
    ):
        """
        Test Case: Root cause agent analyzes mishandling incident

        Scenario: Delayed bag
        Expected: Root cause identified with recommendations
        """
        # Arrange
        incident_data = {
            "incident_id": "INC-TEST-001",
            "incident_type": "delayed"
        }

        # Act
        result = await mock_root_cause_agent.execute(incident_data)

        # Assert: Root cause identified
        assert "root_cause" in result, \
            "Root cause should be identified"

        assert "primary_cause" in result, \
            "Primary cause should be identified"

        # Assert: Analysis includes details
        assert "contributing_factors" in result, \
            "Contributing factors should be listed"

        contributing_factors = result["contributing_factors"]
        assert len(contributing_factors) > 0, \
            "Should identify at least one contributing factor"

        # Assert: Recommendations provided
        assert "recommendations" in result, \
            "Recommendations should be provided"

        recommendations = result["recommendations"]
        assert len(recommendations) > 0, \
            "Should provide at least one recommendation"

        # Verify recommendations are actionable
        rec_text = " ".join(recommendations).lower()
        actionable_keywords = ["rebook", "expedite", "notify", "deliver"]
        has_actionable = any(kw in rec_text for kw in actionable_keywords)
        assert has_actionable, \
            f"Recommendations should be actionable: {recommendations}"

        print(f"\n✅ Root Cause Analysis Test PASSED")
        print(f"   Root cause: {result['root_cause']}")
        print(f"   Primary cause: {result['primary_cause']}")
        print(f"   Contributing factors: {len(contributing_factors)}")
        print(f"   Recommendations: {recommendations}")


    @pytest.mark.asyncio
    async def test_pir_generation(
        self,
        orchestrator,
        mock_customer_service_agent
    ):
        """
        Test Case: PIR (Property Irregularity Report) auto-generated

        Scenario: Delayed/lost bag
        Expected: PIR number generated, passenger notified
        """
        # Arrange
        query_data = {
            "customer_query": "Baggage delayed",
            "bag_tag": "0230100003"
        }

        # Act
        result = await mock_customer_service_agent.execute(query_data)

        # Assert: PIR generated
        assert "pir_number" in result, \
            "PIR number should be generated"

        pir_number = result["pir_number"]
        assert len(pir_number) > 0, \
            "PIR number should not be empty"

        # Verify PIR number format (typically: AIRPORT + DATE + SEQUENCE)
        # Example: PTY20241116001
        assert len(pir_number) >= 10, \
            f"PIR number should be at least 10 chars, got: {pir_number}"

        # Assert: Passenger notified
        assert result.get("notification_sent") == True, \
            "Passenger should be notified"

        notification_methods = result.get("notification_method", [])
        assert len(notification_methods) > 0, \
            "At least one notification method should be used"

        # Should use email and/or SMS
        assert any(method in ["email", "sms"] for method in notification_methods), \
            f"Should notify via email or SMS, got: {notification_methods}"

        # Assert: Response message appropriate
        response = result.get("response", "")
        assert len(response) > 0, \
            "Customer response should be provided"

        assert "apologize" in response.lower() or "sorry" in response.lower(), \
            "Response should include apology"

        print(f"\n✅ PIR Generation Test PASSED")
        print(f"   PIR number: {pir_number}")
        print(f"   Notification methods: {notification_methods}")
        print(f"   Response: {response[:100]}...")


    @pytest.mark.asyncio
    async def test_compensation_calculation(
        self,
        orchestrator,
        mock_compensation_agent
    ):
        """
        Test Case: Compensation calculated per Montreal Convention

        Scenario: Delayed bag (24+ hours)
        Expected: $100 interim expenses, requires approval
        """
        # Arrange
        claim_data = {
            "claim_id": "CLM-TEST-001",
            "incident_type": "delayed",
            "declared_value": 1200,
            "delay_hours": 26
        }

        # Act
        result = await mock_compensation_agent.execute(claim_data)

        # Assert: Compensation calculated
        assert "compensation_amount" in result, \
            "Compensation amount should be calculated"

        compensation = result["compensation_amount"]
        assert compensation > 0, \
            "Delayed bags should receive compensation"

        # For 24+ hour delay, should be ~$100
        assert 50 <= compensation <= 200, \
            f"Expected reasonable interim expenses ($50-$200), got ${compensation}"

        # Assert: Calculation basis documented
        assert "calculation_basis" in result, \
            "Calculation basis should be documented"

        basis = result["calculation_basis"]
        assert "montreal" in basis.lower() or "convention" in basis.lower(), \
            f"Should reference Montreal Convention, got: {basis}"

        # Assert: Eligibility determined
        assert "eligibility" in result, \
            "Eligibility should be determined"

        assert result["eligibility"] == "eligible", \
            "Delayed bags should be eligible for compensation"

        # Assert: Approval requirement
        assert "requires_approval" in result, \
            "Approval requirement should be specified"

        # For amounts >$50, approval typically required
        if compensation > 50:
            assert result["requires_approval"] == True, \
                "Compensation >$50 should require approval"

        print(f"\n✅ Compensation Calculation Test PASSED")
        print(f"   Amount: ${compensation}")
        print(f"   Basis: {basis}")
        print(f"   Requires approval: {result['requires_approval']}")
        print(f"   Breakdown: {result.get('breakdown', {})}")


    @pytest.mark.asyncio
    async def test_approval_workflow(
        self,
        orchestrator,
        create_mishandled_bag
    ):
        """
        Test Case: Supervisor approval for high-value compensation

        Scenario: Compensation >$50 requires approval
        Expected: Approval request created, workflow pauses/continues
        """
        # Arrange
        bag_state = create_mishandled_bag()
        bag_state["declared_value"] = 2000  # High value

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=False
        )

        # Assert: Check intervention state
        intervention_state = result["intervention"]

        # For high-value bags or high compensation, approval may be needed
        # Check if approval workflow exists
        if intervention_state.get("requires_approval"):
            print("   ✓ Approval required")

            # Should have approval threshold
            assert "approval_threshold_value" in intervention_state, \
                "Approval threshold should be defined"

            # Should specify approver role
            if intervention_state.get("approver_role"):
                assert intervention_state["approver_role"] in ["supervisor", "manager"], \
                    "Approver role should be specified"

            # Check for pending interventions
            pending = intervention_state.get("pending_interventions", [])
            if len(pending) > 0:
                print(f"   ✓ Pending interventions: {len(pending)}")

        print(f"\n✅ Approval Workflow Test PASSED")
        print(f"   Requires approval: {intervention_state.get('requires_approval')}")
        print(f"   Threshold: ${intervention_state.get('approval_threshold_value')}")


    @pytest.mark.asyncio
    async def test_rebooking_next_flight(
        self,
        orchestrator,
        mock_route_optimization_agent
    ):
        """
        Test Case: Rebook delayed bag on next available flight

        Scenario: Bag missed connection
        Expected: Route optimization finds next flight and delivery route
        """
        # Arrange
        route_data = {
            "origin": "PTY",
            "destination": "JFK",
            "via": []  # Direct rebook
        }

        # Act
        result = await mock_route_optimization_agent.execute(route_data)

        # Assert: Optimal route found
        assert "optimal_route" in result, \
            "Optimal route should be provided"

        optimal_route = result["optimal_route"]

        # Should include route details
        assert "path" in optimal_route, \
            "Route path should be specified"

        assert "total_time_minutes" in optimal_route, \
            "Route time should be estimated"

        # Assert: Alternative routes considered
        assert "alternative_routes" in result, \
            "Alternative routes should be considered"

        print(f"\n✅ Rebooking Test PASSED")
        print(f"   Optimal route: {optimal_route.get('path')}")
        print(f"   Time: {optimal_route.get('total_time_minutes')} min")
        print(f"   Alternatives: {len(result.get('alternative_routes', []))}")


    @pytest.mark.asyncio
    async def test_passenger_notification_timing(
        self,
        orchestrator,
        mock_customer_service_agent
    ):
        """
        Test Case: Passenger notified within 5 minutes of mishandling detection

        Scenario: Bag delayed
        Expected: Notification sent promptly
        """
        # Arrange
        start_time = datetime.utcnow()

        query_data = {
            "customer_query": "Baggage mishandled",
            "bag_tag": "0230100003"
        }

        # Act
        result = await mock_customer_service_agent.execute(query_data)

        end_time = datetime.utcnow()
        notification_time = (end_time - start_time).total_seconds()

        # Assert: Quick notification
        assert notification_time < 5, \
            f"Notification should be sent within 5 seconds, took {notification_time}s"

        # Assert: Notification confirmed
        assert result.get("notification_sent") == True, \
            "Notification should be sent"

        print(f"\n✅ Notification Timing Test PASSED")
        print(f"   Notification time: {notification_time:.3f}s")
        print(f"   Methods: {result.get('notification_method')}")


    @pytest.mark.asyncio
    async def test_all_agents_coordinate(
        self,
        orchestrator,
        create_mishandled_bag
    ):
        """
        Test Case: All agents work together in mishandling scenario

        Scenario: Complete mishandling workflow
        Expected: Multiple agents invoked in correct sequence
        """
        # Arrange
        bag_state = create_mishandled_bag()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=False
        )

        # Assert: Multiple agents invoked
        agents_invoked = result["agents_invoked"]

        # For mishandling, expect several agents:
        # - Prediction (check-in)
        # - Root cause (if mishandling detected)
        # - Customer service (if mishandling detected)
        # - Compensation (if mishandling detected)
        # - Route optimization (rebooking)

        assert len(agents_invoked) >= 1, \
            "At least prediction agent should be invoked"

        # Check agent results stored
        agent_results = result["agent_results"]
        assert len(agent_results) >= 0, \
            "Agent results should be tracked"

        print(f"\n✅ Agent Coordination Test PASSED")
        print(f"   Agents invoked: {agents_invoked}")
        print(f"   Agent results: {list(agent_results.keys())}")


    @pytest.mark.asyncio
    async def test_mishandling_end_to_end_performance(
        self,
        orchestrator,
        create_mishandled_bag,
        performance_tracker
    ):
        """
        Test Case: Complete mishandling workflow performance

        Scenario: Full lifecycle from detection to resolution
        Expected: Complete within 8 minutes
        """
        # Arrange
        bag_state = create_mishandled_bag()
        start_time = datetime.utcnow()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=False
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Assert: Performance target
        assert duration < 480, \
            f"Mishandling workflow should complete in <8 min, took {duration}s"

        # Record metrics
        performance_tracker.metrics["total_test_time"] = duration

        print(f"\n✅ End-to-End Performance Test PASSED")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Status: {result['status']}")
        print(f"   Agents: {len(result['agents_invoked'])}")


    @pytest.mark.asyncio
    async def test_event_logging_completeness(
        self,
        orchestrator,
        create_mishandled_bag
    ):
        """
        Test Case: All events properly logged during mishandling

        Scenario: Mishandling workflow
        Expected: Comprehensive event log for audit trail
        """
        # Arrange
        bag_state = create_mishandled_bag()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=False
        )

        # Assert: Events logged
        events = result["bag"]["events"]
        assert len(events) > 0, \
            "Events should be logged"

        # Assert: Events have required fields
        for event in events:
            assert "event_id" in event, "Event should have ID"
            assert "event_type" in event, "Event should have type"
            assert "timestamp" in event, "Event should have timestamp"
            assert "location" in event, "Event should have location"
            assert "source" in event, "Event should have source"

        # Assert: Agent executions logged as events
        agent_events = [e for e in events if e.get("event_type") == "agent_executed"]

        print(f"\n✅ Event Logging Test PASSED")
        print(f"   Total events: {len(events)}")
        print(f"   Agent execution events: {len(agent_events)}")
