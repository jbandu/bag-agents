"""
LangGraph State Definitions and Graph Creation.

Defines the state schema for baggage operations workflows.
"""

from typing import TypedDict, Annotated, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import operator


class BaggageOperationsState(TypedDict):
    """
    State schema for baggage operations workflows.

    This state is shared across all agent nodes in the graph.
    """

    # Input data
    workflow_type: str
    input_parameters: Dict[str, Any]

    # Agent results
    prediction_result: Optional[Dict[str, Any]]
    root_cause_result: Optional[Dict[str, Any]]
    demand_forecast_result: Optional[Dict[str, Any]]
    customer_service_result: Optional[Dict[str, Any]]
    compensation_result: Optional[Dict[str, Any]]
    infrastructure_health_result: Optional[Dict[str, Any]]
    route_optimization_result: Optional[Dict[str, Any]]

    # Workflow metadata
    current_step: str
    completed_steps: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]

    # Aggregated results
    final_output: Optional[Dict[str, Any]]


class IncidentAnalysisState(TypedDict):
    """State for incident analysis workflow."""

    incident_id: str
    incident_type: str
    flight_id: str

    # Results from agents
    prediction: Optional[Dict[str, Any]]
    root_cause: Optional[Dict[str, Any]]
    compensation: Optional[Dict[str, Any]]

    # Workflow control
    completed_steps: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]


class OperationalOptimizationState(TypedDict):
    """State for operational optimization workflow."""

    airport_code: str
    optimization_type: str

    # Results from agents
    demand_forecast: Optional[Dict[str, Any]]
    route_optimization: Optional[Dict[str, Any]]
    infrastructure_health: Optional[Dict[str, Any]]

    # Workflow control
    completed_steps: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]


class CustomerServiceState(TypedDict):
    """State for customer service workflow."""

    customer_query: str
    customer_id: Optional[str]
    bag_tag: Optional[str]

    # Results from agents
    service_response: Optional[Dict[str, Any]]
    bag_prediction: Optional[Dict[str, Any]]

    # Workflow control
    completed_steps: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]
    escalate: bool


def create_state_graph() -> StateGraph:
    """
    Create a LangGraph StateGraph for baggage operations.

    Returns:
        Configured StateGraph instance
    """
    # Create graph with BaggageOperationsState
    workflow = StateGraph(BaggageOperationsState)

    # Node definitions will be added by workflow builders
    # This is a factory function that returns a basic graph

    return workflow


def create_incident_analysis_graph() -> StateGraph:
    """
    Create a graph for incident analysis workflow.

    Flow:
    1. Prediction Agent - Assess risk
    2. Root Cause Agent - Analyze cause
    3. Compensation Agent - Calculate compensation
    4. Aggregate results

    Returns:
        Configured StateGraph for incident analysis
    """
    workflow = StateGraph(IncidentAnalysisState)

    # Nodes will be added by the workflow implementation
    # This provides the structure

    return workflow


def create_optimization_graph() -> StateGraph:
    """
    Create a graph for operational optimization workflow.

    Flow:
    1. Demand Forecast Agent - Predict demand
    2. Route Optimization Agent - Optimize routes
    3. Infrastructure Health Agent - Check equipment
    4. Aggregate insights

    Returns:
        Configured StateGraph for optimization
    """
    workflow = StateGraph(OperationalOptimizationState)

    return workflow


def create_customer_service_graph() -> StateGraph:
    """
    Create a graph for customer service workflow.

    Flow:
    1. Customer Service Agent - Handle query
    2. Prediction Agent - Check bag status (if needed)
    3. Decision - Escalate or resolve
    4. Return response

    Returns:
        Configured StateGraph for customer service
    """
    workflow = StateGraph(CustomerServiceState)

    return workflow


def should_continue(state: BaggageOperationsState) -> str:
    """
    Conditional edge function to determine next step.

    Args:
        state: Current workflow state

    Returns:
        Name of next node or END
    """
    if state.get("errors"):
        # If there are critical errors, end the workflow
        if len(state["errors"]) > 3:
            return END

    # Continue to next step based on workflow type
    current_step = state.get("current_step", "")

    if current_step == "prediction":
        return "root_cause"
    elif current_step == "root_cause":
        return "compensation"
    elif current_step == "compensation":
        return END

    return END


def aggregate_results(state: BaggageOperationsState) -> Dict[str, Any]:
    """
    Aggregate results from multiple agents.

    Args:
        state: Current workflow state

    Returns:
        Aggregated results dictionary
    """
    aggregated = {
        "workflow_type": state.get("workflow_type"),
        "completed_steps": state.get("completed_steps", []),
        "errors": state.get("errors", []),
        "results": {}
    }

    # Collect all agent results
    result_keys = [
        "prediction_result",
        "root_cause_result",
        "demand_forecast_result",
        "customer_service_result",
        "compensation_result",
        "infrastructure_health_result",
        "route_optimization_result"
    ]

    for key in result_keys:
        if state.get(key):
            agent_name = key.replace("_result", "")
            aggregated["results"][agent_name] = state[key]

    return aggregated
