"""
Monitoring and observability utilities using Prometheus.
"""

import logging
import os
from typing import Optional

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    start_http_server,
    REGISTRY
)


logger = logging.getLogger(__name__)


# System-level metrics
system_info = Info(
    'baggage_system',
    'Information about the baggage operations system'
)

active_connections = Gauge(
    'active_connections',
    'Number of active database connections',
    ['database']
)

# API metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'Time spent processing API requests',
    ['method', 'endpoint']
)

# Agent-specific metrics
agent_invocations = Counter(
    'agent_invocations_total',
    'Total number of agent invocations',
    ['agent_name', 'status']
)

agent_processing_time = Histogram(
    'agent_processing_time_seconds',
    'Time spent processing by agents',
    ['agent_name']
)

# LLM metrics
llm_requests = Counter(
    'llm_requests_total',
    'Total number of LLM API requests',
    ['provider', 'model', 'status']
)

llm_token_usage = Counter(
    'llm_token_usage_total',
    'Total number of tokens used',
    ['provider', 'model', 'token_type']
)

llm_latency = Histogram(
    'llm_latency_seconds',
    'LLM API request latency',
    ['provider', 'model']
)

# Business metrics
baggage_predictions = Counter(
    'baggage_predictions_total',
    'Total number of baggage mishandling predictions',
    ['prediction_type', 'risk_level']
)

compensation_processed = Counter(
    'compensation_processed_total',
    'Total compensation claims processed',
    ['status', 'amount_range']
)

route_optimizations = Counter(
    'route_optimizations_total',
    'Total number of route optimizations performed',
    ['optimization_type']
)

# Error tracking
error_count = Counter(
    'errors_total',
    'Total number of errors',
    ['component', 'error_type']
)

# Cache metrics
cache_hits = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)


def setup_monitoring(
    port: Optional[int] = None,
    enable_metrics: bool = True
) -> None:
    """
    Set up Prometheus monitoring server.

    Args:
        port: Port to expose metrics (defaults to env var or 9090)
        enable_metrics: Whether to enable metrics collection
    """
    if not enable_metrics:
        logger.info("Metrics collection disabled")
        return

    metrics_port = port or int(os.getenv('PROMETHEUS_PORT', '9090'))

    try:
        start_http_server(metrics_port)
        logger.info(f"Prometheus metrics server started on port {metrics_port}")

        # Set system info
        system_info.info({
            'version': '1.0.0',
            'environment': os.getenv('ENVIRONMENT', 'development')
        })

    except Exception as e:
        logger.error(f"Failed to start Prometheus metrics server: {e}")
        raise


def track_api_request(method: str, endpoint: str, status: int, duration: float):
    """
    Track an API request.

    Args:
        method: HTTP method
        endpoint: API endpoint
        status: HTTP status code
        duration: Request duration in seconds
    """
    api_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=str(status)
    ).inc()

    api_request_duration.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_agent_execution(agent_name: str, status: str, duration: float):
    """
    Track an agent execution.

    Args:
        agent_name: Name of the agent
        status: Execution status (success/error)
        duration: Execution duration in seconds
    """
    agent_invocations.labels(
        agent_name=agent_name,
        status=status
    ).inc()

    agent_processing_time.labels(
        agent_name=agent_name
    ).observe(duration)


def track_llm_request(
    provider: str,
    model: str,
    status: str,
    latency: float,
    input_tokens: int = 0,
    output_tokens: int = 0
):
    """
    Track an LLM API request.

    Args:
        provider: LLM provider (anthropic/openai)
        model: Model name
        status: Request status
        latency: Request latency in seconds
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    """
    llm_requests.labels(
        provider=provider,
        model=model,
        status=status
    ).inc()

    llm_latency.labels(
        provider=provider,
        model=model
    ).observe(latency)

    if input_tokens > 0:
        llm_token_usage.labels(
            provider=provider,
            model=model,
            token_type='input'
        ).inc(input_tokens)

    if output_tokens > 0:
        llm_token_usage.labels(
            provider=provider,
            model=model,
            token_type='output'
        ).inc(output_tokens)


def track_error(component: str, error_type: str):
    """
    Track an error occurrence.

    Args:
        component: Component where error occurred
        error_type: Type of error
    """
    error_count.labels(
        component=component,
        error_type=error_type
    ).inc()


def track_cache_access(cache_type: str, hit: bool):
    """
    Track a cache access.

    Args:
        cache_type: Type of cache
        hit: Whether it was a cache hit
    """
    if hit:
        cache_hits.labels(cache_type=cache_type).inc()
    else:
        cache_misses.labels(cache_type=cache_type).inc()


def get_metrics_summary() -> dict:
    """
    Get a summary of current metrics.

    Returns:
        Dictionary containing metric summaries
    """
    # This is a simplified version
    # In production, you'd query Prometheus for aggregated data
    return {
        "metrics_enabled": True,
        "registry_collectors": len(list(REGISTRY.collect()))
    }
