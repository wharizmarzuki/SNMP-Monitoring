#!/bin/bash

# ==============================================================================
# SNMP Monitoring System - Dependency Checker
# ==============================================================================
# This script checks if all required dependencies are installed and configured
# Run this before setup to ensure your system is ready

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}SNMP Monitoring - Dependency Checker${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# ==============================================================================
# Helper Functions
# ==============================================================================

check_command() {
    local cmd=$1
    local name=$2
    local required=$3

    if command -v "$cmd" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $name is installed"
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}✗${NC} $name is NOT installed (REQUIRED)"
            ((ERRORS++))
        else
            echo -e "${YELLOW}⚠${NC} $name is NOT installed (optional)"
            ((WARNINGS++))
        fi
        return 1
    fi
}

check_version() {
    local name=$1
    local current=$2
    local required=$3

    if [ "$(printf '%s\n' "$required" "$current" | sort -V | head -n1)" = "$required" ]; then
        echo -e "${GREEN}✓${NC} $name version $current (>= $required required)"
        return 0
    else
        echo -e "${RED}✗${NC} $name version $current is too old (>= $required required)"
        ((ERRORS++))
        return 1
    fi
}

check_port() {
    local port=$1
    local service=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠${NC} Port $port is already in use (needed for $service)"
        ((WARNINGS++))
        return 1
    else
        echo -e "${GREEN}✓${NC} Port $port is available (for $service)"
        return 0
    fi
}

# ==============================================================================
# Check System Requirements
# ==============================================================================

echo -e "${BLUE}Checking System Requirements...${NC}"
echo ""

# Check Python
if check_command python3 "Python 3" true; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    check_version "Python" "$PYTHON_VERSION" "3.12.0"
fi

# Check pip
check_command pip3 "pip (Python package manager)" true

# Check Node.js
if check_command node "Node.js" true; then
    NODE_VERSION=$(node --version | sed 's/v//')
    check_version "Node.js" "$NODE_VERSION" "18.0.0"
fi

# Check npm
check_command npm "npm (Node package manager)" true

# Check git (useful but not strictly required)
check_command git "Git" false

# Check openssl (for generating secrets)
check_command openssl "OpenSSL" true

echo ""

# ==============================================================================
# Check Optional Tools
# ==============================================================================

echo -e "${BLUE}Checking Optional Tools...${NC}"
echo ""

# Check Redis
if check_command redis-server "Redis" false; then
    REDIS_VERSION=$(redis-server --version | awk '{print $3}' | sed 's/v=//')
    echo -e "  Redis version: $REDIS_VERSION"
fi

# Check Redis CLI
check_command redis-cli "Redis CLI" false

# Check if lsof is available (for port checking)
check_command lsof "lsof (for port checking)" false

echo ""

# ==============================================================================
# Check Port Availability
# ==============================================================================

echo -e "${BLUE}Checking Port Availability...${NC}"
echo ""

if command -v lsof &> /dev/null; then
    check_port 8000 "FastAPI backend"
    check_port 3000 "Next.js frontend"
    check_port 6379 "Redis (if using cache)"
else
    echo -e "${YELLOW}⚠${NC} lsof not available, skipping port checks"
    ((WARNINGS++))
fi

echo ""

# ==============================================================================
# Check Python Virtual Environment
# ==============================================================================

echo -e "${BLUE}Checking Python Environment...${NC}"
echo ""

if command -v python3 &> /dev/null; then
    # Check if venv module is available
    if python3 -m venv --help &> /dev/null; then
        echo -e "${GREEN}✓${NC} Python venv module is available"
    else
        echo -e "${RED}✗${NC} Python venv module is NOT available"
        echo -e "  Install with: sudo apt-get install python3-venv"
        ((ERRORS++))
    fi
fi

echo ""

# ==============================================================================
# Check Disk Space
# ==============================================================================

echo -e "${BLUE}Checking Disk Space...${NC}"
echo ""

AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -gt 1 ]; then
    echo -e "${GREEN}✓${NC} Sufficient disk space available (${AVAILABLE_SPACE}GB free)"
else
    echo -e "${YELLOW}⚠${NC} Low disk space (${AVAILABLE_SPACE}GB free, at least 2GB recommended)"
    ((WARNINGS++))
fi

echo ""

# ==============================================================================
# Summary
# ==============================================================================

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}===============================================${NC}"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}All checks passed! ✓${NC}"
    echo -e "You're ready to run ${BLUE}./setup.sh${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}Checks completed with $WARNINGS warning(s) ⚠${NC}"
    echo -e "You can proceed, but some optional features may not work."
    echo -e "Run ${BLUE}./setup.sh${NC} to continue."
    exit 0
else
    echo -e "${RED}Found $ERRORS error(s) and $WARNINGS warning(s) ✗${NC}"
    echo ""
    echo -e "${YELLOW}Please fix the errors above before proceeding.${NC}"
    echo ""
    echo -e "Common fixes:"
    echo -e "  - Install Python 3.12+: ${BLUE}sudo apt-get install python3${NC}"
    echo -e "  - Install Node.js 18+: ${BLUE}https://nodejs.org/${NC}"
    echo -e "  - Install pip: ${BLUE}sudo apt-get install python3-pip${NC}"
    echo -e "  - Install venv: ${BLUE}sudo apt-get install python3-venv${NC}"
    exit 1
fi
