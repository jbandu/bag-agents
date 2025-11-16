#!/bin/bash
# Startup script for Railway deployment

# Use PORT from environment or default to 8000
export PORT=${PORT:-8000}

echo "Starting baggage operations API on port $PORT..."

# Start uvicorn
exec python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT
