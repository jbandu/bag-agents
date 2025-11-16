# Quick Start Guide

Get the Baggage Operations AI Agents system up and running in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- API keys:
  - Anthropic API key (for Claude)
  - OpenAI API key (for embeddings)

## Setup Steps

### 1. Clone and Install

```bash
# Navigate to the project directory
cd bag-agents

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
make install
# or
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Required:
#   ANTHROPIC_API_KEY=your_key_here
#   OPENAI_API_KEY=your_key_here
```

### 3. Start Services with Docker

```bash
# Start all services (PostgreSQL, Neo4j, API, Prometheus, Grafana)
make docker-up
# or
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# List available agents
curl http://localhost:8000/agents

# Access API documentation
open http://localhost:8000/docs
```

## Your First Agent Request

### Using cURL

```bash
curl -X POST http://localhost:8000/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "prediction",
    "input_data": {
      "flight_id": "AA123",
      "departure_airport": "JFK",
      "arrival_airport": "LAX"
    }
  }'
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/agents/invoke",
    json={
        "agent_name": "prediction",
        "input_data": {
            "flight_id": "AA123",
            "departure_airport": "JFK",
            "arrival_airport": "LAX"
        }
    }
)

print(response.json())
```

## Available Endpoints

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **List Agents**: http://localhost:8000/agents
- **Invoke Agent**: POST http://localhost:8000/agents/invoke
- **Execute Workflow**: POST http://localhost:8000/workflows/execute

## Available Services

- **API Server**: http://localhost:8000
- **Neo4j Browser**: http://localhost:7474 (neo4j/password)
- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3000 (admin/admin)
- **PostgreSQL**: localhost:5432 (postgres/postgres)

## Run Tests

```bash
# Run all tests
make test

# Run specific test
pytest tests/test_prediction_agent.py -v
```

## Development

```bash
# Install development dependencies
make dev-install

# Format code
make format

# Run linters
make lint

# Install pre-commit hooks
make pre-commit
```

## Common Commands

```bash
# Start services
make docker-up

# Stop services
make docker-down

# View logs
make docker-logs

# Restart services
make docker-restart

# Run API locally (without Docker)
make run

# Clean up
make clean
```

## Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker info

# Check logs
docker-compose logs

# Restart services
make docker-restart
```

### Database connection errors

```bash
# Wait for databases to be ready
docker-compose ps

# Check database health
curl http://localhost:8000/health
```

### API key errors

- Verify .env file has correct API keys
- Make sure .env is in the project root
- Restart services after updating .env

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Explore agent implementations in `/agents`
3. Check out example workflows in `/langgraph`
4. Add your own custom agents
5. Deploy to production

## Support

- Documentation: See README.md
- API Docs: http://localhost:8000/docs
- Issues: Open an issue on GitHub

Happy coding! 🚀
