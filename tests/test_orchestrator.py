"""
Tests for Baggage Lifecycle Orchestrator.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from langgraph.orchestrator_state import (
    create_initial_bag_state,
    create_initial_orchestrator_state,
    BagStatus,
    RiskLevel,
    EventType
)
from langgraph.baggage_orchestrator import BaggageOrchestrator


@pytest.fixture
def sample_bag_state():
    """Create sample bag state for testing."""
    return create_initial_bag_state(
        bag_id="TEST-001",
        tag_number="TAG123",
        passenger_id="PASS001",
        origin_flight="AA123",
        origin_airport="JFK",
        destination_airport="LAX",
        weight_kg=23.5,
        declared_value=500.00
    )


@pytest.fixture
def sample_orchestrator_state(sample_bag_state):
    """Create sample orchestrator state."""
    return create_initial_orchestrator_state(sample_bag_state, has_connection=False)


@pytest.fixture
def mock_agents():
    """Create mock agents."""
    agents = {}

    # Mock prediction agent
    prediction_mock = Mock()
    prediction_mock.run = AsyncMock(return_value={
        "risk_score": 35,
        "risk_level": "medium",
        "metadata": {"status": "success"}
    })
    agents["prediction"] = prediction_mock

    # Mock infrastructure health agent
    infra_mock = Mock()
    infra_mock.run = AsyncMock(return_value={
        "overall_health": 85,
        "metadata": {"status": "success"}
    })
    agents["infrastructure_health"] = infra_mock

    return agents


@pytest.mark.asyncio
async def test_orchestrator_initialization(mock_agents):
    """Test orchestrator initializes correctly."""
    orchestrator = BaggageOrchestrator(
        agents=mock_agents,
        db_manager=None,
        enable_checkpoints=False
    )

    assert orchestrator.agents == mock_agents
    assert orchestrator.graph is not None


@pytest.mark.asyncio
async def test_check_in_node(sample_orchestrator_state, mock_agents):
    """Test check-in node execution."""
    orchestrator = BaggageOrchestrator(
        agents=mock_agents,
        enable_checkpoints=False
    )

    result = await orchestrator.check_in_node(sample_orchestrator_state)

    assert result["bag"]["current_status"] == BagStatus.CHECK_IN
    assert result["current_node"] == "check_in"
    assert "check_in" in result["previous_nodes"]
    assert len(result["bag"]["events"]) > 0


@pytest.mark.asyncio
async def test_security_screening_node(sample_orchestrator_state, mock_agents):
    """Test security screening node."""
    orchestrator = BaggageOrchestrator(
        agents=mock_agents,
        enable_checkpoints=False
    )

    result = await orchestrator.security_screening_node(sample_orchestrator_state)

    assert result["bag"]["current_status"] == BagStatus.SECURITY_SCREENING
    assert result["current_node"] == "security_screening"


@pytest.mark.asyncio
async def test_sorting_node_with_infrastructure_check(sample_orchestrator_state, mock_agents):
    """Test sorting node with infrastructure health check."""
    orchestrator = BaggageOrchestrator(
        agents=mock_agents,
        enable_checkpoints=False
    )

    result = await orchestrator.sorting_node(sample_orchestrator_state)

    assert result["bag"]["current_status"] == BagStatus.SORTING
    assert "infrastructure_health" in result.get("agent_results", {})


@pytest.mark.asyncio
async def test_route_from_in_flight_no_connection(sample_orchestrator_state):
    """Test routing from in_flight without connection."""
    orchestrator = BaggageOrchestrator(enable_checkpoints=False)

    # No connection
    sample_orchestrator_state["connection"] = None

    next_node = orchestrator.route_from_in_flight(sample_orchestrator_state)

    assert next_node == "arrival"


@pytest.mark.asyncio
async def test_route_from_in_flight_with_connection():
    """Test routing from in_flight with connection."""
    orchestrator = BaggageOrchestrator(enable_checkpoints=False)

    bag_state = create_initial_bag_state(
        bag_id="TEST-002",
        tag_number="TAG456",
        passenger_id="PASS002",
        origin_flight="AA123",
        origin_airport="JFK",
        destination_airport="SFO",
        weight_kg=20.0,
        connection_flight="AA456",
        connection_airport="ORD"
    )

    state = create_initial_orchestrator_state(bag_state, has_connection=True)

    next_node = orchestrator.route_from_in_flight(state)

    assert next_node == "transfer"


@pytest.mark.asyncio
async def test_route_from_claim_high_value():
    """Test routing from claim with high-value bag."""
    orchestrator = BaggageOrchestrator(enable_checkpoints=False)

    bag_state = create_initial_bag_state(
        bag_id="TEST-003",
        tag_number="TAG789",
        passenger_id="PASS003",
        origin_flight="AA789",
        origin_airport="LAX",
        destination_airport="JFK",
        weight_kg=15.0,
        declared_value=6000.00  # High value
    )

    state = create_initial_orchestrator_state(bag_state, has_connection=False)

    next_node = orchestrator.route_from_claim(state)

    assert next_node == "request_approval"


@pytest.mark.asyncio
async def test_route_from_claim_regular_value():
    """Test routing from claim with regular value bag."""
    orchestrator = BaggageOrchestrator(enable_checkpoints=False)

    state = create_initial_orchestrator_state(
        create_initial_bag_state(
            bag_id="TEST-004",
            tag_number="TAG012",
            passenger_id="PASS004",
            origin_flight="AA012",
            origin_airport="ORD",
            destination_airport="LAX",
            weight_kg=20.0,
            declared_value=500.00  # Regular value
        ),
        has_connection=False
    )

    next_node = orchestrator.route_from_claim(state)

    assert next_node == "delivered"


@pytest.mark.asyncio
async def test_delivered_node(sample_orchestrator_state, mock_agents):
    """Test delivered terminal node."""
    orchestrator = BaggageOrchestrator(
        agents=mock_agents,
        enable_checkpoints=False
    )

    result = await orchestrator.delivered_node(sample_orchestrator_state)

    assert result["bag"]["current_status"] == BagStatus.DELIVERED
    assert result["status"] == "completed"
    assert result["completed_at"] is not None


@pytest.mark.asyncio
async def test_mishandled_node(sample_orchestrator_state):
    """Test mishandled node."""
    orchestrator = BaggageOrchestrator(enable_checkpoints=False)

    result = await orchestrator.mishandled_node(sample_orchestrator_state)

    assert result["current_node"] == "mishandled"
    assert len(result["bag"]["alerts"]) > 0


@pytest.mark.asyncio
async def test_create_event_helper():
    """Test event creation helper."""
    orchestrator = BaggageOrchestrator(enable_checkpoints=False)

    event = orchestrator._create_event(
        EventType.RFID_SCAN,
        "JFK-SORTING",
        {"reader_id": "RFID-001"}
    )

    assert event["event_type"] == EventType.RFID_SCAN
    assert event["location"] == "JFK-SORTING"
    assert event["details"]["reader_id"] == "RFID-001"
    assert event["source"] == "orchestrator"


@pytest.mark.asyncio
async def test_create_alert_helper():
    """Test alert creation helper."""
    orchestrator = BaggageOrchestrator(enable_checkpoints=False)

    alert = orchestrator._create_alert(
        RiskLevel.HIGH,
        "Test alert message"
    )

    assert alert["severity"] == RiskLevel.HIGH
    assert alert["message"] == "Test alert message"
    assert alert["resolved_at"] is None


@pytest.mark.asyncio
async def test_state_persistence():
    """Test state is properly updated through nodes."""
    orchestrator = BaggageOrchestrator(enable_checkpoints=False)

    bag_state = create_initial_bag_state(
        bag_id="TEST-005",
        tag_number="TAG345",
        passenger_id="PASS005",
        origin_flight="AA345",
        origin_airport="JFK",
        destination_airport="LAX",
        weight_kg=22.0
    )

    state = create_initial_orchestrator_state(bag_state, has_connection=False)

    # Execute sequence of nodes
    state = await orchestrator.check_in_node(state)
    state = await orchestrator.security_screening_node(state)
    state = await orchestrator.sorting_node(state)

    # Verify state progression
    assert len(state["previous_nodes"]) == 3
    assert state["previous_nodes"] == ["check_in", "security_screening", "sorting"]
    assert state["bag"]["current_status"] == BagStatus.SORTING


@pytest.mark.asyncio
async def test_error_handling_in_nodes():
    """Test error handling when agent invocation fails."""

    # Create agent that raises error
    failing_agent = Mock()
    failing_agent.run = AsyncMock(side_effect=Exception("Agent error"))

    agents = {"prediction": failing_agent}

    orchestrator = BaggageOrchestrator(agents=agents, enable_checkpoints=False)

    bag_state = create_initial_bag_state(
        bag_id="TEST-006",
        tag_number="TAG678",
        passenger_id="PASS006",
        origin_flight="AA678",
        origin_airport="LAX",
        destination_airport="JFK",
        weight_kg=18.0
    )

    state = create_initial_orchestrator_state(bag_state, has_connection=False)

    # Should not raise exception, error should be logged
    result = await orchestrator.check_in_node(state)

    # Verify error was captured
    assert len(result.get("errors", [])) > 0


@pytest.mark.asyncio
async def test_complete_workflow_execution(mock_agents):
    """Test complete workflow from start to end."""
    orchestrator = BaggageOrchestrator(
        agents=mock_agents,
        enable_checkpoints=False
    )

    bag_state = create_initial_bag_state(
        bag_id="TEST-007",
        tag_number="TAG901",
        passenger_id="PASS007",
        origin_flight="AA901",
        origin_airport="ORD",
        destination_airport="SFO",
        weight_kg=25.0,
        declared_value=300.00
    )

    # Process through workflow
    result = await orchestrator.process_bag(bag_state, has_connection=False)

    # Verify completion
    assert result is not None
    assert "bag" in result
    assert "workflow_id" in result


@pytest.mark.asyncio
async def test_connection_state_creation():
    """Test connection state is created correctly."""
    bag_state = create_initial_bag_state(
        bag_id="TEST-008",
        tag_number="TAG234",
        passenger_id="PASS008",
        origin_flight="AA234",
        origin_airport="JFK",
        destination_airport="LAX",
        weight_kg=20.0,
        connection_flight="AA567",
        connection_airport="ORD"
    )

    state = create_initial_orchestrator_state(bag_state, has_connection=True)

    assert state["connection"] is not None
    assert state["connection"]["has_connection"] is True
    assert state["connection"]["minimum_connection_time"] == 45


@pytest.mark.asyncio
async def test_intervention_state_initialization():
    """Test intervention state is initialized correctly."""
    bag_state = create_initial_bag_state(
        bag_id="TEST-009",
        tag_number="TAG567",
        passenger_id="PASS009",
        origin_flight="AA567",
        origin_airport="LAX",
        destination_airport="ORD",
        weight_kg=19.0
    )

    state = create_initial_orchestrator_state(bag_state, has_connection=False)

    assert state["intervention"] is not None
    assert state["intervention"]["pending_interventions"] == []
    assert state["intervention"]["requires_approval"] is False
    assert state["intervention"]["approval_threshold_value"] == 500.0


# Stress test
@pytest.mark.asyncio
@pytest.mark.slow
async def test_concurrent_bag_processing():
    """
    Stress test with multiple bags processed concurrently.

    Tests system performance under load.
    """
    orchestrator = BaggageOrchestrator(enable_checkpoints=False)

    # Create 100 bags
    bags = []
    for i in range(100):
        bag_state = create_initial_bag_state(
            bag_id=f"STRESS-{i:03d}",
            tag_number=f"TAG{i:06d}",
            passenger_id=f"PASS{i:03d}",
            origin_flight=f"AA{i:03d}",
            origin_airport="JFK",
            destination_airport="LAX",
            weight_kg=20.0 + (i % 10)
        )
        bags.append(bag_state)

    # Process all bags concurrently
    tasks = [
        orchestrator.process_bag(bag, has_connection=False)
        for bag in bags
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Verify all processed
    successful = sum(1 for r in results if not isinstance(r, Exception))
    assert successful >= 90  # Allow for some failures in stress test

    print(f"\n✅ Processed {successful}/100 bags successfully in stress test")
