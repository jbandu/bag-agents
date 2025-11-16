"""
Airline Service Client

SDK for bag-agents service to communicate with airline service.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


logger = logging.getLogger(__name__)


class AirlineServiceClient:
    """
    Client for interacting with the airline service.

    Provides methods for:
    - Retrieving flight information
    - Getting flight schedules
    - Checking flight status
    - Accessing passenger data
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize airline service client.

        Args:
            base_url: Base URL of airline service (defaults to env var)
            api_key: Service API key (defaults to env var)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv(
            "AIRLINE_SERVICE_URL",
            "https://airline.numberlabs.com"
        )
        self.api_key = api_key or os.getenv("AIRLINE_SERVICE_API_KEY")
        self.timeout = timeout

        if not self.api_key:
            logger.warning("Airline service API key not configured")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._get_headers()
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "BagAgents-Client/1.0"
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_flight(self, flight_id: str) -> Dict[str, Any]:
        """
        Get flight information by ID.

        Args:
            flight_id: Flight identifier or flight number

        Returns:
            Flight data

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(f"/api/airline/flights/{flight_id}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error fetching flight {flight_id}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_flight_status(self, flight_number: str, date: str) -> Dict[str, Any]:
        """
        Get current flight status.

        Args:
            flight_number: Flight number (e.g., "AA123")
            date: Flight date (YYYY-MM-DD)

        Returns:
            Flight status data

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                f"/api/airline/flights/{flight_number}/status",
                params={"date": date}
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error fetching status for flight {flight_number}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_passenger(self, passenger_id: str) -> Dict[str, Any]:
        """
        Get passenger information.

        Args:
            passenger_id: Passenger identifier

        Returns:
            Passenger data

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                f"/api/airline/passengers/{passenger_id}"
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error fetching passenger {passenger_id}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_connection_flights(
        self,
        origin: str,
        destination: str,
        date: str
    ) -> List[Dict[str, Any]]:
        """
        Get available connection flights.

        Args:
            origin: Origin airport code
            destination: Destination airport code
            date: Travel date (YYYY-MM-DD)

        Returns:
            List of available flights

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                "/api/airline/flights/search",
                params={
                    "origin": origin,
                    "destination": destination,
                    "date": date
                }
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(
                f"Error fetching connections {origin}->{destination}: {e}"
            )
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def notify_passenger(
        self,
        passenger_id: str,
        notification_type: str,
        message: str,
        channel: str = "email"
    ) -> Dict[str, Any]:
        """
        Send notification to passenger.

        Args:
            passenger_id: Passenger identifier
            notification_type: Type of notification
            message: Notification message
            channel: Delivery channel (email, sms, push)

        Returns:
            Notification delivery status

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            data = {
                "passenger_id": passenger_id,
                "type": notification_type,
                "message": message,
                "channel": channel
            }

            response = await self.client.post(
                f"/api/airline/passengers/{passenger_id}/notify",
                json=data
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error notifying passenger {passenger_id}: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Singleton instance
_airline_client: Optional[AirlineServiceClient] = None


def get_airline_client() -> AirlineServiceClient:
    """
    Get or create singleton airline service client.

    Returns:
        AirlineServiceClient instance
    """
    global _airline_client
    if _airline_client is None:
        _airline_client = AirlineServiceClient()
    return _airline_client
