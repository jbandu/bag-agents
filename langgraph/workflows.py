"""
LangGraph Workflow Implementations.

Defines specific workflows for different baggage operations use cases.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .state_graph import (
    IncidentAnalysisState,
    OperationalOptimizationState,
    CustomerServiceState
)


async def run_prediction_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute prediction agent node.

    Args:
        state: Current workflow state

    Returns:
        Updated state with prediction results
    """
    # Import here to avoid circular dependencies
    from agents.prediction_agent import PredictionAgent

    agent = PredictionAgent()
    result = await agent.run(state.get("input_parameters", {}))

    return {
        **state,
        "prediction": result,
        "completed_steps": ["prediction"],
        "current_step": "prediction"
    }


async def run_root_cause_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute root cause agent node.

    Args:
        state: Current workflow state

    Returns:
        Updated state with root cause results
    """
    from agents.root_cause_agent import RootCauseAgent

    agent = RootCauseAgent()
    result = await agent.run(state.get("input_parameters", {}))

    return {
        **state,
        "root_cause": result,
        "completed_steps": ["root_cause"],
        "current_step": "root_cause"
    }


async def run_compensation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute compensation agent node.

    Args:
        state: Current workflow state

    Returns:
        Updated state with compensation results
    """
    from agents.compensation_agent import CompensationAgent

    agent = CompensationAgent()
    result = await agent.run(state.get("input_parameters", {}))

    return {
        **state,
        "compensation": result,
        "completed_steps": ["compensation"],
        "current_step": "compensation"
    }


async def run_demand_forecast_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute demand forecast agent node.

    Args:
        state: Current workflow state

    Returns:
        Updated state with demand forecast results
    """
    from agents.demand_forecast_agent import DemandForecastAgent

    agent = DemandForecastAgent()
    result = await agent.run(state.get("input_parameters", {}))

    return {
        **state,
        "demand_forecast": result,
        "completed_steps": ["demand_forecast"],
        "current_step": "demand_forecast"
    }


async def run_route_optimization_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute route optimization agent node.

    Args:
        state: Current workflow state

    Returns:
        Updated state with route optimization results
    """
    from agents.route_optimization_agent import RouteOptimizationAgent

    agent = RouteOptimizationAgent()
    result = await agent.run(state.get("input_parameters", {}))

    return {
        **state,
        "route_optimization": result,
        "completed_steps": ["route_optimization"],
        "current_step": "route_optimization"
    }


async def run_infrastructure_health_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute infrastructure health agent node.

    Args:
        state: Current workflow state

    Returns:
        Updated state with infrastructure health results
    """
    from agents.infrastructure_health_agent import InfrastructureHealthAgent

    agent = InfrastructureHealthAgent()
    result = await agent.run(state.get("input_parameters", {}))

    return {
        **state,
        "infrastructure_health": result,
        "completed_steps": ["infrastructure_health"],
        "current_step": "infrastructure_health"
    }


async def run_customer_service_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute customer service agent node.

    Args:
        state: Current workflow state

    Returns:
        Updated state with customer service results
    """
    from agents.customer_service_agent import CustomerServiceAgent

    agent = CustomerServiceAgent()
    result = await agent.run(state.get("input_parameters", {}))

    return {
        **state,
        "service_response": result,
        "completed_steps": ["customer_service"],
        "current_step": "customer_service",
        "escalate": result.get("escalate", False)
    }


def incident_analysis_workflow() -> StateGraph:
    """
    Create incident analysis workflow.

    Flow: Prediction -> Root Cause -> Compensation

    Returns:
        Configured StateGraph
    """
    workflow = StateGraph(IncidentAnalysisState)

    # Add nodes
    workflow.add_node("prediction", run_prediction_node)
    workflow.add_node("root_cause", run_root_cause_node)
    workflow.add_node("compensation", run_compensation_node)

    # Add edges
    workflow.set_entry_point("prediction")
    workflow.add_edge("prediction", "root_cause")
    workflow.add_edge("root_cause", "compensation")
    workflow.add_edge("compensation", END)

    return workflow.compile()


def operational_optimization_workflow() -> StateGraph:
    """
    Create operational optimization workflow.

    Flow: Demand Forecast -> Route Optimization -> Infrastructure Health

    Returns:
        Configured StateGraph
    """
    workflow = StateGraph(OperationalOptimizationState)

    # Add nodes
    workflow.add_node("demand_forecast", run_demand_forecast_node)
    workflow.add_node("route_optimization", run_route_optimization_node)
    workflow.add_node("infrastructure_health", run_infrastructure_health_node)

    # Add edges (can run in parallel, but we'll do sequential for now)
    workflow.set_entry_point("demand_forecast")
    workflow.add_edge("demand_forecast", "route_optimization")
    workflow.add_edge("route_optimization", "infrastructure_health")
    workflow.add_edge("infrastructure_health", END)

    return workflow.compile()


def customer_service_workflow() -> StateGraph:
    """
    Create customer service workflow.

    Flow: Customer Service -> Prediction (conditional) -> Response

    Returns:
        Configured StateGraph
    """
    workflow = StateGraph(CustomerServiceState)

    # Add nodes
    workflow.add_node("customer_service", run_customer_service_node)
    workflow.add_node("bag_prediction", run_prediction_node)

    # Conditional edge based on whether escalation is needed
    def should_predict(state: CustomerServiceState) -> str:
        """Determine if we need bag prediction."""
        if state.get("bag_tag"):
            return "bag_prediction"
        return END

    # Add edges
    workflow.set_entry_point("customer_service")
    workflow.add_conditional_edges(
        "customer_service",
        should_predict,
        {
            "bag_prediction": "bag_prediction",
            END: END
        }
    )
    workflow.add_edge("bag_prediction", END)

    return workflow.compile()


async def execute_workflow(
    workflow_type: str,
    input_parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a specific workflow.

    Args:
        workflow_type: Type of workflow to execute
        input_parameters: Input parameters for the workflow

    Returns:
        Workflow execution results

    Raises:
        ValueError: If workflow type is not recognized
    """
    workflows = {
        "incident_analysis": incident_analysis_workflow,
        "operational_optimization": operational_optimization_workflow,
        "customer_service": customer_service_workflow
    }

    if workflow_type not in workflows:
        raise ValueError(f"Unknown workflow type: {workflow_type}")

    # Get the workflow
    workflow = workflows[workflow_type]()

    # Prepare initial state
    initial_state = {
        "input_parameters": input_parameters,
        "completed_steps": [],
        "errors": []
    }

    # Execute workflow
    result = await workflow.ainvoke(initial_state)

    return result
