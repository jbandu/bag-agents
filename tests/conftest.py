"""
Pytest configuration and fixtures for testing.
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock()
    client.generate = AsyncMock(return_value="Mocked LLM response")
    client.generate_with_context = AsyncMock(return_value="Mocked context response")
    client.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    return client


@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing."""
    db = Mock()
    db.query_postgres = AsyncMock(return_value=[("result",)])
    db.query_neo4j = AsyncMock(return_value=[{"result": "data"}])
    db.execute_postgres = AsyncMock(return_value=1)
    db.health_check = AsyncMock(return_value={"postgres": True, "neo4j": True})
    return db


@pytest.fixture
def sample_flight_data() -> Dict[str, Any]:
    """Sample flight data for testing."""
    return {
        "flight_id": "AA123",
        "departure_airport": "JFK",
        "arrival_airport": "LAX",
        "departure_time": "2024-11-15T10:00:00Z",
        "arrival_time": "2024-11-15T14:00:00Z",
        "connection_time": 45
    }


@pytest.fixture
def sample_incident_data() -> Dict[str, Any]:
    """Sample incident data for testing."""
    return {
        "incident_id": "INC-2024-001",
        "incident_type": "delayed",
        "flight_id": "AA123",
        "affected_bags": 5,
        "timestamp": "2024-11-15T12:00:00Z"
    }


@pytest.fixture
def sample_claim_data() -> Dict[str, Any]:
    """Sample compensation claim data for testing."""
    return {
        "claim_id": "CLM-2024-001",
        "incident_type": "delayed",
        "delay_hours": 24,
        "declared_value": 1000,
        "customer_tier": "gold"
    }


@pytest.fixture
def sample_customer_query() -> Dict[str, Any]:
    """Sample customer service query for testing."""
    return {
        "customer_query": "Where is my bag?",
        "bag_tag": "BAG123456",
        "customer_id": "CUST001",
        "language": "en"
    }


@pytest.fixture
def sample_airport_data() -> Dict[str, Any]:
    """Sample airport data for testing."""
    return {
        "airport_code": "JFK",
        "forecast_horizon": 24,
        "include_events": True
    }
