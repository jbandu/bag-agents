# Multi-stage build for baggage operations AI agents

# Build stage
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY agents/ ./agents/
COPY models/ ./models/
COPY baggage_workflows/ ./baggage_workflows/
COPY utils/ ./utils/
COPY api/ ./api/
COPY start.sh ./start.sh

# Make start script executable
RUN chmod +x start.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose ports
# 8000 for API
# 9090 for Prometheus metrics
EXPOSE 8000 9090

# Health check - use PORT env variable
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import os, requests; port=os.getenv('PORT', '8000'); requests.get(f'http://localhost:{port}/health')"

# Run the application
CMD ["./start.sh"]
