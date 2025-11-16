"""
Webhook Registry

Manages webhook subscriptions and event delivery.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Webhook event types."""
    # Bag events
    BAG_SCANNED = "bag.scanned"
    BAG_STATUS_CHANGED = "bag.status_changed"
    BAG_DELAYED = "bag.delayed"
    BAG_LOST = "bag.lost"
    BAG_DELIVERED = "bag.delivered"

    # Flight events
    FLIGHT_DELAYED = "flight.delayed"
    FLIGHT_CANCELLED = "flight.cancelled"
    FLIGHT_DEPARTED = "flight.departed"
    FLIGHT_ARRIVED = "flight.arrived"

    # Agent events
    AGENT_EXECUTED = "agent.executed"
    PREDICTION_GENERATED = "prediction.generated"
    COMPENSATION_CALCULATED = "compensation.calculated"


@dataclass
class WebhookSubscription:
    """Webhook subscription configuration."""
    id: str
    service_name: str
    endpoint_url: str
    event_types: Set[EventType]
    secret: Optional[str] = None
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookEvent:
    """Webhook event to be delivered."""
    id: str
    event_type: EventType
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    retry_count: int = 0
    max_retries: int = 3


class WebhookRegistry:
    """
    Manages webhook subscriptions and event delivery.

    Allows services to register webhooks to receive events.
    """

    def __init__(self):
        """Initialize webhook registry."""
        self.subscriptions: Dict[str, WebhookSubscription] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.delivery_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)

    def register_webhook(
        self,
        service_name: str,
        endpoint_url: str,
        event_types: List[EventType],
        secret: Optional[str] = None
    ) -> str:
        """
        Register a webhook subscription.

        Args:
            service_name: Name of subscribing service
            endpoint_url: Webhook endpoint URL
            event_types: List of event types to subscribe to
            secret: Optional webhook secret for verification

        Returns:
            Subscription ID
        """
        import uuid

        subscription_id = str(uuid.uuid4())

        subscription = WebhookSubscription(
            id=subscription_id,
            service_name=service_name,
            endpoint_url=endpoint_url,
            event_types=set(event_types),
            secret=secret
        )

        self.subscriptions[subscription_id] = subscription

        self.logger.info(
            f"Registered webhook for {service_name}: "
            f"{len(event_types)} event types"
        )

        return subscription_id

    def unregister_webhook(self, subscription_id: str):
        """
        Unregister a webhook subscription.

        Args:
            subscription_id: Subscription ID to remove
        """
        if subscription_id in self.subscriptions:
            subscription = self.subscriptions[subscription_id]
            del self.subscriptions[subscription_id]

            self.logger.info(
                f"Unregistered webhook for {subscription.service_name}"
            )

    async def publish_event(
        self,
        event_type: EventType,
        data: Dict[str, Any]
    ):
        """
        Publish event to all subscribed webhooks.

        Args:
            event_type: Type of event
            data: Event payload
        """
        import uuid

        event = WebhookEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            data=data
        )

        # Find matching subscriptions
        matching_subs = [
            sub for sub in self.subscriptions.values()
            if event_type in sub.event_types and sub.active
        ]

        if not matching_subs:
            self.logger.debug(
                f"No subscribers for event type: {event_type}"
            )
            return

        self.logger.info(
            f"Publishing {event_type} event to {len(matching_subs)} subscribers"
        )

        # Queue event for delivery to each subscription
        for subscription in matching_subs:
            await self.event_queue.put((subscription, event))

    async def start_delivery_worker(self):
        """
        Start webhook delivery worker.

        Processes events from queue and delivers to endpoints.
        """
        self.logger.info("Starting webhook delivery worker")

        while True:
            try:
                subscription, event = await self.event_queue.get()

                # Deliver event (with retry logic)
                success = await self._deliver_webhook(subscription, event)

                if not success and event.retry_count < event.max_retries:
                    # Requeue for retry
                    event.retry_count += 1
                    await asyncio.sleep(2 ** event.retry_count)  # Exponential backoff
                    await self.event_queue.put((subscription, event))

                self.event_queue.task_done()

            except Exception as e:
                self.logger.error(f"Error in delivery worker: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _deliver_webhook(
        self,
        subscription: WebhookSubscription,
        event: WebhookEvent
    ) -> bool:
        """
        Deliver webhook event to endpoint.

        Args:
            subscription: Webhook subscription
            event: Event to deliver

        Returns:
            True if delivery successful
        """
        try:
            payload = {
                "event_id": event.id,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "data": event.data
            }

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "NumberLabs-Webhooks/1.0",
                "X-Event-Type": event.event_type,
                "X-Event-ID": event.id
            }

            # Add signature if secret configured
            if subscription.secret:
                import hmac
                import hashlib
                import json

                signature = hmac.new(
                    subscription.secret.encode(),
                    json.dumps(payload).encode(),
                    hashlib.sha256
                ).hexdigest()

                headers["X-Webhook-Signature"] = signature

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    subscription.endpoint_url,
                    json=payload,
                    headers=headers
                )

                if response.status_code in [200, 201, 202, 204]:
                    self.logger.info(
                        f"Delivered {event.event_type} to {subscription.service_name}"
                    )
                    return True
                else:
                    self.logger.warning(
                        f"Failed to deliver webhook to {subscription.service_name}: "
                        f"Status {response.status_code}"
                    )
                    return False

        except Exception as e:
            self.logger.error(
                f"Error delivering webhook to {subscription.service_name}: {e}"
            )
            return False

    def get_subscriptions(
        self,
        service_name: Optional[str] = None
    ) -> List[WebhookSubscription]:
        """
        Get webhook subscriptions.

        Args:
            service_name: Filter by service name (optional)

        Returns:
            List of subscriptions
        """
        if service_name:
            return [
                sub for sub in self.subscriptions.values()
                if sub.service_name == service_name
            ]

        return list(self.subscriptions.values())


# Singleton instance
_webhook_registry: Optional[WebhookRegistry] = None


def get_webhook_registry() -> WebhookRegistry:
    """
    Get or create singleton webhook registry.

    Returns:
        WebhookRegistry instance
    """
    global _webhook_registry
    if _webhook_registry is None:
        _webhook_registry = WebhookRegistry()
    return _webhook_registry
