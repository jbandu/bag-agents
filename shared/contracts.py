"""
Shared Data Contracts

Defines common data models used across all services (bag, airline, agents).
These contracts ensure consistent data structures for inter-service communication.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


# =====================================================================
# ENUMS
# =====================================================================

class BagStatus(str, Enum):
    """Bag status values."""
    CHECKED_IN = "checked_in"
    SECURITY = "security"
    SORTING = "sorting"
    LOADING = "loading"
    IN_FLIGHT = "in_flight"
    ARRIVED = "arrived"
    CLAIM = "claim"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    LOST = "lost"
    DAMAGED = "damaged"


class FlightStatus(str, Enum):
    """Flight status values."""
    SCHEDULED = "scheduled"
    BOARDING = "boarding"
    DEPARTED = "departed"
    IN_FLIGHT = "in_flight"
    LANDED = "landed"
    ARRIVED = "arrived"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class ScanType(str, Enum):
    """Scan type values."""
    RFID = "rfid"
    BARCODE = "barcode"
    MANUAL = "manual"
    AUTOMATED = "automated"


class NotificationType(str, Enum):
    """Notification types."""
    BAG_STATUS = "bag_status"
    FLIGHT_UPDATE = "flight_update"
    DELAY_ALERT = "delay_alert"
    DELIVERY_READY = "delivery_ready"
    COMPENSATION = "compensation"


# =====================================================================
# BAG MODELS
# =====================================================================

class Bag(BaseModel):
    """Bag data model."""

    id: str = Field(..., description="Unique bag identifier")
    tag_number: str = Field(..., description="Baggage tag number")
    passenger_id: str = Field(..., description="Passenger identifier")

    # Flight information
    origin_flight_id: str = Field(..., description="Origin flight ID")
    destination_flight_id: Optional[str] = Field(None, description="Destination flight ID for connections")

    # Location and status
    current_status: BagStatus = Field(..., description="Current bag status")
    current_location: Optional[str] = Field(None, description="Current location code")

    # Bag details
    weight_kg: float = Field(..., description="Bag weight in kilograms", gt=0)
    declared_value: float = Field(default=0.0, description="Declared value in USD", ge=0)
    special_handling: Optional[str] = Field(None, description="Special handling requirements")

    # Timestamps
    checked_in_at: datetime = Field(..., description="Check-in timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Risk assessment (from AI agents)
    risk_score: Optional[float] = Field(None, description="Risk score (0-100)", ge=0, le=100)
    risk_level: Optional[str] = Field(None, description="Risk level (low, medium, high)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "bag_123",
                "tag_number": "BAG123456",
                "passenger_id": "pass_001",
                "origin_flight_id": "AA123",
                "current_status": "in_flight",
                "current_location": "JFK",
                "weight_kg": 23.5,
                "declared_value": 500.0,
                "checked_in_at": "2024-11-15T10:00:00Z",
                "updated_at": "2024-11-15T12:30:00Z"
            }
        }


class BagScanEvent(BaseModel):
    """Bag scan event model."""

    id: str = Field(..., description="Unique scan event ID")
    bag_id: str = Field(..., description="Bag identifier")

    # Scan details
    scan_type: ScanType = Field(..., description="Type of scan")
    location: str = Field(..., description="Scan location code")
    timestamp: datetime = Field(..., description="Scan timestamp")

    # Scanner information
    scanner_id: Optional[str] = Field(None, description="Scanner device ID")
    handler_id: Optional[str] = Field(None, description="Handler/operator ID")

    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional scan metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "scan_456",
                "bag_id": "bag_123",
                "scan_type": "rfid",
                "location": "JFK-SORTING-A",
                "timestamp": "2024-11-15T11:30:00Z",
                "scanner_id": "RFID-001",
                "metadata": {"signal_strength": 85}
            }
        }


# =====================================================================
# FLIGHT MODELS
# =====================================================================

class Flight(BaseModel):
    """Flight data model."""

    id: str = Field(..., description="Unique flight identifier")
    flight_number: str = Field(..., description="Flight number (e.g., AA123)")

    # Route
    origin_airport: str = Field(..., description="Origin airport code (IATA)")
    destination_airport: str = Field(..., description="Destination airport code (IATA)")

    # Schedule
    scheduled_departure: datetime = Field(..., description="Scheduled departure time")
    scheduled_arrival: datetime = Field(..., description="Scheduled arrival time")
    actual_departure: Optional[datetime] = Field(None, description="Actual departure time")
    actual_arrival: Optional[datetime] = Field(None, description="Actual arrival time")

    # Status
    status: FlightStatus = Field(..., description="Current flight status")

    # Aircraft
    aircraft_type: Optional[str] = Field(None, description="Aircraft type")
    tail_number: Optional[str] = Field(None, description="Aircraft tail number")

    # Gates and terminals
    departure_gate: Optional[str] = Field(None, description="Departure gate")
    arrival_gate: Optional[str] = Field(None, description="Arrival gate")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "flight_789",
                "flight_number": "AA123",
                "origin_airport": "JFK",
                "destination_airport": "LAX",
                "scheduled_departure": "2024-11-15T14:00:00Z",
                "scheduled_arrival": "2024-11-15T18:00:00Z",
                "status": "in_flight",
                "departure_gate": "B22"
            }
        }


# =====================================================================
# PASSENGER MODELS
# =====================================================================

class Passenger(BaseModel):
    """Passenger data model."""

    id: str = Field(..., description="Unique passenger identifier")
    email: str = Field(..., description="Passenger email")

    # Personal information
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")

    # Loyalty
    loyalty_tier: Optional[str] = Field(None, description="Loyalty program tier")
    loyalty_number: Optional[str] = Field(None, description="Loyalty program number")

    # Preferences
    notification_preferences: Dict[str, bool] = Field(
        default_factory=lambda: {"email": True, "sms": False, "push": False},
        description="Notification preferences"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "pass_001",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "loyalty_tier": "gold",
                "notification_preferences": {"email": True, "sms": True}
            }
        }


# =====================================================================
# EVENT MODELS
# =====================================================================

class Event(BaseModel):
    """Generic event model for webhooks."""

    id: str = Field(..., description="Unique event ID")
    event_type: str = Field(..., description="Event type")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(..., description="Event payload")
    source_service: str = Field(..., description="Service that generated the event")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "evt_123",
                "event_type": "bag.scanned",
                "timestamp": "2024-11-15T12:00:00Z",
                "data": {"bag_id": "bag_123", "location": "JFK"},
                "source_service": "bag-tracking"
            }
        }


# =====================================================================
# NOTIFICATION MODELS
# =====================================================================

class Notification(BaseModel):
    """Notification model."""

    id: str = Field(..., description="Unique notification ID")
    recipient_id: str = Field(..., description="Recipient (passenger) ID")

    # Notification details
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")

    # Delivery
    channel: str = Field(..., description="Delivery channel (email, sms, push)")
    sent_at: datetime = Field(..., description="Sent timestamp")
    delivered: bool = Field(default=False, description="Delivery confirmation")

    # Related resources
    bag_id: Optional[str] = Field(None, description="Related bag ID")
    flight_id: Optional[str] = Field(None, description="Related flight ID")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "notif_456",
                "recipient_id": "pass_001",
                "type": "bag_status",
                "title": "Bag Status Update",
                "message": "Your bag has arrived at LAX",
                "channel": "email",
                "sent_at": "2024-11-15T18:05:00Z",
                "delivered": True,
                "bag_id": "bag_123"
            }
        }


# =====================================================================
# API RESPONSE MODELS
# =====================================================================

class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool = Field(..., description="Whether request succeeded")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PaginatedResponse(BaseModel):
    """Paginated API response."""

    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether more items available")
