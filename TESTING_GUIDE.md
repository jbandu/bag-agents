# Copa Airlines Baggage Operations AI - Quick Test Guide

## 🚀 System Status

✅ **Application**: https://bag-agents-production.up.railway.app/health
✅ **Database**: Neon PostgreSQL with 13 tables
✅ **Demo Data**: 10 passengers, 8 flights, 8 bags, 13 equipment items
✅ **AI Agents**: 8 agents ready (prediction, root_cause, demand_forecast, customer_service, compensation, infrastructure_health, route_optimization, orchestrator)

---

## 📊 Demo Data Overview

### Passengers (10)
- **Diamond**: Maria Rodriguez (CM123456)
- **Platinum**: Carlos Santos (CM234567), Ana Martinez (CM345678)
- **Gold**: Luis Garcia (CM456789), Sofia Ramirez (CM567890)
- **Silver**: Diego Morales (CM678901), Isabella Fernandez (CM789012)
- **Standard**: Miguel Torres (CM890123), Carmen Lopez (CM901234), Roberto Diaz (CM012345)

### Flights (8)
Copa Airlines routes through PTY hub:
- **CM101**: BOG→PTY (08:00-09:45)
- **CM102**: PTY→JFK (11:00-16:30) - Connection flight
- **CM201**: LIM→PTY (10:00-12:15)
- **CM202**: PTY→MIA (14:00-17:45) - Connection flight
- **CM301**: SCL→PTY (07:00-10:30)
- **CM302**: PTY→LAX (12:00-17:15) - Connection flight
- **CM401**: GUA→PTY (09:00-11:00)
- **CM501**: PTY→MEX (13:00-16:30)

### High-Risk Scenarios
1. **Bag 0230556789**: Diamond passenger, 45-min connection (BOG→PTY→JFK) - HIGH RISK
2. **Equipment SORT-A**: Sorting system at 73% health, 85% utilization - DEGRADED

### Incidents (3)
1. **INC-2024-001**: Mishandled bag (damaged) - Platinum passenger
2. **INC-2024-002**: Delayed bag (missed connection) - Gold passenger
3. **INC-2024-003**: Lost bag - Silver passenger

---

## 🧪 Testing AI Agents

### Test 1: Prediction Agent - Identify At-Risk Bags

```bash
curl -X POST https://bag-agents-production.up.railway.app/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "agent_name": "prediction",
    "input_data": {
      "flight_id": "CM102",
      "connection_time_minutes": 45,
      "equipment_health": 73
    }
  }'
```

**Expected**: Should identify bags at risk of missing CM102 (PTY→JFK) connection

---

### Test 2: Root Cause Analysis - Analyze Incident

```bash
curl -X POST https://bag-agents-production.up.railway.app/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "agent_name": "root_cause",
    "input_data": {
      "incident_id": "INC-2024-002",
      "bag_tag": "0230556790",
      "incident_type": "delayed"
    }
  }'
```

**Expected**: RCA for delayed bag incident with confidence score and recommendations

---

### Test 3: Customer Service - Handle Complaint

```bash
curl -X POST https://bag-agents-production.up.railway.app/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "agent_name": "customer_service",
    "input_data": {
      "pnr": "CM123456",
      "issue": "My bag was damaged during flight CM101",
      "loyalty_tier": "Diamond"
    }
  }'
```

**Expected**: Personalized response for Diamond passenger with priority handling

---

### Test 4: Compensation Agent - Process Claim

```bash
curl -X POST https://bag-agents-production.up.railway.app/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "agent_name": "compensation",
    "input_data": {
      "incident_id": "INC-2024-001",
      "passenger_pnr": "CM234567",
      "claim_amount": 500,
      "incident_type": "damage"
    }
  }'
```

**Expected**: Compensation recommendation based on incident severity and loyalty tier

---

### Test 5: Demand Forecast - Predict Baggage Load

```bash
curl -X POST https://bag-agents-production.up.railway.app/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "agent_name": "demand_forecast",
    "input_data": {
      "hub": "PTY",
      "date": "2024-12-15",
      "flights": ["CM101", "CM102", "CM201", "CM202"]
    }
  }'
```

**Expected**: Baggage volume forecast with capacity recommendations

---

### Test 6: Infrastructure Health - Equipment Check

```bash
curl -X POST https://bag-agents-production.up.railway.app/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "agent_name": "infrastructure_health",
    "input_data": {
      "location": "PTY",
      "equipment_ids": ["SORT-A", "CONV-B1", "SCAN-C1"]
    }
  }'
```

**Expected**: Health status with alerts for SORT-A (73% health)

---

### Test 7: Route Optimization - Bag Routing

```bash
curl -X POST https://bag-agents-production.up.railway.app/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "agent_name": "route_optimization",
    "input_data": {
      "origin": "BOG",
      "destination": "JFK",
      "connection_hub": "PTY",
      "connection_time": 45
    }
  }'
```

**Expected**: Optimized routing with risk assessment for tight connection

---

### Test 8: Orchestrator - Multi-Agent Workflow

```bash
curl -X POST https://bag-agents-production.up.railway.app/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "agent_name": "orchestrator",
    "input_data": {
      "task": "handle_delayed_bag",
      "bag_tag": "0230556789",
      "pnr": "CM123456"
    }
  }'
```

**Expected**: Coordinates prediction, customer service, and compensation agents

---

## 🔑 API Key Setup

Currently, the API uses header-based authentication. You need to add an API key:

### Option 1: Development Mode (No Auth)
Add to Railway environment variables:
```
ENVIRONMENT=development
```

### Option 2: Production Mode (With API Key)
Add to Railway environment variables:
```
API_KEYS=copa-demo-key-2024,copa-prod-key-2024
```

Then use in requests:
```bash
-H "X-API-Key: copa-demo-key-2024"
```

---

## 📈 Monitoring Endpoints

### Health Check
```bash
curl https://bag-agents-production.up.railway.app/health
```

### List All Agents
```bash
curl https://bag-agents-production.up.railway.app/api/v1/agents
```

### Agent Status
```bash
curl https://bag-agents-production.up.railway.app/api/v1/agents/{agent_name}/status
```

### Prometheus Metrics
```
http://bag-agents-production.up.railway.app:9090/metrics
```

---

## 🎯 Demo Scenarios for Copa Meeting (Dec 15)

### Scenario 1: Connection Risk Management
**Story**: Diamond passenger Maria Rodriguez (CM123456) has a tight 45-minute connection at PTY.

**Test Flow**:
1. Prediction Agent identifies high-risk bag
2. Infrastructure Agent checks equipment capacity
3. Route Optimization suggests alternative path if needed
4. Customer Service sends proactive notification

### Scenario 2: Incident Resolution
**Story**: Platinum passenger Carlos Santos (CM234567) reports damaged bag on CM101.

**Test Flow**:
1. Root Cause Analysis investigates the damage
2. Customer Service provides immediate response
3. Compensation Agent calculates fair compensation
4. Orchestrator coordinates end-to-end resolution

### Scenario 3: Hub Operations Optimization
**Story**: PTY hub handling peak morning arrivals with degraded SORT-A equipment.

**Test Flow**:
1. Demand Forecast predicts baggage volume
2. Infrastructure Health flags SORT-A degradation
3. Route Optimization redistributes load
4. Orchestrator coordinates resource allocation

---

## 🛠️ Troubleshooting

### If agents return 401 Unauthorized
Add `ENVIRONMENT=development` to Railway variables (temporary)

### If agents return 500 errors
Check Railway logs for detailed error messages

### If database queries fail
Verify DATABASE_URL is set correctly in Railway

---

## 📚 Next Steps

1. **Add API key** to Railway environment variables
2. **Test each agent** with the curl commands above
3. **Review responses** and adjust prompts if needed
4. **Prepare demo scenarios** for Copa presentation
5. **Monitor performance** via Prometheus metrics

---

## 🎉 Summary

- ✅ 8 AI agents deployed and ready
- ✅ PostgreSQL database with realistic Copa data
- ✅ RESTful API with health checks
- ✅ Railway hosting with auto-scaling
- ✅ Complete demo scenarios for Copa meeting

**Live URL**: https://bag-agents-production.up.railway.app
