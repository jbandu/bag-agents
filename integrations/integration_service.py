"""
Copa Airlines Integration Service

Orchestrates all Copa integration adapters and manages data flow.
Main entry point for Copa Airlines integrations.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from .config import get_copa_config
from .copa.dcs_adapter import get_dcs_adapter
from .copa.flight_ops_adapter import get_flight_ops_adapter
from .copa.bhs_adapter import get_bhs_adapter
from .mock_copa_data import get_mock_generator


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CopaIntegrationService:
    """
    Main integration service for Copa Airlines

    Coordinates all adapters and manages data flow to the baggage operations system.
    """

    def __init__(self):
        self.config = get_copa_config()
        self.dcs_adapter = None
        self.flight_ops_adapter = None
        self.bhs_adapter = None
        self.mock_generator = None

        self.event_callbacks: Dict[str, List[Callable]] = {
            "bag_checked": [],
            "bag_scanned": [],
            "flight_status_changed": [],
            "bag_mishandled": [],
        }

        self.is_running = False
        self.tasks: List[asyncio.Task] = []

    async def initialize(self):
        """Initialize the integration service"""
        logger.info("Initializing Copa Integration Service...")

        # Initialize mock generator
        self.mock_generator = get_mock_generator()

        if self.config.use_mock_data:
            logger.warning("Using MOCK DATA mode for Copa integrations")
            # Pre-generate mock data
            self.mock_flights = self.mock_generator.generate_flights(num_flights=50)
            self.mock_bags = self.mock_generator.generate_bags(
                num_bags=1500,
                flights=self.mock_flights
            )
            logger.info(
                f"Generated mock data: {len(self.mock_flights)} flights, "
                f"{len(self.mock_bags)} bags"
            )
        else:
            # Initialize real adapters
            if self.config.dcs_enabled:
                self.dcs_adapter = await get_dcs_adapter()
                logger.info("DCS adapter initialized")

            if self.config.flight_ops_enabled:
                self.flight_ops_adapter = await get_flight_ops_adapter()
                logger.info("Flight Ops adapter initialized")

            if self.config.bhs_enabled:
                self.bhs_adapter = await get_bhs_adapter()
                logger.info("BHS adapter initialized")

        logger.info("Copa Integration Service initialized successfully")

    async def start(self):
        """Start the integration service and begin data synchronization"""
        if self.is_running:
            logger.warning("Integration service is already running")
            return

        logger.info("Starting Copa Integration Service...")
        self.is_running = True

        if self.config.use_mock_data:
            # Start mock data streaming
            task = asyncio.create_task(self._stream_mock_events())
            self.tasks.append(task)
        else:
            # Start real adapter listeners
            if self.dcs_adapter:
                task = asyncio.create_task(
                    self.dcs_adapter.listen_for_checkin_events(self._handle_checkin_event)
                )
                self.tasks.append(task)

            if self.flight_ops_adapter:
                task = asyncio.create_task(
                    self.flight_ops_adapter.listen_for_flight_updates(self._handle_flight_update)
                )
                self.tasks.append(task)

            if self.bhs_adapter:
                task = asyncio.create_task(
                    self.bhs_adapter.listen_for_scan_events(self._handle_scan_event)
                )
                self.tasks.append(task)

        logger.info(f"Integration service started with {len(self.tasks)} active tasks")

    async def stop(self):
        """Stop the integration service"""
        if not self.is_running:
            return

        logger.info("Stopping Copa Integration Service...")
        self.is_running = False

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

        # Close adapters
        if self.dcs_adapter:
            await self.dcs_adapter.close()
        if self.flight_ops_adapter:
            await self.flight_ops_adapter.close()
        if self.bhs_adapter:
            await self.bhs_adapter.close()

        logger.info("Integration service stopped")

    def register_callback(self, event_type: str, callback: Callable):
        """
        Register a callback for specific event types

        Args:
            event_type: Type of event (bag_checked, bag_scanned, flight_status_changed, etc.)
            callback: Async function to call when event occurs
        """
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []

        self.event_callbacks[event_type].append(callback)
        logger.info(f"Registered callback for event type: {event_type}")

    async def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Trigger all registered callbacks for an event type"""
        callbacks = self.event_callbacks.get(event_type, [])

        for callback in callbacks:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Error in callback for {event_type}: {e}")

    async def _handle_checkin_event(self, event: Dict[str, Any]):
        """Handle bag check-in event from DCS"""
        logger.info(f"Check-in event: {event.get('data', {}).get('tag_number')}")
        await self._trigger_callbacks("bag_checked", event)

    async def _handle_flight_update(self, event: Dict[str, Any]):
        """Handle flight status update from Flight Ops"""
        logger.info(f"Flight update: {event.get('data', {}).get('flight_number')}")
        await self._trigger_callbacks("flight_status_changed", event)

    async def _handle_scan_event(self, event: Dict[str, Any]):
        """Handle bag scan event from BHS"""
        logger.info(f"Scan event: {event.get('data', {}).get('bag_tag')}")
        await self._trigger_callbacks("bag_scanned", event)

    async def _stream_mock_events(self):
        """Stream mock events for demo purposes"""
        logger.info("Starting mock event streaming...")

        event_count = 0

        while self.is_running:
            try:
                # Randomly generate events
                event_type = asyncio.get_event_loop().time() % 3

                if event_type < 1:
                    # Generate check-in event
                    if self.mock_bags:
                        bag = self.mock_bags[event_count % len(self.mock_bags)]
                        await self._trigger_callbacks("bag_checked", {
                            "event_type": "bag_checked_in",
                            "data": bag,
                            "timestamp": datetime.utcnow().isoformat()
                        })

                elif event_type < 2:
                    # Generate scan event
                    if self.mock_bags:
                        bag = self.mock_bags[event_count % len(self.mock_bags)]
                        await self._trigger_callbacks("bag_scanned", {
                            "event_type": "bag_scanned",
                            "data": {
                                "bag_tag": bag["tag_number"],
                                "location": bag["current_location"],
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                            "timestamp": datetime.utcnow().isoformat()
                        })

                else:
                    # Generate flight update
                    if self.mock_flights:
                        flight = self.mock_flights[event_count % len(self.mock_flights)]
                        await self._trigger_callbacks("flight_status_changed", {
                            "event_type": "flight_status_changed",
                            "data": flight,
                            "timestamp": datetime.utcnow().isoformat()
                        })

                event_count += 1

                # Wait before next event
                await asyncio.sleep(5)  # Event every 5 seconds

            except Exception as e:
                logger.error(f"Error streaming mock event: {e}")
                await asyncio.sleep(1)

    # Synchronous data retrieval methods

    async def get_flights(
        self,
        airport: Optional[str] = None,
        hours_ahead: int = 6
    ) -> List[Dict[str, Any]]:
        """Get active flights"""
        if self.config.use_mock_data:
            # Filter mock flights
            return [
                f for f in self.mock_flights
                if not airport or f["departure_airport"] == airport
            ][:20]  # Limit to 20
        elif self.flight_ops_adapter:
            return await self.flight_ops_adapter.get_active_flights(airport, hours_ahead)
        else:
            return []

    async def get_bags(
        self,
        flight_number: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get bags"""
        if self.config.use_mock_data:
            bags = self.mock_bags

            if flight_number:
                bags = [b for b in bags if b.get("flight_number") == flight_number]
            if status:
                bags = [b for b in bags if b.get("status") == status]

            return bags[:100]  # Limit to 100
        elif self.dcs_adapter:
            return await self.dcs_adapter.get_checked_bags(flight_number=flight_number)
        else:
            return []

    async def get_bag_details(self, bag_tag: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific bag"""
        if self.config.use_mock_data:
            # Search in mock bags
            for bag in self.mock_bags:
                if bag["tag_number"] == bag_tag:
                    return bag

            # Check demo scenario bags
            for scenario_bag in self.mock_generator.demo_scenario_bags.values():
                if scenario_bag["tag_number"] == bag_tag:
                    return scenario_bag

            return None
        elif self.dcs_adapter:
            return await self.dcs_adapter.get_bag_details(bag_tag)
        else:
            return None

    async def get_demo_scenarios(self) -> List[Dict[str, Any]]:
        """Get Copa demo scenarios for December 15th presentation"""
        if self.mock_generator:
            return self.mock_generator.get_demo_scenarios()
        else:
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all integrations"""
        health = {
            "service": "healthy",
            "mode": "mock" if self.config.use_mock_data else "live",
            "adapters": {}
        }

        if not self.config.use_mock_data:
            if self.dcs_adapter:
                health["adapters"]["dcs"] = await self.dcs_adapter.health_check()
            if self.flight_ops_adapter:
                health["adapters"]["flight_ops"] = await self.flight_ops_adapter.health_check()
            if self.bhs_adapter:
                health["adapters"]["bhs"] = await self.bhs_adapter.health_check()

        return health


# Global service instance
_integration_service: Optional[CopaIntegrationService] = None


async def get_integration_service() -> CopaIntegrationService:
    """Get or create integration service instance"""
    global _integration_service
    if _integration_service is None:
        _integration_service = CopaIntegrationService()
        await _integration_service.initialize()
    return _integration_service


async def start_integration_service():
    """Start the Copa integration service"""
    service = await get_integration_service()
    await service.start()
    return service
