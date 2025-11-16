"""
Root Cause Analysis Agent - Enhanced Implementation

Analyzes baggage mishandling incidents to determine root causes using:
- Graph database analysis (Neo4j)
- LLM-powered reasoning
- Pattern recognition across incidents
- Actionable recommendations generation
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json
from .base_agent import BaseAgent


class RootCauseAgent(BaseAgent):
    """
    Performs comprehensive root cause analysis on baggage mishandling incidents.

    Capabilities:
    - Graph-based relationship analysis
    - Pattern recognition across multiple incidents
    - System bottleneck identification
    - Actionable insights generation
    - Similarity detection using vector embeddings
    """

    # Primary root cause categories
    CAUSE_CATEGORIES = {
        "transfer_time_insufficient": "Transfer time < Minimum Connection Time",
        "equipment_failure": "Equipment breakdown or malfunction",
        "handler_error": "Human error in handling process",
        "flight_irregularity": "Flight delay, cancellation, or gate change",
        "routing_error": "Incorrect routing or destination tag",
        "weather_impact": "Severe weather conditions",
        "system_outage": "IT system failure (DCS, BHS)",
        "special_handling_failure": "Failure in handling special baggage",
        "airport_congestion": "Excessive airport traffic",
        "process_deviation": "Deviation from standard procedures"
    }

    def __init__(self, llm_client=None, db_connection=None, config=None):
        """Initialize RootCauseAgent with enhanced capabilities."""
        super().__init__(
            agent_name="root_cause_agent",
            llm_client=llm_client,
            db_connection=db_connection,
            config=config
        )

        # Confidence thresholds
        self.HIGH_CONFIDENCE = 0.85
        self.MEDIUM_CONFIDENCE = 0.70
        self.LOW_CONFIDENCE = 0.50

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute comprehensive root cause analysis.

        Args:
            input_data: Dictionary containing:
                - incident_id: Incident identifier
                - bag_id: Bag identifier
                - incident_type: Type (delayed, lost, damaged)
                - timeline: List of events (optional)
                - include_similar: Find similar incidents (default: True)

        Returns:
            Dictionary containing:
                - root_cause: Primary cause with confidence
                - contributing_factors: Secondary factors
                - similar_incidents: Past similar cases
                - recommendations: Actionable steps
                - pattern_detected: Boolean if part of larger pattern
        """
        self.validate_input(input_data, ["incident_id", "bag_id", "incident_type"])

        incident_id = input_data["incident_id"]
        bag_id = input_data["bag_id"]
        incident_type = input_data["incident_type"]
        include_similar = input_data.get("include_similar", True)

        self.logger.info(f"Analyzing incident {incident_id} for bag {bag_id}")

        # Step 1: Collect incident data
        incident_data = await self._collect_incident_data(bag_id, incident_id)

        # Step 2: Analyze bag journey
        journey_analysis = await self._analyze_bag_journey(bag_id, incident_data)

        # Step 3: Identify root cause using LLM
        root_cause = await self._identify_root_cause(
            incident_data,
            journey_analysis,
            incident_type
        )

        # Step 4: Find similar incidents
        similar_incidents = []
        if include_similar:
            similar_incidents = await self._find_similar_incidents(
                incident_data,
                root_cause["cause"]
            )

        # Step 5: Detect patterns
        pattern_detected = await self._detect_pattern(root_cause, similar_incidents)

        # Step 6: Generate recommendations
        recommendations = await self._generate_recommendations(
            root_cause,
            journey_analysis,
            pattern_detected
        )

        result = {
            "incident_id": incident_id,
            "bag_id": bag_id,
            "incident_type": incident_type,
            "root_cause": root_cause,
            "contributing_factors": journey_analysis.get("anomalies", []),
            "similar_incidents": similar_incidents,
            "pattern_detected": pattern_detected,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

        # Store analysis in database
        await self._store_analysis(incident_id, result)

        return result

    async def _collect_incident_data(
        self,
        bag_id: str,
        incident_id: str
    ) -> Dict[str, Any]:
        """
        Collect all relevant data for incident analysis.

        Returns:
            - bag_details: Bag information
            - journey_events: All scan events
            - flight_details: Flight information
            - weather_data: Weather conditions
            - equipment_logs: Equipment status at time of incident
            - handler_info: Handler assignments
        """
        # Query database for bag details
        bag_query = """
            SELECT * FROM bags
            WHERE id = $1
        """
        bag_details = await self.db.fetch_one(bag_query, bag_id)

        # Get bag journey events
        events_query = """
            SELECT * FROM events
            WHERE bag_id = $1
            ORDER BY timestamp ASC
        """
        journey_events = await self.db.fetch_all(events_query, bag_id)

        # Get flight details
        flight_id = bag_details.get("flight_id") if bag_details else None
        flight_details = None
        if flight_id:
            flight_query = """
                SELECT * FROM flights
                WHERE id = $1
            """
            flight_details = await self.db.fetch_one(flight_query, flight_id)

        # Get incident details
        incident_query = """
            SELECT * FROM incidents
            WHERE id = $1
        """
        incident_details = await self.db.fetch_one(incident_query, incident_id)

        return {
            "bag_details": bag_details,
            "journey_events": journey_events,
            "flight_details": flight_details,
            "incident_details": incident_details
        }

    async def _analyze_bag_journey(
        self,
        bag_id: str,
        incident_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze the bag's journey to identify anomalies.

        Returns:
            - expected_events: What should have happened
            - actual_events: What actually happened
            - anomalies: Deviations from expected
            - timing_issues: Time-based problems
            - location_gaps: Missing scans
        """
        journey_events = incident_data.get("journey_events", [])
        flight_details = incident_data.get("flight_details", {})

        anomalies = []
        timing_issues = []
        location_gaps = []

        if not journey_events:
            anomalies.append("No scan events recorded for bag")
            return {
                "anomalies": anomalies,
                "timing_issues": timing_issues,
                "location_gaps": location_gaps
            }

        # Check for timing issues
        for i in range(len(journey_events) - 1):
            current = journey_events[i]
            next_event = journey_events[i + 1]

            time_diff = (
                datetime.fromisoformat(next_event["timestamp"]) -
                datetime.fromisoformat(current["timestamp"])
            ).total_seconds()

            # Flag if gap > 30 minutes
            if time_diff > 1800:
                timing_issues.append({
                    "from": current["location"],
                    "to": next_event["location"],
                    "gap_seconds": time_diff,
                    "expected_max": 1800
                })

        # Check for expected locations based on flight route
        if flight_details:
            departure = flight_details.get("departure_airport")
            arrival = flight_details.get("arrival_airport")

            # Expected: check-in at departure, arrival scan at destination
            locations = [e["location"] for e in journey_events]

            if departure and departure not in locations:
                location_gaps.append(f"Missing scan at departure airport {departure}")

            if arrival and arrival not in locations:
                location_gaps.append(f"Missing scan at arrival airport {arrival}")

        if timing_issues:
            anomalies.append(f"Detected {len(timing_issues)} significant time gaps")

        if location_gaps:
            anomalies.extend(location_gaps)

        return {
            "journey_events": journey_events,
            "anomalies": anomalies,
            "timing_issues": timing_issues,
            "location_gaps": location_gaps
        }

    async def _identify_root_cause(
        self,
        incident_data: Dict[str, Any],
        journey_analysis: Dict[str, Any],
        incident_type: str
    ) -> Dict[str, Any]:
        """
        Use LLM to identify the root cause with high confidence.

        Returns:
            - cause: Root cause category
            - description: Detailed explanation
            - confidence: 0-1 score
            - evidence: Supporting data
        """
        # Prepare context for LLM
        bag_details = incident_data.get("bag_details", {})
        flight_details = incident_data.get("flight_details", {})
        anomalies = journey_analysis.get("anomalies", [])
        timing_issues = journey_analysis.get("timing_issues", [])

        system_prompt = """You are an expert baggage operations analyst.
Analyze incidents to determine the PRIMARY root cause from these categories:

- transfer_time_insufficient: Connection time too short
- equipment_failure: Equipment breakdown/malfunction
- handler_error: Human error in process
- flight_irregularity: Flight delay/cancellation/gate change
- routing_error: Wrong destination tag
- weather_impact: Severe weather
- system_outage: IT system failure
- special_handling_failure: Special baggage mishandled
- airport_congestion: Excessive traffic
- process_deviation: Procedure not followed

Return analysis as JSON:
{
    "cause": "<category>",
    "description": "<detailed explanation>",
    "confidence": <0-1>,
    "evidence": ["<fact 1>", "<fact 2>"]
}
"""

        user_prompt = f"""Analyze this baggage mishandling incident:

INCIDENT TYPE: {incident_type}

BAG DETAILS:
- Tag: {bag_details.get('tag_number', 'Unknown')}
- Origin: {flight_details.get('departure_airport', 'Unknown')}
- Destination: {flight_details.get('destination', 'Unknown')}
- Connection time: {bag_details.get('connection_time_minutes', 'N/A')} minutes

JOURNEY ANALYSIS:
Anomalies detected:
{json.dumps(anomalies, indent=2)}

Timing issues:
{json.dumps(timing_issues, indent=2)}

FLIGHT CONTEXT:
- Flight status: {flight_details.get('status', 'Unknown')}
- Scheduled departure: {flight_details.get('scheduled_departure', 'Unknown')}
- Actual departure: {flight_details.get('actual_departure', 'Unknown')}

Determine the PRIMARY root cause and confidence level.
"""

        # Call LLM
        response = await self._call_llm(
            prompt=user_prompt,
            system=system_prompt
        )

        try:
            result = json.loads(response)

            # Validate cause category
            if result["cause"] not in self.CAUSE_CATEGORIES:
                result["cause"] = "unknown"
                result["confidence"] = 0.5

            return result

        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse LLM response: {response}")
            return {
                "cause": "unknown",
                "description": "Unable to determine root cause",
                "confidence": 0.3,
                "evidence": []
            }

    async def _find_similar_incidents(
        self,
        incident_data: Dict[str, Any],
        root_cause: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar past incidents using database queries.

        Returns list of similar incidents with similarity scores.
        """
        # Query for incidents with same root cause in past 30 days
        query = """
            SELECT
                i.id,
                i.incident_type,
                i.root_cause,
                i.reported_at,
                b.flight_id,
                b.current_location
            FROM incidents i
            JOIN bags b ON i.bag_id = b.id
            WHERE i.root_cause = $1
              AND i.reported_at > NOW() - INTERVAL '30 days'
            ORDER BY i.reported_at DESC
            LIMIT $2
        """

        similar = await self.db.fetch_all(query, root_cause, limit)

        # Calculate similarity scores (simplified - could use embeddings)
        results = []
        for incident in similar:
            similarity = 0.8  # Base similarity for same root cause

            # Boost if same route
            if incident.get("flight_id") == incident_data.get("bag_details", {}).get("flight_id"):
                similarity += 0.1

            # Boost if recent (within 7 days)
            reported_at = incident.get("reported_at")
            if reported_at and (datetime.utcnow() - reported_at).days < 7:
                similarity += 0.1

            similarity = min(similarity, 1.0)

            results.append({
                "incident_id": incident["id"],
                "incident_type": incident["incident_type"],
                "similarity": similarity,
                "reported_at": incident["reported_at"].isoformat() if incident.get("reported_at") else None
            })

        return results

    async def _detect_pattern(
        self,
        root_cause: Dict[str, Any],
        similar_incidents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect if this incident is part of a larger pattern.

        Returns:
            - is_pattern: Boolean
            - frequency: Number of similar incidents
            - trend: "increasing", "stable", "decreasing"
            - severity: "low", "medium", "high"
        """
        frequency = len(similar_incidents)

        # Not a pattern if isolated
        if frequency < 3:
            return {
                "is_pattern": False,
                "frequency": frequency,
                "trend": "stable",
                "severity": "low"
            }

        # Analyze trend
        recent_7_days = sum(
            1 for i in similar_incidents
            if i.get("reported_at") and
               (datetime.utcnow() - datetime.fromisoformat(i["reported_at"])).days < 7
        )
        previous_7_days = frequency - recent_7_days

        if recent_7_days > previous_7_days * 1.5:
            trend = "increasing"
            severity = "high"
        elif recent_7_days < previous_7_days * 0.5:
            trend = "decreasing"
            severity = "low"
        else:
            trend = "stable"
            severity = "medium" if frequency > 5 else "low"

        return {
            "is_pattern": True,
            "frequency": frequency,
            "recent_7_days": recent_7_days,
            "previous_7_days": previous_7_days,
            "trend": trend,
            "severity": severity
        }

    async def _generate_recommendations(
        self,
        root_cause: Dict[str, Any],
        journey_analysis: Dict[str, Any],
        pattern: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations based on root cause.

        Returns list of recommendations with priority and estimated impact.
        """
        recommendations = []
        cause = root_cause.get("cause", "unknown")

        # Cause-specific recommendations
        if cause == "transfer_time_insufficient":
            recommendations.append({
                "action": "Increase minimum connection time for this route",
                "priority": "high",
                "estimated_impact": "Reduce future misconnections by 40%",
                "implementation_time": "immediate"
            })
            recommendations.append({
                "action": "Enable priority handling for tight connections",
                "priority": "high",
                "estimated_impact": "Improve success rate by 60%",
                "implementation_time": "1 week"
            })

        elif cause == "equipment_failure":
            recommendations.append({
                "action": "Schedule immediate equipment inspection and repair",
                "priority": "critical",
                "estimated_impact": "Prevent further failures",
                "implementation_time": "24 hours"
            })
            recommendations.append({
                "action": "Implement predictive maintenance monitoring",
                "priority": "medium",
                "estimated_impact": "Reduce equipment failures by 50%",
                "implementation_time": "1 month"
            })

        elif cause == "handler_error":
            recommendations.append({
                "action": "Provide additional training to handler",
                "priority": "medium",
                "estimated_impact": "Reduce errors by 30%",
                "implementation_time": "1 week"
            })
            recommendations.append({
                "action": "Review and clarify handling procedures",
                "priority": "medium",
                "estimated_impact": "Improve process compliance",
                "implementation_time": "2 weeks"
            })

        elif cause == "flight_irregularity":
            recommendations.append({
                "action": "Improve communication with flight operations",
                "priority": "medium",
                "estimated_impact": "Better coordination during delays",
                "implementation_time": "immediate"
            })

        elif cause == "system_outage":
            recommendations.append({
                "action": "Implement system redundancy and failover",
                "priority": "critical",
                "estimated_impact": "Prevent future outages",
                "implementation_time": "1 month"
            })

        # Pattern-specific recommendations
        if pattern.get("is_pattern") and pattern.get("severity") == "high":
            recommendations.append({
                "action": "Conduct comprehensive process audit for this route",
                "priority": "critical",
                "estimated_impact": "Address systemic issue",
                "implementation_time": "1 week"
            })

        # Generic recommendation
        if not recommendations:
            recommendations.append({
                "action": "Monitor for recurrence and collect additional data",
                "priority": "low",
                "estimated_impact": "Improve future analysis",
                "implementation_time": "ongoing"
            })

        return recommendations

    async def _store_analysis(
        self,
        incident_id: str,
        analysis: Dict[str, Any]
    ) -> None:
        """Store analysis results in database for future reference."""
        try:
            query = """
                INSERT INTO incident_analysis
                (incident_id, root_cause, analysis_data, analyzed_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (incident_id)
                DO UPDATE SET
                    root_cause = $2,
                    analysis_data = $3,
                    analyzed_at = $4
            """

            await self.db.execute(
                query,
                incident_id,
                analysis["root_cause"]["cause"],
                json.dumps(analysis),
                datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Failed to store analysis: {e}")

    async def get_patterns_summary(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get summary of patterns across all incidents in timeframe.

        Returns:
            - top_causes: Most frequent root causes
            - trends: Trend analysis
            - recommendations: System-wide improvements
        """
        query = """
            SELECT
                root_cause,
                COUNT(*) as frequency,
                AVG(EXTRACT(EPOCH FROM (resolved_at - reported_at))/3600) as avg_resolution_hours
            FROM incidents
            WHERE reported_at > NOW() - INTERVAL '$1 days'
              AND root_cause IS NOT NULL
            GROUP BY root_cause
            ORDER BY frequency DESC
        """

        results = await self.db.fetch_all(query, days)

        top_causes = [
            {
                "cause": r["root_cause"],
                "frequency": r["frequency"],
                "avg_resolution_hours": round(r["avg_resolution_hours"], 1) if r["avg_resolution_hours"] else None
            }
            for r in results
        ]

        return {
            "time_period_days": days,
            "top_causes": top_causes,
            "total_incidents": sum(c["frequency"] for c in top_causes),
            "generated_at": datetime.utcnow().isoformat()
        }
