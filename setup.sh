#!/bin/bash

# ==============================================================================
# SNMP Monitoring System - Interactive Setup Wizard
# ==============================================================================
# This script will interactively configure your SNMP monitoring system
# It handles both development and production setups
#
# Usage:
#   ./setup.sh              # Interactive development setup
#   ./setup.sh --production # Production setup with stricter validation
#   ./setup.sh --help       # Show help message

set -e  # Exit on error

# ==============================================================================
# Configuration
# ==============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
SCRIPTS_DIR="$SCRIPT_DIR/scripts"

# Default values
IS_PRODUCTION=false
AUTO_START=false
SKIP_DEPS_CHECK=false

# ==============================================================================
# Helper Functions
# ==============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}===============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===============================================${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}→${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

prompt_input() {
    local prompt=$1
    local default=$2
    local var_name=$3
    local is_secret=${4:-false}

    if [ -n "$default" ]; then
        prompt_text="$prompt [$default]: "
    else
        prompt_text="$prompt: "
    fi

    if [ "$is_secret" = true ]; then
        read -s -p "$(echo -e ${CYAN}${prompt_text}${NC})" value
        echo "" # New line after secret input
    else
        read -p "$(echo -e ${CYAN}${prompt_text}${NC})" value
    fi

    if [ -z "$value" ]; then
        value=$default
    fi

    eval $var_name="'$value'"
}

prompt_yes_no() {
    local prompt=$1
    local default=$2

    if [ "$default" = "y" ]; then
        prompt_text="$prompt [Y/n]: "
    else
        prompt_text="$prompt [y/N]: "
    fi

    read -p "$(echo -e ${CYAN}${prompt_text}${NC})" response

    if [ -z "$response" ]; then
        response=$default
    fi

    if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

validate_ip() {
    local ip=$1
    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        return 0
    else
        return 1
    fi
}

validate_cidr() {
    local cidr=$1
    if [[ $cidr =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[0-9]{1,2}$ ]]; then
        return 0
    else
        return 1
    fi
}

validate_email() {
    local email=$1
    if [[ $email =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

validate_port() {
    local port=$1
    if [[ $port =~ ^[0-9]+$ ]] && [ $port -ge 1 ] && [ $port -le 65535 ]; then
        return 0
    else
        return 1
    fi
}

# ==============================================================================
# Parse Arguments
# ==============================================================================

show_help() {
    echo "SNMP Monitoring System - Setup Wizard"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --production     Run production setup (stricter validation)"
    echo "  --skip-deps      Skip dependency checking"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Interactive development setup"
    echo "  $0 --production       # Production setup"
    echo ""
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --production)
            IS_PRODUCTION=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS_CHECK=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# ==============================================================================
# Main Setup Flow
# ==============================================================================

print_header "SNMP Monitoring System - Setup Wizard"

if [ "$IS_PRODUCTION" = true ]; then
    print_warning "Running in PRODUCTION mode"
else
    echo -e "Running in ${CYAN}DEVELOPMENT${NC} mode"
fi

echo ""

# Step 1: Check Dependencies
if [ "$SKIP_DEPS_CHECK" = false ]; then
    print_step "Checking system dependencies..."

    if [ -f "$SCRIPTS_DIR/check-dependencies.sh" ]; then
        bash "$SCRIPTS_DIR/check-dependencies.sh" || {
            print_error "Dependency check failed. Please fix the issues above."
            echo ""
            echo "Run with --skip-deps to bypass this check (not recommended)"
            exit 1
        }
    else
        print_warning "Dependency checker not found, skipping..."
    fi
    echo ""
fi

# Step 2: Interactive Configuration
print_header "Configuration"

print_step "Let's configure your SNMP monitoring system..."
echo ""

# Environment type confirmation
if [ "$IS_PRODUCTION" = true ]; then
    ENVIRONMENT="production"
    print_step "Environment: ${RED}PRODUCTION${NC}"
else
    ENVIRONMENT="development"
    print_step "Environment: ${CYAN}DEVELOPMENT${NC}"
fi
echo ""

# Network Discovery Configuration
print_step "Network Discovery Configuration"
echo ""

prompt_input "Enter network range for device discovery (CIDR format, e.g., 192.168.1.0/24)" "192.168.1.0/24" DISCOVERY_NETWORK

while ! validate_cidr "$DISCOVERY_NETWORK"; do
    print_error "Invalid CIDR format. Please use format: 192.168.1.0/24"
    prompt_input "Enter network range for device discovery (CIDR)" "192.168.1.0/24" DISCOVERY_NETWORK
done

print_success "Network discovery will scan: $DISCOVERY_NETWORK"
echo ""

# SNMP Configuration
print_step "SNMP Configuration"
echo ""

prompt_input "SNMP community string" "public" SNMP_COMMUNITY
prompt_input "SNMP timeout (seconds)" "10" SNMP_TIMEOUT
prompt_input "SNMP retries" "3" SNMP_RETRIES
echo ""

# Email Configuration
print_step "Email Configuration (for alerts)"
echo ""

print_warning "For Gmail, you need to create an App Password:"
echo "  1. Go to: https://myaccount.google.com/apppasswords"
echo "  2. Generate an app password for 'Mail'"
echo "  3. Use that password below (not your regular Gmail password)"
echo ""

prompt_input "SMTP server" "smtp.gmail.com" SMTP_SERVER
prompt_input "SMTP port" "587" SMTP_PORT

while ! validate_port "$SMTP_PORT"; do
    print_error "Invalid port number"
    prompt_input "SMTP port" "587" SMTP_PORT
done

prompt_input "Sender email address" "" SENDER_EMAIL

while ! validate_email "$SENDER_EMAIL"; do
    print_error "Invalid email format"
    prompt_input "Sender email address" "" SENDER_EMAIL
done

prompt_input "Sender email password (app-specific password)" "" SENDER_PASSWORD true
echo ""

# Redis Configuration
print_step "Redis Cache Configuration"
echo ""

print_info "Redis provides significant performance improvements through caching."
print_info "The application will work without Redis, but with reduced performance."
echo ""

if prompt_yes_no "Enable Redis caching? (improves performance)" "y"; then
    CACHE_ENABLED="true"

    # Check if Redis is installed and running
    print_step "Checking Redis installation..."

    if command -v redis-server &> /dev/null; then
        print_success "Redis is installed"
        REDIS_VERSION=$(redis-server --version | awk '{print $3}')
        print_info "Version: $REDIS_VERSION"

        # Check if Redis is running
        if redis-cli -h localhost -p 6379 ping &> /dev/null 2>&1; then
            print_success "Redis is running"
        else
            print_warning "Redis is installed but not running"
            echo ""
            if prompt_yes_no "Would you like to start Redis now?" "y"; then
                print_step "Starting Redis..."

                # Detect OS and start Redis
                if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                    if [ -f /etc/debian_version ]; then
                        sudo systemctl start redis-server 2>/dev/null || sudo service redis-server start 2>/dev/null
                        sudo systemctl enable redis-server 2>/dev/null || true
                    elif [ -f /etc/redhat-release ]; then
                        sudo systemctl start redis 2>/dev/null || sudo service redis start 2>/dev/null
                        sudo systemctl enable redis 2>/dev/null || true
                    fi
                elif [[ "$OSTYPE" == "darwin"* ]]; then
                    brew services start redis 2>/dev/null || redis-server --daemonize yes
                fi

                sleep 2

                if redis-cli ping &> /dev/null 2>&1; then
                    print_success "Redis started successfully"
                else
                    print_warning "Could not start Redis automatically"
                    print_info "You can start it manually later with:"
                    print_info "  sudo systemctl start redis-server  (Linux)"
                    print_info "  brew services start redis  (macOS)"
                fi
            fi
        fi
    else
        print_warning "Redis is not installed"
        echo ""
        print_info "Redis provides:"
        print_info "  - Faster dashboard performance"
        print_info "  - Reduced database queries"
        print_info "  - Better scalability"
        echo ""

        if prompt_yes_no "Would you like to install Redis now?" "y"; then
            print_step "Installing Redis..."

            # Detect OS and install
            if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                if [ -f /etc/debian_version ]; then
                    print_info "Detected Debian/Ubuntu system"
                    sudo apt-get update -qq
                    sudo apt-get install -y redis-server
                    sudo systemctl start redis-server
                    sudo systemctl enable redis-server
                elif [ -f /etc/redhat-release ]; then
                    print_info "Detected RedHat/CentOS system"
                    sudo yum install -y redis
                    sudo systemctl start redis
                    sudo systemctl enable redis
                else
                    print_error "Unsupported Linux distribution"
                    print_info "Please install Redis manually:"
                    print_info "  Ubuntu/Debian: sudo apt-get install redis-server"
                    print_info "  RedHat/CentOS: sudo yum install redis"
                    CACHE_ENABLED="false"
                fi
            elif [[ "$OSTYPE" == "darwin"* ]]; then
                print_info "Detected macOS"
                if command -v brew &> /dev/null; then
                    brew install redis
                    brew services start redis
                else
                    print_error "Homebrew is not installed"
                    print_info "Install Homebrew first: https://brew.sh"
                    print_info "Then run: brew install redis"
                    CACHE_ENABLED="false"
                fi
            else
                print_error "Unsupported operating system: $OSTYPE"
                print_info "Please install Redis manually"
                CACHE_ENABLED="false"
            fi

            if [ "$CACHE_ENABLED" = "true" ]; then
                sleep 3
                if redis-cli ping &> /dev/null 2>&1; then
                    print_success "Redis installed and running successfully!"
                    REDIS_VERSION=$(redis-server --version | awk '{print $3}')
                    print_info "Version: $REDIS_VERSION"
                else
                    print_warning "Redis installation may have failed"
                    print_info "You can verify later with: redis-cli ping"
                fi
            fi
        else
            print_step "Skipping Redis installation"
            print_warning "Continuing without Redis - caching will be disabled"
            CACHE_ENABLED="false"
        fi
    fi

    if [ "$CACHE_ENABLED" = "true" ]; then
        prompt_input "Redis host" "localhost" REDIS_HOST
        prompt_input "Redis port" "6379" REDIS_PORT
        prompt_input "Redis database number (0-15)" "0" REDIS_DB
        print_success "Redis caching enabled"
    else
        REDIS_HOST="localhost"
        REDIS_PORT="6379"
        REDIS_DB="0"
    fi
else
    CACHE_ENABLED="false"
    REDIS_HOST="localhost"
    REDIS_PORT="6379"
    REDIS_DB="0"
    print_step "Redis caching disabled"
fi
echo ""

# Application Settings
print_step "Application Settings"
echo ""

prompt_input "Device polling interval (seconds)" "60" POLLING_INTERVAL
prompt_input "Discovery concurrency (max parallel scans)" "20" DISCOVERY_CONCURRENCY
prompt_input "Polling concurrency (max parallel polls)" "20" POLLING_CONCURRENCY
echo ""

# Frontend URL
print_step "Frontend Configuration"
echo ""

if [ "$IS_PRODUCTION" = true ]; then
    prompt_input "Frontend URL (e.g., https://your-domain.com)" "http://localhost:3000" FRONTEND_URL
else
    FRONTEND_URL="http://localhost:3000"
    print_step "Frontend URL: $FRONTEND_URL"
fi
echo ""

# Security - JWT Secret
print_step "Security Configuration"
echo ""

print_step "Generating secure JWT secret key..."
JWT_SECRET_KEY=$(openssl rand -hex 32)
print_success "JWT secret generated"
echo ""

# Admin User Configuration
print_step "Admin User Configuration"
echo ""

prompt_input "Admin username" "admin" ADMIN_USERNAME

while [ ${#ADMIN_USERNAME} -lt 3 ]; do
    print_error "Username must be at least 3 characters"
    prompt_input "Admin username" "admin" ADMIN_USERNAME
done

prompt_input "Admin email" "$SENDER_EMAIL" ADMIN_EMAIL

while ! validate_email "$ADMIN_EMAIL"; do
    print_error "Invalid email format"
    prompt_input "Admin email" "$SENDER_EMAIL" ADMIN_EMAIL
done

prompt_input "Admin password" "" ADMIN_PASSWORD true
echo ""

while [ ${#ADMIN_PASSWORD} -lt 6 ]; do
    print_error "Password must be at least 6 characters"
    prompt_input "Admin password" "" ADMIN_PASSWORD true
    echo ""
done

prompt_input "Confirm admin password" "" ADMIN_PASSWORD_CONFIRM true
echo ""

while [ "$ADMIN_PASSWORD" != "$ADMIN_PASSWORD_CONFIRM" ]; do
    print_error "Passwords do not match"
    prompt_input "Admin password" "" ADMIN_PASSWORD true
    echo ""
    prompt_input "Confirm admin password" "" ADMIN_PASSWORD_CONFIRM true
    echo ""
done

print_success "Admin credentials configured"
echo ""

# ==============================================================================
# Step 3: Create Configuration Files
# ==============================================================================

print_header "Creating Configuration Files"

# Create backend .env
print_step "Creating backend/.env..."

cat > "$BACKEND_DIR/.env" << EOF
# SNMP Monitoring System - Backend Environment Variables
# Generated by setup.sh on $(date)
# Environment: $ENVIRONMENT

# ============================================================================
# SNMP Configuration
# ============================================================================
SNMP_COMMUNITY=$SNMP_COMMUNITY
SNMP_TIMEOUT=$SNMP_TIMEOUT
SNMP_RETRIES=$SNMP_RETRIES

# ============================================================================
# Network Discovery
# ============================================================================
DISCOVERY_NETWORK=$DISCOVERY_NETWORK

# ============================================================================
# Database
# ============================================================================
DATABASE_URL=sqlite:///./monitoring.db

# ============================================================================
# Application Settings
# ============================================================================
POLLING_INTERVAL=$POLLING_INTERVAL
DISCOVERY_CONCURRENCY=$DISCOVERY_CONCURRENCY
POLLING_CONCURRENCY=$POLLING_CONCURRENCY

# ============================================================================
# Email Settings
# ============================================================================
SMTP_SERVER=$SMTP_SERVER
SMTP_PORT=$SMTP_PORT
SENDER_EMAIL=$SENDER_EMAIL
SENDER_PASSWORD=$SENDER_PASSWORD

# ============================================================================
# Redis Cache Configuration
# ============================================================================
REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT
REDIS_DB=$REDIS_DB
CACHE_ENABLED=$CACHE_ENABLED

# ============================================================================
# Security / JWT Configuration
# ============================================================================
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24

# ============================================================================
# Frontend Configuration
# ============================================================================
FRONTEND_URL=$FRONTEND_URL

# ============================================================================
# Logging
# ============================================================================
LOG_LEVEL=INFO

# ============================================================================
# Environment
# ============================================================================
ENVIRONMENT=$ENVIRONMENT
DEBUG=false
EOF

print_success "Backend .env created"

# Create frontend .env.local
print_step "Creating frontend/.env.local..."

cat > "$FRONTEND_DIR/.env.local" << EOF
# SNMP Monitoring System - Frontend Environment Variables
# Generated by setup.sh on $(date)

NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

print_success "Frontend .env.local created"
echo ""

# ==============================================================================
# Step 4: Install Dependencies
# ==============================================================================

print_header "Installing Dependencies"

# Backend dependencies
print_step "Setting up Python virtual environment..."
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_step "Virtual environment already exists"
fi

print_step "Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
print_success "Python packages installed"
deactivate

cd "$SCRIPT_DIR"
echo ""

# Frontend dependencies
print_step "Installing Node.js packages..."
cd "$FRONTEND_DIR"

if prompt_yes_no "Install frontend dependencies now? (may take a few minutes)" "y"; then
    npm install --legacy-peer-deps
    print_success "Node.js packages installed"
else
    print_warning "Skipped frontend dependency installation"
    print_step "You can install later with: cd frontend && npm install --legacy-peer-deps"
fi

cd "$SCRIPT_DIR"
echo ""

# ==============================================================================
# Step 5: Initialize Database and Create Admin User
# ==============================================================================

print_header "Database Setup"

print_step "The database will be initialized when the backend starts for the first time"
print_step "Creating admin user configuration..."

# Create a temporary Python script to create admin user
cat > "$BACKEND_DIR/temp_create_admin.py" << EOF
import sys
sys.path.insert(0, '$BACKEND_DIR')

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core import models
from app.core.security import get_password_hash

# Create all tables
models.Base.metadata.create_all(engine)

db: Session = SessionLocal()

try:
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.username == "$ADMIN_USERNAME").first()

    if existing_user:
        print("Admin user already exists, skipping creation")
    else:
        # Create admin user
        hashed_password = get_password_hash("$ADMIN_PASSWORD")
        user = models.User(
            username="$ADMIN_USERNAME",
            email="$ADMIN_EMAIL",
            hashed_password=hashed_password,
            is_active=True,
            is_admin=True
        )
        db.add(user)
        db.commit()
        print("Admin user created successfully")

    # Add admin email to alert recipients if not exists
    existing_recipient = db.query(models.AlertRecipient).filter(
        models.AlertRecipient.email == "$ADMIN_EMAIL"
    ).first()

    if not existing_recipient:
        recipient = models.AlertRecipient(email="$ADMIN_EMAIL", is_active=True)
        db.add(recipient)
        db.commit()
        print("Admin email added to alert recipients")
    else:
        print("Admin email already in alert recipients")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
EOF

# Run the admin creation script
cd "$BACKEND_DIR"
source venv/bin/activate
python temp_create_admin.py
rm temp_create_admin.py
deactivate
cd "$SCRIPT_DIR"

print_success "Database initialized and admin user created"
echo ""

# ==============================================================================
# Step 6: Final Steps
# ==============================================================================

print_header "Setup Complete!"

echo -e "${GREEN}✓${NC} Configuration files created"
echo -e "${GREEN}✓${NC} Dependencies installed"
echo -e "${GREEN}✓${NC} Database initialized"
echo -e "${GREEN}✓${NC} Admin user created"
echo ""

print_header "Next Steps"

echo "1. Start the backend:"
echo -e "   ${BLUE}cd backend${NC}"
echo -e "   ${BLUE}source venv/bin/activate${NC}"
echo -e "   ${BLUE}uvicorn main:app --reload${NC}"
echo ""
echo "2. Start the frontend (in a new terminal):"
echo -e "   ${BLUE}cd frontend${NC}"
echo -e "   ${BLUE}npm run dev${NC}"
echo ""
echo "3. Access the application:"
echo -e "   Frontend: ${CYAN}http://localhost:3000${NC}"
echo -e "   Backend API: ${CYAN}http://localhost:8000${NC}"
echo -e "   API Docs: ${CYAN}http://localhost:8000/docs${NC}"
echo ""
echo "4. Login with your admin credentials:"
echo -e "   Username: ${CYAN}$ADMIN_USERNAME${NC}"
echo -e "   Email: ${CYAN}$ADMIN_EMAIL${NC}"
echo ""

if [ -f "$SCRIPT_DIR/Makefile" ]; then
    echo "Or use the Makefile:"
    echo -e "   ${BLUE}make dev${NC}    # Start both backend and frontend"
    echo -e "   ${BLUE}make stop${NC}   # Stop all services"
    echo -e "   ${BLUE}make logs${NC}   # View logs"
    echo ""
fi

if [ "$CACHE_ENABLED" = "true" ]; then
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping &> /dev/null 2>&1; then
        print_success "Redis is running and ready!"
    else
        print_warning "Redis caching is enabled but Redis may not be running"
        print_info "Start Redis with:"
        echo -e "   ${BLUE}sudo systemctl start redis-server${NC}  (Linux)"
        echo -e "   ${BLUE}brew services start redis${NC}  (macOS)"
        print_info "Or check status with: redis-cli ping"
    fi
    echo ""
fi

print_success "Setup completed successfully!"
echo ""
echo -e "For troubleshooting, run: ${BLUE}./scripts/validate-setup.sh${NC}"
echo ""

# Ask if user wants to start services
if prompt_yes_no "Would you like to start the services now?" "n"; then
    print_step "Starting services..."

    if [ -f "$SCRIPT_DIR/start-dev.sh" ]; then
        bash "$SCRIPT_DIR/start-dev.sh"
    else
        print_warning "start-dev.sh not found. Please start services manually."
    fi
fi
