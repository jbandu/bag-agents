"""
Data Mapper for Copa Airlines Integration

Transforms Copa's data formats to our internal schema and vice versa.
Handles timezone conversions, field name translations, and data normalization.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from zoneinfo import ZoneInfo
import re


class CopaDataMapper:
    """Maps Copa Airlines data to internal schema"""

    # Copa to Internal field mappings
    BAG_FIELD_MAP = {
        "bagTagNumber": "tag_number",
        "passengerPNR": "passenger_id",
        "passengerName": "passenger_name",
        "flightNumber": "flight_id",
        "currentStatus": "status",
        "currentLocation": "current_location",
        "finalDestination": "destination",
        "weightKG": "weight",
        "checkedDateTime": "checked_at",
        "lastScanDateTime": "last_scan_at",
        "priorityCode": "priority",
    }

    FLIGHT_FIELD_MAP = {
        "flightNumber": "flight_number",
        "airlineCode": "airline",
        "departureStation": "departure_airport",
        "arrivalStation": "arrival_airport",
        "scheduledDepartureTime": "scheduled_departure",
        "actualDepartureTime": "actual_departure",
        "scheduledArrivalTime": "scheduled_arrival",
        "actualArrivalTime": "actual_arrival",
        "flightStatus": "status",
        "gateNumber": "gate",
        "aircraftRegistration": "aircraft_reg",
        "totalBags": "bags_checked",
        "loadedBags": "bags_loaded",
    }

    STATUS_MAP = {
        # Copa status codes to internal status
        "CHK": "checked",
        "LOD": "loaded",
        "TRN": "in_transit",
        "XFR": "transferred",
        "DLV": "delivered",
        "DLY": "delayed",
        "LST": "lost",
        "DMG": "damaged",
        "OHD": "checked",  # On Hold
        "SCN": "in_transit",  # Scanned
    }

    FLIGHT_STATUS_MAP = {
        "SCH": "scheduled",
        "BRD": "boarding",
        "DEP": "departed",
        "ARR": "arrived",
        "DLY": "delayed",
        "CXL": "cancelled",
        "DIV": "diverted",
    }

    def __init__(self, copa_timezone: str = "America/Panama"):
        self.copa_tz = ZoneInfo(copa_timezone)
        self.utc_tz = timezone.utc

    def map_bag_data(self, copa_bag: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Copa bag data to internal schema

        Args:
            copa_bag: Bag data from Copa systems

        Returns:
            Mapped bag data in internal format
        """
        mapped = {}

        # Map fields using field map
        for copa_field, internal_field in self.BAG_FIELD_MAP.items():
            if copa_field in copa_bag:
                mapped[internal_field] = copa_bag[copa_field]

        # Transform status code
        if "currentStatus" in copa_bag:
            copa_status = copa_bag["currentStatus"]
            mapped["status"] = self.STATUS_MAP.get(copa_status, copa_status.lower())

        # Convert timestamps to UTC ISO format
        for time_field in ["checked_at", "last_scan_at"]:
            if time_field in mapped and mapped[time_field]:
                mapped[time_field] = self._convert_timestamp(mapped[time_field])

        # Generate unique bag ID if not present
        if "id" not in mapped and "tag_number" in mapped:
            mapped["id"] = f"BAG_{mapped['tag_number']}"

        # Add risk assessment placeholder
        mapped["risk_level"] = self._assess_bag_risk(mapped, copa_bag)

        # Add position data if available
        if "locationX" in copa_bag and "locationY" in copa_bag:
            mapped["position"] = {
                "x": copa_bag["locationX"],
                "y": copa_bag["locationY"],
                "z": copa_bag.get("locationZ", 0)
            }

        return mapped

    def map_flight_data(self, copa_flight: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Copa flight data to internal schema

        Args:
            copa_flight: Flight data from Copa systems

        Returns:
            Mapped flight data in internal format
        """
        mapped = {}

        # Map fields
        for copa_field, internal_field in self.FLIGHT_FIELD_MAP.items():
            if copa_field in copa_flight:
                mapped[internal_field] = copa_flight[copa_field]

        # Transform flight status
        if "flightStatus" in copa_flight:
            copa_status = copa_flight["flightStatus"]
            mapped["status"] = self.FLIGHT_STATUS_MAP.get(copa_status, copa_status.lower())

        # Convert timestamps
        for time_field in ["scheduled_departure", "actual_departure",
                          "scheduled_arrival", "actual_arrival"]:
            if time_field in mapped and mapped[time_field]:
                mapped[time_field] = self._convert_timestamp(mapped[time_field])

        # Generate flight ID
        if "id" not in mapped and "flight_number" in mapped:
            mapped["id"] = f"FLT_{mapped['flight_number']}_{self._get_date_suffix(mapped.get('scheduled_departure'))}"

        # Calculate missing bags
        checked = mapped.get("bags_checked", 0)
        loaded = mapped.get("bags_loaded", 0)
        mapped["bags_missing"] = max(0, checked - loaded)

        # Add at-risk connections count (calculated elsewhere)
        mapped["at_risk_connections"] = copa_flight.get("atRiskConnections", 0)

        return mapped

    def map_bhs_event(self, copa_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Copa BHS event (BSM/BPM/BTM message) to internal format

        Args:
            copa_event: BHS event from Copa systems

        Returns:
            Mapped event data
        """
        # Parse IATA bag message format
        message_type = copa_event.get("messageType", "BSM")

        event = {
            "event_type": self._map_message_type(message_type),
            "bag_tag": copa_event.get("bagTagNumber"),
            "flight_number": copa_event.get("flightNumber"),
            "location": copa_event.get("stationCode"),
            "timestamp": self._convert_timestamp(copa_event.get("timestamp")),
            "equipment_id": copa_event.get("equipmentID"),
            "raw_message": copa_event.get("rawMessage"),
        }

        # Add specific fields based on message type
        if message_type == "BSM":  # Bag Source Message
            event["status"] = "checked"
            event["destination"] = copa_event.get("destination")
            event["weight"] = copa_event.get("weight")
        elif message_type == "BPM":  # Bag Processing Message
            event["status"] = "in_transit"
            event["action"] = copa_event.get("processingAction")
        elif message_type == "BTM":  # Bag Transfer Message
            event["status"] = "transferred"
            event["transfer_point"] = copa_event.get("transferPoint")

        return event

    def map_passenger_data(self, copa_passenger: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Copa passenger data to internal format"""
        return {
            "id": copa_passenger.get("pnr"),
            "pnr": copa_passenger.get("pnr"),
            "first_name": copa_passenger.get("firstName"),
            "last_name": copa_passenger.get("lastName"),
            "email": copa_passenger.get("email"),
            "phone": copa_passenger.get("phone"),
            "frequent_flyer_number": copa_passenger.get("connectMilesNumber"),
            "tier": copa_passenger.get("connectMilesTier"),
            "checked_bags": copa_passenger.get("checkedBags", 0),
        }

    def _convert_timestamp(self, timestamp: Any) -> str:
        """
        Convert Copa timestamp to UTC ISO format

        Handles multiple input formats:
        - ISO strings
        - Unix timestamps
        - Copa custom format
        """
        if not timestamp:
            return None

        try:
            # If already a datetime object
            if isinstance(timestamp, datetime):
                dt = timestamp
            # If ISO string
            elif isinstance(timestamp, str) and 'T' in timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            # If Unix timestamp
            elif isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp, tz=self.utc_tz)
            # Copa custom format: YYYYMMDDHHMM
            elif isinstance(timestamp, str) and len(timestamp) == 12:
                dt = datetime.strptime(timestamp, "%Y%m%d%H%M")
                dt = dt.replace(tzinfo=self.copa_tz)
            else:
                # Try parsing as string
                dt = datetime.fromisoformat(str(timestamp))

            # Convert to UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=self.copa_tz)

            return dt.astimezone(self.utc_tz).isoformat()

        except Exception as e:
            print(f"Error converting timestamp {timestamp}: {e}")
            return None

    def _assess_bag_risk(self, mapped_bag: Dict[str, Any], copa_bag: Dict[str, Any]) -> str:
        """
        Assess bag risk level based on Copa data

        Returns: 'low', 'medium', 'high', or 'critical'
        """
        # Check for explicit priority codes
        priority = copa_bag.get("priorityCode", "")
        if priority in ["RUSH", "VIP"]:
            return "high"

        # Check connection time
        connection_time = copa_bag.get("connectionTimeMinutes", 999)
        if connection_time < 30:
            return "critical"
        elif connection_time < 45:
            return "high"
        elif connection_time < 60:
            return "medium"

        # Check for delayed status
        if mapped_bag.get("status") == "delayed":
            return "high"

        return "low"

    def _map_message_type(self, message_type: str) -> str:
        """Map IATA message type to internal event type"""
        type_map = {
            "BSM": "bag_checked",
            "BPM": "bag_processed",
            "BTM": "bag_transferred",
            "BUM": "bag_loaded",
            "BNS": "bag_not_loaded",
        }
        return type_map.get(message_type, "bag_event")

    def _get_date_suffix(self, timestamp: Optional[str]) -> str:
        """Get date suffix from timestamp for ID generation"""
        if not timestamp:
            return datetime.now(tz=self.utc_tz).strftime("%Y%m%d")

        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%Y%m%d")
        except:
            return datetime.now(tz=self.utc_tz).strftime("%Y%m%d")

    def reverse_map_bag(self, internal_bag: Dict[str, Any]) -> Dict[str, Any]:
        """Map internal bag data back to Copa format (for updates)"""
        copa_bag = {}

        # Reverse field mapping
        reverse_map = {v: k for k, v in self.BAG_FIELD_MAP.items()}
        for internal_field, value in internal_bag.items():
            if internal_field in reverse_map:
                copa_bag[reverse_map[internal_field]] = value

        # Reverse status mapping
        if "status" in internal_bag:
            reverse_status = {v: k for k, v in self.STATUS_MAP.items()}
            copa_bag["currentStatus"] = reverse_status.get(
                internal_bag["status"],
                internal_bag["status"].upper()
            )

        return copa_bag


# Global mapper instance
copa_mapper = CopaDataMapper()


def get_copa_mapper() -> CopaDataMapper:
    """Get Copa data mapper instance"""
    return copa_mapper
