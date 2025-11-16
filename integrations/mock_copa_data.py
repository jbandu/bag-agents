"""
Mock Copa Airlines Data Generator

Generates realistic mock data for demo scenarios when Copa systems are unavailable.

Demo Scenarios:
1. Normal bag flow: PTY → JFK via connection
2. At-risk connection that succeeds
3. Mishandled bag with PIR and recovery
4. Multiple flights with various statuses
5. Real-time event simulation
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo


class MockCopaDataGenerator:
    """Generates realistic mock data for Copa Airlines demo"""

    # Copa route network (hub: PTY Panama)
    ROUTES = [
        # North America
        ("PTY", "JFK", 6.5),  # New York
        ("PTY", "EWR", 6.5),  # Newark
        ("PTY", "IAD", 5.5),  # Washington DC
        ("PTY", "MIA", 3.5),  # Miami
        ("PTY", "LAX", 8.5),  # Los Angeles
        ("PTY", "SFO", 8.0),  # San Francisco
        ("PTY", "ORD", 6.0),  # Chicago
        ("PTY", "YYZ", 7.0),  # Toronto
        ("PTY", "MEX", 4.5),  # Mexico City
        # South America
        ("PTY", "BOG", 2.0),  # Bogota
        ("PTY", "LIM", 3.5),  # Lima
        ("PTY", "GYE", 2.0),  # Guayaquil
        ("PTY", "UIO", 2.5),  # Quito
        ("PTY", "GUA", 2.0),  # Guatemala City
        ("PTY", "SAL", 1.5),  # San Salvador
        ("PTY", "SJO", 1.0),  # San Jose Costa Rica
        ("PTY", "EZE", 8.0),  # Buenos Aires
        ("PTY", "GRU", 8.0),  # Sao Paulo
        ("PTY", "CCS", 2.5),  # Caracas
        ("PTY", "CTG", 1.5),  # Cartagena
    ]

    AIRCRAFT_TYPES = ["737-800", "737-MAX9", "737-700", "E190"]

    PASSENGER_NAMES = [
        "Maria Garcia", "Juan Rodriguez", "Carlos Martinez", "Ana Lopez",
        "Diego Hernandez", "Sofia Gonzalez", "Miguel Perez", "Isabella Sanchez",
        "Luis Ramirez", "Camila Torres", "Jose Rivera", "Valentina Flores",
        "Fernando Gomez", "Lucia Diaz", "Antonio Cruz", "Elena Morales"
    ]

    def __init__(self, seed: Optional[int] = None):
        if seed:
            random.seed(seed)

        self.copa_tz = ZoneInfo("America/Panama")
        self.generated_bags = []
        self.generated_flights = []
        self.demo_scenario_bags = {}

    def generate_flight_number(self) -> str:
        """Generate a Copa flight number"""
        return f"CM{random.randint(100, 999)}"

    def generate_pnr(self) -> str:
        """Generate a 6-character PNR"""
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return ''.join(random.choice(chars) for _ in range(6))

    def generate_bag_tag(self) -> str:
        """Generate a 10-digit bag tag number"""
        # Copa uses IATA code 230
        return f"0230{random.randint(100000, 999999)}"

    def generate_flights(
        self,
        num_flights: int = 50,
        base_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate mock flights

        Args:
            num_flights: Number of flights to generate
            base_time: Base time for schedule (defaults to now)

        Returns:
            List of flight dictionaries
        """
        if not base_time:
            base_time = datetime.now(tz=self.copa_tz)

        flights = []

        for i in range(num_flights):
            # Pick a random route
            origin, destination, duration_hours = random.choice(self.ROUTES)

            # Determine if outbound or inbound to PTY hub
            if origin == "PTY":
                departure_airport = origin
                arrival_airport = destination
            else:
                # Reverse the route (inbound to hub)
                departure_airport = destination
                arrival_airport = origin

            flight_number = self.generate_flight_number()

            # Schedule time (spread across next 24 hours)
            scheduled_departure = base_time + timedelta(
                hours=random.uniform(0, 24)
            )
            scheduled_arrival = scheduled_departure + timedelta(hours=duration_hours)

            # Determine flight status
            status_weights = [
                ("scheduled", 0.5),
                ("boarding", 0.15),
                ("departed", 0.2),
                ("delayed", 0.1),
                ("arrived", 0.05),
            ]
            status = random.choices(
                [s[0] for s in status_weights],
                weights=[s[1] for s in status_weights]
            )[0]

            # Add delay if delayed
            actual_departure = None
            actual_arrival = None

            if status == "delayed":
                delay_minutes = random.randint(15, 120)
                actual_departure = scheduled_departure + timedelta(minutes=delay_minutes)
                actual_arrival = scheduled_arrival + timedelta(minutes=delay_minutes)
            elif status == "departed":
                actual_departure = scheduled_departure
            elif status == "arrived":
                actual_departure = scheduled_departure
                actual_arrival = scheduled_arrival

            # Generate bags count
            aircraft_type = random.choice(self.AIRCRAFT_TYPES)
            load_factor = random.uniform(0.7, 0.95)

            if "MAX" in aircraft_type:
                max_passengers = 180
            elif "800" in aircraft_type:
                max_passengers = 160
            elif "700" in aircraft_type:
                max_passengers = 140
            else:  # E190
                max_passengers = 100

            passengers = int(max_passengers * load_factor)
            bags_per_passenger = random.uniform(0.9, 1.2)
            bags_checked = int(passengers * bags_per_passenger)
            bags_loaded = bags_checked if status in ["departed", "arrived"] else random.randint(0, bags_checked)

            flight = {
                "id": f"FLT_{flight_number}_{scheduled_departure.strftime('%Y%m%d')}",
                "flight_number": flight_number,
                "airline": "CM",
                "departure_airport": departure_airport,
                "arrival_airport": arrival_airport,
                "scheduled_departure": scheduled_departure.isoformat(),
                "actual_departure": actual_departure.isoformat() if actual_departure else None,
                "scheduled_arrival": scheduled_arrival.isoformat(),
                "actual_arrival": actual_arrival.isoformat() if actual_arrival else None,
                "status": status,
                "gate": f"{random.choice(['A', 'B', 'C'])}{random.randint(1, 20)}",
                "aircraft_reg": f"HP-{random.randint(1000, 9999)}CMP",
                "aircraft_type": aircraft_type,
                "bags_checked": bags_checked,
                "bags_loaded": bags_loaded,
                "bags_missing": max(0, bags_checked - bags_loaded),
                "at_risk_connections": random.randint(0, 5) if departure_airport == "PTY" else 0,
            }

            flights.append(flight)

        self.generated_flights = flights
        return flights

    def generate_bags(
        self,
        num_bags: int = 1500,
        flights: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate mock bags

        Args:
            num_bags: Number of bags to generate
            flights: Associated flights (generates flights if not provided)

        Returns:
            List of bag dictionaries
        """
        if not flights:
            flights = self.generate_flights()

        if not flights:
            raise ValueError("No flights available to assign bags to")

        bags = []

        for i in range(num_bags):
            # Pick a random flight
            flight = random.choice(flights)

            bag_tag = self.generate_bag_tag()
            pnr = self.generate_pnr()
            passenger_name = random.choice(self.PASSENGER_NAMES)

            # Determine bag status
            if flight["status"] == "arrived":
                status = "delivered"
            elif flight["status"] == "departed":
                status = random.choice(["loaded", "in_transit"])
            elif flight["status"] == "boarding":
                status = random.choice(["checked", "loaded"])
            else:
                status = "checked"

            # Risk level based on various factors
            risk_factors = []
            risk_level = "low"

            # Check for tight connections (if PTY is involved)
            if flight["departure_airport"] == "PTY" and random.random() < 0.1:
                connection_time = random.randint(30, 90)
                if connection_time < 45:
                    risk_level = "high"
                    risk_factors.append("Tight connection")
            else:
                connection_time = None

            # Random delays increase risk
            if flight["status"] == "delayed":
                risk_level = "medium"
                risk_factors.append("Flight delayed")

            # Small chance of mishandling
            if random.random() < 0.003:  # 0.3% mishandling rate
                status = random.choice(["delayed", "lost"])
                risk_level = "critical"
                risk_factors.append("Mishandled")

            checked_at = datetime.fromisoformat(flight["scheduled_departure"]) - timedelta(hours=random.uniform(1, 3))

            bag = {
                "id": f"BAG_{bag_tag}",
                "tag_number": bag_tag,
                "passenger_id": pnr,
                "passenger_name": passenger_name,
                "flight_id": flight["id"],
                "flight_number": flight["flight_number"],
                "status": status,
                "risk_level": risk_level,
                "current_location": flight["departure_airport"],
                "destination": flight["arrival_airport"],
                "weight": round(random.uniform(15, 30), 1),
                "checked_at": checked_at.isoformat(),
                "last_scan_at": (checked_at + timedelta(minutes=random.randint(5, 60))).isoformat(),
                "connection_time_minutes": connection_time,
                "predicted_issues": risk_factors if risk_factors else None,
                "priority": "VIP" if random.random() < 0.05 else "NORMAL",
            }

            bags.append(bag)

        self.generated_bags = bags
        return bags

    def generate_demo_scenario_1(self) -> Dict[str, Any]:
        """
        Demo Scenario 1: Normal bag flow PTY → JFK with connection

        Passenger checks in bag in Bogota (BOG) → Panama (PTY) → New York (JFK)
        """
        base_time = datetime.now(tz=self.copa_tz)

        # Leg 1: BOG → PTY
        flight1 = {
            "id": "FLT_CM101_20241215",
            "flight_number": "CM101",
            "airline": "CM",
            "departure_airport": "BOG",
            "arrival_airport": "PTY",
            "scheduled_departure": (base_time + timedelta(hours=1)).isoformat(),
            "scheduled_arrival": (base_time + timedelta(hours=3)).isoformat(),
            "status": "boarding",
            "gate": "B12",
            "bags_checked": 145,
            "bags_loaded": 120,
            "bags_missing": 25,
            "at_risk_connections": 0,
        }

        # Leg 2: PTY → JFK
        flight2 = {
            "id": "FLT_CM451_20241215",
            "flight_number": "CM451",
            "airline": "CM",
            "departure_airport": "PTY",
            "arrival_airport": "JFK",
            "scheduled_departure": (base_time + timedelta(hours=5)).isoformat(),
            "scheduled_arrival": (base_time + timedelta(hours=11.5)).isoformat(),
            "status": "scheduled",
            "gate": "A5",
            "bags_checked": 0,
            "bags_loaded": 0,
            "bags_missing": 0,
            "at_risk_connections": 3,
        }

        # The bag
        bag = {
            "id": "BAG_0230556789",
            "tag_number": "0230556789",
            "passenger_id": "ABC123",
            "passenger_name": "Maria Rodriguez",
            "flight_id": "FLT_CM451_20241215",  # Final flight
            "flight_number": "CM451",
            "status": "checked",
            "risk_level": "medium",
            "current_location": "BOG",
            "destination": "JFK",
            "weight": 23.5,
            "checked_at": (base_time - timedelta(minutes=90)).isoformat(),
            "last_scan_at": (base_time - timedelta(minutes=30)).isoformat(),
            "connection_time_minutes": 120,  # 2 hour connection in PTY
            "predicted_issues": ["International connection"],
            "priority": "NORMAL",
        }

        self.demo_scenario_bags["scenario_1"] = bag

        return {
            "scenario": 1,
            "description": "Normal bag flow with connection",
            "flights": [flight1, flight2],
            "bag": bag,
            "journey": [
                {"location": "BOG", "event": "checked", "timestamp": bag["checked_at"]},
                {"location": "BOG", "event": "screened", "timestamp": (base_time - timedelta(minutes=25)).isoformat()},
                {"location": "BOG", "event": "loaded_to_aircraft", "timestamp": (base_time + timedelta(minutes=30)).isoformat()},
                {"location": "PTY", "event": "unloaded", "timestamp": (base_time + timedelta(hours=3, minutes=15)).isoformat()},
                {"location": "PTY", "event": "transferred", "timestamp": (base_time + timedelta(hours=4)).isoformat()},
                {"location": "PTY", "event": "loaded_to_aircraft", "timestamp": (base_time + timedelta(hours=4, minutes=45)).isoformat()},
                {"location": "JFK", "event": "unloaded", "timestamp": (base_time + timedelta(hours=11, minutes=40)).isoformat()},
                {"location": "JFK", "event": "delivered_to_carousel", "timestamp": (base_time + timedelta(hours=12)).isoformat()},
            ]
        }

    def generate_demo_scenario_2(self) -> Dict[str, Any]:
        """
        Demo Scenario 2: At-risk connection that succeeds with AI intervention
        """
        base_time = datetime.now(tz=self.copa_tz)

        # Incoming flight is delayed
        flight1 = {
            "id": "FLT_CM202_20241215",
            "flight_number": "CM202",
            "airline": "CM",
            "departure_airport": "MIA",
            "arrival_airport": "PTY",
            "scheduled_departure": (base_time - timedelta(hours=2)).isoformat(),
            "actual_departure": (base_time - timedelta(hours=1, minutes=30)).isoformat(),  # 30 min delay
            "scheduled_arrival": (base_time + timedelta(hours=1.5)).isoformat(),
            "actual_arrival": (base_time + timedelta(hours=2)).isoformat(),
            "status": "delayed",
            "gate": "C8",
            "bags_checked": 98,
            "bags_loaded": 98,
            "bags_missing": 0,
        }

        # Connecting flight
        flight2 = {
            "id": "FLT_CM645_20241215",
            "flight_number": "CM645",
            "airline": "CM",
            "departure_airport": "PTY",
            "arrival_airport": "LIM",
            "scheduled_departure": (base_time + timedelta(hours=2, minutes=30)).isoformat(),
            "scheduled_arrival": (base_time + timedelta(hours=6)).isoformat(),
            "status": "scheduled",
            "gate": "A3",
            "bags_checked": 45,
            "bags_loaded": 0,
            "bags_missing": 0,
            "at_risk_connections": 4,
        }

        # At-risk bag
        bag = {
            "id": "BAG_0230667890",
            "tag_number": "0230667890",
            "passenger_id": "XYZ789",
            "passenger_name": "Carlos Martinez",
            "flight_id": "FLT_CM645_20241215",
            "flight_number": "CM645",
            "status": "in_transit",
            "risk_level": "critical",
            "current_location": "MIA",
            "destination": "LIM",
            "weight": 25.3,
            "checked_at": (base_time - timedelta(hours=3)).isoformat(),
            "last_scan_at": (base_time - timedelta(hours=2)).isoformat(),
            "connection_time_minutes": 30,  # Only 30 minutes!
            "predicted_issues": ["Tight connection due to delay", "High risk of misconnection"],
            "priority": "RUSH",  # Flagged by AI for priority handling
        }

        self.demo_scenario_bags["scenario_2"] = bag

        return {
            "scenario": 2,
            "description": "At-risk connection saved by AI intervention",
            "flights": [flight1, flight2],
            "bag": bag,
            "ai_intervention": {
                "predicted_at": (base_time - timedelta(minutes=45)).isoformat(),
                "risk_score": 0.87,
                "recommended_actions": [
                    "Flag bag for priority handling in PTY",
                    "Alert ground crew",
                    "Pre-position bag near connecting gate",
                    "Consider holding flight CM645 for 5 minutes if needed"
                ],
                "outcome": "Bag successfully made connection",
            },
            "journey": [
                {"location": "MIA", "event": "checked", "timestamp": bag["checked_at"], "priority": "NORMAL"},
                {"location": "MIA", "event": "ai_risk_detected", "timestamp": (base_time - timedelta(minutes=45)).isoformat()},
                {"location": "MIA", "event": "priority_upgraded", "timestamp": (base_time - timedelta(minutes=45)).isoformat()},
                {"location": "PTY", "event": "unloaded", "timestamp": (base_time + timedelta(hours=2, minutes=10)).isoformat()},
                {"location": "PTY", "event": "expedited_transfer", "timestamp": (base_time + timedelta(hours=2, minutes=18)).isoformat()},
                {"location": "PTY", "event": "loaded_to_aircraft", "timestamp": (base_time + timedelta(hours=2, minutes=25)).isoformat()},
                {"location": "LIM", "event": "delivered", "timestamp": (base_time + timedelta(hours=6, minutes=20)).isoformat()},
            ]
        }

    def generate_demo_scenario_3(self) -> Dict[str, Any]:
        """
        Demo Scenario 3: Mishandled bag with PIR, AI detection, and recovery
        """
        base_time = datetime.now(tz=self.copa_tz)

        flight = {
            "id": "FLT_CM777_20241215",
            "flight_number": "CM777",
            "airline": "CM",
            "departure_airport": "PTY",
            "arrival_airport": "JFK",
            "scheduled_departure": (base_time - timedelta(hours=8)).isoformat(),
            "actual_departure": (base_time - timedelta(hours=8)).isoformat(),
            "scheduled_arrival": (base_time - timedelta(hours=1.5)).isoformat(),
            "actual_arrival": (base_time - timedelta(hours=1.5)).isoformat(),
            "status": "arrived",
            "bags_checked": 156,
            "bags_loaded": 155,
            "bags_missing": 1,
        }

        bag = {
            "id": "BAG_0230778901",
            "tag_number": "0230778901",
            "passenger_id": "DEF456",
            "passenger_name": "Ana Lopez",
            "flight_id": "FLT_CM777_20241215",
            "flight_number": "CM777",
            "status": "lost",
            "risk_level": "critical",
            "current_location": "PTY",  # Found in Panama
            "destination": "JFK",
            "weight": 22.1,
            "checked_at": (base_time - timedelta(hours=10)).isoformat(),
            "last_scan_at": (base_time - timedelta(hours=9, minutes=30)).isoformat(),
            "priority": "VIP",
        }

        self.demo_scenario_bags["scenario_3"] = bag

        return {
            "scenario": 3,
            "description": "Mishandled bag with PIR and AI-powered recovery",
            "flight": flight,
            "bag": bag,
            "mishandling_case": {
                "reported_at": (base_time - timedelta(hours=1)).isoformat(),
                "pir_number": "PTYCM20241215001",
                "passenger_name": "Ana Lopez",
                "passenger_contact": "ana.lopez@email.com",
                "type": "delayed",
                "status": "located",
            },
            "ai_analysis": {
                "root_cause": "Bag missed loading due to late check-in",
                "location_prediction": "Likely in PTY baggage holding area",
                "confidence": 0.94,
                "recommended_actions": [
                    "Search PTY baggage holding area",
                    "Put on next PTY-JFK flight (CM789 in 4 hours)",
                    "Notify passenger via email",
                    "Arrange delivery to residence"
                ]
            },
            "journey": [
                {"location": "PTY", "event": "checked", "timestamp": bag["checked_at"]},
                {"location": "PTY", "event": "last_scan", "timestamp": bag["last_scan_at"]},
                {"location": "PTY", "event": "missed_loading", "timestamp": (base_time - timedelta(hours=8, minutes=15)).isoformat()},
                {"location": "JFK", "event": "passenger_reports_missing", "timestamp": (base_time - timedelta(hours=1)).isoformat()},
                {"location": "PTY", "event": "ai_location_prediction", "timestamp": (base_time - timedelta(minutes=55)).isoformat()},
                {"location": "PTY", "event": "bag_found", "timestamp": (base_time - timedelta(minutes=30)).isoformat()},
                {"location": "PTY", "event": "loaded_on_recovery_flight", "timestamp": (base_time + timedelta(hours=3, minutes=45)).isoformat()},
            ]
        }

    def get_demo_scenarios(self) -> List[Dict[str, Any]]:
        """Get all demo scenarios"""
        return [
            self.generate_demo_scenario_1(),
            self.generate_demo_scenario_2(),
            self.generate_demo_scenario_3(),
        ]


# Global instance
_mock_generator: Optional[MockCopaDataGenerator] = None


def get_mock_generator() -> MockCopaDataGenerator:
    """Get or create mock data generator instance"""
    global _mock_generator
    if _mock_generator is None:
        _mock_generator = MockCopaDataGenerator()
    return _mock_generator
