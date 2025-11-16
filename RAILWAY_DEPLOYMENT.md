# Railway Deployment Guide

Complete guide to deploy the Copa Airlines Baggage Operations AI Agent System to Railway.

## Prerequisites

1. **Railway Account**: Sign up at https://railway.app
2. **GitHub Repository**: Your code should be in a GitHub repo
3. **Neon Database**: Already configured (you have the connection string)
4. **Anthropic API Key**: For Claude LLM integration

## Quick Deploy (3 Steps)

### Step 1: Create Railway Project

```bash
# Install Railway CLI (optional but recommended)
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init
```

**Or use the Railway Dashboard:**
1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account
5. Select the `bag-agents` repository
6. Select branch: `claude/baggage-operations-dashboard-01XogJ9TpYLmDKcUf6Qe3fGD`

### Step 2: Configure Environment Variables

In Railway Dashboard → Your Project → Variables, add these:

```bash
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://neondb_owner:npg_UyzqOD5geV3Y@ep-plain-lake-adl8g160-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require

# Anthropic Claude API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Neo4j (if using for graph routing)
NEO4J_URI=neo4j+s://your-neo4j-instance.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=*

# Copa Airlines Settings
COPA_HUB_AIRPORT=PTY
COPA_TIMEZONE=America/Panama

# Optional: Redis for caching
REDIS_URL=redis://your-redis-instance:6379
```

### Step 3: Deploy

Railway will automatically deploy when you push to your branch!

```bash
# Push your code
git push origin claude/baggage-operations-dashboard-01XogJ9TpYLmDKcUf6Qe3fGD

# Railway will automatically build and deploy
```

## Detailed Configuration

### Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `ANTHROPIC_API_KEY` | ✅ Yes | Claude API key for LLM | `sk-ant-...` |
| `NEO4J_URI` | ⚠️ Optional | Neo4j graph database | `neo4j+s://xxx.neo4j.io` |
| `NEO4J_USER` | ⚠️ Optional | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | ⚠️ Optional | Neo4j password | `your_password` |
| `REDIS_URL` | ⚠️ Optional | Redis for caching | `redis://localhost:6379` |
| `ENVIRONMENT` | No | Environment name | `production` |
| `LOG_LEVEL` | No | Logging level | `INFO` |
| `CORS_ORIGINS` | No | Allowed CORS origins | `*` or `https://yourdomain.com` |
| `COPA_HUB_AIRPORT` | No | Copa hub airport code | `PTY` |
| `COPA_TIMEZONE` | No | Copa timezone | `America/Panama` |

### Railway CLI Commands

```bash
# Link to your project
railway link

# View logs
railway logs

# Open in browser
railway open

# Run migrations
railway run psql $DATABASE_URL -f migrations/001_create_schema.sql
railway run psql $DATABASE_URL -f migrations/002_seed_demo_data.sql

# SSH into container
railway shell

# Check status
railway status

# Set environment variable
railway variables set ANTHROPIC_API_KEY=sk-ant-...

# Deploy specific branch
railway up
```

## Database Setup on Railway

### Option 1: Use Your Existing Neon Database (Recommended)

✅ Already configured! Just use the DATABASE_URL you provided.

### Option 2: Add Railway PostgreSQL

1. In Railway Dashboard → Your Project
2. Click "+ New" → "Database" → "PostgreSQL"
3. Railway will create a new Postgres instance
4. Copy the `DATABASE_URL` from Variables
5. Run migrations:

```bash
# Using Railway CLI
railway run psql $DATABASE_URL -f migrations/001_create_schema.sql
railway run psql $DATABASE_URL -f migrations/002_seed_demo_data.sql

# Or directly
psql $DATABASE_URL -f migrations/001_create_schema.sql
psql $DATABASE_URL -f migrations/002_seed_demo_data.sql
```

## Post-Deployment

### 1. Verify Deployment

```bash
# Check if service is running
curl https://your-app.railway.app/health

# Expected response:
# {"status": "healthy", "timestamp": "2024-11-16T..."}
```

### 2. Run Database Migrations

```bash
# Connect to your Neon database
psql 'postgresql://neondb_owner:npg_UyzqOD5geV3Y@ep-plain-lake-adl8g160-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require' -f migrations/001_create_schema.sql

psql 'postgresql://neondb_owner:npg_UyzqOD5geV3Y@ep-plain-lake-adl8g160-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require' -f migrations/002_seed_demo_data.sql
```

### 3. Test API Endpoints

```bash
# Get base URL from Railway
RAILWAY_URL=https://your-app.railway.app

# Test health endpoint
curl $RAILWAY_URL/health

# Test agents
curl $RAILWAY_URL/api/v1/agents

# Test root cause analysis
curl -X POST $RAILWAY_URL/api/v1/agents/root-cause \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "d0000001-0000-0000-0000-000000000001",
    "bag_id": "c0000001-0000-0000-0000-000000000006"
  }'
```

### 4. Monitor Logs

```bash
# Stream logs in real-time
railway logs --follow

# Or in Railway Dashboard → Your Service → Logs
```

## Troubleshooting

### Build Fails

**Problem**: Docker build fails
**Solution**:
```bash
# Check Dockerfile is valid
docker build -t test .

# Check railway.json
cat railway.json

# View build logs in Railway Dashboard
```

### Database Connection Issues

**Problem**: Can't connect to Neon
**Solution**:
```bash
# Verify DATABASE_URL is set correctly
railway variables

# Test connection manually
psql $DATABASE_URL -c "SELECT version();"

# Check if Neon instance is accessible
ping ep-plain-lake-adl8g160-pooler.c-2.us-east-1.aws.neon.tech
```

### LLM API Errors

**Problem**: Anthropic API calls failing
**Solution**:
```bash
# Verify API key is set
railway variables | grep ANTHROPIC

# Test API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-sonnet-20240229","max_tokens":10,"messages":[{"role":"user","content":"test"}]}'
```

### Application Crashes

**Problem**: App keeps restarting
**Solution**:
```bash
# Check logs for errors
railway logs --tail 100

# Check memory usage (Railway free tier: 512MB)
# Reduce worker count if needed

# Check health endpoint
curl https://your-app.railway.app/health
```

## Scaling

### Horizontal Scaling

In Railway Dashboard → Your Service → Settings:
- Adjust "Replicas" count (Pro plan required)
- Enable "Auto-scaling" based on CPU/Memory

### Vertical Scaling

- Upgrade Railway plan for more resources
- Free: 512MB RAM, 1 vCPU
- Starter: 8GB RAM, 8 vCPUs
- Pro: 32GB RAM, 32 vCPUs

### Database Scaling

For Neon:
1. Go to Neon Dashboard
2. Adjust compute size
3. Enable autoscaling
4. Add read replicas if needed

## CI/CD Pipeline

Railway automatically deploys on git push. Customize with GitHub Actions:

```yaml
# .github/workflows/railway-deploy.yml
name: Deploy to Railway

on:
  push:
    branches: [main, claude/baggage-operations-dashboard-*]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Railway
        run: npm i -g @railway/cli

      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

## Monitoring

### Built-in Metrics

Railway provides:
- CPU usage
- Memory usage
- Network traffic
- Response times

Access in Dashboard → Your Service → Metrics

### Custom Metrics

Add Prometheus endpoint:
```python
# In api/main.py
from prometheus_client import make_asgi_app

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

Then configure Railway to scrape `/metrics`

### Logging

Railway automatically captures:
- stdout/stderr
- Application logs
- Access logs

Configure log retention in Dashboard → Settings

## Security

### Environment Variables

✅ Railway encrypts all environment variables
✅ Never commit `.env` files
✅ Use Railway's secret management

### Network Security

```bash
# Restrict CORS
CORS_ORIGINS=https://yourdomain.com,https://dashboard.yourdomain.com

# Enable rate limiting in your API
# Add in api/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

### Database Security

- Use Neon's connection pooler (already in your URL)
- Enable SSL (already configured: `sslmode=require`)
- Rotate passwords regularly
- Use read-only users for dashboards

## Cost Optimization

### Railway Pricing

- **Free Tier**: $0/month, 500 execution hours
- **Starter**: $5/month, no execution hour limit
- **Pro**: $20/month, priority support

### Neon Pricing

- **Free Tier**: 0.5GB storage, 1 project
- **Pro**: $19/month, 10GB storage, autoscaling

### Tips to Reduce Costs

1. **Use sleep mode** for non-production environments
2. **Optimize Docker image** size (current: ~200MB)
3. **Cache LLM responses** with Redis
4. **Batch database queries** to reduce connections
5. **Use connection pooling** (already configured in Neon URL)

## Production Checklist

Before going live:

- [ ] Database migrations run successfully
- [ ] Environment variables set correctly
- [ ] Health check endpoint responds
- [ ] All 6 agents tested
- [ ] CORS configured for your frontend domain
- [ ] Monitoring and alerting configured
- [ ] Backup strategy in place (Neon handles this)
- [ ] Rate limiting enabled
- [ ] SSL/TLS enabled (Railway handles this)
- [ ] Custom domain configured (optional)

## Custom Domain

1. In Railway Dashboard → Your Service → Settings
2. Click "Generate Domain" or "Custom Domain"
3. Add your domain: `api.baggage-ops.com`
4. Update DNS:
   ```
   CNAME api -> your-app.railway.app
   ```
5. Wait for DNS propagation (5-30 minutes)
6. SSL certificate auto-provisioned

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Neon Docs: https://neon.tech/docs
- Project Issues: GitHub Issues

## Quick Reference

```bash
# Most Common Commands
railway login                  # Login to Railway
railway init                   # Initialize project
railway link                   # Link to existing project
railway up                     # Deploy
railway logs                   # View logs
railway variables              # List variables
railway variables set KEY=val  # Set variable
railway open                   # Open in browser
railway status                 # Check status
```

Your app will be available at:
`https://bag-agents-production.up.railway.app` (or similar)
