# Copa Airlines Integration

Comprehensive integration adapters for connecting with Copa Airlines existing systems for real-time baggage operations.

## Overview

This integration package provides seamless connectivity with Copa Airlines' core operational systems:

- **DCS (Departure Control System)**: Passenger check-in and bag tracking
- **Flight Operations**: Real-time flight status and schedules
- **BHS (Baggage Handling System)**: RFID scans and baggage events
- **Passenger Service System**: Customer information (future)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           Copa Airlines Integration Service                  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ DCS Adapter  │  │ Flight Ops   │  │ BHS Adapter  │     │
│  │              │  │ Adapter      │  │              │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                       │
│                    │  Data Mapper   │                       │
│                    └───────┬────────┘                       │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │ Bag Agents API   │
                    │   (FastAPI)      │
                    └──────────────────┘
```

## Quick Start

### Installation

The integration adapters are included in the bag-agents repository:

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
```

### Configuration

Set environment variables for Copa systems:

```bash
# Use mock data for demo (default)
export USE_MOCK_COPA_DATA=true

# Or configure real Copa endpoints
export COPA_DCS_URL=https://api.copa.com/dcs/v1
export COPA_DCS_API_KEY=your-api-key
export COPA_FLIGHT_OPS_URL=https://api.copa.com/flights/v1
export COPA_FLIGHT_OPS_API_KEY=your-api-key
export COPA_BHS_URL=https://api.copa.com/bhs/v1
export COPA_BHS_API_KEY=your-api-key
```

### Running the Integration Service

```python
import asyncio
from integrations.integration_service import start_integration_service

async def main():
    # Start the integration service
    service = await start_integration_service()

    # Register event callbacks
    async def handle_bag_checked(event):
        print(f"Bag checked: {event['data']['tag_number']}")

    service.register_callback("bag_checked", handle_bag_checked)

    # Keep running
    await asyncio.Event().wait()

asyncio.run(main())
```

## Integration Adapters

### 1. DCS Adapter

Connects to Copa's Departure Control System for passenger and bag data.

**Features:**
- Fetch flight manifests with passenger and bag lists
- Get checked bags by flight or time period
- Retrieve individual bag details
- Track connecting bags
- Real-time check-in events

**Example Usage:**

```python
from integrations.copa.dcs_adapter import get_dcs_adapter

# Initialize adapter
dcs = await get_dcs_adapter()

# Get flight manifest
manifest = await dcs.get_flight_manifest("CM123", "2024-12-15")
print(f"Flight has {manifest['total_bags']} bags")

# Get bag details
bag = await dcs.get_bag_details("0230556789")
print(f"Bag status: {bag['status']}")

# Get connecting bags
connections = await dcs.get_connecting_bags(
    arrival_flight="CM101",
    departure_flight="CM451",
    connection_airport="PTY"
)
```

### 2. Flight Operations Adapter

Connects to Copa's Flight Operations system for real-time flight data.

**Features:**
- Get active flights (departing in next N hours)
- Get flight status and delays
- Track aircraft rotations
- Monitor gate assignments
- Real-time flight updates

**Example Usage:**

```python
from integrations.copa.flight_ops_adapter import get_flight_ops_adapter

# Initialize adapter
flight_ops = await get_flight_ops_adapter()

# Get active flights at Panama hub
flights = await flight_ops.get_active_flights(airport="PTY", hours_ahead=6)

# Get specific flight status
flight = await flight_ops.get_flight_status("CM123", "2024-12-15")

# Get delayed flights
delayed = await flight_ops.get_delayed_flights(airport="PTY")

# Get connection opportunities
connections = await flight_ops.get_connection_opportunities(
    arrival_flight="CM101",
    airport="PTY",
    min_connection_time=30
)
```

### 3. BHS Adapter

Connects to Copa's Baggage Handling System for scan events and load status.

**Features:**
- Get RFID scan events
- Track bag journey through system
- Monitor load status by flight
- Get equipment status
- Process IATA bag messages (BSM, BPM, BTM)
- Detect mishandled bags

**Example Usage:**

```python
from integrations.copa.bhs_adapter import get_bhs_adapter

# Initialize adapter
bhs = await get_bhs_adapter()

# Get scan events
scans = await bhs.get_scan_events(bag_tag="0230556789", limit=50)

# Get bag journey
journey = await bhs.get_bag_journey("0230556789")
for event in journey:
    print(f"{event['location']}: {event['event_type']}")

# Get load status for flight
load_status = await bhs.get_load_status("CM123", "2024-12-15")
print(f"Loaded: {load_status['loaded_bags']}/{load_status['total_bags']}")

# Get mishandled bags
mishandled = await bhs.get_mishandled_bags(airport="PTY")
```

## Data Mapping

The `CopaDataMapper` handles transformations between Copa's data formats and our internal schema.

**Copa Status Codes:**
- `CHK` → checked
- `LOD` → loaded
- `TRN` → in_transit
- `XFR` → transferred
- `DLV` → delivered
- `DLY` → delayed
- `LST` → lost
- `DMG` → damaged

**Timestamp Conversion:**
- Copa uses `America/Panama` timezone
- All timestamps converted to UTC ISO format
- Handles multiple input formats (ISO, Unix, Copa custom)

## Mock Data Mode

For demos and testing, the system can run in mock data mode.

**Activating Mock Mode:**

```bash
export USE_MOCK_COPA_DATA=true
```

**Mock Data Generation:**

```python
from integrations.mock_copa_data import get_mock_generator

generator = get_mock_generator()

# Generate flights and bags
flights = generator.generate_flights(num_flights=50)
bags = generator.generate_bags(num_bags=1500, flights=flights)

# Get demo scenarios
scenarios = generator.get_demo_scenarios()
```

## December 15th Demo Scenarios

Three pre-configured demo scenarios showcase the system capabilities:

### Scenario 1: Normal International Connection
**Route:** BOG → PTY → JFK
**Purpose:** Show normal bag flow through Copa hub
**Highlights:**
- 2-hour connection time in Panama
- Smooth transfer between flights
- Real-time tracking at each stage

### Scenario 2: At-Risk Connection Saved by AI
**Route:** MIA → PTY → LIM
**Challenge:** Incoming flight delayed, only 30-minute connection
**Solution:** AI predicts risk and triggers priority handling
**Outcome:** Bag makes tight connection
**Highlights:**
- AI risk prediction (87% confidence)
- Automated priority flagging
- Expedited transfer
- Proactive intervention

### Scenario 3: Mishandled Bag Recovery
**Route:** PTY → JFK
**Problem:** Bag missed loading
**Solution:** AI-powered location prediction and recovery
**Highlights:**
- PIR (Property Irregularity Report) auto-generated
- AI root cause analysis
- 94% confident location prediction
- 4-hour resolution (vs industry 24+ hours)

### Running Demo Scenarios

```bash
# Run all demo scenarios
python -m integrations.copa_demo_script
```

Or programmatically:

```python
from integrations.copa_demo_script import CopaDemoRunner

demo = CopaDemoRunner()
await demo.run_all_scenarios()

# Or individual scenarios
await demo.run_scenario_1()  # Normal flow
await demo.run_scenario_2()  # At-risk connection
await demo.run_scenario_3()  # Mishandled bag recovery
```

## Event Handling

The integration service supports event-driven architecture:

**Event Types:**
- `bag_checked`: Bag checked in at DCS
- `bag_scanned`: Bag scanned by BHS
- `flight_status_changed`: Flight status update
- `bag_mishandled`: Bag flagged as mishandled

**Registering Callbacks:**

```python
service = await get_integration_service()

async def handle_at_risk_bag(event):
    bag = event['data']
    if bag.get('risk_level') in ['high', 'critical']:
        # Trigger alert or intervention
        await trigger_intervention(bag)

service.register_callback("bag_checked", handle_at_risk_bag)
```

## Error Handling

All adapters include comprehensive error handling:

**Retry Logic:**
- Configurable retry attempts (default: 3)
- Exponential backoff (5s, 10s, 20s)
- Graceful degradation to mock data

**Health Checks:**

```python
health = await service.health_check()
print(health)
# {
#   "service": "healthy",
#   "mode": "mock",
#   "adapters": {
#     "dcs": true,
#     "flight_ops": true,
#     "bhs": true
#   }
# }
```

## Performance

**Polling Intervals (configurable):**
- DCS: 30 seconds
- Flight Ops: 60 seconds
- BHS: 10 seconds

**Data Limits:**
- Active flights: Last 6 hours
- Bag events: Last 24 hours
- Event retention: 30 days

**Caching:**
- Cache TTL: 5 minutes
- Reduces API calls by ~70%

## Production Deployment

### Prerequisites

1. **Copa API Credentials:**
   - DCS API key
   - Flight Ops API key
   - BHS API key
   - VPN access (if required)

2. **Network Requirements:**
   - Outbound HTTPS to Copa endpoints
   - Webhook endpoint (optional, for real-time events)

### Configuration

Create production configuration:

```python
# config/production.py
copa_config = CopaIntegrationConfig(
    use_mock_data=False,
    dcs_base_url="https://api.copa.com/dcs/v1",
    dcs_api_key=os.getenv("COPA_DCS_API_KEY"),
    flight_ops_base_url="https://api.copa.com/flights/v1",
    flight_ops_api_key=os.getenv("COPA_FLIGHT_OPS_API_KEY"),
    bhs_base_url="https://api.copa.com/bhs/v1",
    bhs_api_key=os.getenv("COPA_BHS_API_KEY"),
    bhs_listen_mode=True,  # Use webhooks
    retry_attempts=5,
    log_level="INFO",
)
```

### Monitoring

**Metrics to Monitor:**
- Integration service uptime
- Adapter health check status
- Event processing rate
- API response times
- Error rates
- Data freshness

**Logging:**

```python
# All adapters use structured logging
logger.info("Bag checked", extra={
    "bag_tag": "0230556789",
    "flight": "CM123",
    "airport": "PTY"
})
```

## Troubleshooting

### Connection Issues

```bash
# Test Copa endpoints
curl -H "X-API-Key: $COPA_DCS_API_KEY" https://api.copa.com/dcs/v1/health
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Fallback to Mock Data

If Copa systems are unavailable:

```python
# Service automatically falls back if health checks fail
# Or force mock mode:
export USE_MOCK_COPA_DATA=true
```

## API Integration with bag-agents

The integration is exposed through the main FastAPI app:

```python
# api/main.py
from integrations.integration_service import get_integration_service

@app.on_event("startup")
async def startup():
    service = await get_integration_service()
    await service.start()

@app.get("/copa/flights")
async def get_copa_flights(airport: str = "PTY"):
    service = await get_integration_service()
    return await service.get_flights(airport=airport)

@app.get("/copa/bags/{bag_tag}")
async def get_copa_bag(bag_tag: str):
    service = await get_integration_service()
    return await service.get_bag_details(bag_tag)

@app.get("/copa/demo-scenarios")
async def get_demo_scenarios():
    service = await get_integration_service()
    return await service.get_demo_scenarios()
```

## Support

For issues or questions about Copa integration:

1. Check adapter health: `await adapter.health_check()`
2. Review logs in `logs/integration.log`
3. Verify Copa API credentials
4. Test with mock data mode first
5. Contact Copa IT support for API issues

## License

MIT License - See LICENSE file in repository root.
