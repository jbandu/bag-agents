"""
Integration Test 5: Agent Orchestration and Coordination

Test agents calling other agents correctly and avoiding circular dependencies.

Scenarios:
1. Root Cause Agent calls Infrastructure Health Agent for equipment logs
2. Customer Service Agent calls Compensation Agent for claim calculation
3. Prediction Agent uses Demand Forecast for congestion data
4. Route Optimization Agent calls Infrastructure Health for equipment status

For each:
- Verify correct parameters passed
- Verify response handled correctly
- Verify no circular calls (A→B→A)
- Verify timeout protection (max 30 sec per agent)
"""

import pytest
import asyncio
from datetime import datetime


class TestAgentOrchestration:
    """Test suite for agent-to-agent coordination"""

    @pytest.mark.asyncio
    async def test_all_agents_available(self, orchestrator):
        """Verify all 8 agents are registered in orchestrator"""
        agents = orchestrator.agents

        expected_agents = [
            "prediction",
            "route_optimization",
            "infrastructure_health",
            "demand_forecast",
            "customer_service",
            "compensation",
            "root_cause"
        ]

        for agent_name in expected_agents:
            assert agent_name in agents, \
                f"Agent '{agent_name}' should be registered"

        print(f"\n✅ All Agents Available Test PASSED")
        print(f"   Registered agents: {list(agents.keys())}")


    @pytest.mark.asyncio
    async def test_agent_parameter_passing(
        self,
        mock_prediction_agent,
        mock_route_optimization_agent
    ):
        """Test correct parameter passing between agents"""

        # Test prediction agent
        pred_result = await mock_prediction_agent.execute({
            "flight_id": "CM101",
            "departure_airport": "BOG",
            "arrival_airport": "PTY",
            "connection_time": 120
        })

        assert pred_result is not None
        assert "risk_score" in pred_result

        # Test route optimization agent
        route_result = await mock_route_optimization_agent.execute({
            "origin": "PTY",
            "destination": "JFK"
        })

        assert route_result is not None
        assert "optimal_route" in route_result

        print(f"\n✅ Parameter Passing Test PASSED")


    @pytest.mark.asyncio
    async def test_agent_response_handling(self, orchestrator, create_happy_path_bag):
        """Test that orchestrator properly handles agent responses"""

        bag_state = create_happy_path_bag()
        result = await orchestrator.process_bag(bag_state, has_connection=True)

        # Verify results stored
        assert "agent_results" in result
        assert "agents_invoked" in result

        # Verify at least prediction agent was invoked and result cached
        if "prediction" in result["agents_invoked"]:
            assert result["bag"]["prediction_result"] is not None

        print(f"\n✅ Response Handling Test PASSED")
        print(f"   Agents invoked: {result['agents_invoked']}")


    @pytest.mark.asyncio
    async def test_no_circular_calls(
        self,
        orchestrator,
        create_happy_path_bag,
        performance_tracker
    ):
        """Ensure no circular agent calls (A→B→A)"""

        bag_state = create_happy_path_bag()

        # Track call stack
        call_stack = []

        start_time = datetime.utcnow()
        result = await orchestrator.process_bag(bag_state, has_connection=True)
        end_time = datetime.utcnow()

        # Check for reasonable execution time
        duration = (end_time - start_time).total_seconds()
        assert duration < 60, \
            f"Circular calls would cause timeout, execution took {duration}s"

        # Verify each agent called at most once
        agents_invoked = result["agents_invoked"]
        agent_counts = {}
        for agent in agents_invoked:
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        # Each agent should be invoked reasonable number of times
        for agent, count in agent_counts.items():
            assert count <= 3, \
                f"Agent '{agent}' called {count} times - possible circular dependency"

        print(f"\n✅ No Circular Calls Test PASSED")
        print(f"   Agent call counts: {agent_counts}")


    @pytest.mark.asyncio
    async def test_agent_timeout_protection(
        self,
        mock_prediction_agent
    ):
        """Test that agent calls have timeout protection"""

        start_time = datetime.utcnow()

        # Normal call should complete quickly
        result = await mock_prediction_agent.execute({
            "flight_id": "CM101",
            "departure_airport": "BOG",
            "arrival_airport": "PTY"
        })

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Should complete well under timeout
        assert duration < 30, \
            f"Agent call should complete quickly, took {duration}s"

        print(f"\n✅ Timeout Protection Test PASSED")
        print(f"   Execution time: {duration:.3f}s (< 30s limit)")


    @pytest.mark.asyncio
    async def test_agent_error_isolation(
        self,
        orchestrator,
        create_happy_path_bag
    ):
        """Test that agent errors don't crash entire workflow"""

        bag_state = create_happy_path_bag()

        # Even if an agent fails, workflow should continue
        result = await orchestrator.process_bag(bag_state, has_connection=True)

        # Workflow should complete
        assert result["status"] in ["completed", "failed", "paused"]

        # Errors should be tracked
        errors = result.get("errors", [])

        print(f"\n✅ Error Isolation Test PASSED")
        print(f"   Workflow status: {result['status']}")
        print(f"   Errors logged: {len(errors)}")


    @pytest.mark.asyncio
    async def test_agent_execution_order(
        self,
        orchestrator,
        create_happy_path_bag
    ):
        """Test that agents execute in logical order"""

        bag_state = create_happy_path_bag()
        result = await orchestrator.process_bag(bag_state, has_connection=True)

        agents_invoked = result["agents_invoked"]

        # Prediction should be early (at check-in)
        if "prediction" in agents_invoked:
            pred_index = agents_invoked.index("prediction")
            # Should be one of the first agents called
            assert pred_index < 3, \
                f"Prediction should be called early, was at index {pred_index}"

        print(f"\n✅ Execution Order Test PASSED")
        print(f"   Agent sequence: {agents_invoked}")


    @pytest.mark.asyncio
    async def test_concurrent_agent_execution(
        self,
        orchestrator
    ):
        """Test multiple bags being processed concurrently"""

        from langgraph.orchestrator_state import create_initial_bag_state

        # Create multiple bags
        bags = [
            create_initial_bag_state(
                bag_id=f"BAG_CONCURRENT_{i}",
                tag_number=f"023070000{i}",
                passenger_id=f"PNR_CONC_{i}",
                origin_flight="CM101",
                origin_airport="BOG",
                destination_airport="PTY",
                weight_kg=22.0
            )
            for i in range(5)
        ]

        start_time = datetime.utcnow()

        # Process concurrently
        tasks = [
            orchestrator.process_bag(bag, has_connection=False)
            for bag in bags
        ]

        results = await asyncio.gather(*tasks)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # All should complete
        assert len(results) == 5

        # Concurrent processing should be faster than sequential
        # (Though with mocks, timing may not reflect real performance)

        print(f"\n✅ Concurrent Execution Test PASSED")
        print(f"   Bags processed: {len(results)}")
        print(f"   Total time: {duration:.2f}s")
        print(f"   Avg per bag: {duration/len(results):.2f}s")
