#!/bin/bash

# ==============================================================================
# SNMP Monitoring System - Setup Validator
# ==============================================================================
# This script validates your setup configuration and tests connections
# Run this after setup.sh to ensure everything is configured correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Counters
ERRORS=0
WARNINGS=0
PASSED=0

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}SNMP Monitoring - Setup Validator${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# ==============================================================================
# Helper Functions
# ==============================================================================

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# ==============================================================================
# Check Configuration Files
# ==============================================================================

echo -e "${BLUE}Checking Configuration Files...${NC}"
echo ""

# Check backend .env
if [ -f "$BACKEND_DIR/.env" ]; then
    check_pass "Backend .env file exists"

    # Source the .env file
    export $(cat "$BACKEND_DIR/.env" | grep -v '^#' | xargs)

    # Check required variables
    REQUIRED_VARS=(
        "SNMP_COMMUNITY"
        "DISCOVERY_NETWORK"
        "DATABASE_URL"
        "SENDER_EMAIL"
        "SENDER_PASSWORD"
        "JWT_SECRET_KEY"
        "FRONTEND_URL"
    )

    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            check_fail "$var is not set in .env"
        else
            check_pass "$var is configured"
        fi
    done

    # Check if JWT secret is still default
    if [ "$JWT_SECRET_KEY" = "CHANGE-THIS-IN-PRODUCTION-USE-SETUP-SCRIPT" ]; then
        check_warn "JWT_SECRET_KEY is still the default value - should be changed!"
    fi

    # Validate DISCOVERY_NETWORK format
    if [[ $DISCOVERY_NETWORK =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[0-9]{1,2}$ ]]; then
        check_pass "DISCOVERY_NETWORK format is valid: $DISCOVERY_NETWORK"
    else
        check_fail "DISCOVERY_NETWORK format is invalid: $DISCOVERY_NETWORK"
    fi

    # Validate email format
    if [[ $SENDER_EMAIL =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        check_pass "SENDER_EMAIL format is valid"
    else
        check_fail "SENDER_EMAIL format is invalid"
    fi

else
    check_fail "Backend .env file not found"
    check_warn "Run ./setup.sh to create configuration"
fi

echo ""

# Check frontend .env.local
if [ -f "$FRONTEND_DIR/.env.local" ]; then
    check_pass "Frontend .env.local file exists"
else
    check_fail "Frontend .env.local file not found"
fi

echo ""

# ==============================================================================
# Check Python Environment
# ==============================================================================

echo -e "${BLUE}Checking Python Environment...${NC}"
echo ""

if [ -d "$BACKEND_DIR/venv" ]; then
    check_pass "Python virtual environment exists"

    # Check if dependencies are installed
    if [ -f "$BACKEND_DIR/venv/bin/python" ]; then
        cd "$BACKEND_DIR"
        source venv/bin/activate

        # Check key packages
        KEY_PACKAGES=("fastapi" "uvicorn" "sqlalchemy" "pysnmp" "redis")

        for package in "${KEY_PACKAGES[@]}"; do
            if python -c "import $package" 2>/dev/null; then
                check_pass "Python package '$package' is installed"
            else
                check_fail "Python package '$package' is NOT installed"
            fi
        done

        deactivate
        cd "$PROJECT_DIR"
    fi
else
    check_fail "Python virtual environment not found"
    check_warn "Run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

echo ""

# ==============================================================================
# Check Node.js Environment
# ==============================================================================

echo -e "${BLUE}Checking Node.js Environment...${NC}"
echo ""

if [ -d "$FRONTEND_DIR/node_modules" ]; then
    check_pass "Node.js packages are installed"

    # Check for key packages
    if [ -d "$FRONTEND_DIR/node_modules/next" ]; then
        check_pass "Next.js is installed"
    else
        check_fail "Next.js is NOT installed"
    fi

    if [ -d "$FRONTEND_DIR/node_modules/react" ]; then
        check_pass "React is installed"
    else
        check_fail "React is NOT installed"
    fi
else
    check_fail "Node.js packages not installed"
    check_warn "Run: cd frontend && npm install --legacy-peer-deps"
fi

echo ""

# ==============================================================================
# Test Database Connection
# ==============================================================================

echo -e "${BLUE}Testing Database...${NC}"
echo ""

if [ -f "$BACKEND_DIR/.env" ]; then
    cd "$BACKEND_DIR"
    source venv/bin/activate 2>/dev/null || true

    # Create test script
    cat > test_db.py << 'EOF'
import sys
try:
    from sqlalchemy import create_engine
    from app.core.database import engine, SessionLocal
    from app.core.models import User

    # Test connection
    db = SessionLocal()
    user_count = db.query(User).count()
    db.close()

    print(f"Database connection successful")
    print(f"User count: {user_count}")

    if user_count == 0:
        print("WARNING: No users found in database")
        sys.exit(2)
    sys.exit(0)
except Exception as e:
    print(f"Database connection failed: {e}")
    sys.exit(1)
EOF

    if python test_db.py 2>&1 | grep -q "Database connection successful"; then
        check_pass "Database connection successful"

        user_count=$(python test_db.py 2>&1 | grep "User count:" | awk '{print $3}')
        if [ "$user_count" -gt 0 ]; then
            check_pass "Database has $user_count user(s)"
        else
            check_warn "No users found - run setup.sh or scripts/setup_admin.py"
        fi
    else
        check_fail "Database connection failed"
    fi

    rm test_db.py
    deactivate 2>/dev/null || true
    cd "$PROJECT_DIR"
else
    check_warn "Cannot test database - .env not found"
fi

echo ""

# ==============================================================================
# Test Redis Connection
# ==============================================================================

echo -e "${BLUE}Testing Redis Connection...${NC}"
echo ""

if [ "$CACHE_ENABLED" = "true" ]; then
    # Try to connect to Redis
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>&1 | grep -q "PONG"; then
            check_pass "Redis connection successful ($REDIS_HOST:$REDIS_PORT)"
        else
            check_fail "Cannot connect to Redis at $REDIS_HOST:$REDIS_PORT"
            check_warn "Make sure Redis is running: sudo systemctl start redis"
        fi
    else
        check_warn "redis-cli not installed, cannot test Redis connection"
    fi
else
    check_pass "Redis caching is disabled (no connection test needed)"
fi

echo ""

# ==============================================================================
# Test SMTP Connection
# ==============================================================================

echo -e "${BLUE}Testing Email Configuration...${NC}"
echo ""

if [ -n "$SENDER_EMAIL" ] && [ -n "$SENDER_PASSWORD" ]; then
    check_pass "Email credentials are configured"

    if [ "$SMTP_SERVER" = "smtp.gmail.com" ]; then
        check_pass "Using Gmail SMTP server"

        if [[ ${#SENDER_PASSWORD} -eq 16 ]] && [[ ! "$SENDER_PASSWORD" =~ [^a-zA-Z] ]]; then
            check_pass "Password appears to be a Gmail app password (16 chars)"
        else
            check_warn "Password doesn't look like a Gmail app password"
            check_warn "Gmail requires app-specific passwords: https://myaccount.google.com/apppasswords"
        fi
    fi

    # Offer to send test email
    echo ""
    if [ -f "$SCRIPT_DIR/test-email.py" ]; then
        echo -e "${BLUE}Want to send a test email?${NC}"
        echo "Run: python scripts/test-email.py"
    fi
else
    check_fail "Email credentials not configured"
fi

echo ""

# ==============================================================================
# Check Port Availability
# ==============================================================================

echo -e "${BLUE}Checking Port Availability...${NC}"
echo ""

if command -v lsof &> /dev/null; then
    # Check backend port (8000)
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        check_warn "Port 8000 is in use (backend may already be running)"
    else
        check_pass "Port 8000 is available (for backend)"
    fi

    # Check frontend port (3000)
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        check_warn "Port 3000 is in use (frontend may already be running)"
    else
        check_pass "Port 3000 is available (for frontend)"
    fi

    # Check Redis port (6379) if enabled
    if [ "$CACHE_ENABLED" = "true" ]; then
        if lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            check_pass "Port 6379 is in use (Redis is running)"
        else
            check_warn "Port 6379 is not in use (Redis may not be running)"
        fi
    fi
else
    check_warn "lsof not available, skipping port checks"
fi

echo ""

# ==============================================================================
# Check File Permissions
# ==============================================================================

echo -e "${BLUE}Checking File Permissions...${NC}"
echo ""

# Check if scripts are executable
SCRIPTS=("setup.sh" "start-dev.sh" "stop-dev.sh" "scripts/check-dependencies.sh" "scripts/validate-setup.sh")

for script in "${SCRIPTS[@]}"; do
    script_path="$PROJECT_DIR/$script"
    if [ -f "$script_path" ]; then
        if [ -x "$script_path" ]; then
            check_pass "$script is executable"
        else
            check_warn "$script is not executable"
            echo "  Fix with: chmod +x $script"
        fi
    fi
done

echo ""

# ==============================================================================
# Summary
# ==============================================================================

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

TOTAL=$((PASSED + ERRORS + WARNINGS))

echo -e "${GREEN}Passed:   $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Errors:   $ERRORS${NC}"
echo -e "Total:    $TOTAL"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Your setup is ready.${NC}"
    echo ""
    echo "Start the services with:"
    echo -e "  ${BLUE}make dev${NC}  (if you have Make)"
    echo "  OR"
    echo -e "  ${BLUE}./start-dev.sh${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Setup is functional but has some warnings.${NC}"
    echo "Review the warnings above and fix if needed."
    echo ""
    echo "You can still start the services:"
    echo -e "  ${BLUE}make dev${NC}  or  ${BLUE}./start-dev.sh${NC}"
    exit 0
else
    echo -e "${RED}✗ Setup has errors that need to be fixed.${NC}"
    echo ""
    echo "Common fixes:"
    echo -e "  - Run ${BLUE}./setup.sh${NC} to configure everything interactively"
    echo -e "  - Install missing dependencies: ${BLUE}./scripts/check-dependencies.sh${NC}"
    echo -e "  - Check .env file in backend directory"
    exit 1
fi
