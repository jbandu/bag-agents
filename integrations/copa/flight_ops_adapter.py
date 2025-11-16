"""
Copa Airlines Flight Operations Adapter

Integrates with Copa's Flight Operations system to fetch:
- Real-time flight status (delays, gate changes, cancellations)
- Flight schedule updates
- Aircraft rotations
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from ..config import get_copa_config
from ..data_mapper import get_copa_mapper


logger = logging.getLogger(__name__)


class CopaFlightOpsAdapter:
    """Adapter for Copa Airlines Flight Operations System"""

    def __init__(self):
        self.config = get_copa_config()
        self.mapper = get_copa_mapper()
        self.base_url = self.config.flight_ops_base_url
        self.api_key = self.config.flight_ops_api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize the adapter and HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                    "User-Agent": "BagAgents/1.0"
                }
            )
        logger.info("Copa Flight Ops adapter initialized")

    async def close(self):
        """Close the adapter and cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Copa Flight Ops adapter closed")

    async def get_active_flights(
        self,
        airport: Optional[str] = None,
        hours_ahead: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Get active flights (departing in next N hours)

        Args:
            airport: Filter by airport code (defaults to PTY hub)
            hours_ahead: Look ahead time window in hours

        Returns:
            List of active flights
        """
        try:
            airport = airport or self.config.copa_hub_airport
            url = f"{self.base_url}/flights/active"
            params = {
                "airport": airport,
                "hoursAhead": hours_ahead
            }

            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                flights = [
                    self.mapper.map_flight_data(flight)
                    for flight in data.get("flights", [])
                ]

                logger.info(f"Retrieved {len(flights)} active flights for {airport}")
                return flights

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching active flights: {e}")
            return []

    async def get_flight_status(
        self,
        flight_number: str,
        flight_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get current status for a specific flight

        Args:
            flight_number: Copa flight number (e.g., "CM123")
            flight_date: Flight date in YYYY-MM-DD format (defaults to today)

        Returns:
            Flight status or None if not found
        """
        try:
            if not flight_date:
                flight_date = datetime.utcnow().strftime("%Y-%m-%d")

            url = f"{self.base_url}/flights/{flight_number}"
            params = {"date": flight_date}

            async with self.session.get(url, params=params) as response:
                if response.status == 404:
                    logger.warning(f"Flight not found: {flight_number} on {flight_date}")
                    return None

                response.raise_for_status()
                flight_data = await response.json()

                return self.mapper.map_flight_data(flight_data)

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching flight status for {flight_number}: {e}")
            return None

    async def get_delayed_flights(
        self,
        airport: Optional[str] = None,
        min_delay_minutes: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Get currently delayed flights

        Args:
            airport: Filter by airport code
            min_delay_minutes: Minimum delay in minutes

        Returns:
            List of delayed flights
        """
        try:
            airport = airport or self.config.copa_hub_airport
            url = f"{self.base_url}/flights/delayed"
            params = {
                "airport": airport,
                "minDelayMinutes": min_delay_minutes
            }

            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                flights = [
                    self.mapper.map_flight_data(flight)
                    for flight in data.get("flights", [])
                ]

                logger.info(f"Retrieved {len(flights)} delayed flights")
                return flights

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching delayed flights: {e}")
            return []

    async def get_aircraft_rotation(
        self,
        aircraft_registration: str,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get aircraft rotation schedule

        Args:
            aircraft_registration: Aircraft registration number
            date: Date in YYYY-MM-DD format (defaults to today)

        Returns:
            List of flights for this aircraft
        """
        try:
            if not date:
                date = datetime.utcnow().strftime("%Y-%m-%d")

            url = f"{self.base_url}/aircraft/{aircraft_registration}/rotation"
            params = {"date": date}

            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                rotation = [
                    self.mapper.map_flight_data(flight)
                    for flight in data.get("flights", [])
                ]

                logger.info(
                    f"Retrieved rotation for {aircraft_registration}: "
                    f"{len(rotation)} flights"
                )
                return rotation

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching aircraft rotation: {e}")
            return []

    async def get_gate_assignments(
        self,
        airport: str,
        terminal: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get current gate assignments

        Args:
            airport: Airport code
            terminal: Terminal filter (optional)

        Returns:
            Dictionary mapping flight numbers to gate numbers
        """
        try:
            url = f"{self.base_url}/airports/{airport}/gates"
            params = {}
            if terminal:
                params["terminal"] = terminal

            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                assignments = {}
                for assignment in data.get("gateAssignments", []):
                    flight_num = assignment.get("flightNumber")
                    gate = assignment.get("gate")
                    if flight_num and gate:
                        assignments[flight_num] = gate

                logger.info(f"Retrieved {len(assignments)} gate assignments for {airport}")
                return assignments

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching gate assignments: {e}")
            return {}

    async def listen_for_flight_updates(self, callback):
        """
        Listen for real-time flight updates (status changes, delays, etc.)

        Args:
            callback: Async function to call with each update
        """
        logger.info(f"Flight Ops polling mode: interval={self.config.flight_ops_poll_interval}s")

        # Track flight states to detect changes
        flight_states = {}

        while True:
            try:
                # Get current active flights
                flights = await self.get_active_flights()

                for flight in flights:
                    flight_id = flight.get("id")
                    if not flight_id:
                        continue

                    # Check if flight state changed
                    previous_state = flight_states.get(flight_id)
                    current_state = {
                        "status": flight.get("status"),
                        "gate": flight.get("gate"),
                        "actual_departure": flight.get("actual_departure"),
                        "actual_arrival": flight.get("actual_arrival"),
                    }

                    if previous_state != current_state:
                        # Flight state changed - trigger callback
                        try:
                            await callback({
                                "event_type": "flight_status_changed",
                                "data": flight,
                                "previous_state": previous_state,
                                "current_state": current_state,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        except Exception as e:
                            logger.error(f"Error in callback for flight {flight_id}: {e}")

                        flight_states[flight_id] = current_state

                # Clean up old flight states (older than 24 hours)
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                flight_states = {
                    fid: state for fid, state in flight_states.items()
                    if fid in [f.get("id") for f in flights]
                }

            except Exception as e:
                logger.error(f"Error polling for flight updates: {e}")

            await asyncio.sleep(self.config.flight_ops_poll_interval)

    async def get_connection_opportunities(
        self,
        arrival_flight: str,
        airport: str,
        min_connection_time: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get viable connection flights from an arriving flight

        Args:
            arrival_flight: Incoming flight number
            airport: Connection airport code
            min_connection_time: Minimum connection time in minutes

        Returns:
            List of connecting flight options with connection times
        """
        try:
            url = f"{self.base_url}/flights/{arrival_flight}/connections"
            params = {
                "airport": airport,
                "minConnectionTime": min_connection_time
            }

            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                connections = []
                for conn in data.get("connections", []):
                    connection = self.mapper.map_flight_data(conn["departureFlight"])
                    connection["connection_info"] = {
                        "arrival_flight": arrival_flight,
                        "connection_time_minutes": conn.get("connectionTimeMinutes"),
                        "connection_airport": airport,
                        "is_viable": conn.get("isViable", True),
                    }
                    connections.append(connection)

                logger.info(f"Found {len(connections)} connection opportunities")
                return connections

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching connection opportunities: {e}")
            return []

    async def health_check(self) -> bool:
        """
        Check if Copa Flight Ops is reachable

        Returns:
            True if healthy
        """
        try:
            url = f"{self.base_url}/health"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Copa Flight Ops health check failed: {e}")
            return False


# Global adapter instance
_flight_ops_adapter: Optional[CopaFlightOpsAdapter] = None


async def get_flight_ops_adapter() -> CopaFlightOpsAdapter:
    """Get or create Copa Flight Ops adapter instance"""
    global _flight_ops_adapter
    if _flight_ops_adapter is None:
        _flight_ops_adapter = CopaFlightOpsAdapter()
        await _flight_ops_adapter.initialize()
    return _flight_ops_adapter
