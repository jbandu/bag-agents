# Copa Airlines AI Agents - Quick Test Reference

## 🎯 System Ready!

✅ **API URL**: https://bag-agents-production.up.railway.app
✅ **Database**: PostgreSQL with Copa demo data
✅ **Authentication**: Development mode (no API key required)
✅ **All 8 Agents**: Ready and operational

---

## 🧪 Quick Test Commands

### 1. Prediction Agent - Risk Assessment
```bash
curl -X POST https://bag-agents-production.up.railway.app/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "prediction",
    "input_data": {
      "flight_id": "CM102",
      "departure_airport": "PTY",
      "arrival_airport": "JFK",
      "connection_time": 45
    }
  }'
```

**Expected**: Returns risk score, contributing factors, and recommendations for PTY→JFK connection.

---

### 2. Root Cause Analysis - Investigate Incident
```bash
curl -X POST https://bag-agents-production.up.railway.app/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "root_cause",
    "input_data": {
      "incident_id": "INC-2024-002",
      "bag_tag": "0230556790",
      "incident_type": "delayed"
    }
  }'
```

**Expected**: Returns root cause analysis with confidence score and corrective actions.

---

### 3. Customer Service - Handle Inquiry
```bash
curl -X POST https://bag-agents-production.up.railway.app/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "customer_service",
    "input_data": {
      "pnr": "CM123456",
      "issue": "My bag was damaged during flight CM101",
      "loyalty_tier": "Diamond"
    }
  }'
```

**Expected**: Returns personalized response for Diamond passenger with priority handling.

---

### 4. Compensation Agent - Process Claim
```bash
curl -X POST https://bag-agents-production.up.railway.app/agents/invoke \
  -H "Content-Type: application/json" \
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

**Expected**: Returns compensation recommendation based on incident and loyalty tier.

---

### 5. Demand Forecast - Predict Load
```bash
curl -X POST https://bag-agents-production.up.railway.app/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "demand_forecast",
    "input_data": {
      "hub": "PTY",
      "date": "2024-12-15",
      "flights": ["CM101", "CM102", "CM201", "CM202"]
    }
  }'
```

**Expected**: Returns baggage volume forecast with capacity recommendations.

---

### 6. Infrastructure Health - Equipment Check
```bash
curl -X POST https://bag-agents-production.up.railway.app/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "infrastructure_health",
    "input_data": {
      "location": "PTY",
      "equipment_ids": ["SORT-A", "CONV-B1", "SCAN-C1"]
    }
  }'
```

**Expected**: Returns health status with alerts for SORT-A (73% health).

---

### 7. Route Optimization - Bag Routing
```bash
curl -X POST https://bag-agents-production.up.railway.app/agents/invoke \
  -H "Content-Type: application/json" \
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

**Expected**: Returns optimized routing with risk assessment for tight connection.

---

### 8. Orchestrator - Multi-Agent Workflow
```bash
curl -X POST https://bag-agents-production.up.railway.app/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "orchestrator",
    "input_data": {
      "task": "handle_delayed_bag",
      "bag_tag": "0230556789",
      "pnr": "CM123456"
    }
  }'
```

**Expected**: Coordinates multiple agents to handle delayed bag scenario.

---

## 📊 System Monitoring

### Health Check
```bash
curl https://bag-agents-production.up.railway.app/health
```

### List All Agents
```bash
curl https://bag-agents-production.up.railway.app/agents
```

### API Information
```bash
curl https://bag-agents-production.up.railway.app/
```

---

## 📈 Demo Scenarios for Copa Meeting (Dec 15)

### Scenario 1: High-Risk Connection
**Diamond passenger Maria Rodriguez (CM123456) with 45-min connection at PTY**

1. Test prediction agent (shows HIGH RISK)
2. Test infrastructure agent (checks PTY equipment)
3. Test customer service (sends proactive alert)

### Scenario 2: Incident Resolution
**Platinum passenger Carlos Santos (CM234567) reports damaged bag**

1. Test root cause agent (analyzes damage)
2. Test customer service (immediate response)
3. Test compensation agent (calculates payout)

### Scenario 3: Hub Operations
**PTY hub morning peak with degraded SORT-A equipment**

1. Test demand forecast (predicts volume)
2. Test infrastructure health (flags equipment issue)
3. Test route optimization (redistributes load)

---

## 🎉 Success!

Your Copa Airlines Baggage Operations AI system is fully operational:

- ✅ 8 AI agents deployed and responding
- ✅ PostgreSQL database with realistic Copa data
- ✅ RESTful API with comprehensive endpoints
- ✅ Railway hosting with auto-scaling
- ✅ Ready for Copa Airlines demo on December 15th

**Next Steps**:
1. Test each agent with the commands above
2. Verify responses match your requirements
3. Prepare demo scenarios for Copa presentation
4. (Optional) Add API key authentication for production

For detailed documentation, see `TESTING_GUIDE.md` in the repository.
