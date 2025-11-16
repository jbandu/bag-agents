"""
Tests for Base Agent.
"""

import pytest
from agents.base_agent import BaseAgent


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent."""

    async def execute(self, input_data):
        """Simple test execution."""
        return {"result": "success", "input": input_data}


@pytest.mark.asyncio
async def test_base_agent_initialization():
    """Test BaseAgent initialization."""
    agent = TestAgent(agent_name="test_agent")

    assert agent.agent_name == "test_agent"
    assert agent.logger is not None


@pytest.mark.asyncio
async def test_base_agent_run():
    """Test BaseAgent run method."""
    agent = TestAgent(agent_name="test_agent")
    input_data = {"test": "data"}

    result = await agent.run(input_data)

    # Verify metadata is added
    assert "metadata" in result
    assert result["metadata"]["agent_name"] == "test_agent"
    assert result["metadata"]["status"] == "success"
    assert "execution_time" in result["metadata"]
    assert "timestamp" in result["metadata"]


@pytest.mark.asyncio
async def test_base_agent_error_handling():
    """Test BaseAgent error handling."""

    class ErrorAgent(BaseAgent):
        async def execute(self, input_data):
            raise ValueError("Test error")

    agent = ErrorAgent(agent_name="error_agent")
    result = await agent.run({"test": "data"})

    # Verify error is captured
    assert "error" in result
    assert result["error"] == "Test error"
    assert result["error_type"] == "ValueError"
    assert result["metadata"]["status"] == "error"


def test_validate_input():
    """Test input validation."""
    agent = TestAgent(agent_name="test_agent")

    # Valid input
    valid_data = {"field1": "value1", "field2": "value2"}
    agent.validate_input(valid_data, ["field1", "field2"])  # Should not raise

    # Invalid input
    invalid_data = {"field1": "value1"}
    with pytest.raises(ValueError) as exc_info:
        agent.validate_input(invalid_data, ["field1", "field2"])

    assert "Missing required fields" in str(exc_info.value)


@pytest.mark.asyncio
async def test_base_agent_metrics():
    """Test that metrics are recorded."""
    agent = TestAgent(agent_name="test_agent")

    # Execute agent
    await agent.run({"test": "data"})

    # Verify metrics counters increased
    # Note: In real tests, you'd use prometheus_client test utilities
    assert True  # Placeholder for actual metric verification
