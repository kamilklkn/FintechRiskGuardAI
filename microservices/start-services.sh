#!/bin/bash

echo "Starting Microservices..."

# Colors
GREEN='\033[0.32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create data directories
mkdir -p agent-service/data task-service/data memory-service/data

# Export service URLs
export AGENT_SERVICE_URL=http://localhost:8001
export TASK_SERVICE_URL=http://localhost:8002
export MEMORY_SERVICE_URL=http://localhost:8003

# Start services in background
echo -e "${BLUE}Starting Agent Service (Port 8001)...${NC}"
cd agent-service && python main.py > ../logs/agent-service.log 2>&1 &
AGENT_PID=$!
cd ..

sleep 2

echo -e "${BLUE}Starting Task Service (Port 8002)...${NC}"
cd task-service && python main.py > ../logs/task-service.log 2>&1 &
TASK_PID=$!
cd ..

sleep 2

echo -e "${BLUE}Starting Memory Service (Port 8003)...${NC}"
cd memory-service && python main.py > ../logs/memory-service.log 2>&1 &
MEMORY_PID=$!
cd ..

sleep 2

echo -e "${BLUE}Starting API Gateway (Port 8000)...${NC}"
cd gateway && python main.py > ../logs/gateway.log 2>&1 &
GATEWAY_PID=$!
cd ..

sleep 3

echo ""
echo -e "${GREEN}✅ All services started!${NC}"
echo ""
echo "Service URLs:"
echo "  API Gateway:     http://localhost:8000"
echo "  Agent Service:   http://localhost:8001"
echo "  Task Service:    http://localhost:8002"
echo "  Memory Service:  http://localhost:8003"
echo ""
echo "Admin Panel:       http://localhost:8000/admin"
echo "Health Check:      http://localhost:8000/health"
echo ""
echo "Process IDs:"
echo "  Gateway: $GATEWAY_PID"
echo "  Agent:   $AGENT_PID"
echo "  Task:    $TASK_PID"
echo "  Memory:  $MEMORY_PID"
echo ""
echo "To stop all services:"
echo "  kill $GATEWAY_PID $AGENT_PID $TASK_PID $MEMORY_PID"
echo "  or run: ./stop-services.sh"
echo ""
echo "Logs are in logs/ directory"
