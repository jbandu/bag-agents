"""
Copa Airlines DCS (Departure Control System) Adapter

Integrates with Copa's DCS to fetch:
- Passenger check-in data
- Flight manifests
- Bag tag numbers
- Check-in events
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from ..config import get_copa_config
from ..data_mapper import get_copa_mapper


logger = logging.getLogger(__name__)


class CopaDCSAdapter:
    """Adapter for Copa Airlines Departure Control System"""

    def __init__(self):
        self.config = get_copa_config()
        self.mapper = get_copa_mapper()
        self.base_url = self.config.dcs_base_url
        self.api_key = self.config.dcs_api_key
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
        logger.info("Copa DCS adapter initialized")

    async def close(self):
        """Close the adapter and cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Copa DCS adapter closed")

    async def get_flight_manifest(self, flight_number: str, flight_date: str) -> Dict[str, Any]:
        """
        Get complete flight manifest including all passengers and bags

        Args:
            flight_number: Copa flight number (e.g., "CM123")
            flight_date: Flight date in YYYY-MM-DD format

        Returns:
            Flight manifest with passengers and bags
        """
        try:
            url = f"{self.base_url}/flights/{flight_number}/manifest"
            params = {"date": flight_date}

            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                manifest = await response.json()

                # Transform manifest to internal format
                transformed = {
                    "flight": self.mapper.map_flight_data(manifest.get("flight", {})),
                    "passengers": [
                        self.mapper.map_passenger_data(pax)
                        for pax in manifest.get("passengers", [])
                    ],
                    "bags": [
                        self.mapper.map_bag_data(bag)
                        for bag in manifest.get("bags", [])
                    ],
                    "total_passengers": manifest.get("totalPassengers", 0),
                    "total_bags": manifest.get("totalBags", 0),
                }

                logger.info(
                    f"Retrieved manifest for {flight_number}: "
                    f"{transformed['total_passengers']} pax, "
                    f"{transformed['total_bags']} bags"
                )

                return transformed

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching manifest for {flight_number}: {e}")
            raise

    async def get_checked_bags(
        self,
        flight_number: Optional[str] = None,
        airport: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recently checked bags

        Args:
            flight_number: Filter by flight number
            airport: Filter by airport code
            since: Get bags checked since this time

        Returns:
            List of checked bags
        """
        try:
            url = f"{self.base_url}/bags/checked"
            params = {}

            if flight_number:
                params["flightNumber"] = flight_number
            if airport:
                params["airport"] = airport
            if since:
                params["since"] = since.isoformat()

            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                bags = [
                    self.mapper.map_bag_data(bag)
                    for bag in data.get("bags", [])
                ]

                logger.info(f"Retrieved {len(bags)} checked bags")
                return bags

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching checked bags: {e}")
            return []

    async def get_bag_details(self, bag_tag: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific bag

        Args:
            bag_tag: Bag tag number

        Returns:
            Bag details or None if not found
        """
        try:
            url = f"{self.base_url}/bags/{bag_tag}"

            async with self.session.get(url) as response:
                if response.status == 404:
                    logger.warning(f"Bag not found: {bag_tag}")
                    return None

                response.raise_for_status()
                bag_data = await response.json()

                return self.mapper.map_bag_data(bag_data)

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching bag details for {bag_tag}: {e}")
            return None

    async def get_passenger_bags(self, pnr: str) -> List[Dict[str, Any]]:
        """
        Get all bags for a passenger

        Args:
            pnr: Passenger Name Record

        Returns:
            List of bags for the passenger
        """
        try:
            url = f"{self.base_url}/passengers/{pnr}/bags"

            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                bags = [
                    self.mapper.map_bag_data(bag)
                    for bag in data.get("bags", [])
                ]

                logger.info(f"Retrieved {len(bags)} bags for PNR {pnr}")
                return bags

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching bags for PNR {pnr}: {e}")
            return []

    async def get_connecting_bags(
        self,
        arrival_flight: str,
        departure_flight: str,
        connection_airport: str
    ) -> List[Dict[str, Any]]:
        """
        Get bags transferring between flights

        Args:
            arrival_flight: Incoming flight number
            departure_flight: Outgoing flight number
            connection_airport: Airport code for connection

        Returns:
            List of connecting bags with connection time info
        """
        try:
            url = f"{self.base_url}/bags/connections"
            params = {
                "arrivalFlight": arrival_flight,
                "departureFlight": departure_flight,
                "airport": connection_airport
            }

            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                bags = []
                for bag_data in data.get("connectingBags", []):
                    bag = self.mapper.map_bag_data(bag_data)

                    # Add connection-specific info
                    bag["connection_info"] = {
                        "arrival_flight": arrival_flight,
                        "departure_flight": departure_flight,
                        "connection_airport": connection_airport,
                        "connection_time_minutes": bag_data.get("connectionTimeMinutes"),
                        "is_at_risk": bag_data.get("connectionTimeMinutes", 999) < 45,
                    }

                    bags.append(bag)

                logger.info(f"Retrieved {len(bags)} connecting bags")
                return bags

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching connecting bags: {e}")
            return []

    async def listen_for_checkin_events(self, callback):
        """
        Listen for real-time check-in events (webhook or polling)

        Args:
            callback: Async function to call with each event
        """
        if self.config.dcs_listen_mode == "webhook":
            # In webhook mode, events come via HTTP POST to our endpoint
            # This would be handled by the FastAPI app
            logger.info("DCS running in webhook mode")
            return
        else:
            # Polling mode: check for new events periodically
            logger.info(f"DCS polling mode: interval={self.config.dcs_poll_interval}s")

            last_check = datetime.utcnow() - timedelta(minutes=5)

            while True:
                try:
                    # Get recent check-in events
                    bags = await self.get_checked_bags(since=last_check)

                    for bag in bags:
                        try:
                            await callback({
                                "event_type": "bag_checked_in",
                                "data": bag,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        except Exception as e:
                            logger.error(f"Error in callback for bag {bag.get('tag_number')}: {e}")

                    last_check = datetime.utcnow()

                except Exception as e:
                    logger.error(f"Error polling for check-in events: {e}")

                await asyncio.sleep(self.config.dcs_poll_interval)

    async def update_bag_status(self, bag_tag: str, status: str, location: str) -> bool:
        """
        Update bag status in Copa DCS (if allowed)

        Args:
            bag_tag: Bag tag number
            status: New status
            location: Current location

        Returns:
            True if successful
        """
        try:
            # Map internal status back to Copa format
            copa_bag = self.mapper.reverse_map_bag({
                "tag_number": bag_tag,
                "status": status,
                "current_location": location
            })

            url = f"{self.base_url}/bags/{bag_tag}/status"

            async with self.session.patch(url, json=copa_bag) as response:
                response.raise_for_status()
                logger.info(f"Updated bag {bag_tag} status to {status}")
                return True

        except aiohttp.ClientError as e:
            logger.error(f"Error updating bag status for {bag_tag}: {e}")
            return False

    async def health_check(self) -> bool:
        """
        Check if Copa DCS is reachable

        Returns:
            True if healthy
        """
        try:
            url = f"{self.base_url}/health"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Copa DCS health check failed: {e}")
            return False


# Global adapter instance
_dcs_adapter: Optional[CopaDCSAdapter] = None


async def get_dcs_adapter() -> CopaDCSAdapter:
    """Get or create Copa DCS adapter instance"""
    global _dcs_adapter
    if _dcs_adapter is None:
        _dcs_adapter = CopaDCSAdapter()
        await _dcs_adapter.initialize()
    return _dcs_adapter
