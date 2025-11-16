# Copa Airlines Demo System - LLM Context Documentation

## System Overview

This is a comprehensive AI-powered baggage handling demonstration system for Copa Airlines, designed for a December 15, 2025 presentation. The system demonstrates all 8 baggage handling agents working together through a LangGraph orchestrator.

## Data Architecture

### 1. Flight Data Structure (`Copa_flights_demo.json`)

**Purpose:** Realistic Copa Airlines flight schedule for demo day

**Key Fields:**
- `flight_number`: Copa format (CM###)
- `aircraft_type`: 737-800, 737-MAX9, 737-700, E190
- `origin/destination`: IATA airport codes
- `scheduled_departure/arrival`: ISO 8601 timestamps (Panama timezone UTC-5)
- `gate`: Terminal 1 gates (A1-A30)
- `pax_count`: Passenger count based on load factor (75-92%)
- `expected_bags`: Calculated as ~1.1 bags per passenger
- `connection_bags`: Bags connecting through PTY hub
- `wave`: Operational wave (morning, midday, afternoon_peak)

**Operational Waves:**
1. Morning (06:00-09:00): Overnight USA arrivals, South America departures
2. Midday (11:00-14:00): South America arrivals, USA/Caribbean departures
3. Afternoon Peak (14:00-18:00): Main demo period, heavy connection traffic

**Generation Logic:**
- Routes based on Copa's actual network (hub: PTY Panama)
- Wave-based scheduling (flights clustered in operational peaks)
- Realistic load factors and bag counts
- Status distribution: 85% on-time, 10% delayed, 5% boarding

### 2. Baggage Data Structure (`Copa_bags_demo.json`)

**Purpose:** 2,000 realistic bags with full passenger details and journey information

**Key Fields:**
```json
{
  "bag_id": "0230######",  // Copa IATA code 230
  "passenger": {
    "name": "First Last",  // Latin American (2 surnames) or North American
    "booking_ref": "ABC123",  // 6-char PNR
    "contact": "+country-area-number",
    "email": "user@domain.com",
    "frequent_flyer": "CM#########",  // PreferMember number
    "tier": "Gold|Platinum|etc"  // or null
  },
  "journey": {
    "type": "local|connection",
    "origin": "AIRPORT",
    "destination": "AIRPORT",
    "inbound_flight": "CM###",  // For connections
    "outbound_flight": "CM###",
    "connection_time_min": 30-240,  // Calculated time between flights
    "connection_category": "normal|tight|very_tight",
    "mct_min": 45  // Minimum Connection Time at PTY
  },
  "characteristics": {
    "weight_kg": 15-32,  // Average 23kg
    "type": "standard|oversized|fragile",
    "special_handling": null|"priority"|"fragile",
    "declared_value_usd": 0-15000
  },
  "risk_factors": {
    "tight_connection": boolean,  // If connection < MCT + buffer
    "first_bag": boolean,  // First checked bag
    "vip_passenger": boolean,  // Platinum/Presidential tier
    "high_value": boolean,  // >$2000 declared value
    "international": boolean
  }
}
```

**Distribution:**
- 60% connections (1,200 bags): Copa hub model
- 40% local (800 bags): PTY origin or destination
- Connection types: 80% normal, 15% tight, 5% very tight
- VIP passengers: ~10% (higher in connections)
- High-value bags: ~3%

**Connection Categorization:**
```python
def categorize_connection(connection_time: int) -> str:
    if connection_time >= MCT + 30:  # >= 75 min
        return "normal"  # Comfortable connection
    elif connection_time >= MCT:  # 45-74 min
        return "tight"  # Risky, may need intervention
    else:  # < 45 min
        return "very_tight"  # Will likely miss connection
```

**Generation Process:**
1. Load 60 flights from flight schedule
2. Generate 800 local bags from random flights
3. Find all arriving flights (destination=PTY)
4. For each arriving flight, find possible connecting flights
5. Pre-compute all connections and categorize (normal/tight/very_tight)
6. Generate 960 normal, 180 tight, 60 very tight connections
7. Assign realistic passenger demographics based on route
8. Calculate risk factors

**Bug Fix Applied (lines 248-295):**
The current_status and current_location are now determined BEFORE the bag dictionary creation to avoid UnboundLocalError. This ensures status is properly set based on inbound flight status.

### 3. Demo Scenarios Structure (`Copa_demo_scenarios.json`)

**Purpose:** 5 hand-crafted bags demonstrating specific AI capabilities

**Scenarios:**

1. **TAG-DEMO-001: Happy Path**
   - Normal operations demonstration
   - 120-min connection (comfortable)
   - Low risk score (15)
   - Shows standard flow without intervention

2. **TAG-DEMO-002: AI Prevention** ⭐ MAIN DEMO
   - Tight connection created by delay
   - Original: 50 min, Delayed: 35 min (< MCT 45)
   - Risk score: 87 (CRITICAL)
   - AI detects, recommends expedite, connection succeeds
   - ROI calculation: $395 saved / $5 cost = 79x

3. **TAG-DEMO-003: Mishandling Recovery**
   - 45-min delay causes missed connection
   - Complete lifecycle:
     - Root Cause: "insufficient_transfer_time" due to "flight_irregularity"
     - PIR: PTY20251215001 auto-generated
     - Notification: SMS + Email within 5 min
     - Compensation: $100 (Montreal Convention)
     - Rebooking: Next flight CM123
     - Delivery: Same day 21:00

4. **TAG-DEMO-004: Equipment Failure**
   - Conveyor CONV-5 motor failure
   - 23 bags affected (including TAG-DEMO-004)
   - Infrastructure Health detects in <1 sec
   - Route Optimization reroutes: 12 → CONV-6, 11 → manual cart
   - Demand Forecast dispatches +3 handlers
   - Work order WO-PTY-20251215-003 created
   - Zero missed connections

5. **TAG-DEMO-5-xxx: Scale Demo**
   - 200 bags processed simultaneously
   - Afternoon peak (14:00-18:00)
   - Performance metrics:
     - Throughput: 6.2 bags/sec
     - Prediction avg: 145ms
     - Route optimization avg: 89ms
     - Success rate: 100%

## LLM Integration Points

### Agent Context Requirements

When processing bags, agents need this context:

**Prediction Agent:**
```python
{
  "flight_id": "CM###",
  "departure_airport": "XXX",
  "arrival_airport": "YYY",
  "connection_time": minutes,  # For connections
  "historical_performance": {},  # Optional
  "weather_conditions": {}  # Optional
}
```

**Route Optimization Agent:**
```python
{
  "origin": "PTY-T1",
  "destination": "GATE-A##",
  "via": ["SORT-1", "CONV-X"],  # Optional routing
  "priority": boolean,  # For expedited transfers
  "equipment_status": {}  # From Infrastructure Health
}
```

**Root Cause Agent:**
```python
{
  "incident_id": "INC-###",
  "incident_type": "delayed|lost|damaged",
  "bag_journey": [],  # Event history
  "flight_data": {},
  "equipment_logs": {}  # From Infrastructure Health
}
```

**Customer Service Agent:**
```python
{
  "customer_query": "Baggage delayed|lost|...",
  "bag_tag": "0230######",
  "passenger_info": {},
  "incident_details": {}
}
```

**Compensation Agent:**
```python
{
  "claim_id": "CLM-###",
  "incident_type": "delayed|lost|damaged",
  "delay_hours": number,
  "declared_value": USD,
  "customer_tier": "Gold|Platinum|..."
}
```

## State Machine Flow

```
check_in → security_screening → sorting → loading → in_flight
                                    ↓
                                mishandled → root_cause_analysis → compensation
                                                                         ↓
                            ← ← ← ← ← ← request_approval ← ← ← ← ← ← ← ←

For connections:
in_flight → transfer → sorting (for connecting flight) → loading → in_flight → arrival → claim → delivered
```

## Key Business Rules

### MCT (Minimum Connection Time)
- PTY hub: **45 minutes**
- Includes: deplaning, transfer, security (international), boarding
- Tight connections (<MCT) trigger high-risk alerts

### Connection Risk Scoring
```python
risk_score = base_risk
if connection_time < MCT:
    risk_score += 50
if connection_time < MCT - 10:
    risk_score += 30
if inbound_delayed:
    risk_score += delay_minutes
if vip_passenger:
    risk_score += 10  # Higher priority
if high_value:
    risk_score += 10
```

### Compensation Rules (Montreal Convention)
- Delayed >24 hours: $100 interim expenses
- Lost bag: Up to $1,500 or declared value
- Damaged: Up to 50% of declared value or actual damage
- Requires approval if >$50

### Copa PreferMember Tiers
- **Silver:** 25,000 miles
- **Gold:** 50,000 miles
- **Platinum:** 75,000 miles
- **Presidential Platinum:** 100,000+ miles
- Distribution: ~68% no status, 32% with status (higher in connections)

## Data Quality Standards

### Validation Rules

**Flight Numbers:**
- Format: CM### (CM100-CM999)
- Must be unique per day

**Bag Tags:**
- Format: 0230###### (10 digits)
- IATA code 230 (Copa Airlines)
- Must be unique globally

**Times:**
- All in Panama timezone (UTC-5)
- ISO 8601 format: "2025-12-15T14:30:00-05:00"
- No unrealistic times (all 06:00-23:00)

**Connection Times:**
- Must be >= 15 minutes (absolute minimum)
- MCT = 45 minutes
- Comfortable = 75+ minutes
- Calculated as: (outbound_departure - inbound_arrival)

**Passenger Data:**
- Names: Latin American (2 surnames) or North American (1 surname)
- Phones: +country-area-number format
- Emails: Valid format, common domains
- PNRs: 6 alphanumeric characters (no O, I, 0, 1)

**Weights:**
- Range: 15-32 kg
- Average: 23 kg
- Standard deviation: ~4 kg

## Demo Presentation Flow

### T+0:00 - Introduction (30s)
- Show dashboard with all systems operational
- Display 60 flights, 2,000 bags active
- Highlight afternoon peak wave (25 flights)

### T+0:30 - Scenario 1: Happy Path (60s)
- TAG-DEMO-001: JFK → PTY → GRU
- Show smooth progression through states
- Prediction Agent: Risk 15 (LOW)
- All checkpoints green
- Delivered on time

### T+1:30 - Scenario 2: AI Prevention (120s) ⭐ MAIN DEMO
- TAG-DEMO-002: LAX → PTY → MEX
- T+1:00: Inbound CM490 delayed 15 min
- T+1:15: Connection time drops from 50 to 35 min
- T+1:20: Prediction Agent flags CRITICAL (risk 87)
- T+1:25: Orchestrator recommends "EXPEDITE TRANSFER"
- T+1:30: Handler receives mobile alert
- T+1:45: Bag priority routed via CONV-2
- T+2:00: Bag transferred in 8 minutes (vs normal 15)
- T+2:25: Loaded on CM685
- T+2:30: Flight departs with bag onboard
- **Show ROI: $395 saved / $5 cost = 79x**

### T+3:30 - Scenario 3: Mishandling (120s)
- TAG-DEMO-003: MIA → PTY → BOG
- 45 min delay → missed connection
- T+3:35: System detects mishandling
- T+4:00: Root Cause analyzes
- T+4:30: PIR PTY20251215001 generated
- T+4:35: Passenger notified (SMS + Email)
- T+5:00: Compensation calculated ($100)
- T+5:15: Supervisor approves
- T+5:30: Rebooked on CM123 (18:30)
- T+6:00: Bag loaded
- **Delivered same day with compensation**

### T+5:30 - Scenario 4: Equipment Failure (90s)
- TAG-DEMO-004: BOG → PTY → MIA
- T+5:30: CONV-5 motor fails
- T+5:31: Infrastructure Health detects
- T+5:32: 23 bags affected
- T+5:35: Route Optimization recalculates
- T+5:36: 12 bags → CONV-6, 11 → manual cart
- T+5:40: Demand Forecast: +3 handlers needed
- T+6:00: All 23 bags rerouted
- T+6:30: Work order created
- **Zero missed connections**

### T+7:00 - Scenario 5: Scale (120s)
- 200 bags active (TAG-DEMO-5-001 to 5-200)
- Real-time dashboard showing:
  - 6.2 bags/sec throughput
  - 12 at-risk connections detected
  - All 12 interventions successful
  - 100% success rate
- 3D visualization of PTY hub
- Live agent activity monitoring

### T+9:00 - ROI & Impact (60s)
- Per intervention: 79x ROI
- Daily savings: $4,740 (12 interventions × $395)
- Annual savings: $2.1M
- Mishandling rate: <0.15% (vs industry 0.5%)
- Customer satisfaction improvement

## Implementation Notes

### File Sizes
- Copa_flights_demo.json: 37 KB (1,292 lines)
- Copa_bags_demo.json: 2.3 MB (80,421 lines)
- Copa_demo_scenarios.json: 17 KB (467 lines)

### Performance Characteristics
- Flight generation: ~1 second for 60 flights
- Bag generation: ~10 seconds for 2,000 bags
- Scenario loading: Instant
- Total data load time: <15 seconds

### Dependencies
- Python 3.11+
- Standard library only (json, random, datetime)
- No external dependencies for generation
- LangGraph + agents for orchestration

### Extensibility
- Easy to generate more flights (change count in script)
- Easy to adjust connection distribution (modify percentages)
- Easy to add new scenarios (JSON structure)
- Data can be regenerated with different seeds for variety

## Troubleshooting

### Common Issues

**Issue:** Not enough tight/very tight connections
**Solution:** Flight schedule may not have enough close departures. Regenerate flights or adjust MCT threshold.

**Issue:** Bag weights unrealistic
**Solution:** Check weight_kg range in generate_bags.py (should be 15-32 kg)

**Issue:** Connection times negative
**Solution:** Verify flight schedule has logical arrival/departure times

**Issue:** Passenger names not diverse
**Solution:** Expand FIRST_NAMES and LAST_NAMES dictionaries in generate_bags.py

### Data Validation

Run these checks before demo:
```python
# 1. All bags have valid connections
for bag in bags:
    if bag['journey']['type'] == 'connection':
        assert bag['journey']['connection_time_min'] >= 15

# 2. All flight numbers are Copa format
for flight in flights:
    assert flight['flight_number'].startswith('CM')

# 3. All bag tags are Copa format
for bag in bags:
    assert bag['tag_number'].startswith('0230')

# 4. Connection distribution is correct
connection_bags = [b for b in bags if b['journey']['type'] == 'connection']
normal = [b for b in connection_bags if b['journey']['connection_category'] == 'normal']
tight = [b for b in connection_bags if b['journey']['connection_category'] == 'tight']
very_tight = [b for b in connection_bags if b['journey']['connection_category'] == 'very_tight']

assert len(normal) / len(connection_bags) ≈ 0.80
assert len(tight) / len(connection_bags) ≈ 0.15
assert len(very_tight) / len(connection_bags) ≈ 0.05
```

## Security & Privacy

### Data Sanitization
- All passenger names are fictional
- All phone numbers are fictional (valid format but not real)
- All email addresses are fictional
- All PNRs are randomly generated
- No real Copa Airlines data used

### Demo Mode
- Data is clearly marked as demo/test
- Not connected to real Copa systems
- Isolated environment
- Can be reset at any time

## Summary

This demo system provides:
1. **Realistic flight operations** - 60 Copa flights across 3 waves
2. **Comprehensive bag data** - 2,000 bags with full passenger details
3. **Targeted scenarios** - 5 demonstrations of AI capabilities
4. **Business impact** - Clear ROI and value proposition
5. **Production-ready** - All validation, error handling, documentation

Perfect for demonstrating Copa Airlines' AI-powered baggage handling system on December 15, 2025.
