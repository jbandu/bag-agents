"""
Copa Airlines Integration Configuration
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
import os


class CopaIntegrationConfig(BaseModel):
    """Configuration for Copa Airlines integrations"""

    # DCS Configuration
    dcs_enabled: bool = Field(default=True, description="Enable DCS integration")
    dcs_base_url: str = Field(
        default=os.getenv("COPA_DCS_URL", "https://api.copa.com/dcs/v1"),
        description="Copa DCS API base URL"
    )
    dcs_api_key: str = Field(
        default=os.getenv("COPA_DCS_API_KEY", ""),
        description="Copa DCS API key"
    )
    dcs_poll_interval: int = Field(default=30, description="DCS polling interval in seconds")

    # Flight Operations Configuration
    flight_ops_enabled: bool = Field(default=True, description="Enable Flight Ops integration")
    flight_ops_base_url: str = Field(
        default=os.getenv("COPA_FLIGHT_OPS_URL", "https://api.copa.com/flights/v1"),
        description="Copa Flight Ops API base URL"
    )
    flight_ops_api_key: str = Field(
        default=os.getenv("COPA_FLIGHT_OPS_API_KEY", ""),
        description="Copa Flight Ops API key"
    )
    flight_ops_poll_interval: int = Field(default=60, description="Flight ops polling interval in seconds")

    # BHS Configuration
    bhs_enabled: bool = Field(default=True, description="Enable BHS integration")
    bhs_base_url: str = Field(
        default=os.getenv("COPA_BHS_URL", "https://api.copa.com/bhs/v1"),
        description="Copa BHS API base URL"
    )
    bhs_api_key: str = Field(
        default=os.getenv("COPA_BHS_API_KEY", ""),
        description="Copa BHS API key"
    )
    bhs_poll_interval: int = Field(default=10, description="BHS polling interval in seconds")
    bhs_listen_mode: bool = Field(default=False, description="Use webhook mode for BHS events")
    bhs_webhook_url: str = Field(default="", description="Webhook URL for BHS events")

    # Passenger Service Configuration
    pss_enabled: bool = Field(default=False, description="Enable PSS integration")
    pss_base_url: str = Field(
        default=os.getenv("COPA_PSS_URL", "https://api.copa.com/pss/v1"),
        description="Copa PSS API base URL"
    )
    pss_api_key: str = Field(
        default=os.getenv("COPA_PSS_API_KEY", ""),
        description="Copa PSS API key"
    )

    # Mock Data Configuration (for demo)
    use_mock_data: bool = Field(
        default=os.getenv("USE_MOCK_COPA_DATA", "true").lower() == "true",
        description="Use mock data when Copa systems unavailable"
    )
    mock_flights_per_day: int = Field(default=50, description="Number of mock flights per day")
    mock_bags_per_day: int = Field(default=1500, description="Number of mock bags per day")
    mock_mishandling_rate: float = Field(default=0.003, description="Mock mishandling rate (0.3%)")

    # Copa Specific Settings
    copa_hub_airport: str = Field(default="PTY", description="Copa hub airport code (Panama)")
    copa_airline_code: str = Field(default="CM", description="Copa airline IATA code")
    copa_timezone: str = Field(default="America/Panama", description="Copa operations timezone")

    # Integration Service Settings
    retry_attempts: int = Field(default=3, description="Number of retry attempts on failure")
    retry_delay: int = Field(default=5, description="Delay between retries in seconds")
    log_level: str = Field(default="INFO", description="Logging level")

    # Data Retention
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    event_retention_days: int = Field(default=30, description="Event retention in days")

    class Config:
        env_prefix = "COPA_"


# Global configuration instance
copa_config = CopaIntegrationConfig()


def get_copa_config() -> CopaIntegrationConfig:
    """Get Copa integration configuration"""
    return copa_config


def update_copa_config(updates: Dict[str, Any]) -> CopaIntegrationConfig:
    """Update Copa configuration dynamically"""
    global copa_config
    for key, value in updates.items():
        if hasattr(copa_config, key):
            setattr(copa_config, key, value)
    return copa_config
