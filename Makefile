# ==============================================================================
# SNMP Monitoring System - Makefile
# ==============================================================================
# Common commands for development and deployment
#
# Usage:
#   make setup      - Run interactive setup wizard
#   make dev        - Start development servers
#   make stop       - Stop all services
#   make validate   - Validate setup configuration
#   make health     - Check system health
#   make test-email - Send test email
#   make logs       - View logs
#   make clean      - Clean temporary files
#   make reset      - Reset to clean state

.PHONY: help setup dev stop validate health test-email logs clean reset install-backend install-frontend check-deps

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

# Directories
BACKEND_DIR := backend
FRONTEND_DIR := frontend
SCRIPTS_DIR := scripts

help: ## Show this help message
	@echo "$(BLUE)SNMP Monitoring System - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ==============================================================================
# Setup Commands
# ==============================================================================

setup: ## Run interactive setup wizard
	@echo "$(BLUE)Running setup wizard...$(NC)"
	@./setup.sh

check-deps: ## Check system dependencies
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@./$(SCRIPTS_DIR)/check-dependencies.sh

validate: ## Validate setup configuration
	@echo "$(BLUE)Validating setup...$(NC)"
	@./$(SCRIPTS_DIR)/validate-setup.sh

# ==============================================================================
# Installation Commands
# ==============================================================================

install-backend: ## Install backend dependencies
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	@cd $(BACKEND_DIR) && \
		python3 -m venv venv && \
		. venv/bin/activate && \
		pip install --upgrade pip && \
		pip install -r requirements.txt
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

install-frontend: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	@cd $(FRONTEND_DIR) && npm install --legacy-peer-deps
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

install: install-backend install-frontend ## Install all dependencies

# ==============================================================================
# Development Commands
# ==============================================================================

dev: ## Start development servers (backend + frontend)
	@echo "$(BLUE)Starting development servers...$(NC)"
	@./start-dev.sh

stop: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	@./stop-dev.sh || true
	@echo "$(GREEN)✓ Services stopped$(NC)"

restart: stop dev ## Restart all services

# ==============================================================================
# Backend Commands
# ==============================================================================

backend: ## Start backend only
	@echo "$(BLUE)Starting backend...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		uvicorn main:app --reload --host 0.0.0.0 --port 8000

backend-prod: ## Start backend in production mode
	@echo "$(BLUE)Starting backend (production)...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# ==============================================================================
# Frontend Commands
# ==============================================================================

frontend: ## Start frontend only
	@echo "$(BLUE)Starting frontend...$(NC)"
	@cd $(FRONTEND_DIR) && npm run dev

frontend-build: ## Build frontend for production
	@echo "$(BLUE)Building frontend...$(NC)"
	@cd $(FRONTEND_DIR) && npm run build
	@echo "$(GREEN)✓ Frontend built$(NC)"

frontend-prod: frontend-build ## Start frontend in production mode
	@echo "$(BLUE)Starting frontend (production)...$(NC)"
	@cd $(FRONTEND_DIR) && npm start

# ==============================================================================
# Health & Monitoring Commands
# ==============================================================================

health: ## Check system health
	@echo "$(BLUE)Checking system health...$(NC)"
	@curl -s http://localhost:8000/health | python3 -m json.tool || \
		echo "$(YELLOW)⚠ Backend is not running$(NC)"

ping: ## Ping the API
	@curl -s http://localhost:8000/ping | python3 -m json.tool || \
		echo "$(YELLOW)⚠ Backend is not running$(NC)"

test-email: ## Send test email
	@echo "$(BLUE)Sending test email...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		python ../$(SCRIPTS_DIR)/test-email.py

# ==============================================================================
# Log Commands
# ==============================================================================

logs: ## View all logs
	@echo "$(BLUE)Viewing logs...$(NC)"
	@if [ -d "logs" ]; then \
		tail -f logs/*.log; \
	else \
		echo "$(YELLOW)No logs directory found$(NC)"; \
	fi

logs-backend: ## View backend logs only
	@echo "$(BLUE)Viewing backend logs...$(NC)"
	@if [ -f "logs/backend.log" ]; then \
		tail -f logs/backend.log; \
	else \
		echo "$(YELLOW)Backend log not found$(NC)"; \
	fi

logs-frontend: ## View frontend logs only
	@echo "$(BLUE)Viewing frontend logs...$(NC)"
	@if [ -f "logs/frontend.log" ]; then \
		tail -f logs/frontend.log; \
	else \
		echo "$(YELLOW)Frontend log not found$(NC)"; \
	fi

# ==============================================================================
# Database Commands
# ==============================================================================

db-init: ## Initialize database
	@echo "$(BLUE)Initializing database...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		python -c "from app.core.database import engine; from app.core import models; models.Base.metadata.create_all(engine)"
	@echo "$(GREEN)✓ Database initialized$(NC)"

create-admin: ## Create admin user
	@echo "$(BLUE)Creating admin user...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		python ../$(SCRIPTS_DIR)/setup_admin.py

# ==============================================================================
# Redis Commands
# ==============================================================================

redis-start: ## Start Redis server
	@echo "$(BLUE)Starting Redis...$(NC)"
	@sudo systemctl start redis-server || redis-server --daemonize yes
	@echo "$(GREEN)✓ Redis started$(NC)"

redis-stop: ## Stop Redis server
	@echo "$(BLUE)Stopping Redis...$(NC)"
	@sudo systemctl stop redis-server || redis-cli shutdown
	@echo "$(GREEN)✓ Redis stopped$(NC)"

redis-status: ## Check Redis status
	@redis-cli ping && echo "$(GREEN)✓ Redis is running$(NC)" || \
		echo "$(YELLOW)⚠ Redis is not running$(NC)"

redis-cli: ## Open Redis CLI
	@redis-cli

# ==============================================================================
# Cleanup Commands
# ==============================================================================

clean: ## Clean temporary files and caches
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@cd $(FRONTEND_DIR) && rm -rf .next 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned temporary files$(NC)"

clean-logs: ## Clean log files
	@echo "$(BLUE)Cleaning logs...$(NC)"
	@rm -rf logs/*.log 2>/dev/null || true
	@echo "$(GREEN)✓ Logs cleaned$(NC)"

clean-db: ## Remove database (WARNING: deletes all data)
	@echo "$(YELLOW)⚠ WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -f $(BACKEND_DIR)/monitoring.db; \
		echo "$(GREEN)✓ Database removed$(NC)"; \
	else \
		echo "Cancelled"; \
	fi

reset: clean clean-logs ## Reset to clean state (keeps database)
	@echo "$(GREEN)✓ System reset to clean state$(NC)"

reset-all: clean clean-logs clean-db ## Complete reset (WARNING: deletes database)
	@echo "$(GREEN)✓ Complete reset performed$(NC)"

# ==============================================================================
# Development Utilities
# ==============================================================================

format-backend: ## Format backend code with black
	@echo "$(BLUE)Formatting backend code...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		black . 2>/dev/null || echo "$(YELLOW)black not installed$(NC)"

lint-backend: ## Lint backend code with flake8
	@echo "$(BLUE)Linting backend code...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		flake8 . 2>/dev/null || echo "$(YELLOW)flake8 not installed$(NC)"

format-frontend: ## Format frontend code with prettier
	@echo "$(BLUE)Formatting frontend code...$(NC)"
	@cd $(FRONTEND_DIR) && \
		npx prettier --write . 2>/dev/null || echo "$(YELLOW)prettier not installed$(NC)"

# ==============================================================================
# Testing Commands
# ==============================================================================

test: ## Run all backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		pytest
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-verbose: ## Run tests with verbose output
	@echo "$(BLUE)Running tests (verbose)...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		pytest -vv

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		pytest --cov=app --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report generated in backend/htmlcov/$(NC)"

test-device: ## Run device endpoint tests only
	@echo "$(BLUE)Running device tests...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		pytest -m device

test-query: ## Run query endpoint tests only
	@echo "$(BLUE)Running query tests...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		pytest -m query

test-alert: ## Run alert workflow tests only
	@echo "$(BLUE)Running alert tests...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		pytest -m alert

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		pytest -m integration

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	@cd $(BACKEND_DIR) && \
		. venv/bin/activate && \
		pytest-watch

# ==============================================================================
# Status & Info Commands
# ==============================================================================

status: ## Show system status
	@echo "$(BLUE)System Status:$(NC)"
	@echo ""
	@echo "Backend (port 8000):"
	@lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 && \
		echo "  $(GREEN)✓ Running$(NC)" || echo "  $(YELLOW)⚠ Not running$(NC)"
	@echo ""
	@echo "Frontend (port 3000):"
	@lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 && \
		echo "  $(GREEN)✓ Running$(NC)" || echo "  $(YELLOW)⚠ Not running$(NC)"
	@echo ""
	@echo "Redis (port 6379):"
	@lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null 2>&1 && \
		echo "  $(GREEN)✓ Running$(NC)" || echo "  $(YELLOW)⚠ Not running$(NC)"
	@echo ""

info: ## Show configuration info
	@echo "$(BLUE)Configuration Information:$(NC)"
	@echo ""
	@if [ -f $(BACKEND_DIR)/.env ]; then \
		echo "Backend .env:"; \
		grep -E "^(ENVIRONMENT|DISCOVERY_NETWORK|CACHE_ENABLED|FRONTEND_URL)=" $(BACKEND_DIR)/.env | sed 's/^/  /'; \
	else \
		echo "  $(YELLOW)Backend .env not found$(NC)"; \
	fi
	@echo ""
	@if [ -f $(FRONTEND_DIR)/.env.local ]; then \
		echo "Frontend .env.local:"; \
		cat $(FRONTEND_DIR)/.env.local | sed 's/^/  /'; \
	else \
		echo "  $(YELLOW)Frontend .env.local not found$(NC)"; \
	fi
	@echo ""

# ==============================================================================
# Quick Start
# ==============================================================================

quickstart: check-deps setup dev ## Complete setup and start (for first-time users)
	@echo "$(GREEN)✓ Quickstart complete!$(NC)"
	@echo ""
	@echo "Access the application at:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
