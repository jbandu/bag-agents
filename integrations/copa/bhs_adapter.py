"""
Copa Airlines BHS (Baggage Handling System) Adapter

Integrates with Copa's BHS to process:
- RFID scan events
- IATA BagMessages (BSM, BPM, BTM, BUM)
- Conveyor belt status
- Load confirmations
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import aiohttp
from ..config import get_copa_config
from ..data_mapper import get_copa_mapper


logger = logging.getLogger(__name__)


class CopaBHSAdapter:
    """Adapter for Copa Airlines Baggage Handling System"""

    def __init__(self):
        self.config = get_copa_config()
        self.mapper = get_copa_mapper()
        self.base_url = self.config.bhs_base_url
        self.api_key = self.config.bhs_api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.event_handlers: List[Callable] = []

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
        logger.info("Copa BHS adapter initialized")

    async def close(self):
        """Close the adapter and cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Copa BHS adapter closed")

    async def get_scan_events(
        self,
        bag_tag: Optional[str] = None,
        location: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get baggage scan events

        Args:
            bag_tag: Filter by bag tag number
            location: Filter by scan location
            since: Get events since this time
            limit: Maximum number of events to return

        Returns:
            List of scan events
        """
        try:
            url = f"{self.base_url}/events/scans"
            params = {"limit": limit}

            if bag_tag:
                params["bagTag"] = bag_tag
            if location:
                params["location"] = location
            if since:
                params["since"] = since.isoformat()

            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                events = [
                    self.mapper.map_bhs_event(event)
                    for event in data.get("events", [])
                ]

                logger.info(f"Retrieved {len(events)} scan events")
                return events

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching scan events: {e}")
            return []

    async def get_bag_journey(self, bag_tag: str) -> List[Dict[str, Any]]:
        """
        Get complete journey/timeline for a bag

        Args:
            bag_tag: Bag tag number

        Returns:
            List of events in chronological order
        """
        try:
            url = f"{self.base_url}/bags/{bag_tag}/journey"

            async with self.session.get(url) as response:
                if response.status == 404:
                    logger.warning(f"No journey found for bag: {bag_tag}")
                    return []

                response.raise_for_status()
                data = await response.json()

                journey = [
                    self.mapper.map_bhs_event(event)
                    for event in data.get("events", [])
                ]

                # Sort by timestamp
                journey.sort(key=lambda x: x.get("timestamp", ""))

                logger.info(f"Retrieved journey for {bag_tag}: {len(journey)} events")
                return journey

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching bag journey for {bag_tag}: {e}")
            return []

    async def get_load_status(
        self,
        flight_number: str,
        flight_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get bag load status for a flight

        Args:
            flight_number: Flight number
            flight_date: Flight date (defaults to today)

        Returns:
            Load status information
        """
        try:
            if not flight_date:
                flight_date = datetime.utcnow().strftime("%Y-%m-%d")

            url = f"{self.base_url}/flights/{flight_number}/load-status"
            params = {"date": flight_date}

            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                load_status = {
                    "flight_number": flight_number,
                    "flight_date": flight_date,
                    "total_bags": data.get("totalBags", 0),
                    "loaded_bags": data.get("loadedBags", 0),
                    "remaining_bags": data.get("remainingBags", 0),
                    "short_checked_bags": data.get("shortCheckedBags", []),
                    "load_complete": data.get("loadComplete", False),
                    "last_updated": data.get("lastUpdated"),
                }

                logger.info(
                    f"Load status for {flight_number}: "
                    f"{load_status['loaded_bags']}/{load_status['total_bags']} loaded"
                )

                return load_status

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching load status for {flight_number}: {e}")
            return {}

    async def get_equipment_status(
        self,
        airport: str,
        equipment_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get status of baggage handling equipment

        Args:
            airport: Airport code
            equipment_type: Filter by equipment type (e.g., 'conveyor', 'sorter')

        Returns:
            List of equipment status
        """
        try:
            url = f"{self.base_url}/airports/{airport}/equipment"
            params = {}
            if equipment_type:
                params["type"] = equipment_type

            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                equipment = []
                for item in data.get("equipment", []):
                    equipment.append({
                        "equipment_id": item.get("id"),
                        "equipment_type": item.get("type"),
                        "location": item.get("location"),
                        "status": item.get("status"),  # operational, degraded, offline
                        "capacity": item.get("capacity"),
                        "current_load": item.get("currentLoad"),
                        "last_maintenance": item.get("lastMaintenance"),
                        "next_maintenance": item.get("nextMaintenance"),
                    })

                logger.info(f"Retrieved status for {len(equipment)} equipment items")
                return equipment

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching equipment status: {e}")
            return []

    async def process_bag_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process IATA bag message (BSM, BPM, BTM, BUM, etc.)

        Args:
            message: IATA bag message data

        Returns:
            Processed event
        """
        try:
            # Map the IATA message to internal format
            event = self.mapper.map_bhs_event(message)

            # Store or forward the event
            url = f"{self.base_url}/messages/process"

            async with self.session.post(url, json=message) as response:
                response.raise_for_status()
                logger.info(
                    f"Processed {message.get('messageType')} for bag "
                    f"{message.get('bagTagNumber')}"
                )

            return event

        except aiohttp.ClientError as e:
            logger.error(f"Error processing bag message: {e}")
            return {}

    async def listen_for_scan_events(self, callback: Callable):
        """
        Listen for real-time scan events

        Args:
            callback: Async function to call with each scan event
        """
        if self.config.bhs_listen_mode:
            # Webhook mode - events pushed to us
            logger.info("BHS running in webhook mode")
            self.event_handlers.append(callback)
            return
        else:
            # Polling mode - check for new events
            logger.info(f"BHS polling mode: interval={self.config.bhs_poll_interval}s")

            last_event_time = datetime.utcnow()

            while True:
                try:
                    # Get recent scan events
                    events = await self.get_scan_events(
                        since=last_event_time,
                        limit=100
                    )

                    for event in events:
                        try:
                            await callback({
                                "event_type": event.get("event_type", "bag_scanned"),
                                "data": event,
                                "timestamp": event.get("timestamp")
                            })
                        except Exception as e:
                            logger.error(
                                f"Error in callback for bag "
                                f"{event.get('bag_tag')}: {e}"
                            )

                    if events:
                        # Update last event time to most recent event
                        last_event_time = max(
                            datetime.fromisoformat(e.get("timestamp"))
                            for e in events
                            if e.get("timestamp")
                        )

                except Exception as e:
                    logger.error(f"Error polling for scan events: {e}")

                await asyncio.sleep(self.config.bhs_poll_interval)

    async def handle_webhook_event(self, event_data: Dict[str, Any]):
        """
        Handle incoming webhook event from Copa BHS

        Args:
            event_data: Webhook payload
        """
        try:
            # Map the event
            event = self.mapper.map_bhs_event(event_data)

            # Call all registered handlers
            for handler in self.event_handlers:
                try:
                    await handler({
                        "event_type": event.get("event_type", "bag_event"),
                        "data": event,
                        "timestamp": event.get("timestamp")
                    })
                except Exception as e:
                    logger.error(f"Error in webhook handler: {e}")

        except Exception as e:
            logger.error(f"Error handling webhook event: {e}")

    async def get_mishandled_bags(
        self,
        airport: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get bags flagged as mishandled by BHS

        Args:
            airport: Filter by airport
            since: Get bags mishandled since this time

        Returns:
            List of mishandled bags
        """
        try:
            url = f"{self.base_url}/bags/mishandled"
            params = {}

            if airport:
                params["airport"] = airport
            if since:
                params["since"] = since.isoformat()

            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                bags = []
                for bag_data in data.get("bags", []):
                    bag = self.mapper.map_bag_data(bag_data)

                    # Add mishandling info
                    bag["mishandling_info"] = {
                        "reason": bag_data.get("mishandlingReason"),
                        "detected_at": bag_data.get("detectedAt"),
                        "station": bag_data.get("station"),
                        "category": bag_data.get("category"),  # delayed, lost, damaged
                    }

                    bags.append(bag)

                logger.info(f"Retrieved {len(bags)} mishandled bags")
                return bags

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching mishandled bags: {e}")
            return []

    async def health_check(self) -> bool:
        """
        Check if Copa BHS is reachable

        Returns:
            True if healthy
        """
        try:
            url = f"{self.base_url}/health"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Copa BHS health check failed: {e}")
            return False


# Global adapter instance
_bhs_adapter: Optional[CopaBHSAdapter] = None


async def get_bhs_adapter() -> CopaBHSAdapter:
    """Get or create Copa BHS adapter instance"""
    global _bhs_adapter
    if _bhs_adapter is None:
        _bhs_adapter = CopaBHSAdapter()
        await _bhs_adapter.initialize()
    return _bhs_adapter
