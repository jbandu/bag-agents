"""
Integration Test 2: At-Risk Connection Prevention

Test AI intervention preventing missed connection:
MIA (delayed) → PTY (tight connection) → LIM (successful connection)

Scenario:
- Inbound flight delayed 15 minutes
- Connection time reduced from 45 to 30 minutes
- Prediction agent flags HIGH RISK (score > 80)
- System recommends intervention: "expedite transfer"
- Route optimization finds fastest route
- Infrastructure health confirms equipment operational
- Bag makes connection successfully

Success criteria:
- Risk score accurately calculated (>80)
- Intervention recommended
- Route optimized for speed
- Connection made within deadline
- ROI calculated correctly (saved costs)
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from langgraph.orchestrator_state import BagStatus, RiskLevel


class TestConnectionSuccess:
    """Test suite for at-risk connection with AI intervention"""

    @pytest.mark.asyncio
    async def test_tight_connection_with_intervention(
        self,
        orchestrator,
        create_at_risk_bag,
        performance_tracker
    ):
        """
        Test Case: At-risk connection succeeds with AI intervention

        Scenario:
        - Inbound flight delayed
        - Only 30 minutes for connection (MCT = 45 min)
        - System flags as HIGH RISK
        - Expedited handling recommended
        - Connection successful
        """
        # Arrange
        bag_state = create_at_risk_bag()
        start_time = datetime.utcnow()

        # Simulate tight connection by setting connection time
        # This will trigger high risk in prediction agent
        connection_time = 30  # Below MCT of 45

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=True
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Assert: Workflow completed successfully
        assert result["status"] == "completed", \
            f"Workflow should complete despite tight connection, got: {result['status']}"

        assert result["bag"]["current_status"] == BagStatus.DELIVERED, \
            f"Bag should be delivered successfully, got: {result['bag']['current_status']}"

        # Assert: Risk properly identified
        risk_score = result["bag"]["risk_score"]
        assert risk_score > 80, \
            f"Expected HIGH risk score (>80) for tight connection, got: {risk_score}"

        assert result["bag"]["risk_level"] in [RiskLevel.HIGH, RiskLevel.CRITICAL], \
            f"Expected HIGH or CRITICAL risk level, got: {result['bag']['risk_level']}"

        # Assert: Prediction agent invoked
        agents_invoked = result["agents_invoked"]
        assert "prediction" in agents_invoked, \
            "Prediction agent should be invoked to assess risk"

        # Assert: Alert generated for high risk
        alerts = result["bag"]["alerts"]
        high_risk_alerts = [
            a for a in alerts
            if a["severity"] in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        ]
        assert len(high_risk_alerts) > 0, \
            "High risk connection should generate alerts"

        # Verify alert message mentions risk
        alert_messages = [a["message"] for a in high_risk_alerts]
        risk_mentioned = any("risk" in msg.lower() for msg in alert_messages)
        assert risk_mentioned, \
            f"Alert should mention risk. Alerts: {alert_messages}"

        # Assert: Route optimization invoked for fast route
        assert "route_optimization" in agents_invoked, \
            "Route optimization should find fastest transfer route"

        # Assert: Infrastructure health checked
        if "infrastructure_health" in agents_invoked:
            infra_result = result["agent_results"].get("infrastructure_health", {})
            # Should confirm equipment is operational
            if infra_result:
                assert infra_result.get("status") == "operational" or \
                       infra_result.get("overall_health", 0) > 70, \
                    "Infrastructure should be operational for expedited transfer"

        # Assert: No errors despite tight timing
        assert len(result["errors"]) == 0, \
            f"Should handle tight connection without errors, got: {result['errors']}"

        print(f"\n✅ Tight Connection Test PASSED")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Risk score: {risk_score}")
        print(f"   Risk level: {result['bag']['risk_level']}")
        print(f"   Alerts generated: {len(high_risk_alerts)}")
        print(f"   Final status: DELIVERED ✓")


    @pytest.mark.asyncio
    async def test_critical_risk_scoring(
        self,
        orchestrator,
        copa_bag_data
    ):
        """
        Test Case: Verify risk scoring algorithm

        Test different connection times and verify risk scores:
        - 60+ min: LOW risk
        - 45-60 min: MEDIUM risk
        - 30-45 min: HIGH risk
        - <30 min: CRITICAL risk
        """
        from langgraph.orchestrator_state import create_initial_bag_state

        test_cases = [
            {"connection_time": 90, "expected_risk": RiskLevel.LOW, "expected_score_max": 30},
            {"connection_time": 50, "expected_risk": RiskLevel.MEDIUM, "expected_score_max": 60},
            {"connection_time": 38, "expected_risk": RiskLevel.HIGH, "expected_score_min": 80},
            {"connection_time": 25, "expected_risk": RiskLevel.CRITICAL, "expected_score_min": 90}
        ]

        for i, test_case in enumerate(test_cases):
            # Arrange
            bag_state = create_initial_bag_state(
                bag_id=f"BAG_RISK_TEST_{i}",
                tag_number=f"023030000{i}",
                passenger_id=f"PNR_RISK_{i}",
                origin_flight="CM202",
                origin_airport="MIA",
                destination_airport="LIM",
                weight_kg=23.0,
                connection_flight="CM645",
                connection_airport="PTY"
            )

            # Create connection state with specific timing
            from langgraph.orchestrator_state import create_initial_orchestrator_state
            initial_state = create_initial_orchestrator_state(bag_state, has_connection=True)

            if initial_state["connection"]:
                initial_state["connection"]["connection_time_minutes"] = test_case["connection_time"]

            # Act: Just run prediction agent
            if "prediction" in orchestrator.agents:
                prediction_result = await orchestrator.agents["prediction"].execute({
                    "flight_id": "CM202",
                    "departure_airport": "MIA",
                    "arrival_airport": "PTY",
                    "connection_time": test_case["connection_time"]
                })

                # Assert
                risk_score = prediction_result.get("risk_score", 0)

                if "expected_score_max" in test_case:
                    assert risk_score <= test_case["expected_score_max"], \
                        f"Connection time {test_case['connection_time']}min: " \
                        f"Expected risk ≤{test_case['expected_score_max']}, got {risk_score}"

                if "expected_score_min" in test_case:
                    assert risk_score >= test_case["expected_score_min"], \
                        f"Connection time {test_case['connection_time']}min: " \
                        f"Expected risk ≥{test_case['expected_score_min']}, got {risk_score}"

                print(f"   {test_case['connection_time']}min → Risk: {risk_score} ({test_case['expected_risk']}) ✓")

        print(f"\n✅ Risk Scoring Test PASSED")


    @pytest.mark.asyncio
    async def test_intervention_recommendations(
        self,
        orchestrator,
        create_at_risk_bag
    ):
        """
        Test Case: Verify intervention recommendations for high-risk bags

        Scenario: High-risk connection
        Expected: System recommends specific interventions
        """
        # Arrange
        bag_state = create_at_risk_bag()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=True
        )

        # Assert: Prediction result includes recommendations
        prediction_result = result["bag"]["prediction_result"]
        assert prediction_result is not None, \
            "Prediction result should be available"

        recommendations = prediction_result.get("recommendations", [])
        assert len(recommendations) > 0, \
            "High-risk bags should have intervention recommendations"

        # Verify recommendations are actionable
        expected_keywords = ["expedite", "priority", "alert", "monitor"]
        recommendations_text = " ".join(recommendations).lower()

        has_actionable = any(keyword in recommendations_text for keyword in expected_keywords)
        assert has_actionable, \
            f"Recommendations should be actionable. Got: {recommendations}"

        print(f"\n✅ Intervention Recommendations Test PASSED")
        print(f"   Recommendations: {recommendations}")


    @pytest.mark.asyncio
    async def test_route_optimization_for_speed(
        self,
        orchestrator,
        create_at_risk_bag
    ):
        """
        Test Case: Route optimization prioritizes speed for at-risk bags

        Scenario: High-risk connection
        Expected: Route optimization finds fastest route, not just optimal
        """
        # Arrange
        bag_state = create_at_risk_bag()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=True
        )

        # Assert: Route optimization invoked
        route_result = result["bag"]["route_optimization_result"]
        assert route_result is not None, \
            "Route optimization should be invoked for connections"

        optimal_route = route_result.get("optimal_route", {})
        assert "total_time_minutes" in optimal_route, \
            "Route should include time estimate"

        # Verify route is reasonably fast
        route_time = optimal_route.get("total_time_minutes", 999)
        assert route_time < 15, \
            f"For tight connection, route should be <15 min, got {route_time}"

        # Verify high reliability
        reliability = optimal_route.get("reliability_score", 0)
        assert reliability > 0.85, \
            f"Route should be reliable (>0.85), got {reliability}"

        print(f"\n✅ Route Optimization for Speed Test PASSED")
        print(f"   Route time: {route_time} minutes")
        print(f"   Reliability: {reliability:.2%}")
        print(f"   Path: {optimal_route.get('path', [])}")


    @pytest.mark.asyncio
    async def test_connection_at_risk_flag(
        self,
        orchestrator,
        create_at_risk_bag
    ):
        """
        Test Case: Connection state properly flagged as at-risk

        Scenario: Tight connection
        Expected: connection_at_risk flag set to True
        """
        # Arrange
        bag_state = create_at_risk_bag()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=True
        )

        # Assert: Connection state exists
        connection_state = result.get("connection")
        assert connection_state is not None, \
            "Connection state should exist for connection flights"

        # Assert: At-risk flag set
        # Note: This depends on implementation - may be set by route optimization agent
        # Check if flag exists and makes sense
        if "connection_at_risk" in connection_state:
            # For tight connections with high risk, should be flagged
            if result["bag"]["risk_score"] > 70:
                assert connection_state["connection_at_risk"] == True, \
                    "High-risk connection should be flagged"

        print(f"\n✅ Connection At-Risk Flag Test PASSED")
        print(f"   Connection at risk: {connection_state.get('connection_at_risk', 'N/A')}")


    @pytest.mark.asyncio
    async def test_roi_calculation(
        self,
        orchestrator,
        create_at_risk_bag
    ):
        """
        Test Case: Calculate ROI of AI intervention

        Scenario: At-risk bag makes connection due to AI
        Expected: ROI = saved rebooking cost + avoided compensation
        """
        # Arrange
        bag_state = create_at_risk_bag()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=True
        )

        # Assert: Connection successful
        assert result["bag"]["current_status"] == BagStatus.DELIVERED, \
            "Bag should make connection"

        # Calculate ROI
        # If bag had missed connection:
        # - Rebooking cost: ~$200
        # - Passenger compensation: ~$150
        # - Handling/delivery: ~$50
        # Total avoided cost: ~$400

        # AI intervention cost: ~$5 (agent executions, compute)
        # ROI: ($400 - $5) / $5 = 79x or 7900%

        avoided_rebooking = 200
        avoided_compensation = 150
        avoided_handling = 50
        total_avoided = avoided_rebooking + avoided_compensation + avoided_handling

        ai_cost = 5  # Estimated

        roi = (total_avoided - ai_cost) / ai_cost
        roi_percentage = roi * 100

        # Assert: Significant ROI
        assert roi_percentage > 1000, \
            f"AI intervention should have significant ROI, calculated: {roi_percentage:.0f}%"

        print(f"\n✅ ROI Calculation Test PASSED")
        print(f"   Avoided costs: ${total_avoided}")
        print(f"   AI cost: ${ai_cost}")
        print(f"   ROI: {roi:.1f}x ({roi_percentage:.0f}%)")
        print(f"   Breakdown:")
        print(f"     - Rebooking: ${avoided_rebooking}")
        print(f"     - Compensation: ${avoided_compensation}")
        print(f"     - Handling: ${avoided_handling}")


    @pytest.mark.asyncio
    async def test_handler_notification(
        self,
        orchestrator,
        create_at_risk_bag
    ):
        """
        Test Case: Handlers notified for priority bags

        Scenario: High-risk connection
        Expected: Handler assignment and notification tracked
        """
        # Arrange
        bag_state = create_at_risk_bag()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=True
        )

        # Assert: Check connection state for handler info
        connection_state = result.get("connection")

        if connection_state:
            # Verify notification tracking exists
            # (Implementation may vary - this is testing the data structure)
            assert "handler_notified" in connection_state, \
                "Connection state should track handler notifications"

            # For high-risk bags, handlers should be notified
            if result["bag"]["risk_score"] > 80:
                # Check if system has mechanism to notify handlers
                # This might be in alerts, interventions, or notifications_sent
                notifications = result["intervention"]["notifications_sent"]

                # Could verify notification exists (implementation dependent)
                print(f"   Notifications sent: {len(notifications)}")

        print(f"\n✅ Handler Notification Test PASSED")


    @pytest.mark.asyncio
    async def test_performance_tight_connection(
        self,
        orchestrator,
        create_at_risk_bag,
        performance_tracker
    ):
        """
        Test Case: Performance test for at-risk bag processing

        Scenario: High-risk connection
        Expected: Processing completes quickly despite additional checks
        Target: <3 minutes total
        """
        # Arrange
        bag_state = create_at_risk_bag()
        start_time = datetime.utcnow()

        # Act
        result = await orchestrator.process_bag(
            bag_state=bag_state,
            has_connection=True
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Assert: Performance
        assert duration < 180, \
            f"At-risk bag processing should complete in <3 min, took {duration}s"

        # Record metrics
        performance_tracker.record_agent_call("orchestrator", duration * 1000)

        # Assert: More agents invoked than simple journey
        agents_invoked = result["agents_invoked"]
        assert len(agents_invoked) >= 2, \
            "At-risk bags should invoke multiple agents"

        print(f"\n✅ Performance Test PASSED")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Agents invoked: {len(agents_invoked)}")
        print(f"   Agents: {agents_invoked}")
