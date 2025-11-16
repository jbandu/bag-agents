"""
Role-Based Access Control (RBAC)

Defines roles and permission checking for the API gateway.
"""

from typing import List, Optional
from enum import Enum


class Role(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"              # Full access to everything
    OPERATIONS = "operations"    # Read/write tracking data
    AGENT = "agent"             # AI agents only
    HANDLER = "handler"         # Update scans, read assignments
    PASSENGER = "passenger"     # Read own bag data only


class Permission(str, Enum):
    """System permissions."""
    # Bag operations
    READ_BAG = "read:bag"
    WRITE_BAG = "write:bag"
    DELETE_BAG = "delete:bag"

    # Airline operations
    READ_FLIGHT = "read:flight"
    WRITE_FLIGHT = "write:flight"
    DELETE_FLIGHT = "delete:flight"

    # Agent operations
    INVOKE_AGENT = "invoke:agent"
    READ_AGENT_RESULTS = "read:agent_results"

    # Scan operations
    CREATE_SCAN = "create:scan"
    READ_SCAN = "read:scan"

    # Admin operations
    MANAGE_USERS = "manage:users"
    MANAGE_ROLES = "manage:roles"
    VIEW_METRICS = "view:metrics"
    MANAGE_SERVICES = "manage:services"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        # Has all permissions
        Permission.READ_BAG,
        Permission.WRITE_BAG,
        Permission.DELETE_BAG,
        Permission.READ_FLIGHT,
        Permission.WRITE_FLIGHT,
        Permission.DELETE_FLIGHT,
        Permission.INVOKE_AGENT,
        Permission.READ_AGENT_RESULTS,
        Permission.CREATE_SCAN,
        Permission.READ_SCAN,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ROLES,
        Permission.VIEW_METRICS,
        Permission.MANAGE_SERVICES,
    ],
    Role.OPERATIONS: [
        # Can read/write tracking data
        Permission.READ_BAG,
        Permission.WRITE_BAG,
        Permission.READ_FLIGHT,
        Permission.WRITE_FLIGHT,
        Permission.INVOKE_AGENT,
        Permission.READ_AGENT_RESULTS,
        Permission.CREATE_SCAN,
        Permission.READ_SCAN,
        Permission.VIEW_METRICS,
    ],
    Role.AGENT: [
        # AI agents - can invoke other agents and read/write bag data
        Permission.READ_BAG,
        Permission.WRITE_BAG,
        Permission.READ_FLIGHT,
        Permission.INVOKE_AGENT,
        Permission.READ_AGENT_RESULTS,
        Permission.READ_SCAN,
    ],
    Role.HANDLER: [
        # Can update scans and read assignments
        Permission.CREATE_SCAN,
        Permission.READ_SCAN,
        Permission.READ_BAG,
        Permission.READ_FLIGHT,
    ],
    Role.PASSENGER: [
        # Can only read their own bag data
        Permission.READ_BAG,
        Permission.READ_SCAN,
    ]
}


def has_permission(role: str, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: User role
        permission: Permission to check

    Returns:
        True if role has permission
    """
    try:
        role_enum = Role(role)
        permissions = ROLE_PERMISSIONS.get(role_enum, [])
        return permission in permissions
    except ValueError:
        return False


def check_permission(role: str, required_role: Role) -> bool:
    """
    Check if user role meets minimum required role.

    Uses role hierarchy: Admin > Operations > Agent > Handler > Passenger

    Args:
        role: User's current role
        required_role: Minimum required role

    Returns:
        True if user meets requirement
    """
    role_hierarchy = {
        Role.ADMIN: 4,
        Role.OPERATIONS: 3,
        Role.AGENT: 2,
        Role.HANDLER: 1,
        Role.PASSENGER: 0
    }

    try:
        user_level = role_hierarchy.get(Role(role), 0)
        required_level = role_hierarchy.get(required_role, 0)
        return user_level >= required_level
    except ValueError:
        return False


def get_role_permissions(role: str) -> List[Permission]:
    """
    Get all permissions for a role.

    Args:
        role: User role

    Returns:
        List of permissions
    """
    try:
        role_enum = Role(role)
        return ROLE_PERMISSIONS.get(role_enum, [])
    except ValueError:
        return []


def can_access_resource(
    user_role: str,
    resource_owner_id: Optional[str],
    requesting_user_id: str
) -> bool:
    """
    Check if user can access a specific resource.

    Passengers can only access their own resources.
    Other roles can access all resources.

    Args:
        user_role: User's role
        resource_owner_id: ID of resource owner
        requesting_user_id: ID of user making request

    Returns:
        True if access allowed
    """
    try:
        role_enum = Role(user_role)

        # Admin and Operations can access everything
        if role_enum in [Role.ADMIN, Role.OPERATIONS, Role.AGENT]:
            return True

        # Handlers can access if related to their assignments
        if role_enum == Role.HANDLER:
            # In production, would check assignment database
            return True

        # Passengers can only access their own resources
        if role_enum == Role.PASSENGER:
            return resource_owner_id == requesting_user_id

        return False

    except ValueError:
        return False
