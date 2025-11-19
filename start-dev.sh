#!/bin/bash
# SNMP Monitoring System - Development Startup Script
# This script starts both backend and frontend services for local testing

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SNMP Monitoring System - Dev Mode${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if services are already running
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo -e "${YELLOW}⚠️  Backend is already running. Stopping it first...${NC}"
    pkill -f "uvicorn main:app"
    sleep 2
fi

if pgrep -f "next dev" > /dev/null; then
    echo -e "${YELLOW}⚠️  Frontend is already running. Stopping it first...${NC}"
    pkill -f "next dev"
    sleep 2
fi

# Start Backend
echo -e "${GREEN}Starting Backend...${NC}"
cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Please run setup first.${NC}"
    exit 1
fi

# Activate venv and start backend
source venv/bin/activate
nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
cd ..

# Wait for backend to initialize
echo "Waiting for backend to initialize..."
sleep 3

# Start Frontend
echo -e "${GREEN}Starting Frontend...${NC}"
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found. Please run 'npm install' first.${NC}"
    exit 1
fi

nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
cd ..

# Wait for frontend to be ready
echo "Waiting for frontend to be ready..."
sleep 5

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Services Running Successfully! ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "📱 ${BLUE}Frontend:${NC}  http://localhost:3000"
echo -e "🔧 ${BLUE}Backend:${NC}   http://localhost:8000"
echo -e "📚 ${BLUE}API Docs:${NC}  http://localhost:8000/docs"
echo ""
echo -e "📋 ${BLUE}Logs:${NC}"
echo -e "   Backend:  tail -f logs/backend.log"
echo -e "   Frontend: tail -f logs/frontend.log"
echo ""
echo -e "${YELLOW}To stop services, run: ./stop-dev.sh${NC}"
echo ""
