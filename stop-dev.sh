#!/bin/bash
# SNMP Monitoring System - Stop Development Services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Stopping SNMP Monitoring Services${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Stop Backend
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo -e "${GREEN}Stopping Backend...${NC}"
    pkill -f "uvicorn main:app"
    echo -e "${GREEN}✓ Backend stopped${NC}"
else
    echo -e "${RED}✗ Backend not running${NC}"
fi

# Stop Frontend
if pgrep -f "next dev" > /dev/null; then
    echo -e "${GREEN}Stopping Frontend...${NC}"
    pkill -f "next dev"
    echo -e "${GREEN}✓ Frontend stopped${NC}"
else
    echo -e "${RED}✗ Frontend not running${NC}"
fi

# Wait a moment for processes to terminate
sleep 1

# Verify all processes are stopped
if ! pgrep -f "uvicorn main:app" > /dev/null && ! pgrep -f "next dev" > /dev/null; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  All services stopped successfully ✓${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo ""
    echo -e "${RED}Warning: Some processes may still be running${NC}"
    echo "Run 'ps aux | grep -E \"uvicorn|next dev\"' to check"
fi

echo ""
