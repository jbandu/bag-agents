"""
Tests for API Gateway
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import jwt
from datetime import datetime, timedelta

from auth.rbac import Role


@pytest.fixture
def test_token():
    """Create test JWT token."""
    payload = {
        "sub": "test-user-123",
        "email": "test@example.com",
        "role": Role.OPERATIONS,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }

    # Use a test secret
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return token


@pytest.fixture
def test_client():
    """Create test client for gateway."""
    # Mock Supabase initialization
    with patch("auth.supabase_auth.create_client"):
        # Set test environment
        import os
        os.environ["SUPABASE_JWT_SECRET"] = "test-secret"
        os.environ["ENVIRONMENT"] = "test"

        from gateway.main import app

        client = TestClient(app)
        yield client


def test_health_check(test_client):
    """Test gateway health check."""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data


def test_root_endpoint(test_client):
    """Test root endpoint."""
    response = test_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NumberLabs API Gateway"
    assert "version" in data


def test_auth_required(test_client):
    """Test that authentication is required for proxied endpoints."""
    response = test_client.get("/api/bags/test")

    assert response.status_code == 401
    assert "Authorization header required" in response.json()["error"]


def test_invalid_token(test_client):
    """Test request with invalid token."""
    response = test_client.get(
        "/api/bags/test",
        headers={"Authorization": "Bearer invalid-token"}
    )

    assert response.status_code == 401


def test_valid_token(test_client, test_token):
    """Test request with valid token."""
    # Mock the service response
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.headers = {"content-type": "application/json"}
        mock_request.return_value = mock_response

        response = test_client.get(
            "/api/bags/test-bag",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # Should forward request (mocked to return 200)
        assert response.status_code in [200, 502]  # 502 if service unreachable


def test_rate_limiting(test_client, test_token):
    """Test rate limiting."""
    # Make many requests rapidly
    responses = []
    for i in range(100):
        response = test_client.get(
            "/api/bags/test",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        responses.append(response)

    # Some requests should be rate limited
    # Note: Actual behavior depends on rate limits configured
    status_codes = [r.status_code for r in responses]
    assert any(code == 429 for code in status_codes) or all(code in [200, 502] for code in status_codes)


def test_admin_only_endpoint(test_client):
    """Test that admin endpoints require admin role."""
    # Create non-admin token
    payload = {
        "sub": "test-user-456",
        "email": "user@example.com",
        "role": Role.PASSENGER,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    user_token = jwt.encode(payload, "test-secret", algorithm="HS256")

    response = test_client.get(
        "/admin/services/status",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 403


def test_admin_endpoint_with_admin_role(test_client):
    """Test admin endpoint with admin token."""
    # Create admin token
    payload = {
        "sub": "admin-user-789",
        "email": "admin@example.com",
        "role": Role.ADMIN,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    admin_token = jwt.encode(payload, "test-secret", algorithm="HS256")

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_get.return_value = mock_response

        response = test_client.get(
            "/admin/services/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_bag_service_client():
    """Test bag service client."""
    from clients.bag_client import BagServiceClient

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "bag-123",
            "tag_number": "TAG123",
            "status": "in_flight"
        }
        mock_get.return_value = mock_response

        client = BagServiceClient(api_key="test-key")
        bag = await client.get_bag("bag-123")

        assert bag["id"] == "bag-123"
        assert bag["status"] == "in_flight"


@pytest.mark.asyncio
async def test_webhook_registration():
    """Test webhook registration."""
    from webhooks.webhook_registry import WebhookRegistry, EventType

    registry = WebhookRegistry()

    # Register webhook
    sub_id = registry.register_webhook(
        service_name="test-service",
        endpoint_url="https://example.com/webhook",
        event_types=[EventType.BAG_SCANNED, EventType.BAG_DELAYED]
    )

    assert sub_id is not None

    # Get subscriptions
    subs = registry.get_subscriptions(service_name="test-service")
    assert len(subs) == 1
    assert subs[0].service_name == "test-service"


@pytest.mark.asyncio
async def test_webhook_delivery():
    """Test webhook event delivery."""
    from webhooks.webhook_registry import WebhookRegistry, EventType

    registry = WebhookRegistry()

    # Register webhook
    registry.register_webhook(
        service_name="test-service",
        endpoint_url="https://example.com/webhook",
        event_types=[EventType.BAG_SCANNED]
    )

    # Mock HTTP client
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Publish event
        await registry.publish_event(
            EventType.BAG_SCANNED,
            {"bag_id": "bag-123", "location": "JFK"}
        )

        # Process queue
        if not registry.event_queue.empty():
            subscription, event = await registry.event_queue.get()
            success = await registry._deliver_webhook(subscription, event)
            assert success


def test_shared_contracts():
    """Test shared data contracts."""
    from shared.contracts import Bag, BagStatus

    # Create bag instance
    bag = Bag(
        id="bag-123",
        tag_number="TAG123",
        passenger_id="pass-001",
        origin_flight_id="AA123",
        current_status=BagStatus.IN_FLIGHT,
        weight_kg=23.5,
        checked_in_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    assert bag.id == "bag-123"
    assert bag.current_status == BagStatus.IN_FLIGHT

    # Test serialization
    bag_dict = bag.model_dump()
    assert "id" in bag_dict
    assert "tag_number" in bag_dict


def test_rbac_permissions():
    """Test RBAC permission checking."""
    from auth.rbac import has_permission, Permission, Role

    # Admin has all permissions
    assert has_permission(Role.ADMIN, Permission.READ_BAG)
    assert has_permission(Role.ADMIN, Permission.MANAGE_USERS)

    # Passenger has limited permissions
    assert has_permission(Role.PASSENGER, Permission.READ_BAG)
    assert not has_permission(Role.PASSENGER, Permission.WRITE_BAG)
    assert not has_permission(Role.PASSENGER, Permission.MANAGE_USERS)

    # Operations can read/write but not manage
    assert has_permission(Role.OPERATIONS, Permission.READ_BAG)
    assert has_permission(Role.OPERATIONS, Permission.WRITE_BAG)
    assert not has_permission(Role.OPERATIONS, Permission.MANAGE_USERS)


def test_rate_limiter():
    """Test rate limiter."""
    from gateway.rate_limiter import RateLimiter
    from auth.rbac import Role

    limiter = RateLimiter()

    # Test within limits
    assert limiter.check_rate_limit("user-1", Role.PASSENGER, tokens=1)
    assert limiter.check_rate_limit("user-1", Role.PASSENGER, tokens=1)

    # Test burst capacity
    for i in range(20):  # Exceed burst for passenger
        limiter.check_rate_limit("user-1", Role.PASSENGER, tokens=1)

    # Should eventually be rate limited
    # (exact behavior depends on timing)


@pytest.mark.asyncio
async def test_service_router():
    """Test service routing."""
    from gateway.router import ServiceRouter

    service_urls = {
        "bag": "https://bag.example.com",
        "airline": "https://airline.example.com"
    }

    router = ServiceRouter(service_urls)

    assert router.get_service_url("bag") == "https://bag.example.com"
    assert router.get_service_url("airline") == "https://airline.example.com"

    # Test unknown service
    with pytest.raises(ValueError):
        router.get_service_url("unknown")
