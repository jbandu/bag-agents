"""
Supabase Authentication Integration

Handles JWT validation and user authentication using Supabase.
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Depends, Header
from supabase import create_client, Client

from auth.rbac import Role


logger = logging.getLogger(__name__)


class SupabaseAuth:
    """
    Supabase authentication handler.

    Provides JWT validation and user management.
    """

    def __init__(self):
        """Initialize Supabase client."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET")

        if not all([self.supabase_url, self.supabase_key]):
            logger.warning("Supabase credentials not configured")
            self.client: Optional[Client] = None
        else:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)

    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Dictionary with access_token, refresh_token, and user data

        Raises:
            Exception: If authentication fails
        """
        if not self.client:
            raise Exception("Supabase not configured")

        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "role": response.user.user_metadata.get("role", Role.PASSENGER),
                    "metadata": response.user.user_metadata
                }
            }

        except Exception as e:
            logger.error(f"Sign in failed: {e}")
            raise Exception("Invalid credentials")

    async def sign_up(
        self,
        email: str,
        password: str,
        role: str = Role.PASSENGER,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sign up new user.

        Args:
            email: User email
            password: User password
            role: User role
            metadata: Additional user metadata

        Returns:
            User data

        Raises:
            Exception: If signup fails
        """
        if not self.client:
            raise Exception("Supabase not configured")

        try:
            user_metadata = metadata or {}
            user_metadata["role"] = role

            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })

            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "role": role
                }
            }

        except Exception as e:
            logger.error(f"Sign up failed: {e}")
            raise Exception("Signup failed")

    async def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New access and refresh tokens

        Raises:
            Exception: If refresh fails
        """
        if not self.client:
            raise Exception("Supabase not configured")

        try:
            response = self.client.auth.refresh_session(refresh_token)

            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token
            }

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise Exception("Invalid refresh token")

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token and extract user data.

        Args:
            token: JWT access token

        Returns:
            Decoded token payload with user data

        Raises:
            HTTPException: If token is invalid
        """
        if not self.supabase_jwt_secret:
            # Fallback for development
            logger.warning("JWT secret not configured, using development mode")
            try:
                # Decode without verification (ONLY for development!)
                decoded = jwt.decode(token, options={"verify_signature": False})
                return decoded
            except Exception as e:
                raise HTTPException(status_code=401, detail="Invalid token")

        try:
            decoded = jwt.decode(
                token,
                self.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated"
            )

            # Extract user data
            return {
                "id": decoded.get("sub"),
                "email": decoded.get("email"),
                "role": decoded.get("user_metadata", {}).get("role", Role.PASSENGER),
                "metadata": decoded.get("user_metadata", {}),
                "exp": decoded.get("exp")
            }

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

    async def create_service_token(
        self,
        service_name: str,
        expires_in_days: int = 365
    ) -> str:
        """
        Create a service account token for inter-service communication.

        Args:
            service_name: Name of the service
            expires_in_days: Token expiration in days

        Returns:
            Service API key (JWT token)
        """
        if not self.supabase_jwt_secret:
            raise Exception("JWT secret not configured")

        # Create service account payload
        payload = {
            "sub": f"service:{service_name}",
            "role": Role.AGENT,
            "service": True,
            "service_name": service_name,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=expires_in_days)
        }

        # Sign token
        token = jwt.encode(
            payload,
            self.supabase_jwt_secret,
            algorithm="HS256"
        )

        return token

    async def sign_out(self, token: str):
        """
        Sign out user (invalidate token).

        Args:
            token: Access token to invalidate
        """
        if not self.client:
            raise Exception("Supabase not configured")

        try:
            self.client.auth.sign_out()
        except Exception as e:
            logger.error(f"Sign out failed: {e}")


# Dependency for FastAPI routes
async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user.

    Args:
        authorization: Authorization header (Bearer token)

    Returns:
        User data from JWT token

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = parts[1]

    # Verify token
    supabase_auth = SupabaseAuth()
    user = supabase_auth.verify_token(token)

    return user


def require_role(required_role: str):
    """
    Dependency factory to require specific role.

    Usage:
        @app.get("/admin/users", dependencies=[Depends(require_role(Role.ADMIN))])

    Args:
        required_role: Required role

    Returns:
        Dependency function
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role", Role.PASSENGER)

        # Admin has access to everything
        if user_role == Role.ADMIN:
            return current_user

        # Check role hierarchy
        role_hierarchy = {
            Role.ADMIN: 4,
            Role.OPERATIONS: 3,
            Role.AGENT: 2,
            Role.HANDLER: 1,
            Role.PASSENGER: 0
        }

        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=403,
                detail=f"Requires {required_role} role or higher"
            )

        return current_user

    return role_checker
