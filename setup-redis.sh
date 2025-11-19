#!/bin/bash

###############################################################################
# Redis Setup Script for SNMP Monitoring System
# This script checks if Redis is installed and running, and offers to install it
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Redis Setup for SNMP Monitoring System"
echo "========================================="
echo ""

# Function to check if Redis is installed
check_redis_installed() {
    if command -v redis-server &> /dev/null; then
        return 0  # Redis is installed
    else
        return 1  # Redis is not installed
    fi
}

# Function to check if Redis is running
check_redis_running() {
    if redis-cli ping &> /dev/null; then
        return 0  # Redis is running
    else
        return 1  # Redis is not running
    fi
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            echo "debian"
        elif [ -f /etc/redhat-release ]; then
            echo "redhat"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)

# Check current Redis status
echo "Checking Redis status..."
echo ""

if check_redis_installed; then
    echo -e "${GREEN}✓ Redis is installed${NC}"
    REDIS_VERSION=$(redis-server --version | awk '{print $3}')
    echo "  Version: $REDIS_VERSION"

    if check_redis_running; then
        echo -e "${GREEN}✓ Redis is running${NC}"
        echo ""
        echo -e "${GREEN}Redis is ready! Your SNMP Monitoring System will use caching.${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Redis is installed but not running${NC}"
        echo ""
        echo "Would you like to start Redis? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "Starting Redis..."
            if [[ "$OS" == "debian" ]]; then
                sudo systemctl start redis-server
                sudo systemctl enable redis-server
            elif [[ "$OS" == "redhat" ]]; then
                sudo systemctl start redis
                sudo systemctl enable redis
            elif [[ "$OS" == "macos" ]]; then
                brew services start redis
            fi

            sleep 2
            if check_redis_running; then
                echo -e "${GREEN}✓ Redis started successfully!${NC}"
                exit 0
            else
                echo -e "${RED}✗ Failed to start Redis${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}Redis not started. The application will work without caching.${NC}"
            exit 0
        fi
    fi
else
    echo -e "${YELLOW}⚠ Redis is not installed${NC}"
    echo ""
    echo "Redis provides significant performance improvements through caching."
    echo "The application will work without Redis, but with reduced performance."
    echo ""
    echo "Would you like to install Redis? (y/n)"
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Installing Redis..."

        if [[ "$OS" == "debian" ]]; then
            echo "Detected Debian/Ubuntu system"
            sudo apt-get update
            sudo apt-get install -y redis-server
            sudo systemctl start redis-server
            sudo systemctl enable redis-server

        elif [[ "$OS" == "redhat" ]]; then
            echo "Detected RedHat/CentOS system"
            sudo yum install -y redis
            sudo systemctl start redis
            sudo systemctl enable redis

        elif [[ "$OS" == "macos" ]]; then
            echo "Detected macOS"
            if ! command -v brew &> /dev/null; then
                echo -e "${RED}✗ Homebrew is not installed${NC}"
                echo "Please install Homebrew first: https://brew.sh"
                exit 1
            fi
            brew install redis
            brew services start redis

        else
            echo -e "${RED}✗ Unsupported operating system: $OSTYPE${NC}"
            echo "Please install Redis manually:"
            echo "  Ubuntu/Debian: sudo apt-get install redis-server"
            echo "  RedHat/CentOS: sudo yum install redis"
            echo "  macOS: brew install redis"
            exit 1
        fi

        # Wait for Redis to start
        echo "Waiting for Redis to start..."
        sleep 3

        # Verify installation
        if check_redis_running; then
            echo ""
            echo -e "${GREEN}✓ Redis installed and running successfully!${NC}"
            echo ""
            echo "Redis info:"
            redis-cli info server | grep redis_version
            echo ""
            exit 0
        else
            echo -e "${RED}✗ Redis installation failed or not running${NC}"
            exit 1
        fi
    else
        echo ""
        echo -e "${YELLOW}Skipping Redis installation.${NC}"
        echo ""
        echo "The SNMP Monitoring System will work without Redis, but:"
        echo "  - No caching benefits"
        echo "  - Slower dashboard performance"
        echo "  - More database queries"
        echo ""
        echo "You can install Redis later by running this script again."
        exit 0
    fi
fi
