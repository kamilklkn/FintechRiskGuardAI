#!/bin/bash

echo "Stopping all microservices..."

# Kill all uvicorn processes running microservices
pkill -f "uvicorn main:app"

# Or kill by port
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null
lsof -ti:8003 | xargs kill -9 2>/dev/null

echo "✅ All services stopped"
