"""
FastAPI Server for Baggage Operations AI Agents.

Provides REST API and WebSocket endpoints for agent invocation.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from utils.database import get_db_manager
from utils.llm import get_llm_client
from utils.monitoring import setup_monitoring, track_api_request
from agents.prediction_agent import PredictionAgent
from agents.root_cause_agent import RootCauseAgent
from agents.demand_forecast_agent import DemandForecastAgent
from agents.customer_service_agent import CustomerServiceAgent
from agents.compensation_agent import CompensationAgent
from agents.infrastructure_health_agent import InfrastructureHealthAgent
from agents.route_optimization_agent import RouteOptimizationAgent
from agents.orchestrator_agent import OrchestratorAgent
from langgraph.workflows import execute_workflow

# Import orchestrator routes
from api import orchestrator_routes


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for request/response
class AgentRequest(BaseModel):
    """Base request model for agent invocation."""

    agent_name: str = Field(..., description="Name of the agent to invoke")
    input_data: Dict[str, Any] = Field(..., description="Input parameters for the agent")


class WorkflowRequest(BaseModel):
    """Request model for workflow execution."""

    workflow_type: str = Field(..., description="Type of workflow to execute")
    parameters: Dict[str, Any] = Field(..., description="Workflow parameters")


class AgentResponse(BaseModel):
    """Response model for agent invocation."""

    agent_name: str
    result: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    databases: Dict[str, bool]
    agents: Dict[str, str]


# Global state
agents: Dict[str, Any] = {}
db_manager = None
llm_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting baggage operations API server...")

    # Initialize monitoring
    try:
        enable_metrics = os.getenv("ENABLE_METRICS", "True").lower() == "true"
        setup_monitoring(enable_metrics=enable_metrics)
    except Exception as e:
        logger.warning(f"Failed to start monitoring: {e}")

    # Initialize database connections
    global db_manager, llm_client
    try:
        db_manager = get_db_manager()
        logger.info("Database connections initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Initialize LLM client
    try:
        llm_client = get_llm_client()
        logger.info("LLM client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")

    # Initialize agents
    global agents
    try:
        agents["prediction"] = PredictionAgent(llm_client=llm_client, db_connection=db_manager)
        agents["root_cause"] = RootCauseAgent(llm_client=llm_client, db_connection=db_manager)
        agents["demand_forecast"] = DemandForecastAgent(llm_client=llm_client, db_connection=db_manager)
        agents["customer_service"] = CustomerServiceAgent(llm_client=llm_client, db_connection=db_manager)
        agents["compensation"] = CompensationAgent(llm_client=llm_client, db_connection=db_manager)
        agents["infrastructure_health"] = InfrastructureHealthAgent(llm_client=llm_client, db_connection=db_manager)
        agents["route_optimization"] = RouteOptimizationAgent(llm_client=llm_client, db_connection=db_manager)

        # Initialize orchestrator with all agents
        agents["orchestrator"] = OrchestratorAgent(
            llm_client=llm_client,
            db_connection=db_manager,
            available_agents=agents
        )

        logger.info(f"Initialized {len(agents)} agents")
    except Exception as e:
        logger.error(f"Failed to initialize agents: {e}")

    logger.info("API server startup complete")

    yield

    # Shutdown
    logger.info("Shutting down API server...")
    if db_manager:
        db_manager.close_all()
    logger.info("API server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Baggage Operations AI Agents API",
    description="AI-powered agents for baggage handling optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include orchestrator routes
app.include_router(orchestrator_routes.router)


# API Key validation (simple implementation)
async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key from request headers.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    if os.getenv("ENVIRONMENT") == "development":
        return "dev-key"

    api_keys = os.getenv("API_KEYS", "").split(",")
    if not api_keys or not x_api_key or x_api_key not in api_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return x_api_key


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns system health status, database connectivity, and agent status.
    """
    # Check database health
    db_health = {"postgres": False, "neo4j": False}
    if db_manager:
        try:
            db_health = await db_manager.health_check()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")

    # Check agent status
    agent_status = {name: "ready" for name in agents.keys()}

    return HealthResponse(
        status="healthy" if all(db_health.values()) else "degraded",
        version="1.0.0",
        databases=db_health,
        agents=agent_status
    )


# Agent invocation endpoint
@app.post("/agents/invoke", response_model=AgentResponse)
async def invoke_agent(
    request: AgentRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Invoke a specific agent.

    Args:
        request: Agent request with agent name and input data
        api_key: Validated API key

    Returns:
        Agent execution results
    """
    import time

    start_time = time.time()

    try:
        agent_name = request.agent_name
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

        agent = agents[agent_name]
        result = await agent.run(request.input_data)

        duration = time.time() - start_time
        track_api_request("POST", "/agents/invoke", 200, duration)

        return AgentResponse(
            agent_name=agent_name,
            result=result,
            metadata=result.get("metadata")
        )

    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        track_api_request("POST", "/agents/invoke", 500, duration)
        logger.error(f"Agent invocation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Workflow execution endpoint
@app.post("/workflows/execute")
async def execute_workflow_endpoint(
    request: WorkflowRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Execute a workflow involving multiple agents.

    Args:
        request: Workflow request with type and parameters
        api_key: Validated API key

    Returns:
        Workflow execution results
    """
    import time

    start_time = time.time()

    try:
        result = await execute_workflow(
            workflow_type=request.workflow_type,
            input_parameters=request.parameters
        )

        duration = time.time() - start_time
        track_api_request("POST", "/workflows/execute", 200, duration)

        return result

    except ValueError as e:
        duration = time.time() - start_time
        track_api_request("POST", "/workflows/execute", 400, duration)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        duration = time.time() - start_time
        track_api_request("POST", "/workflows/execute", 500, duration)
        logger.error(f"Workflow execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for streaming responses
@app.websocket("/ws/agents/{agent_name}")
async def websocket_agent(websocket: WebSocket, agent_name: str):
    """
    WebSocket endpoint for streaming agent responses.

    Args:
        websocket: WebSocket connection
        agent_name: Name of the agent to invoke
    """
    await websocket.accept()

    try:
        if agent_name not in agents:
            await websocket.send_json({
                "error": f"Agent '{agent_name}' not found"
            })
            await websocket.close()
            return

        while True:
            # Receive input data
            data = await websocket.receive_json()

            try:
                agent = agents[agent_name]
                result = await agent.run(data)

                # Send result back
                await websocket.send_json({
                    "status": "success",
                    "result": result
                })

            except Exception as e:
                logger.error(f"WebSocket agent error: {e}", exc_info=True)
                await websocket.send_json({
                    "status": "error",
                    "error": str(e)
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for agent: {agent_name}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close()
        except:
            pass


# List available agents
@app.get("/agents")
async def list_agents():
    """
    List all available agents and their capabilities.

    Returns:
        Dictionary of agent names and descriptions
    """
    agent_info = {}

    for name, agent in agents.items():
        agent_info[name] = {
            "name": agent.agent_name,
            "class": agent.__class__.__name__,
            "description": agent.__class__.__doc__ or "No description available"
        }

    return agent_info


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Baggage Operations AI Agents API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "health": "/health"
    }


# Run the server
if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "4"))

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        reload=os.getenv("ENVIRONMENT") == "development"
    )
