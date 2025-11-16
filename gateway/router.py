"""
Service Router

Routes requests to appropriate microservices.
"""

import logging
from typing import Dict, Any, Optional
import httpx


logger = logging.getLogger(__name__)


class ServiceRouter:
    """
    Routes requests to backend microservices.

    Handles request forwarding, header management, and error handling.
    """

    def __init__(self, service_urls: Dict[str, str]):
        """
        Initialize service router.

        Args:
            service_urls: Mapping of service names to URLs
        """
        self.service_urls = service_urls
        self.logger = logging.getLogger(__name__)

    async def forward_request(
        self,
        service: str,
        path: str,
        method: str,
        headers: Dict[str, str],
        body: bytes,
        http_client: httpx.AsyncClient,
        user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Forward request to backend service.

        Args:
            service: Service name (airline, bag, agents)
            path: Request path
            method: HTTP method
            headers: Request headers
            body: Request body
            http_client: HTTP client for making requests
            user: Authenticated user data

        Returns:
            Dictionary with status_code, headers, and body

        Raises:
            Exception: If forwarding fails
        """
        if service not in self.service_urls:
            raise ValueError(f"Unknown service: {service}")

        target_url = f"{self.service_urls[service]}/{path}"

        # Prepare headers
        forward_headers = self._prepare_headers(headers, user)

        self.logger.info(f"Forwarding {method} request to {service}: {target_url}")

        try:
            # Make request to backend service
            response = await http_client.request(
                method=method,
                url=target_url,
                headers=forward_headers,
                content=body if method in ["POST", "PUT", "PATCH"] else None
            )

            # Return response data
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }

        except httpx.TimeoutException:
            self.logger.error(f"Timeout forwarding request to {service}")
            raise Exception(f"Service {service} timed out")

        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error forwarding to {service}: {e}")
            raise Exception(f"Error communicating with {service}")

        except Exception as e:
            self.logger.error(f"Unexpected error forwarding to {service}: {e}")
            raise Exception(f"Failed to forward request to {service}")

    def _prepare_headers(
        self,
        original_headers: Dict[str, str],
        user: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Prepare headers for forwarding.

        Removes sensitive headers and adds user context.

        Args:
            original_headers: Original request headers
            user: Authenticated user data

        Returns:
            Cleaned headers for forwarding
        """
        # Headers to exclude
        excluded_headers = {
            "host",
            "authorization",  # Don't forward original auth
            "content-length",  # Will be recalculated
        }

        # Copy headers except excluded ones
        forward_headers = {
            key: value
            for key, value in original_headers.items()
            if key.lower() not in excluded_headers
        }

        # Add user context headers
        if user:
            forward_headers["X-User-ID"] = user.get("id", "")
            forward_headers["X-User-Role"] = user.get("role", "")
            forward_headers["X-User-Email"] = user.get("email", "")

        # Add gateway identifier
        forward_headers["X-Forwarded-By"] = "NumberLabs-Gateway"

        return forward_headers

    def get_service_url(self, service: str) -> str:
        """
        Get URL for a service.

        Args:
            service: Service name

        Returns:
            Service URL

        Raises:
            ValueError: If service not found
        """
        if service not in self.service_urls:
            raise ValueError(f"Unknown service: {service}")

        return self.service_urls[service]
