"""
LangGraph Baggage Lifecycle Orchestrator

Manages the complete baggage journey as a stateful graph with agent coordination.
"""

import logging
from typing import Dict, Any, Optional, Literal
from datetime import datetime, timedelta
import uuid

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .orchestrator_state import (
    OrchestratorState,
    BagState,
    BagStatus,
    RiskLevel,
    EventType,
    BagEvent,
    Alert,
    Intervention,
    ApprovalStatus,
    MishandlingState,
    create_initial_bag_state,
    create_initial_orchestrator_state
)

logger = logging.getLogger(__name__)


class BaggageOrchestrator:
    """
    LangGraph-based orchestrator for baggage lifecycle management.

    Coordinates all 8 agents and manages the complete bag journey from
    check-in to delivery, with human-in-the-loop decision points.
    """

    def __init__(
        self,
        agents: Optional[Dict[str, Any]] = None,
        db_manager: Optional[Any] = None,
        enable_checkpoints: bool = True
    ):
        """
        Initialize the baggage orchestrator.

        Args:
            agents: Dictionary of initialized agents
            db_manager: Database manager for state persistence
            enable_checkpoints: Whether to enable state checkpointing
        """
        self.agents = agents or {}
        self.db_manager = db_manager
        self.enable_checkpoints = enable_checkpoints
        self.logger = logging.getLogger(__name__)

        # Create checkpoint saver
        self.checkpointer = MemorySaver() if enable_checkpoints else None

        # Build the state graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine for baggage lifecycle.

        Returns:
            Compiled StateGraph
        """
        # Create graph with OrchestratorState
        workflow = StateGraph(OrchestratorState)

        # Add nodes for each stage
        workflow.add_node("check_in", self.check_in_node)
        workflow.add_node("security_screening", self.security_screening_node)
        workflow.add_node("sorting", self.sorting_node)
        workflow.add_node("loading", self.loading_node)
        workflow.add_node("in_flight", self.in_flight_node)
        workflow.add_node("arrival", self.arrival_node)
        workflow.add_node("transfer", self.transfer_node)
        workflow.add_node("claim", self.claim_node)
        workflow.add_node("delivered", self.delivered_node)

        # Mishandling sub-graph nodes
        workflow.add_node("mishandled", self.mishandled_node)
        workflow.add_node("root_cause_analysis", self.root_cause_analysis_node)
        workflow.add_node("compensation", self.compensation_node)

        # Human-in-the-loop nodes
        workflow.add_node("request_approval", self.request_approval_node)
        workflow.add_node("wait_for_approval", self.wait_for_approval_node)

        # Set entry point
        workflow.set_entry_point("check_in")

        # Normal flow edges
        workflow.add_edge("check_in", "security_screening")
        workflow.add_edge("security_screening", "sorting")

        # Conditional edge from sorting
        workflow.add_conditional_edges(
            "sorting",
            self.route_from_sorting,
            {
                "loading": "loading",
                "mishandled": "mishandled"
            }
        )

        workflow.add_edge("loading", "in_flight")

        # Conditional edge from in_flight
        workflow.add_conditional_edges(
            "in_flight",
            self.route_from_in_flight,
            {
                "arrival": "arrival",
                "transfer": "transfer"
            }
        )

        # Conditional edge from arrival
        workflow.add_conditional_edges(
            "arrival",
            self.route_from_arrival,
            {
                "claim": "claim",
                "mishandled": "mishandled"
            }
        )

        # Transfer handling
        workflow.add_conditional_edges(
            "transfer",
            self.route_from_transfer,
            {
                "sorting": "sorting",
                "mishandled": "mishandled"
            }
        )

        # Claim handling
        workflow.add_conditional_edges(
            "claim",
            self.route_from_claim,
            {
                "delivered": "delivered",
                "request_approval": "request_approval"
            }
        )

        # Approval workflow
        workflow.add_edge("request_approval", "wait_for_approval")
        workflow.add_conditional_edges(
            "wait_for_approval",
            self.route_from_approval,
            {
                "delivered": "delivered",
                "mishandled": "mishandled"
            }
        )

        # Mishandling workflow
        workflow.add_edge("mishandled", "root_cause_analysis")
        workflow.add_edge("root_cause_analysis", "compensation")
        workflow.add_conditional_edges(
            "compensation",
            self.route_from_compensation,
            {
                "request_approval": "request_approval",
                END: END
            }
        )

        # Delivered is terminal
        workflow.add_edge("delivered", END)

        # Compile graph
        if self.checkpointer:
            return workflow.compile(checkpointer=self.checkpointer)
        return workflow.compile()

    # =====================================================================
    # NODE IMPLEMENTATIONS
    # =====================================================================

    async def check_in_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """
        Handle check-in stage.

        - Update bag status
        - Invoke prediction agent to assess risk
        - Create alerts if needed
        """
        self.logger.info(f"Processing check-in for bag {state['bag']['bag_id']}")

        # Update status
        state["bag"]["current_status"] = BagStatus.CHECK_IN
        state["bag"]["updated_at"] = datetime.utcnow().isoformat()
        state["current_node"] = "check_in"

        # Add event
        event = self._create_event(
            EventType.STATUS_UPDATE,
            state["bag"]["current_location"],
            {"status": "check_in"}
        )
        state["bag"]["events"].append(event)

        # Invoke prediction agent if available
        if "prediction" in self.agents:
            try:
                prediction_result = await self.agents["prediction"].run({
                    "flight_id": state["bag"]["origin_flight"],
                    "departure_airport": state["bag"]["origin_airport"],
                    "arrival_airport": state["bag"]["destination_airport"],
                    "connection_time": state["connection"]["connection_time_minutes"]
                    if state.get("connection") else None
                })

                state["bag"]["prediction_result"] = prediction_result
                state["bag"]["risk_score"] = prediction_result.get("risk_score", 0)
                state["bag"]["risk_level"] = RiskLevel(
                    prediction_result.get("risk_level", "low").lower()
                )
                state["agents_invoked"].append("prediction")

                # Create alert if high risk
                if state["bag"]["risk_level"] in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    alert = self._create_alert(
                        RiskLevel.HIGH,
                        f"High risk connection detected: {prediction_result.get('risk_score')}%"
                    )
                    state["bag"]["alerts"].append(alert)

            except Exception as e:
                self.logger.error(f"Prediction agent error: {e}")
                state["errors"].append({"node": "check_in", "error": str(e)})

        state["previous_nodes"].append("check_in")
        return state

    async def security_screening_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """Handle security screening stage."""
        self.logger.info(f"Processing security screening for bag {state['bag']['bag_id']}")

        state["bag"]["current_status"] = BagStatus.SECURITY_SCREENING
        state["bag"]["updated_at"] = datetime.utcnow().isoformat()
        state["current_node"] = "security_screening"

        event = self._create_event(
            EventType.STATUS_UPDATE,
            state["bag"]["current_location"],
            {"status": "security_screening"}
        )
        state["bag"]["events"].append(event)

        state["previous_nodes"].append("security_screening")
        return state

    async def sorting_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """
        Handle sorting stage.

        - Check infrastructure health
        - Determine routing
        """
        self.logger.info(f"Processing sorting for bag {state['bag']['bag_id']}")

        state["bag"]["current_status"] = BagStatus.SORTING
        state["bag"]["updated_at"] = datetime.utcnow().isoformat()
        state["current_node"] = "sorting"

        # Check infrastructure health
        if "infrastructure_health" in self.agents:
            try:
                health_result = await self.agents["infrastructure_health"].run({
                    "airport_code": state["bag"]["current_location"],
                    "equipment_type": "sorting_system"
                })

                state["agent_results"]["infrastructure_health"] = health_result

                # Check if sorting system is degraded
                if health_result.get("overall_health", 100) < 70:
                    alert = self._create_alert(
                        RiskLevel.MEDIUM,
                        "Sorting system degraded - may cause delays"
                    )
                    state["bag"]["alerts"].append(alert)

            except Exception as e:
                self.logger.error(f"Infrastructure health agent error: {e}")

        event = self._create_event(
            EventType.STATUS_UPDATE,
            state["bag"]["current_location"],
            {"status": "sorting"}
        )
        state["bag"]["events"].append(event)

        state["previous_nodes"].append("sorting")
        return state

    async def loading_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """Handle loading stage."""
        self.logger.info(f"Processing loading for bag {state['bag']['bag_id']}")

        state["bag"]["current_status"] = BagStatus.LOADING
        state["bag"]["updated_at"] = datetime.utcnow().isoformat()
        state["current_node"] = "loading"

        event = self._create_event(
            EventType.STATUS_UPDATE,
            state["bag"]["current_location"],
            {"status": "loading", "flight": state["bag"]["origin_flight"]}
        )
        state["bag"]["events"].append(event)

        state["previous_nodes"].append("loading")
        return state

    async def in_flight_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """Handle in-flight stage."""
        self.logger.info(f"Processing in-flight for bag {state['bag']['bag_id']}")

        state["bag"]["current_status"] = BagStatus.IN_FLIGHT
        state["bag"]["updated_at"] = datetime.utcnow().isoformat()
        state["current_node"] = "in_flight"

        event = self._create_event(
            EventType.STATUS_UPDATE,
            "IN_FLIGHT",
            {"flight": state["bag"]["origin_flight"]}
        )
        state["bag"]["events"].append(event)

        state["previous_nodes"].append("in_flight")
        return state

    async def arrival_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """Handle arrival stage."""
        self.logger.info(f"Processing arrival for bag {state['bag']['bag_id']}")

        state["bag"]["current_status"] = BagStatus.ARRIVAL
        state["bag"]["current_location"] = state["bag"]["destination_airport"]
        state["bag"]["updated_at"] = datetime.utcnow().isoformat()
        state["current_node"] = "arrival"

        event = self._create_event(
            EventType.STATUS_UPDATE,
            state["bag"]["destination_airport"],
            {"status": "arrival"}
        )
        state["bag"]["events"].append(event)

        state["previous_nodes"].append("arrival")
        return state

    async def transfer_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """
        Handle transfer stage for connections.

        - Invoke route optimization agent
        - Check connection timing
        - Assign handlers if at-risk
        """
        self.logger.info(f"Processing transfer for bag {state['bag']['bag_id']}")

        state["bag"]["current_status"] = BagStatus.TRANSFER
        state["bag"]["updated_at"] = datetime.utcnow().isoformat()
        state["current_node"] = "transfer"

        # Invoke route optimization for connection
        if "route_optimization" in self.agents and state.get("connection"):
            try:
                route_result = await self.agents["route_optimization"].run({
                    "origin": state["bag"]["origin_airport"],
                    "destination": state["bag"]["destination_airport"],
                    "via": [state["bag"]["connection_airport"]]
                })

                state["bag"]["route_optimization_result"] = route_result
                state["agents_invoked"].append("route_optimization")

                # Check if connection is at risk
                if state["connection"]:
                    state["connection"]["connection_at_risk"] = (
                        route_result.get("optimal_route", {})
                        .get("reliability_score", 1.0) < 0.85
                    )

            except Exception as e:
                self.logger.error(f"Route optimization agent error: {e}")

        event = self._create_event(
            EventType.STATUS_UPDATE,
            state["bag"]["connection_airport"] or state["bag"]["current_location"],
            {"status": "transfer"}
        )
        state["bag"]["events"].append(event)

        state["previous_nodes"].append("transfer")
        return state

    async def claim_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """Handle baggage claim stage."""
        self.logger.info(f"Processing claim for bag {state['bag']['bag_id']}")

        state["bag"]["current_status"] = BagStatus.CLAIM
        state["bag"]["updated_at"] = datetime.utcnow().isoformat()
        state["current_node"] = "claim"

        event = self._create_event(
            EventType.STATUS_UPDATE,
            state["bag"]["destination_airport"],
            {"status": "claim"}
        )
        state["bag"]["events"].append(event)

        state["previous_nodes"].append("claim")
        return state

    async def delivered_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """Handle delivered (terminal) stage."""
        self.logger.info(f"Bag {state['bag']['bag_id']} delivered successfully")

        state["bag"]["current_status"] = BagStatus.DELIVERED
        state["bag"]["updated_at"] = datetime.utcnow().isoformat()
        state["current_node"] = "delivered"
        state["status"] = "completed"
        state["completed_at"] = datetime.utcnow().isoformat()

        event = self._create_event(
            EventType.STATUS_UPDATE,
            state["bag"]["destination_airport"],
            {"status": "delivered"}
        )
        state["bag"]["events"].append(event)

        state["previous_nodes"].append("delivered")
        return state

    async def mishandled_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """Handle mishandling detection."""
        self.logger.warning(f"Mishandling detected for bag {state['bag']['bag_id']}")

        # Determine mishandling type based on current status
        mishandling_type = "delayed"  # Default
        if state["bag"]["current_status"] == BagStatus.LOST:
            mishandling_type = "lost"
        elif state["bag"]["current_status"] == BagStatus.DAMAGED:
            mishandling_type = "damaged"

        state["bag"]["updated_at"] = datetime.utcnow().isoformat()
        state["current_node"] = "mishandled"

        # Create alert
        alert = self._create_alert(
            RiskLevel.HIGH,
            f"Bag mishandled: {mishandling_type}"
        )
        state["bag"]["alerts"].append(alert)

        # Invoke customer service agent
        if "customer_service" in self.agents:
            try:
                cs_result = await self.agents["customer_service"].run({
                    "customer_query": f"Baggage {mishandling_type}",
                    "bag_tag": state["bag"]["tag_number"]
                })
                state["agent_results"]["customer_service"] = cs_result
                state["agents_invoked"].append("customer_service")
            except Exception as e:
                self.logger.error(f"Customer service agent error: {e}")

        state["previous_nodes"].append("mishandled")
        return state

    async def root_cause_analysis_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """Perform root cause analysis on mishandling."""
        self.logger.info(f"Performing root cause analysis for bag {state['bag']['bag_id']}")

        # Invoke root cause agent
        if "root_cause" in self.agents:
            try:
                rca_result = await self.agents["root_cause"].run({
                    "incident_id": f"INC-{state['bag']['bag_id']}",
                    "incident_type": state["bag"]["current_status"]
                })
                state["agent_results"]["root_cause"] = rca_result
                state["agents_invoked"].append("root_cause")
            except Exception as e:
                self.logger.error(f"Root cause agent error: {e}")

        state["current_node"] = "root_cause_analysis"
        state["previous_nodes"].append("root_cause_analysis")
        return state

    async def compensation_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """Calculate and process compensation."""
        self.logger.info(f"Processing compensation for bag {state['bag']['bag_id']}")

        # Invoke compensation agent
        if "compensation" in self.agents:
            try:
                comp_result = await self.agents["compensation"].run({
                    "claim_id": f"CLM-{state['bag']['bag_id']}",
                    "incident_type": state["bag"]["current_status"],
                    "declared_value": state["bag"]["declared_value"]
                })
                state["agent_results"]["compensation"] = comp_result
                state["agents_invoked"].append("compensation")

                # Check if approval needed
                comp_amount = comp_result.get("compensation_amount", 0)
                if comp_amount > state["intervention"]["approval_threshold_value"]:
                    state["intervention"]["requires_approval"] = True
                    state["intervention"]["approver_role"] = "supervisor"

            except Exception as e:
                self.logger.error(f"Compensation agent error: {e}")

        state["current_node"] = "compensation"
        state["previous_nodes"].append("compensation")
        return state

    async def request_approval_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """Request human approval for high-value actions."""
        self.logger.info(f"Requesting approval for bag {state['bag']['bag_id']}")

        # Create intervention requiring approval
        intervention = Intervention(
            intervention_id=str(uuid.uuid4()),
            action="deliver_high_value_bag",
            reason=f"Declared value: ${state['bag']['declared_value']}",
            priority=1,
            requires_approval=True,
            approval_status=ApprovalStatus.PENDING,
            approved_by=None,
            approved_at=None,
            executed=False,
            executed_at=None,
            result=None
        )

        state["intervention"]["pending_interventions"].append(intervention)
        state["intervention"]["interventions_pending"] += 1

        state["current_node"] = "request_approval"
        state["previous_nodes"].append("request_approval")
        return state

    async def wait_for_approval_node(self, state: OrchestratorState) -> Dict[str, Any]:
        """
        Wait for approval (simulated - in production would pause execution).

        In real implementation, this would use interrupt/resume functionality.
        """
        self.logger.info(f"Waiting for approval for bag {state['bag']['bag_id']}")

        # In production, this would check database for approval status
        # For now, simulate auto-approval after timeout
        state["current_node"] = "wait_for_approval"
        state["previous_nodes"].append("wait_for_approval")

        # Simulate timeout approval
        if state["intervention"]["pending_interventions"]:
            intervention = state["intervention"]["pending_interventions"][0]
            intervention["approval_status"] = ApprovalStatus.TIMEOUT
            intervention["executed"] = True
            intervention["executed_at"] = datetime.utcnow().isoformat()

        return state

    # =====================================================================
    # CONDITIONAL EDGE FUNCTIONS
    # =====================================================================

    def route_from_sorting(self, state: OrchestratorState) -> str:
        """Determine next node from sorting."""
        # Check if bag was not sorted properly
        # For now, always go to loading
        return "loading"

    def route_from_in_flight(self, state: OrchestratorState) -> str:
        """Determine next node from in_flight."""
        # Check if bag has connection
        if state.get("connection") and state["connection"]["has_connection"]:
            return "transfer"
        return "arrival"

    def route_from_arrival(self, state: OrchestratorState) -> str:
        """Determine next node from arrival."""
        # Check if bag arrived successfully
        # For now, always go to claim
        return "claim"

    def route_from_transfer(self, state: OrchestratorState) -> str:
        """Determine next node from transfer."""
        # After transfer, go back to sorting for connection flight
        return "sorting"

    def route_from_claim(self, state: OrchestratorState) -> str:
        """Determine next node from claim."""
        # Check if high-value bag requiring approval
        if state["bag"]["declared_value"] > 5000:
            return "request_approval"
        return "delivered"

    def route_from_approval(self, state: OrchestratorState) -> str:
        """Determine next node from approval."""
        # Check approval status
        if state["intervention"]["pending_interventions"]:
            intervention = state["intervention"]["pending_interventions"][0]
            if intervention["approval_status"] in [ApprovalStatus.APPROVED, ApprovalStatus.TIMEOUT]:
                return "delivered"
        return "mishandled"

    def route_from_compensation(self, state: OrchestratorState) -> str:
        """Determine next node from compensation."""
        # Check if compensation requires approval
        if state["intervention"]["requires_approval"]:
            return "request_approval"
        return END

    # =====================================================================
    # HELPER METHODS
    # =====================================================================

    def _create_event(
        self,
        event_type: EventType,
        location: str,
        details: Dict[str, Any]
    ) -> BagEvent:
        """Create a bag event."""
        return BagEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            location=location,
            details=details,
            source="orchestrator"
        )

    def _create_alert(self, severity: RiskLevel, message: str) -> Alert:
        """Create an alert."""
        return Alert(
            alert_id=str(uuid.uuid4()),
            severity=severity,
            message=message,
            created_at=datetime.utcnow().isoformat(),
            resolved_at=None,
            assigned_to=None
        )

    # =====================================================================
    # PUBLIC API
    # =====================================================================

    async def process_bag(
        self,
        bag_state: BagState,
        has_connection: bool = False
    ) -> OrchestratorState:
        """
        Process a bag through the complete lifecycle.

        Args:
            bag_state: Initial bag state
            has_connection: Whether bag has a connection

        Returns:
            Final orchestrator state
        """
        # Create initial orchestrator state
        initial_state = create_initial_orchestrator_state(bag_state, has_connection)

        # Run the graph
        config = {"configurable": {"thread_id": bag_state["bag_id"]}}
        result = await self.graph.ainvoke(initial_state, config=config)

        return result

    async def handle_external_event(
        self,
        bag_id: str,
        event_type: EventType,
        event_data: Dict[str, Any]
    ) -> Optional[OrchestratorState]:
        """
        Handle external event (RFID scan, flight delay, etc.).

        Args:
            bag_id: Bag identifier
            event_type: Type of event
            event_data: Event data

        Returns:
            Updated orchestrator state
        """
        # In production, would load state from checkpoint
        self.logger.info(f"Handling {event_type} event for bag {bag_id}")

        # For now, return None (would need checkpoint retrieval)
        return None

    def get_state(self, bag_id: str) -> Optional[OrchestratorState]:
        """
        Get current state for a bag.

        Args:
            bag_id: Bag identifier

        Returns:
            Current orchestrator state or None
        """
        # In production, would query checkpointer or database
        return None
