"""
Integration Test Configuration and Shared Fixtures

Provides comprehensive fixtures for end-to-end integration tests
of the baggage handling system with all 8 agents.
"""

import pytest
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta

from langgraph.baggage_orchestrator import BaggageOrchestrator
from langgraph.orchestrator_state import (
    create_initial_bag_state,
    BagStatus,
    RiskLevel
)
from agents.prediction_agent import PredictionAgent
from agents.route_optimization_agent import RouteOptimizationAgent
from agents.infrastructure_health_agent import InfrastructureHealthAgent
from agents.demand_forecast_agent import DemandForecastAgent
from agents.customer_service_agent import CustomerServiceAgent
from agents.compensation_agent import CompensationAgent
from agents.root_cause_agent import RootCauseAgent


# =====================================================================
# FIXTURES DATA LOADING
# =====================================================================

@pytest.fixture(scope="session")
def fixtures_dir():
    """Get path to fixtures directory"""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="session")
def copa_flight_schedule(fixtures_dir):
    """Load Copa flight schedule fixture"""
    with open(fixtures_dir / "copa_flight_schedule.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def copa_bag_data(fixtures_dir):
    """Load Copa bag data fixture"""
    with open(fixtures_dir / "copa_bag_data.json") as f:
        return json.load(f)


# =====================================================================
# MOCK LLM AND DATABASE
# =====================================================================

@pytest.fixture
def mock_llm_client():
    """Mock LLM client with realistic responses"""
    client = Mock()

    # Default response
    client.generate = AsyncMock(return_value="Mocked LLM response")

    # Context-aware responses
    async def generate_with_context(prompt, context=None, **kwargs):
        if "risk" in prompt.lower():
            return "High risk connection detected due to tight timing"
        elif "route" in prompt.lower():
            return "Optimal route via conveyor CONV-2, ETA 8 minutes"
        elif "root cause" in prompt.lower():
            return "Primary cause: insufficient transfer time due to inbound delay"
        elif "compensation" in prompt.lower():
            return "Compensation recommended: $100 interim expenses per Montreal Convention"
        elif "customer" in prompt.lower():
            return "PIR filed. Your bag will be delivered within 6 hours."
        return "Mocked LLM response"

    client.generate_with_context = AsyncMock(side_effect=generate_with_context)
    client.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

    return client


@pytest.fixture
def mock_db_connection():
    """Mock database connection with realistic queries"""
    db = Mock()

    # Postgres queries
    async def query_postgres(query, params=None):
        if "flight" in query.lower():
            return [
                ("CM451", "PTY", "JFK", "2024-11-16T10:30:00", "scheduled")
            ]
        elif "bag" in query.lower():
            return [
                ("BAG_001", "0230100001", "check_in", "PTY")
            ]
        return []

    db.query_postgres = AsyncMock(side_effect=query_postgres)

    # Neo4j queries
    async def query_neo4j(query, params=None):
        if "MATCH" in query and "Airport" in query:
            return [
                {"code": "PTY", "name": "Tocumen International", "is_hub": True}
            ]
        elif "equipment" in query.lower() or "conveyor" in query.lower():
            return [
                {"id": "CONV-5", "status": "operational", "health_score": 75},
                {"id": "CONV-6", "status": "operational", "health_score": 92}
            ]
        elif "route" in query.lower() or "path" in query.lower():
            return [
                {
                    "path": ["PTY-T1", "SORT-1", "CONV-2", "PTY-A1"],
                    "total_time_minutes": 8,
                    "reliability_score": 0.95
                }
            ]
        return []

    db.query_neo4j = AsyncMock(side_effect=query_neo4j)

    db.execute_postgres = AsyncMock(return_value=1)
    db.health_check = AsyncMock(return_value={"postgres": True, "neo4j": True})

    return db


# =====================================================================
# AGENT FIXTURES
# =====================================================================

@pytest.fixture
def mock_prediction_agent(mock_llm_client, mock_db_connection):
    """Mock prediction agent with realistic predictions"""
    agent = PredictionAgent(
        llm_client=mock_llm_client,
        db_connection=mock_db_connection
    )

    # Override execute to return deterministic results
    original_execute = agent.execute

    async def execute_with_logic(input_data: Dict[str, Any]) -> Dict[str, Any]:
        connection_time = input_data.get("connection_time")

        # Calculate risk based on connection time
        if connection_time is None:
            risk_score = 10
            risk_level = "low"
        elif connection_time < 40:
            risk_score = 90
            risk_level = "critical"
        elif connection_time < 45:
            risk_score = 85
            risk_level = "high"
        elif connection_time < 60:
            risk_score = 50
            risk_level = "medium"
        else:
            risk_score = 20
            risk_level = "low"

        return {
            "flight_id": input_data.get("flight_id"),
            "route": f"{input_data.get('departure_airport')} -> {input_data.get('arrival_airport')}",
            "risk_score": risk_score,
            "risk_level": risk_level.upper(),
            "contributing_factors": [
                "Short connection time detected" if connection_time and connection_time < 45 else "Normal connection time",
                "High volume period" if connection_time and connection_time < 60 else "Standard volume"
            ],
            "recommendations": [
                "Expedite transfer" if risk_score > 80 else "Standard handling",
                "Alert handlers" if risk_score > 70 else "Monitor connection"
            ],
            "confidence": 0.92
        }

    agent.execute = AsyncMock(side_effect=execute_with_logic)
    return agent


@pytest.fixture
def mock_route_optimization_agent(mock_llm_client, mock_db_connection):
    """Mock route optimization agent"""
    agent = RouteOptimizationAgent(
        llm_client=mock_llm_client,
        db_connection=mock_db_connection
    )

    async def execute_with_logic(input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "origin": input_data.get("origin"),
            "destination": input_data.get("destination"),
            "optimal_route": {
                "path": ["Terminal-1", "Sorter", "Conveyor-2", "Gate-A5"],
                "total_time_minutes": 8,
                "distance_meters": 450,
                "reliability_score": 0.95,
                "equipment_used": ["CONV-2"]
            },
            "alternative_routes": [
                {
                    "path": ["Terminal-1", "Sorter", "Conveyor-6", "Gate-A5"],
                    "total_time_minutes": 10,
                    "reliability_score": 0.92,
                    "equipment_used": ["CONV-6"]
                }
            ],
            "recommendations": ["Use primary route via CONV-2"]
        }

    agent.execute = AsyncMock(side_effect=execute_with_logic)
    return agent


@pytest.fixture
def mock_infrastructure_health_agent(mock_llm_client, mock_db_connection):
    """Mock infrastructure health agent"""
    agent = InfrastructureHealthAgent(
        llm_client=mock_llm_client,
        db_connection=mock_db_connection
    )

    # Track equipment failures for testing
    failed_equipment = set()

    async def execute_with_logic(input_data: Dict[str, Any]) -> Dict[str, Any]:
        equipment_id = input_data.get("equipment_id")
        equipment_type = input_data.get("equipment_type", "")

        # Check if specific equipment is in failed state
        if equipment_id == "CONV-5" and "CONV-5" in failed_equipment:
            status = "failed"
            health_score = 0
        elif equipment_id == "CONV-5":
            status = "operational"
            health_score = 75
        else:
            status = "operational"
            health_score = 95

        return {
            "airport_code": input_data.get("airport_code", "PTY"),
            "equipment_type": equipment_type,
            "equipment_id": equipment_id,
            "status": status,
            "overall_health": health_score,
            "equipment_status": [
                {"id": "CONV-1", "status": "operational", "health": 95},
                {"id": "CONV-2", "status": "operational", "health": 88},
                {"id": "CONV-5", "status": status, "health": health_score},
                {"id": "CONV-6", "status": "operational", "health": 92}
            ],
            "alerts": ["Equipment degradation detected"] if health_score < 80 else [],
            "recommendations": ["Schedule maintenance"] if health_score < 80 else []
        }

    agent.execute = AsyncMock(side_effect=execute_with_logic)
    agent.failed_equipment = failed_equipment  # Allow tests to manipulate
    return agent


@pytest.fixture
def mock_demand_forecast_agent(mock_llm_client, mock_db_connection):
    """Mock demand forecast agent"""
    agent = DemandForecastAgent(
        llm_client=mock_llm_client,
        db_connection=mock_db_connection
    )

    async def execute_with_logic(input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "airport_code": input_data.get("airport_code", "PTY"),
            "forecast_horizon_hours": input_data.get("forecast_horizon", 24),
            "predicted_bag_volume": 1500,
            "peak_hours": ["14:00-18:00"],
            "staffing_recommendation": {
                "handlers_needed": 25,
                "current_staff": 22,
                "additional_needed": 3
            },
            "congestion_forecast": [
                {"hour": "14:00", "congestion_level": "high", "bags": 350},
                {"hour": "15:00", "congestion_level": "high", "bags": 380}
            ]
        }

    agent.execute = AsyncMock(side_effect=execute_with_logic)
    return agent


@pytest.fixture
def mock_customer_service_agent(mock_llm_client, mock_db_connection):
    """Mock customer service agent"""
    agent = CustomerServiceAgent(
        llm_client=mock_llm_client,
        db_connection=mock_db_connection
    )

    async def execute_with_logic(input_data: Dict[str, Any]) -> Dict[str, Any]:
        query_type = input_data.get("customer_query", "")

        if "delayed" in query_type.lower() or "mishandl" in query_type.lower():
            return {
                "response": "We sincerely apologize for the delay. Your bag has been located and will be delivered within 6 hours.",
                "pir_number": f"PTY{datetime.utcnow().strftime('%Y%m%d')}001",
                "notification_sent": True,
                "notification_method": ["email", "sms"],
                "estimated_delivery": (datetime.utcnow() + timedelta(hours=6)).isoformat(),
                "actions_taken": [
                    "PIR filed",
                    "Bag located",
                    "Delivery arranged",
                    "Customer notified"
                ]
            }
        else:
            return {
                "response": "Your bag is on schedule and will arrive at baggage claim as expected.",
                "notification_sent": True,
                "notification_method": ["sms"]
            }

    agent.execute = AsyncMock(side_effect=execute_with_logic)
    return agent


@pytest.fixture
def mock_compensation_agent(mock_llm_client, mock_db_connection):
    """Mock compensation agent"""
    agent = CompensationAgent(
        llm_client=mock_llm_client,
        db_connection=mock_db_connection
    )

    async def execute_with_logic(input_data: Dict[str, Any]) -> Dict[str, Any]:
        incident_type = input_data.get("incident_type", "delayed")
        declared_value = input_data.get("declared_value", 0)
        delay_hours = input_data.get("delay_hours", 24)

        # Calculate compensation
        if incident_type == "lost":
            compensation = min(declared_value, 1500)  # Montreal Convention limit
            requires_approval = compensation > 500
        elif incident_type == "damaged":
            compensation = min(declared_value * 0.5, 1000)
            requires_approval = compensation > 500
        else:  # delayed
            if delay_hours > 24:
                compensation = 100  # Interim expenses
            else:
                compensation = 50
            requires_approval = compensation > 50

        return {
            "claim_id": input_data.get("claim_id"),
            "incident_type": incident_type,
            "compensation_amount": compensation,
            "currency": "USD",
            "calculation_basis": "Montreal Convention",
            "eligibility": "eligible",
            "requires_approval": requires_approval,
            "approval_threshold": 50,
            "breakdown": {
                "interim_expenses": compensation if incident_type == "delayed" else 0,
                "bag_value": compensation if incident_type == "lost" else 0,
                "damage_claim": compensation if incident_type == "damaged" else 0
            },
            "documentation_required": ["PIR", "receipts"] if compensation > 0 else []
        }

    agent.execute = AsyncMock(side_effect=execute_with_logic)
    return agent


@pytest.fixture
def mock_root_cause_agent(mock_llm_client, mock_db_connection):
    """Mock root cause agent"""
    agent = RootCauseAgent(
        llm_client=mock_llm_client,
        db_connection=mock_db_connection
    )

    async def execute_with_logic(input_data: Dict[str, Any]) -> Dict[str, Any]:
        incident_type = input_data.get("incident_type", "delayed")

        return {
            "incident_id": input_data.get("incident_id"),
            "incident_type": incident_type,
            "root_cause": "insufficient_transfer_time",
            "primary_cause": "flight_irregularity",
            "contributing_factors": [
                "Inbound flight delayed 40 minutes",
                "Minimum connection time not met",
                "No buffer time available"
            ],
            "timeline": [
                {"time": "T-40", "event": "Inbound delay detected"},
                {"time": "T-15", "event": "Connection at risk flagged"},
                {"time": "T+0", "event": "Bag missed connection"}
            ],
            "recommendations": [
                "Rebook on next available flight",
                "Expedite through transfer process",
                "Notify passenger proactively"
            ],
            "preventable": True,
            "prevention_strategy": "Earlier risk detection and intervention",
            "confidence": 0.89
        }

    agent.execute = AsyncMock(side_effect=execute_with_logic)
    return agent


# =====================================================================
# ORCHESTRATOR FIXTURE
# =====================================================================

@pytest.fixture
def orchestrator(
    mock_prediction_agent,
    mock_route_optimization_agent,
    mock_infrastructure_health_agent,
    mock_demand_forecast_agent,
    mock_customer_service_agent,
    mock_compensation_agent,
    mock_root_cause_agent,
    mock_db_connection
):
    """Create orchestrator with all mocked agents"""
    agents = {
        "prediction": mock_prediction_agent,
        "route_optimization": mock_route_optimization_agent,
        "infrastructure_health": mock_infrastructure_health_agent,
        "demand_forecast": mock_demand_forecast_agent,
        "customer_service": mock_customer_service_agent,
        "compensation": mock_compensation_agent,
        "root_cause": mock_root_cause_agent
    }

    return BaggageOrchestrator(
        agents=agents,
        db_manager=mock_db_connection,
        enable_checkpoints=True
    )


# =====================================================================
# BAG STATE FACTORIES
# =====================================================================

@pytest.fixture
def create_happy_path_bag(copa_bag_data):
    """Factory to create happy path test bag"""
    def _create():
        data = copa_bag_data["test_bags"]["happy_path"]
        return create_initial_bag_state(
            bag_id=data["bag_id"],
            tag_number=data["tag_number"],
            passenger_id=data["passenger_id"],
            origin_flight=data["origin_flight"],
            origin_airport=data["origin_airport"],
            destination_airport=data["destination_airport"],
            weight_kg=data["weight_kg"],
            declared_value=data["declared_value"],
            connection_flight=data["destination_flight"],
            connection_airport=data["connection_airport"]
        )
    return _create


@pytest.fixture
def create_at_risk_bag(copa_bag_data):
    """Factory to create at-risk connection bag"""
    def _create():
        data = copa_bag_data["test_bags"]["at_risk_connection"]
        return create_initial_bag_state(
            bag_id=data["bag_id"],
            tag_number=data["tag_number"],
            passenger_id=data["passenger_id"],
            origin_flight=data["origin_flight"],
            origin_airport=data["origin_airport"],
            destination_airport=data["destination_airport"],
            weight_kg=data["weight_kg"],
            declared_value=data["declared_value"],
            connection_flight=data["destination_flight"],
            connection_airport=data["connection_airport"]
        )
    return _create


@pytest.fixture
def create_mishandled_bag(copa_bag_data):
    """Factory to create mishandled bag"""
    def _create():
        data = copa_bag_data["test_bags"]["mishandled_delayed"]
        return create_initial_bag_state(
            bag_id=data["bag_id"],
            tag_number=data["tag_number"],
            passenger_id=data["passenger_id"],
            origin_flight=data["origin_flight"],
            origin_airport=data["origin_airport"],
            destination_airport=data["destination_airport"],
            weight_kg=data["weight_kg"],
            declared_value=data["declared_value"]
        )
    return _create


# =====================================================================
# PERFORMANCE MONITORING
# =====================================================================

@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests"""
    class PerformanceTracker:
        def __init__(self):
            self.metrics = {
                "agent_response_times": [],
                "total_test_time": 0,
                "agent_calls": {},
                "errors": []
            }

        def record_agent_call(self, agent_name: str, duration_ms: float):
            if agent_name not in self.metrics["agent_calls"]:
                self.metrics["agent_calls"][agent_name] = []
            self.metrics["agent_calls"][agent_name].append(duration_ms)
            self.metrics["agent_response_times"].append({
                "agent": agent_name,
                "duration_ms": duration_ms
            })

        def record_error(self, error: str):
            self.metrics["errors"].append(error)

        def get_summary(self) -> Dict[str, Any]:
            summary = {
                "total_agent_calls": sum(len(calls) for calls in self.metrics["agent_calls"].values()),
                "total_errors": len(self.metrics["errors"]),
                "agent_performance": {}
            }

            for agent_name, times in self.metrics["agent_calls"].items():
                if times:
                    summary["agent_performance"][agent_name] = {
                        "count": len(times),
                        "avg_ms": sum(times) / len(times),
                        "min_ms": min(times),
                        "max_ms": max(times)
                    }

            return summary

    return PerformanceTracker()
