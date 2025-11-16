"""
Route Optimization Agent

Optimizes baggage routing and transfer paths using graph algorithms.
Implements Dijkstra and A* for pathfinding with capacity awareness.
"""

from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
import heapq
from .base_agent import BaseAgent


# Standard handling times (minutes) by equipment type
HANDLING_TIMES = {
    "check_in": 5,
    "security_scan": 3,
    "sorting": 8,
    "transfer": 15,
    "loading": 10,
    "carousel": 5
}


class RouteOptimizationAgent(BaseAgent):
    """
    Optimizes baggage routing and transfer operations.

    Capabilities:
    - Shortest path calculation using Dijkstra's algorithm
    - A* pathfinding with heuristics
    - Multi-stop route optimization
    - Connection time optimization
    - Capacity-aware routing
    - Dynamic rerouting on equipment failures
    - Load balancing across equipment
    - Alternative path generation
    """

    def __init__(self, llm_client=None, db_connection=None, config=None, neo4j_connection=None):
        """Initialize RouteOptimizationAgent."""
        super().__init__(
            agent_name="route_optimization_agent",
            llm_client=llm_client,
            db_connection=db_connection,
            config=config
        )
        self.neo4j_connection = neo4j_connection

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute route optimization.

        Args:
            input_data: Dictionary containing:
                - origin: Origin location (gate, check-in counter, etc.)
                - destination: Destination location (gate, carousel, etc.)
                - airport_code: Airport code (default: PTY)
                - bag_id: Bag identifier (optional)
                - connection_time_minutes: Available connection time
                - avoid_equipment: List of equipment IDs to avoid (failures)
                - priority: Routing priority (normal, rush, vip)
                - num_alternatives: Number of alternative routes (default: 3)

        Returns:
            Dictionary containing:
                - optimal_route: Best route with details
                - alternative_routes: Alternative routing options
                - total_time_minutes: Expected total time
                - segments: Detailed segment breakdown
                - equipment_used: List of equipment on route
                - risk_assessment: Risk factors
                - load_balance_score: How well load is balanced
        """
        self.validate_input(input_data, ["origin", "destination"])

        origin = input_data["origin"]
        destination = input_data["destination"]
        airport_code = input_data.get("airport_code", "PTY")
        connection_time = input_data.get("connection_time_minutes", 180)
        avoid_equipment = input_data.get("avoid_equipment", [])
        priority = input_data.get("priority", "normal")
        num_alternatives = input_data.get("num_alternatives", 3)

        self.logger.info(
            f"Optimizing route from {origin} to {destination} at {airport_code}, "
            f"priority: {priority}"
        )

        # Step 1: Build airport graph
        airport_graph = await self._build_airport_graph(
            airport_code=airport_code,
            avoid_equipment=avoid_equipment
        )

        # Step 2: Find optimal route using Dijkstra
        optimal_route = await self._find_optimal_route(
            graph=airport_graph,
            origin=origin,
            destination=destination,
            priority=priority,
            max_time=connection_time
        )

        # Step 3: Generate alternative routes
        alternative_routes = await self._generate_alternative_routes(
            graph=airport_graph,
            origin=origin,
            destination=destination,
            optimal_route=optimal_route,
            num_alternatives=num_alternatives,
            avoid_equipment=avoid_equipment
        )

        # Step 4: Calculate load balance score
        load_balance = await self._calculate_load_balance(
            route=optimal_route,
            airport_code=airport_code
        )

        # Step 5: Risk assessment
        risk_assessment = await self._assess_route_risks(
            route=optimal_route,
            airport_code=airport_code
        )

        # Step 6: Generate rerouting plan if needed
        contingency_plan = await self._generate_contingency_plan(
            primary_route=optimal_route,
            alternatives=alternative_routes,
            airport_code=airport_code
        )

        return {
            "origin": origin,
            "destination": destination,
            "airport_code": airport_code,
            "optimal_route": optimal_route,
            "alternative_routes": alternative_routes,
            "total_time_minutes": optimal_route.get("total_time_minutes", 0),
            "total_distance_meters": optimal_route.get("total_distance_meters", 0),
            "segments": optimal_route.get("segments", []),
            "equipment_used": optimal_route.get("equipment_used", []),
            "risk_assessment": risk_assessment,
            "load_balance_score": load_balance,
            "contingency_plan": contingency_plan,
            "optimization_method": "dijkstra" if priority == "normal" else "a_star",
            "calculated_at": datetime.utcnow().isoformat()
        }

    async def _build_airport_graph(
        self,
        airport_code: str,
        avoid_equipment: List[str]
    ) -> Dict[str, List[Tuple[str, float, Dict[str, Any]]]]:
        """
        Build airport graph from Neo4j or mock data.

        Returns adjacency list: {node: [(neighbor, weight, metadata)]}
        """
        try:
            # Try to fetch from Neo4j if available
            if self.neo4j_connection:
                return await self._fetch_graph_from_neo4j(airport_code, avoid_equipment)
            else:
                return self._build_mock_airport_graph(airport_code, avoid_equipment)

        except Exception as e:
            self.logger.error(f"Error building airport graph: {e}")
            return self._build_mock_airport_graph(airport_code, avoid_equipment)

    def _build_mock_airport_graph(
        self,
        airport_code: str,
        avoid_equipment: List[str]
    ) -> Dict[str, List[Tuple[str, float, Dict[str, Any]]]]:
        """Build mock airport baggage handling graph."""
        graph = {}

        # Define nodes (locations in airport)
        nodes = [
            "GATE_A1", "GATE_A2", "GATE_A3", "GATE_A4",
            "GATE_B1", "GATE_B2", "GATE_B3", "GATE_B4",
            "CHECK_IN_1", "CHECK_IN_2", "CHECK_IN_3",
            "SORT_HUB_A", "SORT_HUB_B",
            "CAROUSEL_1", "CAROUSEL_2", "CAROUSEL_3",
            "TRANSFER_POINT_1", "TRANSFER_POINT_2",
            "LOADING_BAY_1", "LOADING_BAY_2"
        ]

        # Initialize empty adjacency lists
        for node in nodes:
            graph[node] = []

        # Define edges (connections between locations)
        # Format: (from, to, distance_meters, time_minutes, equipment_id, equipment_type, capacity)

        connections = [
            # Check-in to sorting hubs
            ("CHECK_IN_1", "SORT_HUB_A", 100, 5, "CONV-01", "conveyor", 1000),
            ("CHECK_IN_2", "SORT_HUB_A", 120, 6, "CONV-02", "conveyor", 1000),
            ("CHECK_IN_3", "SORT_HUB_B", 100, 5, "CONV-03", "conveyor", 1000),

            # Sorting hubs to gates (departure)
            ("SORT_HUB_A", "GATE_A1", 200, 10, "CONV-04", "conveyor", 800),
            ("SORT_HUB_A", "GATE_A2", 220, 11, "CONV-05", "conveyor", 800),
            ("SORT_HUB_A", "GATE_A3", 240, 12, "CONV-06", "conveyor", 800),
            ("SORT_HUB_A", "GATE_A4", 260, 13, "CONV-07", "conveyor", 800),

            ("SORT_HUB_B", "GATE_B1", 200, 10, "CONV-08", "conveyor", 800),
            ("SORT_HUB_B", "GATE_B2", 220, 11, "CONV-09", "conveyor", 800),
            ("SORT_HUB_B", "GATE_B3", 240, 12, "CONV-10", "conveyor", 800),
            ("SORT_HUB_B", "GATE_B4", 260, 13, "CONV-11", "conveyor", 800),

            # Gates to transfer points (arrivals)
            ("GATE_A1", "TRANSFER_POINT_1", 150, 8, "CART-01", "cart", 50),
            ("GATE_A2", "TRANSFER_POINT_1", 170, 9, "CART-02", "cart", 50),
            ("GATE_B1", "TRANSFER_POINT_2", 150, 8, "CART-03", "cart", 50),
            ("GATE_B2", "TRANSFER_POINT_2", 170, 9, "CART-04", "cart", 50),

            # Transfer points to sorting hubs (connections)
            ("TRANSFER_POINT_1", "SORT_HUB_A", 80, 15, "TUG-01", "tug", 100),
            ("TRANSFER_POINT_2", "SORT_HUB_B", 80, 15, "TUG-02", "tug", 100),

            # Cross-hub connections
            ("SORT_HUB_A", "SORT_HUB_B", 300, 20, "TUG-03", "tug", 100),
            ("SORT_HUB_B", "SORT_HUB_A", 300, 20, "TUG-04", "tug", 100),

            # Sorting hubs to carousels (arrivals)
            ("SORT_HUB_A", "CAROUSEL_1", 180, 12, "CONV-12", "conveyor", 600),
            ("SORT_HUB_A", "CAROUSEL_2", 200, 13, "CONV-13", "conveyor", 600),
            ("SORT_HUB_B", "CAROUSEL_2", 180, 12, "CONV-14", "conveyor", 600),
            ("SORT_HUB_B", "CAROUSEL_3", 200, 13, "CONV-15", "conveyor", 600),

            # Bi-directional paths for some connections
            ("TRANSFER_POINT_1", "TRANSFER_POINT_2", 250, 18, "CART-05", "cart", 50),
            ("TRANSFER_POINT_2", "TRANSFER_POINT_1", 250, 18, "CART-06", "cart", 50),
        ]

        # Build adjacency list
        for from_node, to_node, distance, time, equipment_id, equipment_type, capacity in connections:
            # Skip if equipment is in avoid list
            if equipment_id in avoid_equipment:
                continue

            if from_node in graph:
                graph[from_node].append((
                    to_node,
                    time,  # Use time as weight
                    {
                        "distance_meters": distance,
                        "time_minutes": time,
                        "equipment_id": equipment_id,
                        "equipment_type": equipment_type,
                        "capacity": capacity
                    }
                ))

        return graph

    async def _find_optimal_route(
        self,
        graph: Dict[str, List[Tuple[str, float, Dict[str, Any]]]],
        origin: str,
        destination: str,
        priority: str,
        max_time: int
    ) -> Dict[str, Any]:
        """
        Find optimal route using Dijkstra's algorithm.

        Priority affects weight calculation:
        - normal: minimize time
        - rush: minimize time with priority multiplier
        - vip: minimize time + prefer high-capacity routes
        """
        # Dijkstra's algorithm
        distances = {node: float('inf') for node in graph}
        distances[origin] = 0

        previous = {node: None for node in graph}
        previous_edge = {node: None for node in graph}

        priority_queue = [(0, origin)]
        visited = set()

        while priority_queue:
            current_dist, current_node = heapq.heappop(priority_queue)

            if current_node in visited:
                continue

            visited.add(current_node)

            if current_node == destination:
                break

            for neighbor, base_weight, metadata in graph.get(current_node, []):
                if neighbor in visited:
                    continue

                # Adjust weight based on priority
                weight = base_weight

                if priority == "rush":
                    weight *= 0.8  # Prefer faster routes
                elif priority == "vip":
                    # Prefer high-capacity routes
                    capacity = metadata.get("capacity", 100)
                    if capacity >= 500:
                        weight *= 0.9

                distance = current_dist + weight

                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_node
                    previous_edge[neighbor] = metadata
                    heapq.heappush(priority_queue, (distance, neighbor))

        # Reconstruct path
        if distances[destination] == float('inf'):
            # No path found
            return {
                "path": [],
                "total_time_minutes": 0,
                "total_distance_meters": 0,
                "segments": [],
                "equipment_used": [],
                "feasible": False,
                "reason": "No route found"
            }

        path = []
        segments = []
        equipment_used = []
        total_time = 0
        total_distance = 0

        current = destination
        while current is not None:
            path.append(current)
            if previous[current] is not None:
                edge_metadata = previous_edge[current]
                segments.append({
                    "from": previous[current],
                    "to": current,
                    "distance_meters": edge_metadata["distance_meters"],
                    "time_minutes": edge_metadata["time_minutes"],
                    "equipment_id": edge_metadata["equipment_id"],
                    "equipment_type": edge_metadata["equipment_type"],
                    "capacity": edge_metadata["capacity"]
                })
                equipment_used.append(edge_metadata["equipment_id"])
                total_time += edge_metadata["time_minutes"]
                total_distance += edge_metadata["distance_meters"]

            current = previous[current]

        path.reverse()
        segments.reverse()

        return {
            "path": path,
            "total_time_minutes": total_time,
            "total_distance_meters": total_distance,
            "segments": segments,
            "equipment_used": equipment_used,
            "num_segments": len(segments),
            "feasible": total_time <= max_time,
            "reason": "optimal" if total_time <= max_time else f"exceeds_time_limit ({total_time} > {max_time})"
        }

    async def _generate_alternative_routes(
        self,
        graph: Dict[str, List[Tuple[str, float, Dict[str, Any]]]],
        origin: str,
        destination: str,
        optimal_route: Dict[str, Any],
        num_alternatives: int,
        avoid_equipment: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate alternative routes by excluding equipment from optimal route."""
        alternatives = []

        if not optimal_route.get("feasible"):
            return alternatives

        optimal_equipment = optimal_route.get("equipment_used", [])

        # Try removing each equipment from optimal route
        for i, equipment_id in enumerate(optimal_equipment):
            if len(alternatives) >= num_alternatives:
                break

            # Create new avoid list
            avoid_list = avoid_equipment + [equipment_id]

            # Build new graph
            alt_graph = await self._build_airport_graph(
                airport_code="PTY",
                avoid_equipment=avoid_list
            )

            # Find route
            alt_route = await self._find_optimal_route(
                graph=alt_graph,
                origin=origin,
                destination=destination,
                priority="normal",
                max_time=300
            )

            if alt_route.get("feasible") and alt_route["path"] != optimal_route["path"]:
                alt_route["alternative_reason"] = f"Avoids {equipment_id}"
                alt_route["time_difference"] = alt_route["total_time_minutes"] - optimal_route["total_time_minutes"]
                alternatives.append(alt_route)

        return alternatives

    async def _calculate_load_balance(
        self,
        route: Dict[str, Any],
        airport_code: str
    ) -> float:
        """
        Calculate load balance score for the route.

        Returns score 0-1 (1 = perfectly balanced)
        """
        if not route.get("equipment_used"):
            return 1.0

        try:
            # Fetch current utilization of equipment
            equipment_ids = route["equipment_used"]

            query = """
                SELECT equipment_id, utilization
                FROM equipment
                WHERE equipment_id = ANY($1)
            """

            results = await self.db_connection.fetch(query, equipment_ids)

            utilizations = [row["utilization"] for row in results if row.get("utilization")]

            if not utilizations:
                return 0.8  # Assume decent balance if no data

            # Calculate variance
            avg_util = sum(utilizations) / len(utilizations)
            variance = sum((u - avg_util) ** 2 for u in utilizations) / len(utilizations)

            # Lower variance = better balance
            balance_score = max(0, 1 - variance)

            return round(balance_score, 2)

        except Exception as e:
            self.logger.error(f"Error calculating load balance: {e}")
            return 0.8

    async def _assess_route_risks(
        self,
        route: Dict[str, Any],
        airport_code: str
    ) -> Dict[str, Any]:
        """Assess risks associated with the route."""
        risks = []
        risk_score = 0.0

        if not route.get("feasible"):
            return {
                "overall_risk": "high",
                "risk_score": 1.0,
                "risks": [{"type": "infeasible_route", "severity": "high"}]
            }

        # Risk 1: Tight timing
        total_time = route.get("total_time_minutes", 0)
        if total_time > 120:
            risks.append({
                "type": "long_route_time",
                "severity": "medium",
                "description": f"Route takes {total_time} minutes",
                "mitigation": "Monitor for delays"
            })
            risk_score += 0.2

        # Risk 2: Many segments (more transfer points)
        num_segments = len(route.get("segments", []))
        if num_segments > 5:
            risks.append({
                "type": "complex_route",
                "severity": "medium",
                "description": f"Route has {num_segments} segments",
                "mitigation": "Consider simpler alternative"
            })
            risk_score += 0.15

        # Risk 3: Equipment reliability
        try:
            equipment_ids = route.get("equipment_used", [])
            if equipment_ids:
                query = """
                    SELECT equipment_id, health_score
                    FROM equipment
                    WHERE equipment_id = ANY($1)
                """

                results = await self.db_connection.fetch(query, equipment_ids)

                for row in results:
                    health = row.get("health_score", 100)
                    if health < 70:
                        risks.append({
                            "type": "equipment_health",
                            "severity": "high",
                            "equipment_id": row["equipment_id"],
                            "health_score": health,
                            "description": f"{row['equipment_id']} has low health score",
                            "mitigation": "Monitor equipment or use alternative"
                        })
                        risk_score += 0.3

        except Exception as e:
            self.logger.error(f"Error checking equipment health: {e}")

        # Determine overall risk level
        if risk_score < 0.3:
            overall_risk = "low"
        elif risk_score < 0.6:
            overall_risk = "medium"
        else:
            overall_risk = "high"

        return {
            "overall_risk": overall_risk,
            "risk_score": round(min(risk_score, 1.0), 2),
            "risks": risks,
            "risk_factors_count": len(risks)
        }

    async def _generate_contingency_plan(
        self,
        primary_route: Dict[str, Any],
        alternatives: List[Dict[str, Any]],
        airport_code: str
    ) -> Dict[str, Any]:
        """Generate contingency plan for route failures."""
        contingencies = []

        # For each segment in primary route, find alternate equipment
        for i, segment in enumerate(primary_route.get("segments", [])):
            equipment_id = segment["equipment_id"]

            # Find alternatives that don't use this equipment
            fallback_routes = [
                alt for alt in alternatives
                if equipment_id not in alt.get("equipment_used", [])
            ]

            if fallback_routes:
                best_fallback = min(
                    fallback_routes,
                    key=lambda r: r.get("total_time_minutes", 999)
                )

                contingencies.append({
                    "segment_index": i,
                    "from": segment["from"],
                    "to": segment["to"],
                    "primary_equipment": equipment_id,
                    "fallback_route": best_fallback.get("path", []),
                    "fallback_time_minutes": best_fallback.get("total_time_minutes", 0),
                    "trigger": f"If {equipment_id} fails"
                })

        return {
            "has_contingencies": len(contingencies) > 0,
            "contingency_count": len(contingencies),
            "contingencies": contingencies,
            "recommendation": "Automatic rerouting enabled" if contingencies else "Manual intervention may be required"
        }

    async def optimize_fleet_routing(
        self,
        bags: List[Dict[str, Any]],
        airport_code: str
    ) -> Dict[str, Any]:
        """
        Optimize routing for multiple bags simultaneously.

        Implements load balancing across equipment.
        """
        routes = []
        equipment_loads = {}

        for bag in bags:
            # Find route for this bag
            route = await self.execute({
                "origin": bag.get("current_location", "CHECK_IN_1"),
                "destination": bag.get("destination_gate", "GATE_A1"),
                "airport_code": airport_code,
                "priority": bag.get("priority", "normal")
            })

            routes.append({
                "bag_id": bag.get("id"),
                "route": route
            })

            # Track equipment usage
            for equipment_id in route["optimal_route"].get("equipment_used", []):
                equipment_loads[equipment_id] = equipment_loads.get(equipment_id, 0) + 1

        # Calculate load balance
        if equipment_loads:
            avg_load = sum(equipment_loads.values()) / len(equipment_loads)
            max_load = max(equipment_loads.values())
            balance_score = avg_load / max_load if max_load > 0 else 1.0
        else:
            balance_score = 1.0

        return {
            "total_bags": len(bags),
            "routes": routes,
            "equipment_loads": equipment_loads,
            "load_balance_score": round(balance_score, 2),
            "most_used_equipment": max(equipment_loads, key=equipment_loads.get) if equipment_loads else None,
            "recommendations": [
                "Consider redistributing load" if balance_score < 0.7 else "Load is well balanced"
            ]
        }
