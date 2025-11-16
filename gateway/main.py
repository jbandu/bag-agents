"""
Unified API Gateway

Central entry point for all NumberLabs baggage services.
Routes requests to appropriate microservices with authentication and rate limiting.
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import httpx

from auth.supabase_auth import SupabaseAuth, get_current_user, require_role
from auth.rbac import Role, check_permission
from gateway.rate_limiter import RateLimiter
from gateway.router import ServiceRouter
from gateway.logging_middleware import LoggingMiddleware


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Service URLs (configured via environment)
SERVICE_URLS = {
    "airline": os.getenv("AIRLINE_SERVICE_URL", "https://airline.numberlabs.com"),
    "bag": os.getenv("BAG_SERVICE_URL", "https://bag.numberlabs.com"),
    "agents": os.getenv("AGENTS_SERVICE_URL", "http://localhost:8000")
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting API Gateway...")
    logger.info(f"Service URLs: {SERVICE_URLS}")

    # Initialize Supabase Auth
    supabase_auth = SupabaseAuth()
    app.state.supabase_auth = supabase_auth

    # Initialize rate limiter
    rate_limiter = RateLimiter()
    app.state.rate_limiter = rate_limiter

    # Initialize service router
    service_router = ServiceRouter(SERVICE_URLS)
    app.state.service_router = service_router

    # Create HTTP client
    app.state.http_client = httpx.AsyncClient(timeout=30.0)

    logger.info("API Gateway started successfully")

    yield

    # Shutdown
    logger.info("Shutting down API Gateway...")
    await app.state.http_client.aclose()
    logger.info("API Gateway shut down")


# Create FastAPI app
app = FastAPI(
    title="NumberLabs Baggage Services API Gateway",
    description="Unified API gateway for airline, bag tracking, and AI agents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://airline.numberlabs.com",
        "https://bag.numberlabs.com",
        "http://localhost:3000",
        "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)


# =====================================================================
# HEALTH CHECK
# =====================================================================

@app.get("/health")
async def health_check():
    """Gateway health check."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "airline": SERVICE_URLS["airline"],
            "bag": SERVICE_URLS["bag"],
            "agents": SERVICE_URLS["agents"]
        }
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "NumberLabs API Gateway",
        "version": "1.0.0",
        "documentation": "/docs",
        "services": ["airline", "bag", "agents"]
    }


# =====================================================================
# AUTHENTICATION ENDPOINTS
# =====================================================================

@app.post("/auth/login")
async def login(request: Request):
    """
    User login endpoint.

    Authenticates user with Supabase and returns JWT token.
    """
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")

        supabase_auth = request.app.state.supabase_auth
        result = await supabase_auth.sign_in(email, password)

        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "user": result["user"]
        }

    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/auth/refresh")
async def refresh_token(request: Request):
    """Refresh access token using refresh token."""
    try:
        data = await request.json()
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token required")

        supabase_auth = request.app.state.supabase_auth
        result = await supabase_auth.refresh_session(refresh_token)

        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"]
        }

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/auth/service-token")
async def create_service_token(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Create service account token for inter-service communication.

    Requires admin role.
    """
    # Check admin permission
    if not check_permission(current_user.get("role"), Role.ADMIN):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        data = await request.json()
        service_name = data.get("service_name")

        if not service_name:
            raise HTTPException(status_code=400, detail="Service name required")

        supabase_auth = request.app.state.supabase_auth
        token = await supabase_auth.create_service_token(service_name)

        return {
            "service_name": service_name,
            "api_key": token
        }

    except Exception as e:
        logger.error(f"Service token creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# PROXY ROUTES TO SERVICES
# =====================================================================

@app.api_route("/api/airline/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_airline(
    path: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Proxy requests to airline service.

    Routes: /api/airline/* → airline service
    """
    # Check rate limit
    rate_limiter = request.app.state.rate_limiter
    user_id = current_user.get("id", "anonymous")
    role = current_user.get("role", Role.PASSENGER)

    if not rate_limiter.check_rate_limit(user_id, role):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Forward request
    try:
        service_router = request.app.state.service_router
        http_client = request.app.state.http_client

        response = await service_router.forward_request(
            service="airline",
            path=path,
            method=request.method,
            headers=dict(request.headers),
            body=await request.body(),
            http_client=http_client,
            user=current_user
        )

        return JSONResponse(
            content=response["body"],
            status_code=response["status_code"],
            headers=response["headers"]
        )

    except Exception as e:
        logger.error(f"Error proxying to airline service: {e}")
        raise HTTPException(status_code=502, detail="Service unavailable")


@app.api_route("/api/bags/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_bag(
    path: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Proxy requests to bag tracking service.

    Routes: /api/bags/* → bag service
    """
    rate_limiter = request.app.state.rate_limiter
    user_id = current_user.get("id", "anonymous")
    role = current_user.get("role", Role.PASSENGER)

    if not rate_limiter.check_rate_limit(user_id, role):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        service_router = request.app.state.service_router
        http_client = request.app.state.http_client

        response = await service_router.forward_request(
            service="bag",
            path=path,
            method=request.method,
            headers=dict(request.headers),
            body=await request.body(),
            http_client=http_client,
            user=current_user
        )

        return JSONResponse(
            content=response["body"],
            status_code=response["status_code"],
            headers=response["headers"]
        )

    except Exception as e:
        logger.error(f"Error proxying to bag service: {e}")
        raise HTTPException(status_code=502, detail="Service unavailable")


@app.api_route("/api/agents/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_agents(
    path: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Proxy requests to AI agents service.

    Routes: /api/agents/* → bag-agents service
    Requires: AGENT or OPERATIONS role
    """
    # Check role
    role = current_user.get("role", Role.PASSENGER)
    if role not in [Role.ADMIN, Role.OPERATIONS, Role.AGENT]:
        raise HTTPException(
            status_code=403,
            detail="Agent or Operations access required"
        )

    rate_limiter = request.app.state.rate_limiter
    user_id = current_user.get("id", "anonymous")

    if not rate_limiter.check_rate_limit(user_id, role):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        service_router = request.app.state.service_router
        http_client = request.app.state.http_client

        response = await service_router.forward_request(
            service="agents",
            path=path,
            method=request.method,
            headers=dict(request.headers),
            body=await request.body(),
            http_client=http_client,
            user=current_user
        )

        return JSONResponse(
            content=response["body"],
            status_code=response["status_code"],
            headers=response["headers"]
        )

    except Exception as e:
        logger.error(f"Error proxying to agents service: {e}")
        raise HTTPException(status_code=502, detail="Service unavailable")


# =====================================================================
# ADMIN ENDPOINTS
# =====================================================================

@app.get("/admin/services/status")
async def get_services_status(
    request: Request,
    current_user: dict = Depends(require_role(Role.ADMIN))
):
    """Get status of all backend services."""
    http_client = request.app.state.http_client
    statuses = {}

    for service_name, service_url in SERVICE_URLS.items():
        try:
            response = await http_client.get(
                f"{service_url}/health",
                timeout=5.0
            )
            statuses[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "url": service_url,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            statuses[service_name] = {
                "status": "unreachable",
                "url": service_url,
                "error": str(e)
            }

    return {
        "services": statuses,
        "gateway_status": "healthy"
    }


@app.get("/admin/metrics")
async def get_metrics(
    request: Request,
    current_user: dict = Depends(require_role(Role.ADMIN))
):
    """Get gateway metrics."""
    rate_limiter = request.app.state.rate_limiter

    return {
        "rate_limits": rate_limiter.get_stats(),
        "total_requests": 0,  # Would track in production
        "uptime_seconds": 0    # Would track in production
    }


# =====================================================================
# ERROR HANDLERS
# =====================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("GATEWAY_PORT", "8080"))

    uvicorn.run(
        "gateway.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )
