# Baggage Operations AI Agents

AI-powered agent system for analyzing and optimizing baggage handling operations using LangChain, LangGraph, and multi-database architecture.

## Overview

This system provides specialized AI agents that work together to predict, analyze, and optimize baggage handling operations at airports. It combines machine learning models, graph databases, and large language models to deliver intelligent insights and automation.

### Key Features

- **Multi-Agent Architecture**: 7 specialized agents for different aspects of baggage operations
- **LangGraph Workflows**: Orchestrated multi-step workflows using state graphs
- **Dual Database Design**: PostgreSQL (Neon) for structured data, Neo4j for graph relationships
- **Real-time API**: FastAPI server with REST and WebSocket endpoints
- **Production-Ready**: Docker containerization, monitoring, and observability
- **Extensible**: Easy to add new agents and workflows

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI Server                        │
│                    (REST + WebSocket)                       │
└────────────────────┬───────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │  Orchestrator Agent     │
        └────────────┬────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐      ┌────▼────┐      ┌───▼────┐
│Predict│      │Root     │      │Demand  │
│Agent  │      │Cause    │      │Forecast│
└───┬───┘      └────┬────┘      └───┬────┘
    │               │                │
    └───────────────┼────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
    ┌───▼────┐            ┌────▼────┐
    │ Neon   │            │ Neo4j   │
    │  PG    │            │  Graph  │
    └────────┘            └─────────┘
```

## Agents

### 1. Prediction Agent
Predicts potential baggage mishandling incidents using ML models and historical data.

**Capabilities:**
- Real-time risk assessment
- Multi-factor analysis (weather, connections, equipment)
- Confidence scoring

### 2. Root Cause Agent
Performs deep analysis of incidents using graph database relationships.

**Capabilities:**
- Graph-based pattern recognition
- System bottleneck identification
- Actionable insights generation

### 3. Demand Forecast Agent
Forecasts baggage handling demand for resource optimization.

**Capabilities:**
- Short and long-term predictions
- Seasonal pattern recognition
- Resource requirement recommendations

### 4. Customer Service Agent
Handles customer inquiries with intelligent response generation.

**Capabilities:**
- Natural language understanding
- Baggage tracking and status
- Multi-language support
- Escalation detection

### 5. Compensation Agent
Calculates and processes compensation claims.

**Capabilities:**
- Eligibility determination
- Policy compliance checking
- Fraud detection
- Automated claim processing

### 6. Infrastructure Health Agent
Monitors equipment and infrastructure health.

**Capabilities:**
- Predictive maintenance scheduling
- Performance degradation detection
- Capacity planning

### 7. Route Optimization Agent
Optimizes baggage routing using graph algorithms.

**Capabilities:**
- Shortest path calculation
- Capacity-aware routing
- Alternative path generation
- Risk-adjusted optimization

## Installation

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- API keys for:
  - Anthropic Claude
  - OpenAI (for embeddings)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/bag-agents.git
   cd bag-agents
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

### Docker Setup

1. **Configure environment**
   ```bash
   cp .env.example .env
   # Add your API keys to .env
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Check service health**
   ```bash
   docker-compose ps
   curl http://localhost:8000/health
   ```

### Services Available

- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (user: neo4j, password: password)
- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3000 (user: admin, password: admin)

## Usage

### REST API

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Invoke Single Agent
```bash
curl -X POST http://localhost:8000/agents/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "agent_name": "prediction",
    "input_data": {
      "flight_id": "AA123",
      "departure_airport": "JFK",
      "arrival_airport": "LAX"
    }
  }'
```

#### Execute Workflow
```bash
curl -X POST http://localhost:8000/workflows/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "workflow_type": "incident_analysis",
    "parameters": {
      "incident_id": "INC-2024-001",
      "incident_type": "delayed"
    }
  }'
```

#### List Available Agents
```bash
curl http://localhost:8000/agents
```

### WebSocket Connection

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/agents/prediction"
    async with websockets.connect(uri) as websocket:
        # Send request
        await websocket.send(json.dumps({
            "flight_id": "AA123",
            "departure_airport": "JFK",
            "arrival_airport": "LAX"
        }))

        # Receive response
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(test_websocket())
```

### Python SDK

```python
from agents.prediction_agent import PredictionAgent
from utils.llm import get_llm_client
from utils.database import get_db_manager

# Initialize
llm_client = get_llm_client()
db_manager = get_db_manager()

# Create agent
agent = PredictionAgent(
    llm_client=llm_client,
    db_connection=db_manager
)

# Execute
result = await agent.run({
    "flight_id": "AA123",
    "departure_airport": "JFK",
    "arrival_airport": "LAX"
})

print(result)
```

## Development

### Project Structure

```
bag-agents/
├── agents/              # Agent implementations
│   ├── base_agent.py
│   ├── prediction_agent.py
│   ├── root_cause_agent.py
│   └── ...
├── models/              # ML models
│   ├── mishandling_predictor/
│   └── demand_forecaster/
├── langgraph/           # LangGraph workflows
│   ├── state_graph.py
│   └── workflows.py
├── utils/               # Utilities
│   ├── database.py
│   ├── llm.py
│   └── monitoring.py
├── api/                 # FastAPI server
│   └── main.py
├── tests/               # Test suite
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Adding a New Agent

1. **Create agent file**
   ```python
   # agents/my_new_agent.py
   from .base_agent import BaseAgent

   class MyNewAgent(BaseAgent):
       def __init__(self, llm_client=None, db_connection=None, config=None):
           super().__init__(
               agent_name="my_new_agent",
               llm_client=llm_client,
               db_connection=db_connection,
               config=config
           )

       async def execute(self, input_data):
           # Implement your logic
           return {"result": "success"}
   ```

2. **Register in orchestrator** (api/main.py)
   ```python
   from agents.my_new_agent import MyNewAgent

   agents["my_new"] = MyNewAgent(
       llm_client=llm_client,
       db_connection=db_manager
   )
   ```

3. **Add tests**
   ```python
   # tests/test_my_new_agent.py
   import pytest
   from agents.my_new_agent import MyNewAgent

   @pytest.mark.asyncio
   async def test_my_new_agent():
       agent = MyNewAgent()
       result = await agent.run({"test": "data"})
       assert result["metadata"]["status"] == "success"
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agents --cov=utils --cov=api

# Run specific test file
pytest tests/test_prediction_agent.py
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy agents/ utils/ api/

# Run all pre-commit hooks
pre-commit run --all-files
```

## Monitoring

### Prometheus Metrics

The system exposes metrics at `http://localhost:9090/metrics`:

- `agent_requests_total`: Total agent invocations
- `agent_duration_seconds`: Agent execution time
- `api_requests_total`: API request count
- `llm_requests_total`: LLM API calls
- `llm_token_usage_total`: Token consumption

### Grafana Dashboards

Access Grafana at http://localhost:3000 to visualize:
- Agent performance
- API latency
- Database connections
- Error rates
- LLM usage and costs

## Deployment

### Production Deployment

1. **Update environment variables**
   - Use production database URLs (Neon, Neo4j Aura)
   - Set secure API keys
   - Configure CORS appropriately

2. **Build production image**
   ```bash
   docker build -t baggage-agents:latest .
   ```

3. **Deploy to cloud**
   - AWS ECS/EKS
   - Google Cloud Run
   - Azure Container Instances

4. **Set up monitoring**
   - Configure Prometheus scraping
   - Set up Grafana dashboards
   - Enable log aggregation

### Environment Variables

Key production environment variables:

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database
NEON_DB_HOST=your-production-neon-host
NEO4J_URI=bolt://your-neo4j-aura-instance

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Security
API_KEYS=secure-api-key-1,secure-api-key-2

# Monitoring
ENABLE_METRICS=True
PROMETHEUS_PORT=9090
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check documentation at `/docs`
- Review API documentation at `/docs` endpoint

## Roadmap

- [ ] Enhanced ML models for prediction
- [ ] Real-time streaming analytics
- [ ] Mobile app integration
- [ ] Advanced visualization dashboards
- [ ] Multi-tenant support
- [ ] Advanced caching layer
- [ ] Event-driven architecture with Kafka
- [ ] A/B testing framework

## Acknowledgments

- Built with [LangChain](https://langchain.com) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- Powered by [Anthropic Claude](https://anthropic.com)
- Uses [FastAPI](https://fastapi.tiangolo.com) framework
- Database infrastructure: [Neon](https://neon.tech) and [Neo4j](https://neo4j.com)
