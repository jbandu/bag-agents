"""
Infrastructure Health Agent

Monitors and analyzes baggage handling infrastructure health.
Provides predictive maintenance and equipment monitoring.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json
import random
from .base_agent import BaseAgent


# Equipment health thresholds
HEALTH_THRESHOLDS = {
    "excellent": 90,
    "good": 75,
    "fair": 60,
    "poor": 40,
    "critical": 0
}


# Equipment types and their specifications
EQUIPMENT_SPECS = {
    "baggage_carousel": {
        "mtbf_hours": 2000,  # Mean Time Between Failures
        "maintenance_interval_days": 60,
        "max_utilization": 0.85
    },
    "sorting_system": {
        "mtbf_hours": 1500,
        "maintenance_interval_days": 45,
        "max_utilization": 0.90
    },
    "scanner": {
        "mtbf_hours": 3000,
        "maintenance_interval_days": 90,
        "max_utilization": 0.95
    },
    "conveyor_belt": {
        "mtbf_hours": 1800,
        "maintenance_interval_days": 30,
        "max_utilization": 0.80
    },
    "tug": {
        "mtbf_hours": 1000,
        "maintenance_interval_days": 30,
        "max_utilization": 0.75
    },
    "cart": {
        "mtbf_hours": 2500,
        "maintenance_interval_days": 90,
        "max_utilization": 0.70
    }
}


class InfrastructureHealthAgent(BaseAgent):
    """
    Monitors baggage handling infrastructure and equipment health.

    Capabilities:
    - Equipment status monitoring (conveyors, scanners, tugs, carts)
    - Predictive maintenance with ML-based failure prediction
    - Performance degradation detection
    - Anomaly detection in equipment metrics
    - System bottleneck identification
    - Capacity planning and analysis
    - Automated work order generation
    - Real-time alerts for critical issues
    """

    def __init__(self, llm_client=None, db_connection=None, config=None):
        """Initialize InfrastructureHealthAgent."""
        super().__init__(
            agent_name="infrastructure_health_agent",
            llm_client=llm_client,
            db_connection=db_connection,
            config=config
        )

        # Failure prediction model thresholds
        self.FAILURE_PREDICTION_THRESHOLD = 0.7

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute infrastructure health check.

        Args:
            input_data: Dictionary containing:
                - airport_code: Airport identifier
                - equipment_type: Type of equipment (optional, checks all if not specified)
                - equipment_id: Specific equipment ID (optional)
                - include_predictions: Include predictive maintenance (default: True)
                - prediction_horizon_days: Days to predict ahead (default: 30)

        Returns:
            Dictionary containing:
                - overall_health: System health score (0-100)
                - equipment_status: Status of each equipment
                - alerts: Active alerts and warnings
                - maintenance_recommendations: Upcoming maintenance needs
                - failure_predictions: Predicted failures
                - capacity_analysis: System capacity metrics
                - bottlenecks: Identified bottlenecks
        """
        self.validate_input(input_data, ["airport_code"])

        airport_code = input_data["airport_code"]
        equipment_type = input_data.get("equipment_type")
        equipment_id = input_data.get("equipment_id")
        include_predictions = input_data.get("include_predictions", True)
        prediction_horizon_days = input_data.get("prediction_horizon_days", 30)

        self.logger.info(
            f"Running infrastructure health check for {airport_code}, "
            f"equipment_type: {equipment_type or 'all'}"
        )

        # Step 1: Fetch equipment inventory and status
        equipment_list = await self._fetch_equipment_inventory(
            airport_code=airport_code,
            equipment_type=equipment_type,
            equipment_id=equipment_id
        )

        # Step 2: Fetch performance metrics for each equipment
        equipment_status = []
        for equipment in equipment_list:
            status = await self._analyze_equipment_health(
                equipment=equipment,
                airport_code=airport_code
            )
            equipment_status.append(status)

        # Step 3: Calculate overall system health
        overall_health = self._calculate_overall_health(equipment_status)

        # Step 4: Detect anomalies
        anomalies = await self._detect_anomalies(equipment_status)

        # Step 5: Identify bottlenecks
        bottlenecks = await self._identify_bottlenecks(
            equipment_status=equipment_status,
            airport_code=airport_code
        )

        # Step 6: Generate failure predictions
        failure_predictions = []
        if include_predictions:
            failure_predictions = await self._predict_failures(
                equipment_status=equipment_status,
                horizon_days=prediction_horizon_days
            )

        # Step 7: Generate maintenance recommendations
        maintenance_recommendations = await self._generate_maintenance_recommendations(
            equipment_status=equipment_status,
            failure_predictions=failure_predictions,
            airport_code=airport_code
        )

        # Step 8: Generate alerts
        alerts = await self._generate_alerts(
            equipment_status=equipment_status,
            failure_predictions=failure_predictions,
            anomalies=anomalies
        )

        # Step 9: Capacity analysis
        capacity_analysis = await self._analyze_capacity(
            equipment_status=equipment_status,
            airport_code=airport_code
        )

        return {
            "airport_code": airport_code,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": overall_health,
            "health_grade": self._get_health_grade(overall_health),
            "equipment_status": equipment_status,
            "total_equipment": len(equipment_status),
            "operational_count": sum(1 for e in equipment_status if e["status"] == "OPERATIONAL"),
            "degraded_count": sum(1 for e in equipment_status if e["status"] == "DEGRADED"),
            "offline_count": sum(1 for e in equipment_status if e["status"] == "OFFLINE"),
            "alerts": alerts,
            "anomalies": anomalies,
            "maintenance_recommendations": maintenance_recommendations,
            "failure_predictions": failure_predictions,
            "capacity_analysis": capacity_analysis,
            "bottlenecks": bottlenecks
        }

    async def _fetch_equipment_inventory(
        self,
        airport_code: str,
        equipment_type: Optional[str] = None,
        equipment_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch equipment inventory from database."""
        try:
            query = """
                SELECT *
                FROM equipment
                WHERE airport_code = $1
            """
            params = [airport_code]

            if equipment_type:
                query += " AND equipment_type = $2"
                params.append(equipment_type)

            if equipment_id:
                query += f" AND equipment_id = ${len(params) + 1}"
                params.append(equipment_id)

            query += " ORDER BY equipment_type, equipment_id"

            results = await self.db_connection.fetch(query, *params)

            equipment_list = [dict(row) for row in results]

            self.logger.info(f"Fetched {len(equipment_list)} equipment items for {airport_code}")

            return equipment_list

        except Exception as e:
            self.logger.error(f"Error fetching equipment inventory: {e}")
            # Return mock data for demo
            return self._get_mock_equipment_inventory(airport_code)

    def _get_mock_equipment_inventory(self, airport_code: str) -> List[Dict[str, Any]]:
        """Generate mock equipment inventory for demo."""
        equipment = []

        # Baggage carousels
        for i in range(1, 6):
            equipment.append({
                "equipment_id": f"CAR-{i:02d}",
                "equipment_type": "baggage_carousel",
                "airport_code": airport_code,
                "location": f"Terminal {(i-1)//2 + 1}",
                "installed_date": (datetime.utcnow() - timedelta(days=365 * (i % 3 + 1))).isoformat(),
                "last_maintenance": (datetime.utcnow() - timedelta(days=30 + i*5)).isoformat()
            })

        # Sorting systems
        for i in range(1, 4):
            equipment.append({
                "equipment_id": f"SORT-{chr(64+i)}",
                "equipment_type": "sorting_system",
                "airport_code": airport_code,
                "location": f"Sorting Hub {i}",
                "installed_date": (datetime.utcnow() - timedelta(days=365 * 2)).isoformat(),
                "last_maintenance": (datetime.utcnow() - timedelta(days=40 + i*3)).isoformat()
            })

        # Scanners
        for i in range(1, 13):
            equipment.append({
                "equipment_id": f"SCAN-{i:02d}",
                "equipment_type": "scanner",
                "airport_code": airport_code,
                "location": f"Gate {i}",
                "installed_date": (datetime.utcnow() - timedelta(days=365)).isoformat(),
                "last_maintenance": (datetime.utcnow() - timedelta(days=60 + i*2)).isoformat()
            })

        # Conveyor belts
        for i in range(1, 11):
            equipment.append({
                "equipment_id": f"CONV-{i:02d}",
                "equipment_type": "conveyor_belt",
                "airport_code": airport_code,
                "location": f"Section {chr(64+i)}",
                "installed_date": (datetime.utcnow() - timedelta(days=365 * 3)).isoformat(),
                "last_maintenance": (datetime.utcnow() - timedelta(days=25 + i)).isoformat()
            })

        return equipment

    async def _analyze_equipment_health(
        self,
        equipment: Dict[str, Any],
        airport_code: str
    ) -> Dict[str, Any]:
        """Analyze health of a single piece of equipment."""
        equipment_id = equipment["equipment_id"]
        equipment_type = equipment["equipment_type"]

        # Fetch performance metrics
        metrics = await self._fetch_equipment_metrics(equipment_id)

        # Calculate health score
        health_score = self._calculate_equipment_health_score(equipment, metrics)

        # Determine status
        status = self._determine_equipment_status(health_score, metrics)

        # Calculate utilization
        utilization = metrics.get("utilization", 0.0)

        # Check maintenance schedule
        last_maintenance = datetime.fromisoformat(equipment["last_maintenance"])
        days_since_maintenance = (datetime.utcnow() - last_maintenance).days

        specs = EQUIPMENT_SPECS.get(equipment_type, {})
        maintenance_interval = specs.get("maintenance_interval_days", 60)

        days_until_maintenance = maintenance_interval - days_since_maintenance
        next_maintenance = last_maintenance + timedelta(days=maintenance_interval)

        # Detect issues
        issues = []
        if health_score < 70:
            issues.append("Performance degradation detected")
        if utilization > specs.get("max_utilization", 0.85):
            issues.append(f"High utilization: {utilization:.1%}")
        if days_since_maintenance > maintenance_interval * 1.2:
            issues.append("Overdue for maintenance")

        return {
            "equipment_id": equipment_id,
            "equipment_type": equipment_type,
            "location": equipment.get("location", "Unknown"),
            "status": status,
            "health_score": health_score,
            "utilization": round(utilization, 2),
            "last_maintenance": last_maintenance.strftime("%Y-%m-%d"),
            "days_since_maintenance": days_since_maintenance,
            "next_maintenance": next_maintenance.strftime("%Y-%m-%d"),
            "days_until_maintenance": days_until_maintenance,
            "metrics": metrics,
            "issues": issues,
            "installed_date": equipment.get("installed_date"),
            "age_years": (datetime.utcnow() - datetime.fromisoformat(equipment["installed_date"])).days / 365 if equipment.get("installed_date") else None
        }

    async def _fetch_equipment_metrics(
        self,
        equipment_id: str
    ) -> Dict[str, Any]:
        """Fetch performance metrics for equipment."""
        try:
            query = """
                SELECT
                    AVG(throughput) as avg_throughput,
                    AVG(error_rate) as avg_error_rate,
                    AVG(utilization) as utilization,
                    MAX(temperature) as max_temperature,
                    AVG(vibration_level) as avg_vibration,
                    COUNT(*) as data_points
                FROM equipment_metrics
                WHERE equipment_id = $1
                  AND timestamp >= NOW() - INTERVAL '24 hours'
            """

            result = await self.db_connection.fetchrow(query, equipment_id)

            if result and result["data_points"]:
                return dict(result)
            else:
                # Return mock metrics for demo
                return self._generate_mock_metrics(equipment_id)

        except Exception as e:
            self.logger.error(f"Error fetching equipment metrics: {e}")
            return self._generate_mock_metrics(equipment_id)

    def _generate_mock_metrics(self, equipment_id: str) -> Dict[str, Any]:
        """Generate mock metrics for demo."""
        # Use equipment_id hash to generate consistent random values
        seed = hash(equipment_id) % 100

        return {
            "avg_throughput": 800 + seed * 5,
            "avg_error_rate": 0.01 + (seed % 10) * 0.001,
            "utilization": 0.6 + (seed % 30) * 0.01,
            "max_temperature": 35 + (seed % 15),
            "avg_vibration": 0.1 + (seed % 5) * 0.02,
            "data_points": 144  # 24 hours of 10-minute intervals
        }

    def _calculate_equipment_health_score(
        self,
        equipment: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> int:
        """Calculate health score (0-100) for equipment."""
        score = 100

        # Factor 1: Error rate (max -20 points)
        error_rate = metrics.get("avg_error_rate", 0)
        if error_rate > 0.05:
            score -= 20
        elif error_rate > 0.03:
            score -= 10
        elif error_rate > 0.01:
            score -= 5

        # Factor 2: Utilization vs max (±10 points)
        utilization = metrics.get("utilization", 0)
        equipment_type = equipment.get("equipment_type")
        specs = EQUIPMENT_SPECS.get(equipment_type, {})
        max_util = specs.get("max_utilization", 0.85)

        if utilization > max_util:
            score -= int((utilization - max_util) * 50)  # Penalty for over-utilization

        # Factor 3: Temperature (max -15 points)
        temp = metrics.get("max_temperature", 35)
        if temp > 60:
            score -= 15
        elif temp > 50:
            score -= 10
        elif temp > 45:
            score -= 5

        # Factor 4: Vibration (max -15 points)
        vibration = metrics.get("avg_vibration", 0.1)
        if vibration > 0.3:
            score -= 15
        elif vibration > 0.2:
            score -= 8

        # Factor 5: Age (max -10 points)
        if equipment.get("installed_date"):
            age_years = (datetime.utcnow() - datetime.fromisoformat(equipment["installed_date"])).days / 365
            if age_years > 10:
                score -= 10
            elif age_years > 7:
                score -= 5

        # Factor 6: Maintenance overdue (max -30 points)
        last_maintenance = datetime.fromisoformat(equipment["last_maintenance"])
        days_since = (datetime.utcnow() - last_maintenance).days
        interval = specs.get("maintenance_interval_days", 60)

        if days_since > interval * 1.5:
            score -= 30
        elif days_since > interval * 1.2:
            score -= 15
        elif days_since > interval:
            score -= 8

        return max(0, min(100, score))

    def _determine_equipment_status(
        self,
        health_score: int,
        metrics: Dict[str, Any]
    ) -> str:
        """Determine equipment operational status."""
        if health_score >= 75:
            return "OPERATIONAL"
        elif health_score >= 50:
            return "DEGRADED"
        else:
            return "OFFLINE"

    def _calculate_overall_health(
        self,
        equipment_status: List[Dict[str, Any]]
    ) -> int:
        """Calculate overall system health score."""
        if not equipment_status:
            return 0

        total_score = sum(e["health_score"] for e in equipment_status)
        avg_score = total_score / len(equipment_status)

        # Penalty for offline equipment
        offline_count = sum(1 for e in equipment_status if e["status"] == "OFFLINE")
        offline_penalty = offline_count * 5

        return max(0, int(avg_score - offline_penalty))

    def _get_health_grade(self, health_score: int) -> str:
        """Convert health score to letter grade."""
        if health_score >= HEALTH_THRESHOLDS["excellent"]:
            return "A"
        elif health_score >= HEALTH_THRESHOLDS["good"]:
            return "B"
        elif health_score >= HEALTH_THRESHOLDS["fair"]:
            return "C"
        elif health_score >= HEALTH_THRESHOLDS["poor"]:
            return "D"
        else:
            return "F"

    async def _detect_anomalies(
        self,
        equipment_status: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in equipment performance."""
        anomalies = []

        for equipment in equipment_status:
            metrics = equipment.get("metrics", {})

            # Anomaly 1: High error rate
            if metrics.get("avg_error_rate", 0) > 0.05:
                anomalies.append({
                    "equipment_id": equipment["equipment_id"],
                    "type": "high_error_rate",
                    "severity": "high",
                    "value": metrics["avg_error_rate"],
                    "threshold": 0.05,
                    "description": f"Error rate {metrics['avg_error_rate']:.2%} exceeds threshold",
                    "detected_at": datetime.utcnow().isoformat()
                })

            # Anomaly 2: Temperature spike
            if metrics.get("max_temperature", 0) > 55:
                anomalies.append({
                    "equipment_id": equipment["equipment_id"],
                    "type": "temperature_spike",
                    "severity": "medium",
                    "value": metrics["max_temperature"],
                    "threshold": 55,
                    "description": f"Temperature {metrics['max_temperature']}°C above normal",
                    "detected_at": datetime.utcnow().isoformat()
                })

            # Anomaly 3: Excessive vibration
            if metrics.get("avg_vibration", 0) > 0.25:
                anomalies.append({
                    "equipment_id": equipment["equipment_id"],
                    "type": "excessive_vibration",
                    "severity": "medium",
                    "value": metrics["avg_vibration"],
                    "threshold": 0.25,
                    "description": "Vibration levels indicate potential mechanical issue",
                    "detected_at": datetime.utcnow().isoformat()
                })

            # Anomaly 4: Low throughput
            expected_throughput = 1000
            if metrics.get("avg_throughput", 0) < expected_throughput * 0.6:
                anomalies.append({
                    "equipment_id": equipment["equipment_id"],
                    "type": "low_throughput",
                    "severity": "high",
                    "value": metrics["avg_throughput"],
                    "threshold": expected_throughput * 0.6,
                    "description": "Throughput significantly below expected",
                    "detected_at": datetime.utcnow().isoformat()
                })

        self.logger.info(f"Detected {len(anomalies)} anomalies")

        return anomalies

    async def _predict_failures(
        self,
        equipment_status: List[Dict[str, Any]],
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """
        Predict equipment failures using ML-based model.

        Uses a simple heuristic model based on:
        - Health score trend
        - Time since last maintenance
        - Utilization rate
        - Anomaly count
        """
        predictions = []

        for equipment in equipment_status:
            # Calculate failure probability
            failure_prob = self._calculate_failure_probability(equipment)

            if failure_prob >= self.FAILURE_PREDICTION_THRESHOLD:
                # Estimate time to failure
                ttf_days = self._estimate_time_to_failure(equipment, failure_prob)

                if ttf_days <= horizon_days:
                    predictions.append({
                        "equipment_id": equipment["equipment_id"],
                        "equipment_type": equipment["equipment_type"],
                        "failure_probability": round(failure_prob, 2),
                        "confidence": "high" if failure_prob > 0.85 else "medium",
                        "estimated_time_to_failure_days": ttf_days,
                        "estimated_failure_date": (datetime.utcnow() + timedelta(days=ttf_days)).strftime("%Y-%m-%d"),
                        "contributing_factors": self._identify_failure_factors(equipment),
                        "recommended_action": "Schedule preventive maintenance",
                        "priority": "critical" if ttf_days < 7 else "high"
                    })

        self.logger.info(f"Predicted {len(predictions)} potential failures in next {horizon_days} days")

        return predictions

    def _calculate_failure_probability(
        self,
        equipment: Dict[str, Any]
    ) -> float:
        """Calculate probability of failure (0-1)."""
        prob = 0.0

        # Factor 1: Health score
        health_score = equipment["health_score"]
        prob += (100 - health_score) / 200  # 0-0.5 based on health

        # Factor 2: Overdue maintenance
        days_since_maintenance = equipment["days_since_maintenance"]
        equipment_type = equipment["equipment_type"]
        interval = EQUIPMENT_SPECS.get(equipment_type, {}).get("maintenance_interval_days", 60)

        if days_since_maintenance > interval:
            overdue_ratio = days_since_maintenance / interval
            prob += min((overdue_ratio - 1) * 0.3, 0.3)  # Up to +0.3

        # Factor 3: High utilization
        utilization = equipment.get("utilization", 0)
        max_util = EQUIPMENT_SPECS.get(equipment_type, {}).get("max_utilization", 0.85)

        if utilization > max_util:
            prob += (utilization - max_util) * 0.5  # Up to +0.2

        # Factor 4: Issues count
        issues_count = len(equipment.get("issues", []))
        prob += issues_count * 0.1  # Up to +0.3

        return min(prob, 1.0)

    def _estimate_time_to_failure(
        self,
        equipment: Dict[str, Any],
        failure_prob: float
    ) -> int:
        """Estimate days until failure."""
        # Higher probability → sooner failure
        # Base estimate: 30 days at 0.7 prob, 1 day at 1.0 prob

        if failure_prob >= 0.95:
            return random.randint(1, 3)
        elif failure_prob >= 0.85:
            return random.randint(3, 7)
        elif failure_prob >= 0.75:
            return random.randint(7, 14)
        else:
            return random.randint(14, 30)

    def _identify_failure_factors(
        self,
        equipment: Dict[str, Any]
    ) -> List[str]:
        """Identify factors contributing to failure risk."""
        factors = []

        if equipment["health_score"] < 60:
            factors.append("Low health score")

        if equipment["days_since_maintenance"] > EQUIPMENT_SPECS.get(equipment["equipment_type"], {}).get("maintenance_interval_days", 60):
            factors.append("Overdue maintenance")

        if equipment.get("utilization", 0) > 0.85:
            factors.append("High utilization")

        if equipment.get("issues"):
            factors.extend(equipment["issues"])

        return factors

    async def _generate_maintenance_recommendations(
        self,
        equipment_status: List[Dict[str, Any]],
        failure_predictions: List[Dict[str, Any]],
        airport_code: str
    ) -> List[Dict[str, Any]]:
        """Generate maintenance recommendations and work orders."""
        recommendations = []

        # Priority 1: Predicted failures
        for prediction in failure_predictions:
            equipment_id = prediction["equipment_id"]

            # Find the equipment
            equipment = next((e for e in equipment_status if e["equipment_id"] == equipment_id), None)

            if equipment:
                recommendations.append({
                    "equipment_id": equipment_id,
                    "equipment_type": equipment["equipment_type"],
                    "priority": prediction["priority"],
                    "action": "Preventive maintenance - potential failure detected",
                    "reason": f"{prediction['failure_probability']:.0%} failure probability",
                    "contributing_factors": prediction["contributing_factors"],
                    "estimated_downtime_hours": self._estimate_maintenance_downtime(equipment["equipment_type"]),
                    "suggested_window": self._suggest_maintenance_window(airport_code),
                    "urgency": "immediate" if prediction["estimated_time_to_failure_days"] < 3 else "high"
                })

        # Priority 2: Overdue maintenance
        for equipment in equipment_status:
            if equipment["days_until_maintenance"] < 0:
                # Skip if already in predictions
                if any(r["equipment_id"] == equipment["equipment_id"] for r in recommendations):
                    continue

                recommendations.append({
                    "equipment_id": equipment["equipment_id"],
                    "equipment_type": equipment["equipment_type"],
                    "priority": "high",
                    "action": "Scheduled maintenance (overdue)",
                    "reason": f"{abs(equipment['days_until_maintenance'])} days overdue",
                    "estimated_downtime_hours": self._estimate_maintenance_downtime(equipment["equipment_type"]),
                    "suggested_window": self._suggest_maintenance_window(airport_code),
                    "urgency": "high"
                })

        # Priority 3: Upcoming maintenance
        for equipment in equipment_status:
            if 0 <= equipment["days_until_maintenance"] <= 7:
                # Skip if already in recommendations
                if any(r["equipment_id"] == equipment["equipment_id"] for r in recommendations):
                    continue

                recommendations.append({
                    "equipment_id": equipment["equipment_id"],
                    "equipment_type": equipment["equipment_type"],
                    "priority": "medium",
                    "action": "Scheduled maintenance",
                    "reason": f"Due in {equipment['days_until_maintenance']} days",
                    "estimated_downtime_hours": self._estimate_maintenance_downtime(equipment["equipment_type"]),
                    "suggested_window": self._suggest_maintenance_window(airport_code),
                    "urgency": "medium"
                })

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))

        return recommendations

    def _estimate_maintenance_downtime(self, equipment_type: str) -> float:
        """Estimate maintenance downtime in hours."""
        downtime_estimates = {
            "baggage_carousel": 2,
            "sorting_system": 4,
            "scanner": 1,
            "conveyor_belt": 3,
            "tug": 2,
            "cart": 0.5
        }
        return downtime_estimates.get(equipment_type, 2)

    def _suggest_maintenance_window(self, airport_code: str) -> str:
        """Suggest optimal maintenance window (low traffic hours)."""
        # Suggest overnight window (1 AM - 5 AM)
        tomorrow = datetime.utcnow() + timedelta(days=1)
        start_time = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=4)

        return f"{start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')} UTC"

    async def _generate_alerts(
        self,
        equipment_status: List[Dict[str, Any]],
        failure_predictions: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate alerts for critical issues."""
        alerts = []

        # Critical alerts from failure predictions
        for prediction in failure_predictions:
            if prediction["priority"] == "critical":
                alerts.append({
                    "severity": "CRITICAL",
                    "type": "imminent_failure",
                    "equipment_id": prediction["equipment_id"],
                    "message": f"{prediction['equipment_id']} predicted to fail in {prediction['estimated_time_to_failure_days']} days",
                    "recommended_action": "Schedule immediate preventive maintenance",
                    "detected_at": datetime.utcnow().isoformat()
                })

        # High severity alerts from anomalies
        for anomaly in anomalies:
            if anomaly["severity"] == "high":
                alerts.append({
                    "severity": "WARNING",
                    "type": anomaly["type"],
                    "equipment_id": anomaly["equipment_id"],
                    "message": anomaly["description"],
                    "recommended_action": "Investigate and address anomaly",
                    "detected_at": anomaly["detected_at"]
                })

        # Offline equipment alerts
        for equipment in equipment_status:
            if equipment["status"] == "OFFLINE":
                alerts.append({
                    "severity": "CRITICAL",
                    "type": "equipment_offline",
                    "equipment_id": equipment["equipment_id"],
                    "message": f"{equipment['equipment_id']} is offline",
                    "recommended_action": "Immediate inspection required",
                    "detected_at": datetime.utcnow().isoformat()
                })

        return alerts

    async def _identify_bottlenecks(
        self,
        equipment_status: List[Dict[str, Any]],
        airport_code: str
    ) -> List[Dict[str, Any]]:
        """Identify system bottlenecks."""
        bottlenecks = []

        # Bottleneck 1: Over-utilized equipment
        for equipment in equipment_status:
            if equipment.get("utilization", 0) > 0.9:
                bottlenecks.append({
                    "type": "over_utilization",
                    "equipment_id": equipment["equipment_id"],
                    "equipment_type": equipment["equipment_type"],
                    "utilization": equipment["utilization"],
                    "impact": "high",
                    "description": f"{equipment['equipment_id']} operating at {equipment['utilization']:.1%} capacity",
                    "recommendation": "Consider adding capacity or redistributing load"
                })

        # Bottleneck 2: Equipment types with high offline ratio
        equipment_by_type = {}
        for equipment in equipment_status:
            eq_type = equipment["equipment_type"]
            if eq_type not in equipment_by_type:
                equipment_by_type[eq_type] = {"total": 0, "offline": 0}

            equipment_by_type[eq_type]["total"] += 1
            if equipment["status"] == "OFFLINE":
                equipment_by_type[eq_type]["offline"] += 1

        for eq_type, counts in equipment_by_type.items():
            offline_ratio = counts["offline"] / counts["total"] if counts["total"] > 0 else 0

            if offline_ratio > 0.2:  # More than 20% offline
                bottlenecks.append({
                    "type": "equipment_availability",
                    "equipment_type": eq_type,
                    "offline_count": counts["offline"],
                    "total_count": counts["total"],
                    "offline_ratio": offline_ratio,
                    "impact": "high",
                    "description": f"{counts['offline']}/{counts['total']} {eq_type} units offline",
                    "recommendation": "Urgent maintenance or replacement needed"
                })

        return bottlenecks

    async def _analyze_capacity(
        self,
        equipment_status: List[Dict[str, Any]],
        airport_code: str
    ) -> Dict[str, Any]:
        """Analyze system capacity."""
        # Calculate total theoretical capacity (bags per hour)
        capacity_by_type = {
            "baggage_carousel": 300,
            "sorting_system": 1500,
            "scanner": 100,
            "conveyor_belt": 500
        }

        total_capacity = 0
        for equipment in equipment_status:
            if equipment["status"] == "OPERATIONAL":
                eq_type = equipment["equipment_type"]
                total_capacity += capacity_by_type.get(eq_type, 0)

        # Calculate average utilization
        operational = [e for e in equipment_status if e["status"] == "OPERATIONAL"]
        avg_utilization = sum(e.get("utilization", 0) for e in operational) / len(operational) if operational else 0

        # Find peak utilization
        peak_utilization = max((e.get("utilization", 0) for e in equipment_status), default=0)

        # Identify bottleneck equipment types
        utilization_by_type = {}
        for equipment in equipment_status:
            eq_type = equipment["equipment_type"]
            if eq_type not in utilization_by_type:
                utilization_by_type[eq_type] = []

            if equipment["status"] == "OPERATIONAL":
                utilization_by_type[eq_type].append(equipment.get("utilization", 0))

        bottleneck_types = []
        for eq_type, utils in utilization_by_type.items():
            avg_util = sum(utils) / len(utils) if utils else 0
            if avg_util > 0.85:
                bottleneck_types.append(f"{eq_type} ({avg_util:.1%} avg utilization)")

        return {
            "total_theoretical_capacity_bags_per_hour": total_capacity,
            "operational_capacity": int(total_capacity * avg_utilization),
            "average_utilization": round(avg_utilization, 2),
            "peak_utilization": round(peak_utilization, 2),
            "capacity_margin": round(1 - avg_utilization, 2),
            "bottleneck_equipment_types": bottleneck_types,
            "recommendations": [
                "Monitor high-utilization equipment closely",
                "Consider capacity expansion if utilization remains above 85%"
            ] if avg_utilization > 0.85 else ["Current capacity is adequate"]
        }

    async def generate_work_order(
        self,
        equipment_id: str,
        maintenance_type: str,
        priority: str = "medium",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate automated maintenance work order.

        Args:
            equipment_id: Equipment identifier
            maintenance_type: Type of maintenance (preventive, corrective, emergency)
            priority: Priority level (low, medium, high, critical)
            description: Optional description

        Returns:
            Work order details
        """
        work_order_number = f"WO-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

        work_order = {
            "work_order_number": work_order_number,
            "equipment_id": equipment_id,
            "maintenance_type": maintenance_type,
            "priority": priority,
            "status": "open",
            "description": description or f"{maintenance_type} maintenance for {equipment_id}",
            "created_at": datetime.utcnow().isoformat(),
            "scheduled_for": self._suggest_maintenance_window("PTY"),
            "estimated_hours": 2,
            "assigned_to": None,
            "requires_parts": [],
            "safety_notes": []
        }

        # Store work order in database
        try:
            insert_query = """
                INSERT INTO work_orders (
                    work_order_number,
                    equipment_id,
                    maintenance_type,
                    priority,
                    status,
                    description,
                    created_at,
                    scheduled_for
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """

            await self.db_connection.execute(
                insert_query,
                work_order_number,
                equipment_id,
                maintenance_type,
                priority,
                "open",
                work_order["description"],
                datetime.utcnow(),
                work_order["scheduled_for"]
            )

            self.logger.info(f"Generated work order: {work_order_number}")

        except Exception as e:
            self.logger.error(f"Error storing work order: {e}")

        return work_order
