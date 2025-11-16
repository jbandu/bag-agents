# Quick Start Guide

Get the Copa Airlines Baggage Operations AI Agent System up and running in 5 minutes.

## 📋 What You Need

- ✅ Neon PostgreSQL database (you have this)
- 🔑 Anthropic API key for Claude
- 🚂 Railway account (free tier works)

## 🚀 Step 1: Set Up Database (2 minutes)

Run the SQL migrations to create all tables:

```bash
# Create schema (required)
psql 'postgresql://neondb_owner:npg_UyzqOD5geV3Y@ep-plain-lake-adl8g160-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require' -f migrations/001_create_schema.sql

# Load demo data (recommended)
psql 'postgresql://neondb_owner:npg_UyzqOD5geV3Y@ep-plain-lake-adl8g160-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require' -f migrations/002_seed_demo_data.sql
```

**What this creates:**
- ✅ 13 tables (passengers, flights, bags, equipment, etc.)
- ✅ Indexes and foreign keys
- ✅ Sample Copa Airlines data for testing
- ✅ 3 demo scenarios ready to run

## 🚂 Step 2: Deploy to Railway (2 minutes)

### Option A: One-Click Deploy

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repository
4. Select branch: `claude/baggage-operations-dashboard-01XogJ9TpYLmDKcUf6Qe3fGD`
5. Railway automatically detects Dockerfile and deploys!

### Option B: Using Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

## 🔑 Step 3: Configure Environment Variables (1 minute)

In Railway Dashboard → Variables, add:

```bash
# Required
DATABASE_URL=postgresql://neondb_owner:npg_UyzqOD5geV3Y@ep-plain-lake-adl8g160-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional but recommended
ENVIRONMENT=production
LOG_LEVEL=INFO
COPA_HUB_AIRPORT=PTY
```

That's it! Railway will automatically redeploy with the new variables.

## ✅ Step 4: Verify Deployment (30 seconds)

```bash
# Get your Railway URL (e.g., https://bag-agents-production.up.railway.app)
RAILWAY_URL=<your-url-here>

# Test health endpoint
curl $RAILWAY_URL/health

# Test agents endpoint
curl $RAILWAY_URL/api/v1/agents
```

Expected response:
```json
{
  "status": "healthy",
  "agents": [
    "root_cause_agent",
    "customer_service_agent",
    "compensation_agent",
    "demand_forecast_agent",
    "infrastructure_health_agent",
    "route_optimization_agent"
  ]
}
```

## 🎯 Test the Agents

### 1. Root Cause Analysis

```bash
curl -X POST $RAILWAY_URL/api/v1/agents/root-cause \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "d0000001-0000-0000-0000-000000000001",
    "bag_id": "c0000001-0000-0000-0000-000000000006"
  }'
```

### 2. Customer Service

```bash
curl -X POST $RAILWAY_URL/api/v1/agents/customer-service \
  -H "Content-Type: application/json" \
  -d '{
    "customer_query": "Where is my bag 0230556789?",
    "bag_tag": "0230556789",
    "language": "en",
    "channel": "web_chat"
  }'
```

### 3. Demand Forecast

```bash
curl -X POST $RAILWAY_URL/api/v1/agents/demand-forecast \
  -H "Content-Type: application/json" \
  -d '{
    "airport_code": "PTY",
    "forecast_horizon_hours": 24,
    "forecast_type": "hourly"
  }'
```

### 4. Infrastructure Health

```bash
curl -X POST $RAILWAY_URL/api/v1/agents/infrastructure-health \
  -H "Content-Type: application/json" \
  -d '{
    "airport_code": "PTY",
    "include_predictions": true
  }'
```

### 5. Route Optimization

```bash
curl -X POST $RAILWAY_URL/api/v1/agents/route-optimization \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "CHECK_IN_1",
    "destination": "GATE_B2",
    "airport_code": "PTY",
    "priority": "rush"
  }'
```

## 📊 View Demo Data

Query the sample data:

```sql
-- Connect to database
psql 'postgresql://neondb_owner:npg_UyzqOD5geV3Y@ep-plain-lake-adl8g160-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

-- View at-risk bag
SELECT tag_number, status, risk_level, current_location, destination
FROM bags WHERE risk_level IN ('high', 'critical');

-- View equipment health
SELECT equipment_id, equipment_type, status, health_score, utilization
FROM equipment WHERE health_score < 80;

-- View incidents
SELECT pir_number, incident_type, severity, status, root_cause
FROM incidents;

-- View compensation claims
SELECT claim_number, claimed_amount, approval_status, fraud_risk_score
FROM compensation_claims;
```

## 🎓 Next Steps

### Connect Your Frontend

Update your Next.js dashboard to point to Railway:

```typescript
// dashboard/lib/api-client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ||
  'https://your-app.railway.app/api/v1';
```

### Enable WebSockets for Real-Time

```bash
# Add to Railway variables
WEBSOCKET_ENABLED=true
WEBSOCKET_PORT=8001
```

### Add Monitoring

```bash
# Railway provides built-in monitoring
# View in Dashboard → Metrics

# Or add custom metrics
METRICS_ENABLED=true
PROMETHEUS_PORT=9090
```

### Custom Domain

1. Railway Dashboard → Your Service → Settings
2. Add custom domain: `api.baggage-ops.com`
3. Update DNS:
   ```
   CNAME api -> your-app.railway.app
   ```
4. SSL auto-provisioned

## 📚 Full Documentation

- **Database Setup**: [`migrations/README.md`](migrations/README.md)
- **Railway Deployment**: [`RAILWAY_DEPLOYMENT.md`](RAILWAY_DEPLOYMENT.md)
- **Environment Variables**: [`.env.example`](.env.example)
- **Copa Integration**: [`docs/COPA_INTEGRATION.md`](docs/COPA_INTEGRATION.md)
- **System Architecture**: [`docs/LLM_CONTEXT.md`](docs/LLM_CONTEXT.md)

## 🆘 Troubleshooting

### Build fails
```bash
# Check logs
railway logs

# Common fix: dependency conflict resolved
# We fixed numpy version conflict in requirements.txt
```

### Database connection fails
```bash
# Verify DATABASE_URL
railway variables | grep DATABASE

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

### LLM errors
```bash
# Verify API key
railway variables | grep ANTHROPIC

# Check quota
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

## 🎉 You're Ready!

Your Copa Airlines Baggage Operations AI Agent System is now:
- ✅ Deployed on Railway
- ✅ Connected to Neon PostgreSQL
- ✅ All 6 agents running
- ✅ Demo data loaded
- ✅ Ready for December 15th demo!

**Railway URL**: Check Railway Dashboard for your deployment URL

**Estimated setup time**: 5-10 minutes total

**Cost**: Free tier covers everything for testing/demo
