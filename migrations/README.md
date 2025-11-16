# Database Migrations

This directory contains SQL migration scripts for the Copa Airlines Baggage Operations AI Agent System.

## Quick Start

### 1. Run Schema Migration (Required)

Creates all necessary tables, indexes, and constraints:

```bash
psql 'postgresql://neondb_owner:npg_UyzqOD5geV3Y@ep-plain-lake-adl8g160-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require' -f migrations/001_create_schema.sql
```

### 2. Load Demo Data (Optional but Recommended)

Seeds the database with sample Copa Airlines data for testing and demos:

```bash
psql 'postgresql://neondb_owner:npg_UyzqOD5geV3Y@ep-plain-lake-adl8g160-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require' -f migrations/002_seed_demo_data.sql
```

## Migration Files

### 001_create_schema.sql
Creates the complete database schema with:
- **Core Tables**: passengers, flights, bags, bag_events
- **Incident Management**: incidents, root_cause_analysis
- **Compensation**: compensation_claims
- **Customer Service**: customer_service_interactions
- **Infrastructure**: equipment, equipment_metrics, work_orders
- **Analytics**: demand_forecasts, agent_executions
- **Triggers**: Automatic updated_at timestamp updates
- **Indexes**: Optimized for agent query patterns

### 002_seed_demo_data.sql
Populates database with realistic demo data:
- 10 passengers (mix of loyalty tiers: Diamond, Platinum, Gold, Silver, Standard)
- 8 flights (BOG→PTY→JFK connection scenarios)
- 8 bags (including at-risk, delayed, and VIP bags)
- Bag events showing complete journey tracking
- 13 equipment items (carousels, sorting systems, scanners, conveyors, tugs, carts)
- Equipment metrics for monitoring
- 3 incidents (delayed, damaged, lost bags with PIRs)
- 3 compensation claims (different approval statuses)
- Customer service interactions (web chat, email, WhatsApp)
- Work orders (preventive and corrective maintenance)

## Database Schema Overview

### Tables Created

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `passengers` | Customer information | pnr, loyalty_tier, contact info |
| `flights` | Flight schedules | flight_number, departure/arrival airports, status |
| `bags` | Baggage tracking | tag_number, status, risk_level, current_location |
| `bag_events` | Journey tracking | event_type, location, timestamp, equipment_id |
| `incidents` | Mishandled bags & PIRs | pir_number, incident_type, root_cause, status |
| `root_cause_analysis` | RCA results | cause, confidence, evidence, recommendations |
| `compensation_claims` | Claims processing | claim_number, approval_status, fraud_risk_score |
| `customer_service_interactions` | CS conversations | channel, intent, sentiment, escalated |
| `equipment` | Infrastructure | equipment_id, type, health_score, utilization |
| `equipment_metrics` | Time-series monitoring | throughput, error_rate, temperature, vibration |
| `work_orders` | Maintenance tasks | maintenance_type, priority, status |
| `demand_forecasts` | Predictive analytics | airport_code, predicted_bags, confidence |
| `agent_executions` | Audit log | agent_name, execution_time, status |

## Verification

After running migrations, verify the setup:

```bash
# Connect to database
psql 'postgresql://neondb_owner:npg_UyzqOD5geV3Y@ep-plain-lake-adl8g160-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

# Check tables
\dt

# Check sample data
SELECT COUNT(*) FROM passengers;
SELECT COUNT(*) FROM bags;
SELECT COUNT(*) FROM equipment;

# View at-risk bag
SELECT b.tag_number, b.status, b.risk_level, b.current_location, b.destination
FROM bags b
WHERE b.risk_level = 'high' OR b.risk_level = 'critical';

# View equipment health
SELECT equipment_id, equipment_type, status, health_score, utilization
FROM equipment
WHERE health_score < 80
ORDER BY health_score ASC;
```

## Demo Scenarios in Seed Data

### Scenario 1: At-Risk Connection (BOG→PTY→JFK)
- **Passenger**: Juan Martinez (Diamond tier)
- **Bag**: 0230556789
- **Status**: In transit with 45-minute connection time (tight!)
- **Risk Level**: HIGH
- **Flight**: CM123 (arrived) → CM456 (boarding)

### Scenario 2: Delayed Bag Recovery
- **Passenger**: Sofia Fernandez (Standard)
- **Bag**: 0230556794
- **Status**: Delayed at SORT_HUB_B
- **Risk Level**: CRITICAL
- **Incident**: PIR-PTY-20241116-0001 opened
- **Claim**: Auto-approved for $150 interim expenses

### Scenario 3: Equipment Degradation
- **Equipment**: SORT-A (sorting system)
- **Status**: DEGRADED
- **Health Score**: 73/100
- **Utilization**: 85% (high)
- **Work Order**: WO-20241116-1001 (preventive maintenance scheduled)

## Agent Testing

With this data, you can test all agents:

```python
# Root Cause Agent
await root_cause_agent.execute({
    "incident_id": "d0000001-0000-0000-0000-000000000001",
    "bag_id": "c0000001-0000-0000-0000-000000000006"
})

# Customer Service Agent
await customer_service_agent.execute({
    "customer_query": "Where is my bag 0230556789?",
    "bag_tag": "0230556789",
    "language": "en",
    "channel": "web_chat"
})

# Compensation Agent
await compensation_agent.execute({
    "incident_id": "d0000001-0000-0000-0000-000000000001",
    "bag_tag": "0230556794",
    "passenger_id": "a0000001-0000-0000-0000-000000000006",
    "incident_type": "delayed"
})

# Demand Forecast Agent
await demand_forecast_agent.execute({
    "airport_code": "PTY",
    "forecast_horizon_hours": 24,
    "forecast_type": "hourly"
})

# Infrastructure Health Agent
await infrastructure_health_agent.execute({
    "airport_code": "PTY",
    "include_predictions": True
})

# Route Optimization Agent
await route_optimization_agent.execute({
    "origin": "CHECK_IN_1",
    "destination": "GATE_B2",
    "airport_code": "PTY",
    "priority": "rush"
})
```

## Troubleshooting

### Connection Issues
If you get SSL/connection errors:
```bash
# Try with SSL mode disabled (not recommended for production)
psql 'postgresql://...?sslmode=disable'
```

### Table Already Exists
If tables already exist, you can:
```sql
-- Drop all tables (CAUTION: destroys all data!)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- Then re-run migrations
```

### Check Migration Status
```sql
-- See all tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE';

-- Check row counts
SELECT
    schemaname,
    tablename,
    (SELECT COUNT(*) FROM pg_class WHERE oid = tablename::regclass) as row_count
FROM pg_tables
WHERE schemaname = 'public';
```

## Notes

- All timestamps are stored in UTC (TIMESTAMP WITH TIME ZONE)
- UUIDs are used for primary keys to support distributed systems
- Indexes are optimized for agent query patterns
- Triggers automatically update `updated_at` timestamps
- Foreign keys use CASCADE for proper cleanup
- Sample data includes realistic Copa Airlines routes and scenarios

## Support

For issues or questions:
1. Check agent logs for database connection errors
2. Verify Neon database is accessible
3. Ensure migrations ran without errors
4. Check data integrity with verification queries above
