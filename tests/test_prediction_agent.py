"""
Tests for Prediction Agent.
"""

import pytest
from agents.prediction_agent import PredictionAgent


@pytest.mark.asyncio
async def test_prediction_agent_initialization(mock_llm_client, mock_db_connection):
    """Test that PredictionAgent initializes correctly."""
    agent = PredictionAgent(
        llm_client=mock_llm_client,
        db_connection=mock_db_connection
    )

    assert agent.agent_name == "prediction_agent"
    assert agent.llm_client is mock_llm_client
    assert agent.db_connection is mock_db_connection


@pytest.mark.asyncio
async def test_prediction_agent_execute(mock_llm_client, mock_db_connection, sample_flight_data):
    """Test PredictionAgent execution with valid input."""
    agent = PredictionAgent(
        llm_client=mock_llm_client,
        db_connection=mock_db_connection
    )

    result = await agent.execute(sample_flight_data)

    # Verify result structure
    assert "flight_id" in result
    assert "risk_score" in result
    assert "risk_level" in result
    assert "contributing_factors" in result
    assert "recommendations" in result

    # Verify risk score is in valid range
    assert 0 <= result["risk_score"] <= 100


@pytest.mark.asyncio
async def test_prediction_agent_run(mock_llm_client, mock_db_connection, sample_flight_data):
    """Test PredictionAgent run method with metadata."""
    agent = PredictionAgent(
        llm_client=mock_llm_client,
        db_connection=mock_db_connection
    )

    result = await agent.run(sample_flight_data)

    # Verify metadata is added
    assert "metadata" in result
    assert result["metadata"]["agent_name"] == "prediction_agent"
    assert result["metadata"]["status"] == "success"
    assert "execution_time" in result["metadata"]


@pytest.mark.asyncio
async def test_prediction_agent_missing_fields(mock_llm_client, mock_db_connection):
    """Test PredictionAgent with missing required fields."""
    agent = PredictionAgent(
        llm_client=mock_llm_client,
        db_connection=mock_db_connection
    )

    # Missing required fields
    invalid_data = {"flight_id": "AA123"}

    result = await agent.run(invalid_data)

    # Should return error
    assert "error" in result
    assert result["metadata"]["status"] == "error"


@pytest.mark.asyncio
async def test_prediction_agent_risk_levels(mock_llm_client, mock_db_connection):
    """Test that risk levels are valid."""
    agent = PredictionAgent(
        llm_client=mock_llm_client,
        db_connection=mock_db_connection
    )

    result = await agent.execute({
        "flight_id": "AA123",
        "departure_airport": "JFK",
        "arrival_airport": "LAX"
    })

    # Verify risk level is one of the valid values
    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
