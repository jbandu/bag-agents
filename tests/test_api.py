"""
Tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    # Mock the lifespan to avoid actual initialization
    with patch("api.main.get_db_manager"), \
         patch("api.main.get_llm_client"), \
         patch("api.main.setup_monitoring"):

        from api.main import app

        # Mock agents
        with patch.dict("api.main.agents", {
            "prediction": Mock(
                agent_name="prediction_agent",
                run=AsyncMock(return_value={
                    "risk_score": 50,
                    "metadata": {"status": "success"}
                })
            )
        }):
            client = TestClient(app)
            yield client


def test_root_endpoint(test_client):
    """Test the root endpoint."""
    response = test_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Baggage Operations AI Agents API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"


def test_health_check(test_client):
    """Test the health check endpoint."""
    with patch("api.main.db_manager") as mock_db:
        mock_db.health_check = AsyncMock(return_value={
            "postgres": True,
            "neo4j": True
        })

        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "databases" in data


def test_list_agents(test_client):
    """Test listing available agents."""
    response = test_client.get("/agents")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "prediction" in data


def test_invoke_agent_success(test_client):
    """Test successful agent invocation."""
    # Override API key check for testing
    with patch("api.main.verify_api_key", return_value="test-key"):
        response = test_client.post(
            "/agents/invoke",
            json={
                "agent_name": "prediction",
                "input_data": {
                    "flight_id": "AA123",
                    "departure_airport": "JFK",
                    "arrival_airport": "LAX"
                }
            },
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent_name"] == "prediction"
        assert "result" in data


def test_invoke_agent_not_found(test_client):
    """Test invoking non-existent agent."""
    with patch("api.main.verify_api_key", return_value="test-key"):
        response = test_client.post(
            "/agents/invoke",
            json={
                "agent_name": "nonexistent",
                "input_data": {}
            },
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_execute_workflow(test_client):
    """Test workflow execution."""
    with patch("api.main.verify_api_key", return_value="test-key"), \
         patch("api.main.execute_workflow", new_callable=AsyncMock) as mock_workflow:

        mock_workflow.return_value = {
            "workflow_type": "incident_analysis",
            "results": {},
            "success": True
        }

        response = test_client.post(
            "/workflows/execute",
            json={
                "workflow_type": "incident_analysis",
                "parameters": {
                    "incident_id": "INC-001",
                    "incident_type": "delayed"
                }
            },
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_type"] == "incident_analysis"


def test_execute_workflow_invalid_type(test_client):
    """Test workflow execution with invalid type."""
    with patch("api.main.verify_api_key", return_value="test-key"), \
         patch("api.main.execute_workflow", side_effect=ValueError("Unknown workflow")):

        response = test_client.post(
            "/workflows/execute",
            json={
                "workflow_type": "invalid_workflow",
                "parameters": {}
            },
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 400


def test_api_key_validation(test_client):
    """Test API key validation."""
    # Request without API key in development mode should work
    with patch("api.main.os.getenv", return_value="development"):
        response = test_client.post(
            "/agents/invoke",
            json={
                "agent_name": "prediction",
                "input_data": {}
            }
        )
        # Should not get 401 in development mode
        assert response.status_code != 401
