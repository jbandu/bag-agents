"""
Orchestrator Agent

Coordinates execution of multiple agents and manages complex workflows.
"""

from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent


class OrchestratorAgent(BaseAgent):
    """
    Orchestrates multi-agent workflows and coordinates agent interactions.

    Capabilities:
    - Dynamic agent selection
    - Workflow execution
    - Result aggregation
    - Dependency management
    - Error handling and retries
    """

    def __init__(
        self,
        llm_client=None,
        db_connection=None,
        config=None,
        available_agents: Optional[Dict[str, BaseAgent]] = None
    ):
        """
        Initialize OrchestratorAgent.

        Args:
            llm_client: LLM client instance
            db_connection: Database connection
            config: Configuration dictionary
            available_agents: Dictionary of registered agents
        """
        super().__init__(
            agent_name="orchestrator_agent",
            llm_client=llm_client,
            db_connection=db_connection,
            config=config
        )
        self.available_agents = available_agents or {}

    def register_agent(self, agent_name: str, agent: BaseAgent):
        """
        Register an agent with the orchestrator.

        Args:
            agent_name: Unique agent identifier
            agent: Agent instance
        """
        self.available_agents[agent_name] = agent
        self.logger.info(f"Registered agent: {agent_name}")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute orchestrated workflow.

        Args:
            input_data: Dictionary containing:
                - workflow_type: Type of workflow to execute
                - parameters: Workflow-specific parameters
                - agents: List of agents to invoke (optional)

        Returns:
            Dictionary containing:
                - workflow_id: Unique workflow identifier
                - results: Aggregated results from all agents
                - execution_plan: Which agents were executed
                - errors: Any errors encountered
        """
        self.validate_input(input_data, ["workflow_type", "parameters"])

        workflow_type = input_data["workflow_type"]
        parameters = input_data["parameters"]

        # Determine which agents to invoke based on workflow type
        execution_plan = self._plan_workflow(workflow_type, parameters)

        results = {}
        errors = []

        # Execute agents in order
        for step in execution_plan:
            agent_name = step["agent"]
            agent_input = step["input"]

            try:
                if agent_name in self.available_agents:
                    agent = self.available_agents[agent_name]
                    result = await agent.run(agent_input)
                    results[agent_name] = result
                else:
                    error_msg = f"Agent {agent_name} not found"
                    self.logger.warning(error_msg)
                    errors.append(error_msg)

            except Exception as e:
                error_msg = f"Error executing {agent_name}: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)

        return {
            "workflow_type": workflow_type,
            "execution_plan": execution_plan,
            "results": results,
            "errors": errors,
            "success": len(errors) == 0
        }

    def _plan_workflow(
        self,
        workflow_type: str,
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Plan the workflow execution based on type.

        Args:
            workflow_type: Type of workflow
            parameters: Workflow parameters

        Returns:
            List of execution steps
        """
        workflows = {
            "incident_analysis": [
                {
                    "agent": "prediction_agent",
                    "input": parameters
                },
                {
                    "agent": "root_cause_agent",
                    "input": parameters
                },
                {
                    "agent": "compensation_agent",
                    "input": parameters
                }
            ],
            "operational_optimization": [
                {
                    "agent": "demand_forecast_agent",
                    "input": parameters
                },
                {
                    "agent": "route_optimization_agent",
                    "input": parameters
                },
                {
                    "agent": "infrastructure_health_agent",
                    "input": parameters
                }
            ],
            "customer_inquiry": [
                {
                    "agent": "customer_service_agent",
                    "input": parameters
                },
                {
                    "agent": "prediction_agent",
                    "input": parameters
                }
            ]
        }

        return workflows.get(workflow_type, [])

    async def query_agent_capabilities(self) -> Dict[str, List[str]]:
        """
        Query all registered agents for their capabilities.

        Returns:
            Dictionary mapping agent names to capability descriptions
        """
        capabilities = {}

        for agent_name, agent in self.available_agents.items():
            capabilities[agent_name] = {
                "name": agent.agent_name,
                "class": agent.__class__.__name__,
                "description": agent.__class__.__doc__ or "No description available"
            }

        return capabilities
