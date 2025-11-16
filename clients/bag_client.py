"""
Bag Service Client

SDK for bag-agents service to communicate with bag tracking service.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


logger = logging.getLogger(__name__)


class BagServiceClient:
    """
    Client for interacting with the bag tracking service.

    Provides methods for:
    - Retrieving bag information
    - Updating bag status
    - Creating scan events
    - Querying bag history
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize bag service client.

        Args:
            base_url: Base URL of bag service (defaults to env var)
            api_key: Service API key (defaults to env var)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv(
            "BAG_SERVICE_URL",
            "https://bag.numberlabs.com"
        )
        self.api_key = api_key or os.getenv("BAG_SERVICE_API_KEY")
        self.timeout = timeout

        if not self.api_key:
            logger.warning("Bag service API key not configured")

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
    async def get_bag(self, bag_id: str) -> Dict[str, Any]:
        """
        Get bag information by ID.

        Args:
            bag_id: Bag identifier

        Returns:
            Bag data

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(f"/api/bags/{bag_id}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error fetching bag {bag_id}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_bag_by_tag(self, tag_number: str) -> Dict[str, Any]:
        """
        Get bag information by tag number.

        Args:
            tag_number: Baggage tag number

        Returns:
            Bag data

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                f"/api/bags/search",
                params={"tag_number": tag_number}
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error fetching bag by tag {tag_number}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def update_bag_status(
        self,
        bag_id: str,
        status: str,
        location: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update bag status.

        Args:
            bag_id: Bag identifier
            status: New status
            location: Current location (optional)
            notes: Status update notes (optional)

        Returns:
            Updated bag data

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            data = {"status": status}

            if location:
                data["location"] = location
            if notes:
                data["notes"] = notes

            response = await self.client.patch(
                f"/api/bags/{bag_id}/status",
                json=data
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error updating bag {bag_id} status: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def create_scan(
        self,
        bag_id: str,
        location: str,
        scan_type: str = "RFID",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a scan event for a bag.

        Args:
            bag_id: Bag identifier
            location: Scan location
            scan_type: Type of scan (RFID, Manual, etc.)
            metadata: Additional scan metadata

        Returns:
            Scan event data

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            data = {
                "bag_id": bag_id,
                "location": location,
                "scan_type": scan_type,
                "metadata": metadata or {}
            }

            response = await self.client.post(
                f"/api/bags/{bag_id}/scans",
                json=data
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error creating scan for bag {bag_id}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_bag_history(
        self,
        bag_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get scan history for a bag.

        Args:
            bag_id: Bag identifier
            limit: Maximum number of events to return

        Returns:
            List of scan events

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                f"/api/bags/{bag_id}/history",
                params={"limit": limit}
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error fetching history for bag {bag_id}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def search_bags(
        self,
        flight_id: Optional[str] = None,
        status: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for bags matching criteria.

        Args:
            flight_id: Filter by flight ID
            status: Filter by status
            location: Filter by current location
            limit: Maximum number of results

        Returns:
            List of matching bags

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            params = {"limit": limit}

            if flight_id:
                params["flight_id"] = flight_id
            if status:
                params["status"] = status
            if location:
                params["location"] = location

            response = await self.client.get(
                "/api/bags/search",
                params=params
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error searching bags: {e}")
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
_bag_client: Optional[BagServiceClient] = None


def get_bag_client() -> BagServiceClient:
    """
    Get or create singleton bag service client.

    Returns:
        BagServiceClient instance
    """
    global _bag_client
    if _bag_client is None:
        _bag_client = BagServiceClient()
    return _bag_client
