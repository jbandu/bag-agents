# Baggage Operations AI Agents - Complete System Documentation
# LLM Context Document

**Project:** Baggage Operations AI Agents
**Version:** 1.0.0
**Last Updated:** 2024-12-15
**Purpose:** Comprehensive context for AI/LLM understanding of the entire codebase

---

## TABLE OF CONTENTS

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Directory Structure](#3-directory-structure)
4. [Core Components](#4-core-components)
5. [AI Agents System](#5-ai-agents-system)
6. [API Layer](#6-api-layer)
7. [Frontend Dashboard](#7-frontend-dashboard)
8. [Copa Airlines Integration](#8-copa-airlines-integration)
9. [Data Models](#9-data-models)
10. [Configuration](#10-configuration)
11. [Database Schema](#11-database-schema)
12. [Authentication & Authorization](#12-authentication--authorization)
13. [Deployment](#13-deployment)
14. [Code Examples](#14-code-examples)
15. [Testing](#15-testing)
16. [Monitoring & Observability](#16-monitoring--observability)

---

## 1. PROJECT OVERVIEW

### 1.1 What This System Does

This is an **AI-powered baggage operations management system** that uses multiple specialized AI agents to predict, analyze, and optimize baggage handling at airports. The system integrates with airline systems (specifically Copa Airlines for the initial demo) to provide:

- **Real-time baggage tracking** across the entire airport network
- **Predictive analytics** to identify bags at risk of mishandling
- **Root cause analysis** when incidents occur
- **Automated interventions** to prevent problems
- **Customer service automation** for passenger inquiries
- **Compensation processing** for mishandled bags
- **Infrastructure health monitoring**
- **Demand forecasting** for resource optimization

### 1.2 Key Technologies

**Backend:**
- Python 3.11+
- FastAPI (REST API)
- LangChain & LangGraph (AI orchestration)
- Anthropic Claude (LLM)
- PostgreSQL via Neon (structured data)
- Neo4j (graph database for relationships)
- WebSockets (real-time updates)
- Docker (containerization)

**Frontend:**
- Next.js 14 (React framework with App Router)
- TypeScript
- Tailwind CSS + shadcn/ui
- React Query (TanStack Query)
- Socket.io client
- Recharts (visualizations)
- Supabase Auth

**Integration:**
- Copa Airlines DCS (Departure Control System)
- Copa Airlines Flight Operations
- Copa Airlines BHS (Baggage Handling System)
- IATA bag message formats (BSM, BPM, BTM)

### 1.3 System Capabilities

1. **Predict** bags at risk of mishandling (before it happens)
2. **Detect** mishandling incidents automatically
3. **Analyze** root causes using graph relationships
4. **Intervene** proactively to prevent issues
5. **Communicate** with passengers automatically
6. **Compensate** eligible passengers per airline policy
7. **Monitor** equipment and infrastructure health
8. **Optimize** bag routing and resource allocation
9. **Forecast** demand for staffing and capacity planning
10. **Visualize** operations in real-time dashboard

---

## 2. SYSTEM ARCHITECTURE

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Next.js Dashboard (TypeScript)                          │   │
│  │  - Real-time Operations Dashboard                        │   │
│  │  - Flight Operations View                                │   │
│  │  - Mishandled Bags Management                            │   │
│  │  - AI Agent Insights                                     │   │
│  │  - Analytics & Reports                                   │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼───────────────────────────────────────────────┘
                    │ HTTP/WebSocket
┌───────────────────▼───────────────────────────────────────────────┐
│                      API GATEWAY LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI Gateway                                         │   │
│  │  - Rate Limiting                                         │   │
│  │  - Request Routing                                       │   │
│  │  - Logging & Monitoring                                  │   │
│  │  - API Key Authentication                                │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼───────────────────────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────────────────────┐
│                    APPLICATION LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI Main Application                                │   │
│  │  - RESTful API Endpoints                                 │   │
│  │  - WebSocket Endpoints                                   │   │
│  │  - Agent Invocation                                      │   │
│  │  - Workflow Execution                                    │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼───────────────────────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────────────────────┐
│                  AI ORCHESTRATION LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LangGraph Orchestrator                                  │   │
│  │  - State Management                                      │   │
│  │  │  - Multi-Step Workflows                                    │
│  │  - Event System                                          │   │
│  │  - State Persistence                                     │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼───────────────────────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────────────────────┐
│                      AI AGENTS LAYER                              │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐              │
│  │ Prediction  │ │ Root Cause  │ │   Demand     │              │
│  │   Agent     │ │   Agent     │ │  Forecast    │              │
│  └─────────────┘ └─────────────┘ └──────────────┘              │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐              │
│  │  Customer   │ │Compensation │ │Infrastructure│              │
│  │  Service    │ │   Agent     │ │    Health    │              │
│  └─────────────┘ └─────────────┘ └──────────────┘              │
│  ┌─────────────┐                                                 │
│  │    Route    │                                                 │
│  │Optimization │                                                 │
│  └─────────────┘                                                 │
└───────────────────┼───────────────────────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────────────────────┐
│                   INTEGRATION LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Copa Airlines Integration Service                       │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │   │
│  │  │ DCS Adapter  │ │ Flight Ops   │ │ BHS Adapter  │    │   │
│  │  │              │ │   Adapter    │ │              │    │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘    │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │  Data Mapper (Copa ↔ Internal Formats)           │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼───────────────────────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────────────────────┐
│                     DATA LAYER                                    │
│  ┌─────────────┐         ┌─────────────┐                         │
│  │  PostgreSQL │         │    Neo4j    │                         │
│  │   (Neon)    │         │   (Graph)   │                         │
│  │             │         │             │                         │
│  │ - Bags      │         │ - Flights   │                         │
│  │ - Flights   │         │ - Bags      │                         │
│  │ - Passengers│         │ - Passengers│                         │
│  │ - Incidents │         │ - Routes    │                         │
│  │ - Events    │         │ - Equipment │                         │
│  └─────────────┘         └─────────────┘                         │
└───────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

**Typical Bag Check-in Flow:**

1. Passenger checks bag at Copa Airlines counter
2. Copa DCS → DCS Adapter → Data Mapper → Internal Format
3. Prediction Agent analyzes risk factors
4. If high risk: Alert created, intervention suggested
5. Bag scanned by BHS → BHS Adapter → Event processed
6. Root Cause Agent monitors for anomalies
7. Dashboard shows real-time status
8. WebSocket pushes updates to connected clients

**Incident Response Flow:**

1. Bag flagged as mishandled (delayed/lost/damaged)
2. Event triggers Root Cause Agent
3. Graph analysis identifies probable cause
4. Customer Service Agent generates communication
5. Compensation Agent evaluates claim
6. Infrastructure Health Agent checks equipment
7. Resolution tracked and analyzed
8. Insights fed back to Prediction Agent

### 2.3 Agent Orchestration

The system uses **LangGraph** for stateful, multi-step agent workflows:

```python
# Workflow Example: Incident Analysis
incident → [Prediction Check] → [Root Cause Analysis] →
          [Compensation Evaluation] → [Customer Communication] →
          [Resolution Tracking]
```

Each step maintains state, can branch based on conditions, and has access to:
- Previous step outputs
- Database queries
- LLM reasoning
- External API calls

---

## 3. DIRECTORY STRUCTURE

```
bag-agents/
├── agents/                      # AI Agents (7 specialized agents)
│   ├── base_agent.py           # Base class all agents inherit from
│   ├── prediction_agent.py     # Predicts bag mishandling risk
│   ├── root_cause_agent.py     # Analyzes incident causes
│   ├── demand_forecast_agent.py# Forecasts baggage volume
│   ├── customer_service_agent.py# Handles passenger inquiries
│   ├── compensation_agent.py   # Processes compensation claims
│   ├── infrastructure_health_agent.py # Monitors equipment
│   ├── route_optimization_agent.py    # Optimizes bag routing
│   └── orchestrator_agent.py   # Coordinates multiple agents
│
├── api/                        # FastAPI REST API
│   ├── main.py                 # Main API application
│   └── orchestrator_routes.py  # Workflow execution endpoints
│
├── auth/                       # Authentication & Authorization
│   ├── supabase_auth.py        # Supabase integration
│   └── rbac.py                 # Role-based access control
│
├── clients/                    # External service clients
│   ├── airline_client.py       # Airline system integration
│   └── bag_client.py           # Bag tracking client
│
├── dashboard/                  # Next.js Frontend
│   ├── app/                    # App Router pages
│   │   ├── (dashboard)/
│   │   │   ├── dashboard/      # Main overview page
│   │   │   ├── flights/        # Flight operations view
│   │   │   ├── bags/           # Bag tracking
│   │   │   ├── mishandled/     # Mishandled bags dashboard
│   │   │   ├── agents/         # AI agent insights
│   │   │   ├── approvals/      # Pending approvals
│   │   │   ├── analytics/      # Analytics & reports
│   │   │   └── settings/       # Settings
│   │   └── (auth)/             # Authentication pages
│   ├── components/             # React components
│   │   ├── ui/                 # shadcn/ui components
│   │   ├── dashboard/          # Dashboard-specific components
│   │   └── layout/             # Layout components
│   ├── lib/                    # Utilities and clients
│   │   ├── api-client.ts       # Backend API client
│   │   ├── websocket-client.ts # WebSocket client
│   │   ├── types.ts            # TypeScript types
│   │   ├── supabase.ts         # Supabase config
│   │   └── utils.ts            # Utility functions
│   └── providers/              # React context providers
│       ├── query-provider.tsx  # React Query setup
│       └── theme-provider.tsx  # Dark mode support
│
├── docs/                       # Documentation
│   ├── COPA_INTEGRATION.md     # Copa integration guide
│   ├── API_GATEWAY.md          # API Gateway documentation
│   └── ORCHESTRATOR.md         # Orchestrator guide
│
├── examples/                   # Usage examples
│   └── orchestrator_demo.py    # Orchestrator demo script
│
├── gateway/                    # API Gateway
│   ├── main.py                 # Gateway entry point
│   ├── router.py               # Request routing
│   ├── rate_limiter.py         # Rate limiting logic
│   └── logging_middleware.py   # Request logging
│
├── integrations/               # External system integrations
│   ├── config.py               # Integration configuration
│   ├── data_mapper.py          # Data format transformations
│   ├── integration_service.py  # Main integration orchestrator
│   ├── mock_copa_data.py       # Mock data generator
│   ├── copa_demo_script.py     # Demo scenario runner
│   └── copa/                   # Copa Airlines adapters
│       ├── dcs_adapter.py      # DCS integration
│       ├── flight_ops_adapter.py # Flight Ops integration
│       └── bhs_adapter.py      # BHS integration
│
├── langgraph/                  # LangGraph workflows
│   ├── baggage_orchestrator.py # Main orchestrator
│   ├── state_graph.py          # State graph definition
│   ├── orchestrator_state.py   # State models
│   ├── workflows.py            # Pre-defined workflows
│   ├── event_system.py         # Event handling
│   └── state_persistence.py    # State storage
│
├── models/                     # ML Models
│   ├── mishandling_predictor/  # Mishandling prediction model
│   └── demand_forecaster/      # Demand forecasting model
│
├── shared/                     # Shared code
│   └── contracts.py            # Data contracts and schemas
│
├── tests/                      # Test suite
│   ├── test_api.py
│   ├── test_agents.py
│   ├── test_orchestrator.py
│   └── conftest.py             # Pytest configuration
│
├── utils/                      # Utility modules
│   ├── database.py             # Database connections
│   ├── llm.py                  # LLM client setup
│   └── monitoring.py           # Metrics and monitoring
│
├── webhooks/                   # Webhook handling
│   └── webhook_registry.py     # Webhook registration
│
├── docker-compose.yml          # Docker services definition
├── Dockerfile                  # API container
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
├── Makefile                    # Development commands
└── README.md                   # Main documentation
```

---

## 4. CORE COMPONENTS

### 4.1 Base Agent Class

**File:** `agents/base_agent.py`

All AI agents inherit from this base class which provides:

```python
class BaseAgent:
    """Base class for all AI agents"""

    def __init__(self, agent_name: str, llm_client, db_connection, config):
        self.agent_name = agent_name
        self.llm = llm_client  # Anthropic Claude client
        self.db = db_connection
        self.config = config
        self.logger = logging.getLogger(agent_name)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method
        Returns: {
            "result": <agent output>,
            "metadata": {
                "status": "success" | "error",
                "execution_time": <seconds>,
                "llm_calls": <count>,
                "confidence": <0-1>
            }
        }
        """
        pass

    async def _call_llm(self, prompt: str, system: str) -> str:
        """Make LLM API call with retry logic"""
        pass

    async def _log_execution(self, input_data, result):
        """Log execution for monitoring"""
        pass
```

**Key Features:**
- Standardized input/output format
- Built-in LLM client with retry logic
- Database access
- Logging and monitoring
- Error handling
- Execution metrics

### 4.2 LangGraph Orchestrator

**File:** `langgraph/baggage_orchestrator.py`

Coordinates multi-agent workflows using state graphs:

```python
class BaggageOrchestrator:
    """Orchestrates complex multi-agent workflows"""

    def __init__(self):
        self.graph = StateGraph(OrchestratorState)
        self.agents = {
            "prediction": PredictionAgent(),
            "root_cause": RootCauseAgent(),
            "customer_service": CustomerServiceAgent(),
            # ... other agents
        }

    def build_graph(self):
        """Define state machine"""
        # Add nodes (agents)
        self.graph.add_node("predict", self._predict_node)
        self.graph.add_node("analyze", self._analyze_node)
        self.graph.add_node("communicate", self._communicate_node)

        # Add edges (transitions)
        self.graph.add_edge("predict", "analyze")
        self.graph.add_conditional_edges(
            "analyze",
            self._should_communicate,
            {"yes": "communicate", "no": END}
        )

        return self.graph.compile()

    async def execute_workflow(self, workflow_type: str, input_data):
        """Execute a predefined workflow"""
        pass
```

**Workflow Types:**
1. `incident_analysis` - Analyze mishandling incident
2. `risk_assessment` - Assess bag risk
3. `customer_inquiry` - Handle customer question
4. `compensation_claim` - Process compensation
5. `demand_forecast` - Forecast demand

### 4.3 Data Mapper

**File:** `integrations/data_mapper.py`

Transforms Copa's data formats to internal schema:

```python
class CopaDataMapper:
    """Maps Copa Airlines data to internal format"""

    # Copa field names → Internal field names
    BAG_FIELD_MAP = {
        "bagTagNumber": "tag_number",
        "passengerPNR": "passenger_id",
        "currentStatus": "status",
        # ... 20+ field mappings
    }

    # Copa status codes → Internal status
    STATUS_MAP = {
        "CHK": "checked",
        "LOD": "loaded",
        "TRN": "in_transit",
        "DLY": "delayed",
        "LST": "lost",
    }

    def map_bag_data(self, copa_bag: Dict) -> Dict:
        """Transform Copa bag to internal format"""
        mapped = {}
        for copa_field, internal_field in self.BAG_FIELD_MAP.items():
            if copa_field in copa_bag:
                mapped[internal_field] = copa_bag[copa_field]

        # Convert timestamps to UTC
        mapped["checked_at"] = self._convert_timestamp(
            copa_bag["checkedDateTime"]
        )

        # Assess risk
        mapped["risk_level"] = self._assess_risk(copa_bag)

        return mapped

    def _convert_timestamp(self, timestamp) -> str:
        """Convert Copa timestamp to UTC ISO format"""
        # Handles: ISO strings, Unix timestamps, Copa custom format
        pass
```

---

## 5. AI AGENTS SYSTEM

### 5.1 Agent Overview

The system has **7 specialized AI agents**, each with specific responsibilities:

| Agent | Purpose | Key Capabilities |
|-------|---------|------------------|
| **Prediction** | Predict mishandling risk | ML model + LLM reasoning, multi-factor analysis |
| **Root Cause** | Analyze incident causes | Graph database queries, pattern recognition |
| **Demand Forecast** | Forecast baggage volume | Time series analysis, seasonal patterns |
| **Customer Service** | Handle inquiries | NLU, baggage tracking, multi-language |
| **Compensation** | Process claims | Policy compliance, fraud detection |
| **Infrastructure** | Monitor equipment | Predictive maintenance, capacity planning |
| **Route Optimization** | Optimize routing | Graph algorithms, capacity-aware pathfinding |

### 5.2 Prediction Agent

**File:** `agents/prediction_agent.py`

**Purpose:** Predict bags at risk of mishandling **before** problems occur

**Inputs:**
```python
{
    "bag_tag": "0230556789",
    "flight_id": "CM123",
    "connection_time_minutes": 45,
    "weather_conditions": "stormy",
    "equipment_status": "degraded",
    "historical_performance": {...}
}
```

**Process:**
1. Query historical data for similar scenarios
2. Check ML model prediction (if trained)
3. Analyze risk factors with LLM:
   - Tight connections (<45 min)
   - Weather delays
   - Equipment issues
   - Peak congestion times
   - Special handling requirements
4. Calculate confidence score
5. Suggest interventions

**Output:**
```python
{
    "risk_score": 0.87,  # 0-1 scale
    "risk_level": "high",  # low/medium/high/critical
    "risk_factors": [
        "Connection time only 35 minutes",
        "Arrival flight delayed 15 minutes",
        "High traffic period in hub"
    ],
    "suggested_interventions": [
        "Flag for priority handling",
        "Alert ground crew at connection point",
        "Pre-position bag near connecting gate"
    ],
    "confidence": 0.94
}
```

### 5.3 Root Cause Agent

**File:** `agents/root_cause_agent.py`

**Purpose:** Determine why mishandling occurred using graph analysis

**Inputs:**
```python
{
    "incident_id": "INC-2024-001",
    "bag_id": "BAG_0230556789",
    "incident_type": "delayed",
    "timeline": [...]  # Event history
}
```

**Process:**
1. Query Neo4j for bag's complete journey graph
2. Identify anomalies in event sequence
3. Compare to successful journeys
4. Use LLM to reason about probable causes
5. Generate actionable insights

**Neo4j Query Example:**
```cypher
MATCH (b:Bag {tag: '0230556789'})-[r:SCANNED_AT]->(l:Location)
RETURN b, r, l
ORDER BY r.timestamp
```

**Output:**
```python
{
    "root_cause": "Bag missed loading due to late arrival of connecting flight",
    "contributing_factors": [
        "Weather delay on inbound flight",
        "Ground crew shift change during critical window",
        "Conveyor belt C3 running at 70% capacity"
    ],
    "similar_incidents": 12,  # In past 30 days
    "recommendations": [
        "Increase buffer time for weather-impacted connections",
        "Schedule ground crew overlap during peak times",
        "Schedule maintenance for conveyor C3"
    ],
    "confidence": 0.89
}
```

### 5.4 Customer Service Agent

**File:** `agents/customer_service_agent.py`

**Purpose:** Handle passenger inquiries about their bags

**Inputs:**
```python
{
    "query": "Where is my bag? My flight was CM123 yesterday.",
    "passenger_name": "John Smith",
    "pnr": "ABC123",  # Optional
    "language": "en"
}
```

**Process:**
1. Parse query using LLM (extract intent, entities)
2. Look up passenger in database
3. Get bag status and location
4. Generate natural language response
5. Detect if escalation needed

**Output:**
```python
{
    "response": "I found your bag (tag 0230556789). It was delayed on flight CM123 but has been located at Panama airport. It's being loaded on the next flight CM456 departing at 3:30 PM today and will arrive in New York at 10:45 PM. We'll deliver it to your residence tomorrow morning.",
    "escalate": false,
    "sentiment": "concerned",
    "follow_up_required": true,
    "suggested_actions": [
        "Send tracking link via email",
        "Schedule delivery",
        "Offer compensation voucher"
    ]
}
```

### 5.5 Compensation Agent

**File:** `agents/compensation_agent.py`

**Purpose:** Evaluate and process compensation claims

**Inputs:**
```python
{
    "incident_id": "INC-2024-001",
    "passenger_tier": "Gold",
    "delay_hours": 24,
    "bag_value": 500,
    "passenger_expenses": 150
}
```

**Process:**
1. Check airline policy rules
2. Evaluate eligibility
3. Calculate compensation amount
4. Detect fraud indicators
5. Generate approval recommendation

**Output:**
```python
{
    "eligible": true,
    "compensation_amount": 250,
    "compensation_type": "monetary",
    "breakdown": {
        "delay_compensation": 150,
        "expense_reimbursement": 100,
        "goodwill_gesture": 0
    },
    "requires_approval": false,  # Auto-approve if < $300
    "fraud_score": 0.05,  # Low risk
    "policy_compliance": true
}
```

---

## 6. API LAYER

### 6.1 FastAPI Main Application

**File:** `api/main.py`

**Base URL:** `http://localhost:8000`

**Key Endpoints:**

```python
# Health Check
GET /health
Response: {"status": "healthy", "timestamp": "2024-12-15T10:00:00Z"}

# List Available Agents
GET /agents
Response: ["prediction", "root_cause", "demand_forecast", ...]

# Invoke Single Agent
POST /agents/invoke
Body: {
    "agent_name": "prediction",
    "input_data": {
        "flight_id": "CM123",
        "bag_tag": "0230556789"
    }
}
Response: {
    "result": {...},
    "metadata": {
        "status": "success",
        "execution_time": 1.234,
        "agent": "prediction"
    }
}

# Execute Workflow
POST /workflows/execute
Body: {
    "workflow_type": "incident_analysis",
    "parameters": {
        "incident_id": "INC-2024-001"
    }
}
Response: {
    "workflow_id": "wf_abc123",
    "status": "completed",
    "steps": [
        {"step": "prediction_check", "result": {...}},
        {"step": "root_cause_analysis", "result": {...}},
        {"step": "compensation_evaluation", "result": {...}}
    ]
}

# WebSocket Connection
WS /ws/agents/{agent_name}
Send: {"input": {...}}
Receive: {"type": "result", "data": {...}}

# Copa Integration Endpoints
GET /copa/flights?airport=PTY
GET /copa/bags/{bag_tag}
GET /copa/demo-scenarios
```

### 6.2 API Gateway

**File:** `gateway/main.py`

**Purpose:** Single entry point with rate limiting, logging, routing

**Features:**
- Rate limiting: 100 requests/minute per API key
- Request/response logging
- Route-based routing to backend services
- API key authentication
- Metrics collection

**Gateway Flow:**
```
Client Request → [Rate Limiter] → [Auth Check] → [Logger] →
                 [Router] → Backend Service → [Logger] → Response
```

---

## 7. FRONTEND DASHBOARD

### 7.1 Dashboard Overview

**Technology:** Next.js 14 with App Router, TypeScript, Tailwind CSS

**Pages:**

| Route | Purpose | Key Features |
|-------|---------|--------------|
| `/dashboard` | Main overview | KPIs, at-risk bags, agent status |
| `/flights` | Flight operations | Active flights, bag counts, delays |
| `/bags` | Bag tracking | Search bags, view journey |
| `/bags/[id]` | Bag details | Complete timeline, status |
| `/mishandled` | Mishandled bags | Cases, status, handler assignment |
| `/agents` | AI agents | Agent insights, predictions |
| `/approvals` | Pending approvals | Human-in-loop decisions |
| `/analytics` | Analytics | Charts, reports, exports |
| `/settings` | Settings | Configuration, preferences |

### 7.2 API Client

**File:** `dashboard/lib/api-client.ts`

**Usage:**

```typescript
import apiClient from '@/lib/api-client'

// Get flights
const flights = await apiClient.getFlights({ airport: 'PTY' })

// Get bag details
const bag = await apiClient.getBag('BAG_0230556789')

// Get KPI metrics
const kpis = await apiClient.getKPIMetrics()

// Get AI predictions
const predictions = await apiClient.getPredictions()

// Export report
const blob = await apiClient.exportReport('analytics', 'pdf', {
    start_date: '2024-01-01',
    end_date: '2024-12-31'
})
```

### 7.3 WebSocket Client

**File:** `dashboard/lib/websocket-client.ts`

**Purpose:** Real-time updates from backend

**Usage:**

```typescript
import wsClient from '@/lib/websocket-client'

// Connect
const socket = wsClient.connect('/bags')

// Subscribe to bag updates
wsClient.onBagUpdate((bag) => {
    console.log('Bag updated:', bag)
    updateUI(bag)
})

// Subscribe to flight updates
wsClient.onFlightUpdate((flight) => {
    console.log('Flight updated:', flight)
    updateUI(flight)
})

// Subscribe to alerts
wsClient.onAlert((alert) => {
    showNotification(alert.message, alert.severity)
})
```

### 7.4 TypeScript Types

**File:** `dashboard/lib/types.ts`

**Key Types:**

```typescript
export type BagStatus = 'checked' | 'loaded' | 'in_transit' |
                        'transferred' | 'delivered' | 'delayed' |
                        'lost' | 'damaged'

export type BagRiskLevel = 'low' | 'medium' | 'high' | 'critical'

export interface Bag {
    id: string
    tag_number: string
    passenger_id: string
    passenger_name: string
    flight_id: string
    status: BagStatus
    risk_level: BagRiskLevel
    current_location: string
    destination: string
    weight: number
    checked_at: string
    last_scan_at: string
    position?: { x: number; y: number; z: number }
    connection_time_minutes?: number
    predicted_issues?: string[]
}

export interface Flight {
    id: string
    flight_number: string
    airline: string
    departure_airport: string
    arrival_airport: string
    scheduled_departure: string
    actual_departure?: string
    scheduled_arrival: string
    status: FlightStatus
    gate?: string
    bags_checked: number
    bags_loaded: number
    bags_missing: number
    at_risk_connections: number
}

export interface KPIMetrics {
    mishandling_rate: number
    mishandling_rate_change: number
    on_time_delivery_rate: number
    on_time_delivery_change: number
    avg_resolution_time_hours: number
    resolution_time_change: number
    total_bags_today: number
    bags_at_risk: number
    active_incidents: number
}
```

---

## 8. COPA AIRLINES INTEGRATION

### 8.1 Integration Architecture

**Components:**
1. **DCS Adapter** - Passenger check-in and bag data
2. **Flight Ops Adapter** - Real-time flight information
3. **BHS Adapter** - Baggage handling system events
4. **Data Mapper** - Format transformations
5. **Integration Service** - Orchestrator

### 8.2 DCS Adapter

**File:** `integrations/copa/dcs_adapter.py`

**Key Methods:**

```python
class CopaDCSAdapter:
    async def get_flight_manifest(self, flight_number, flight_date):
        """Get complete passenger and bag list for flight"""

    async def get_checked_bags(self, flight_number=None, since=None):
        """Get recently checked bags"""

    async def get_bag_details(self, bag_tag):
        """Get details for specific bag"""

    async def get_connecting_bags(self, arrival_flight,
                                  departure_flight, airport):
        """Get bags transferring between flights"""

    async def listen_for_checkin_events(self, callback):
        """Real-time check-in event stream"""
```

### 8.3 Mock Data for Demo

**File:** `integrations/mock_copa_data.py`

**Generates:**
- 50 realistic Copa flights per day
- 1,500 bags across Copa network
- 3 pre-configured demo scenarios

**Demo Scenarios:**

1. **Normal Connection (BOG→PTY→JFK)**
   - 2-hour connection time
   - Smooth transfer
   - Complete journey tracking

2. **At-Risk Connection (MIA→PTY→LIM)**
   - Flight delayed 30 minutes
   - Only 30-minute connection
   - AI predicts risk and triggers priority handling
   - Bag successfully makes connection

3. **Mishandled Bag Recovery (PTY→JFK)**
   - Bag missed loading
   - PIR auto-generated
   - AI predicts location (94% confidence)
   - Recovered in 4 hours vs industry 24+ hours

**Run Demo:**

```bash
python -m integrations.copa_demo_script
```

---

## 9. DATA MODELS

### 9.1 PostgreSQL Schema (Neon)

**Tables:**

```sql
-- Bags Table
CREATE TABLE bags (
    id UUID PRIMARY KEY,
    tag_number VARCHAR(10) UNIQUE NOT NULL,
    passenger_id VARCHAR(6),
    flight_id VARCHAR(50),
    status VARCHAR(20),
    risk_level VARCHAR(10),
    current_location VARCHAR(3),  -- Airport code
    destination VARCHAR(3),
    weight DECIMAL(5,2),
    checked_at TIMESTAMP,
    last_scan_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Flights Table
CREATE TABLE flights (
    id VARCHAR(50) PRIMARY KEY,
    flight_number VARCHAR(10),
    airline VARCHAR(2),
    departure_airport VARCHAR(3),
    arrival_airport VARCHAR(3),
    scheduled_departure TIMESTAMP,
    actual_departure TIMESTAMP,
    scheduled_arrival TIMESTAMP,
    actual_arrival TIMESTAMP,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Incidents Table
CREATE TABLE incidents (
    id VARCHAR(50) PRIMARY KEY,
    bag_id UUID REFERENCES bags(id),
    incident_type VARCHAR(20),  -- delayed, lost, damaged
    reported_at TIMESTAMP,
    resolved_at TIMESTAMP,
    root_cause TEXT,
    compensation_amount DECIMAL(10,2),
    status VARCHAR(20)
);

-- Events Table (Event Sourcing)
CREATE TABLE events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(50),
    bag_id UUID,
    flight_id VARCHAR(50),
    location VARCHAR(3),
    timestamp TIMESTAMP,
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent Executions (Monitoring)
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY,
    agent_name VARCHAR(50),
    input_data JSONB,
    output_data JSONB,
    execution_time DECIMAL(10,3),
    status VARCHAR(20),
    executed_at TIMESTAMP DEFAULT NOW()
);
```

### 9.2 Neo4j Graph Schema

**Nodes:**
- `Bag` - Baggage items
- `Flight` - Flights
- `Passenger` - Passengers
- `Location` - Airports, gates, equipment
- `Equipment` - Conveyors, sorters, scanners

**Relationships:**
```cypher
(Bag)-[:CHECKED_BY]->(Passenger)
(Bag)-[:ON_FLIGHT]->(Flight)
(Bag)-[:SCANNED_AT {timestamp, equipment_id}]->(Location)
(Flight)-[:DEPARTS_FROM]->(Location)
(Flight)-[:ARRIVES_AT]->(Location)
(Bag)-[:TRANSFERRED_TO]->(Flight)
(Equipment)-[:LOCATED_IN]->(Location)
```

**Example Queries:**

```cypher
-- Get bag journey
MATCH (b:Bag {tag: '0230556789'})-[r:SCANNED_AT]->(l:Location)
RETURN b, r, l
ORDER BY r.timestamp

-- Find bags at risk
MATCH (b:Bag)-[:ON_FLIGHT]->(f:Flight)
WHERE f.status = 'delayed'
  AND b.connection_time_minutes < 45
RETURN b, f

-- Identify equipment issues
MATCH (e:Equipment)-[:LOCATED_IN]->(l:Location)
WHERE e.status = 'degraded'
RETURN e, l
```

---

## 10. CONFIGURATION

### 10.1 Environment Variables

**Backend (Python):**

```bash
# Database
NEON_DB_HOST=your-neon-host
NEON_DB_NAME=baggage_ops
NEON_DB_USER=user
NEON_DB_PASSWORD=password
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLM
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...  # For embeddings

# API
API_PORT=8000
API_KEYS=key1,key2,key3  # Comma-separated

# Copa Integration
USE_MOCK_COPA_DATA=true  # Use mock data for demo
COPA_DCS_URL=https://api.copa.com/dcs/v1
COPA_DCS_API_KEY=your-key
COPA_FLIGHT_OPS_URL=https://api.copa.com/flights/v1
COPA_FLIGHT_OPS_API_KEY=your-key
COPA_BHS_URL=https://api.copa.com/bhs/v1
COPA_BHS_API_KEY=your-key

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO
```

**Frontend (Next.js):**

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Backend API
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000

# Mapbox (optional)
NEXT_PUBLIC_MAPBOX_TOKEN=your-mapbox-token
```

### 10.2 Docker Compose

**File:** `docker-compose.yml`

**Services:**
- `api` - FastAPI backend (port 8000)
- `gateway` - API Gateway (port 8080)
- `neo4j` - Graph database (port 7474, 7687)
- `prometheus` - Metrics (port 9091)
- `grafana` - Dashboards (port 3000)

**Start Services:**

```bash
docker-compose up -d
```

---

## 11. DATABASE SCHEMA

### 11.1 Bag Journey Example

**PostgreSQL Record:**

```json
{
    "id": "BAG_0230556789",
    "tag_number": "0230556789",
    "passenger_id": "ABC123",
    "flight_id": "FLT_CM123_20241215",
    "status": "in_transit",
    "risk_level": "medium",
    "current_location": "PTY",
    "destination": "JFK",
    "checked_at": "2024-12-15T08:00:00Z"
}
```

**Neo4j Graph:**

```cypher
(bag:Bag {tag: '0230556789'})
-[:SCANNED_AT {timestamp: '08:00:00', equipment: 'CHECK_IN_01'}]->(bog:Location {code: 'BOG'})
-[:SCANNED_AT {timestamp: '08:30:00', equipment: 'CONVEYOR_A1'}]->(bog)
-[:SCANNED_AT {timestamp: '09:00:00', equipment: 'LOADER_03'}]->(bog)
(bag)-[:ON_FLIGHT]->(f1:Flight {number: 'CM101'})
-[:SCANNED_AT {timestamp: '11:15:00', equipment: 'UNLOADER_05'}]->(pty:Location {code: 'PTY'})
-[:SCANNED_AT {timestamp: '11:30:00', equipment: 'TRANSFER_BELT'}]->(pty)
(bag)-[:TRANSFERRED_TO]->(f2:Flight {number: 'CM451'})
```

---

## 12. AUTHENTICATION & AUTHORIZATION

### 12.1 Supabase Auth

**File:** `auth/supabase_auth.py`

**User Roles:**
- `admin` - Full access
- `operator` - View and manage operations
- `handler` - Update bag status, assign cases
- `viewer` - Read-only access

**Protected Endpoints:**

```python
from auth.supabase_auth import require_auth, require_role

@app.get("/admin/stats")
@require_auth
@require_role(["admin"])
async def admin_stats():
    # Only admins can access
    pass

@app.post("/bags/{bag_id}/status")
@require_auth
@require_role(["admin", "operator", "handler"])
async def update_bag_status(bag_id: str):
    # Multiple roles allowed
    pass
```

### 12.2 API Key Authentication

**File:** `gateway/main.py`

```python
def verify_api_key(api_key: str) -> bool:
    valid_keys = os.getenv("API_KEYS", "").split(",")
    return api_key in valid_keys

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    if not api_key or not verify_api_key(api_key):
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid API key"}
        )
    return await call_next(request)
```

---

## 13. DEPLOYMENT

### 13.1 Development

```bash
# Backend
cd /home/user/bag-agents
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload

# Frontend
cd dashboard
npm install
npm run dev
```

### 13.2 Production

**Backend (Docker):**

```bash
docker build -t baggage-agents:latest .
docker run -p 8000:8000 \
    -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
    -e NEON_DB_HOST=$NEON_DB_HOST \
    baggage-agents:latest
```

**Frontend (Vercel):**

```bash
cd dashboard
vercel --prod
```

### 13.3 Monitoring

**Prometheus Metrics:**
- `agent_requests_total` - Agent invocations
- `agent_duration_seconds` - Execution time
- `llm_requests_total` - LLM API calls
- `llm_token_usage_total` - Token consumption

**Grafana Dashboards:**
- Agent performance
- API latency
- Error rates
- LLM costs

---

## 14. CODE EXAMPLES

### 14.1 Invoke Prediction Agent

```python
from agents.prediction_agent import PredictionAgent
from utils.llm import get_llm_client
from utils.database import get_db_manager

# Initialize
llm = get_llm_client()
db = get_db_manager()
agent = PredictionAgent(llm_client=llm, db_connection=db)

# Execute
result = await agent.run({
    "flight_id": "CM123",
    "bag_tag": "0230556789",
    "connection_time_minutes": 35,
    "weather": "stormy"
})

print(f"Risk Score: {result['result']['risk_score']}")
print(f"Interventions: {result['result']['suggested_interventions']}")
```

### 14.2 Execute Workflow

```python
from langgraph.baggage_orchestrator import BaggageOrchestrator

orchestrator = BaggageOrchestrator()

result = await orchestrator.execute_workflow(
    workflow_type="incident_analysis",
    parameters={
        "incident_id": "INC-2024-001",
        "bag_tag": "0230556789"
    }
)

for step in result["steps"]:
    print(f"{step['name']}: {step['result']}")
```

### 14.3 Copa Integration

```python
from integrations.integration_service import get_integration_service

# Initialize service
service = await get_integration_service()
await service.start()

# Register callback for bag events
async def handle_bag_checked(event):
    bag = event['data']
    print(f"Bag checked: {bag['tag_number']}")

    # Run prediction
    prediction = await prediction_agent.run(bag)
    if prediction['risk_score'] > 0.7:
        # Alert operators
        await send_alert(bag, prediction)

service.register_callback("bag_checked", handle_bag_checked)

# Get demo scenarios
scenarios = await service.get_demo_scenarios()
for scenario in scenarios:
    print(f"Scenario {scenario['scenario']}: {scenario['description']}")
```

### 14.4 Dashboard React Query

```typescript
'use client'

import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api-client'

export function FlightsList() {
    const { data: flights, isLoading } = useQuery({
        queryKey: ['flights', 'active'],
        queryFn: () => apiClient.getFlights({ hours_ahead: 6 }),
        refetchInterval: 30000  // Refresh every 30s
    })

    if (isLoading) return <div>Loading...</div>

    return (
        <div>
            {flights.map(flight => (
                <FlightCard key={flight.id} flight={flight} />
            ))}
        </div>
    )
}
```

---

## 15. TESTING

### 15.1 Test Structure

```bash
tests/
├── test_api.py              # API endpoint tests
├── test_base_agent.py       # Base agent tests
├── test_prediction_agent.py # Prediction agent tests
├── test_orchestrator.py     # Orchestrator tests
├── test_gateway.py          # Gateway tests
└── conftest.py              # Pytest fixtures
```

### 15.2 Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=agents --cov=api --cov=langgraph

# Specific test file
pytest tests/test_prediction_agent.py

# Verbose output
pytest -v
```

### 15.3 Example Test

```python
import pytest
from agents.prediction_agent import PredictionAgent

@pytest.mark.asyncio
async def test_prediction_agent_high_risk(mock_llm, mock_db):
    agent = PredictionAgent(
        llm_client=mock_llm,
        db_connection=mock_db
    )

    result = await agent.run({
        "flight_id": "CM123",
        "connection_time_minutes": 25  # Very tight
    })

    assert result["metadata"]["status"] == "success"
    assert result["result"]["risk_level"] in ["high", "critical"]
    assert len(result["result"]["suggested_interventions"]) > 0
```

---

## 16. MONITORING & OBSERVABILITY

### 16.1 Logging

All components use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Bag checked", extra={
    "bag_tag": "0230556789",
    "flight": "CM123",
    "airport": "PTY",
    "timestamp": "2024-12-15T10:00:00Z"
})
```

### 16.2 Metrics

**Prometheus Integration:**

```python
from prometheus_client import Counter, Histogram

# Define metrics
agent_requests = Counter(
    'agent_requests_total',
    'Total agent invocations',
    ['agent_name', 'status']
)

agent_duration = Histogram(
    'agent_duration_seconds',
    'Agent execution time',
    ['agent_name']
)

# Record metrics
with agent_duration.labels(agent_name='prediction').time():
    result = await agent.run(input_data)

agent_requests.labels(
    agent_name='prediction',
    status='success'
).inc()
```

### 16.3 Health Checks

```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await db.health_check(),
        "llm": await llm.health_check(),
        "copa_integration": await copa_service.health_check()
    }

    status = "healthy" if all(checks.values()) else "degraded"

    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## APPENDIX A: Quick Reference Commands

```bash
# Start backend
uvicorn api.main:app --reload

# Start frontend
cd dashboard && npm run dev

# Run tests
pytest

# Start all services (Docker)
docker-compose up -d

# Run Copa demo
python -m integrations.copa_demo_script

# Check logs
docker-compose logs -f api

# Database migrations
alembic upgrade head

# Code formatting
black .
ruff check .

# Type checking
mypy agents/ api/ utils/
```

---

## APPENDIX B: File Purposes Summary

| File | Purpose |
|------|---------|
| `agents/base_agent.py` | Base class for all agents |
| `agents/prediction_agent.py` | Predicts bag mishandling risk |
| `agents/root_cause_agent.py` | Analyzes incident causes |
| `api/main.py` | FastAPI application |
| `api/orchestrator_routes.py` | Workflow execution endpoints |
| `dashboard/lib/api-client.ts` | Frontend API client |
| `dashboard/app/(dashboard)/dashboard/page.tsx` | Main dashboard page |
| `integrations/copa/dcs_adapter.py` | Copa DCS integration |
| `integrations/mock_copa_data.py` | Demo data generator |
| `langgraph/baggage_orchestrator.py` | Multi-agent orchestrator |
| `utils/database.py` | Database connections |
| `utils/llm.py` | LLM client setup |

---

## APPENDIX C: Data Flow Diagrams

**Bag Check-in Flow:**

```
Copa DCS → DCS Adapter → Data Mapper → Internal Format
    ↓
Prediction Agent (analyze risk)
    ↓
If high risk: Create alert → Dashboard notification
    ↓
Event stored in PostgreSQL + Neo4j
    ↓
WebSocket → Update connected dashboards
```

**Incident Response Flow:**

```
Mishandling detected → Root Cause Agent
    ↓
Graph query in Neo4j → Pattern analysis
    ↓
LLM reasoning → Probable cause identified
    ↓
Customer Service Agent → Generate communication
    ↓
Compensation Agent → Evaluate claim
    ↓
Resolution tracked → Analytics updated
```

---

**END OF DOCUMENT**

This document provides comprehensive context for LLMs to understand the entire baggage operations AI agent system. It covers architecture, components, APIs, data models, integrations, and includes code examples for all major features.
