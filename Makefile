SHELL := /bin/bash

# Variables
PROJECT_NAME := triware
PYTHON_VERSION := 3.11
NODE_VERSION := 18

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

.PHONY: help setup dev test build deploy clean docker-build docker-up docker-down

help: ## Show this help message
	@echo "Smart Triage Kiosk System - Makefile Commands"
	@echo "============================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup the development environment
	@echo -e "$(GREEN)Setting up development environment...$(NC)"
	@make setup-backend
	@make setup-frontend
	@make setup-ml
	@echo -e "$(GREEN)✓ Setup complete!$(NC)"

setup-backend: ## Setup backend dependencies
	@echo -e "$(YELLOW)Setting up backend...$(NC)"
	cd backend && python -m venv venv
	cd backend && source venv/bin/activate && pip install -r requirements.txt
	cd backend && source venv/bin/activate && pip install -r requirements-dev.txt

setup-frontend: ## Setup frontend dependencies
	@echo -e "$(YELLOW)Setting up frontend...$(NC)"
	cd frontend && npm install

setup-ml: ## Setup ML dependencies
	@echo -e "$(YELLOW)Setting up ML environment...$(NC)"
	cd ml && python -m venv venv
	cd ml && source venv/bin/activate && pip install -r requirements.txt

dev: ## Start development environment
	@echo -e "$(GREEN)Starting development environment...$(NC)"
	docker-compose up -d postgres redis minio mlflow
	@echo -e "$(YELLOW)Waiting for services to be ready...$(NC)"
	@sleep 5
	@make dev-backend &
	@make dev-frontend &
	@make dev-ml &
	wait

dev-backend: ## Start backend development server
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && npm start

dev-ml: ## Start ML service development server
	cd ml && source venv/bin/activate && python -m uvicorn main:app --reload --port 8001

test: ## Run all tests
	@echo -e "$(GREEN)Running tests...$(NC)"
	@make test-backend
	@make test-frontend
	@make test-ml

test-backend: ## Run backend tests
	cd backend && source venv/bin/activate && pytest tests/ -v --cov=app --cov-report=html

test-frontend: ## Run frontend tests
	cd frontend && npm test -- --coverage --watchAll=false

test-ml: ## Run ML tests
	cd ml && source venv/bin/activate && pytest tests/ -v

test-e2e: ## Run end-to-end tests
	cd frontend && npx cypress run

lint: ## Run linting on all code
	@echo -e "$(GREEN)Running linting...$(NC)"
	cd backend && source venv/bin/activate && black . && isort . && flake8 .
	cd frontend && npm run lint:fix
	cd ml && source venv/bin/activate && black . && isort .

format: ## Format all code
	@make lint

build: ## Build production images
	@echo -e "$(GREEN)Building production images...$(NC)"
	docker-compose -f docker-compose.prod.yml build

deploy-local: ## Deploy to local environment
	@echo -e "$(GREEN)Deploying to local environment...$(NC)"
	docker-compose -f docker-compose.prod.yml up -d

deploy-staging: ## Deploy to staging environment
	@echo -e "$(GREEN)Deploying to staging...$(NC)"
	# Add staging deployment commands here

deploy-prod: ## Deploy to production
	@echo -e "$(RED)Deploying to production...$(NC)"
	@echo -e "$(YELLOW)Are you sure? [y/N]$(NC)"
	@read -r response && [[ $$response =~ ^[Yy]$$ ]]
	# Add production deployment commands here

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start services with Docker
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

migrations: ## Create and run database migrations
	cd backend && source venv/bin/activate && alembic revision --autogenerate -m "$(msg)"
	cd backend && source venv/bin/activate && alembic upgrade head

db-reset: ## Reset database (WARNING: destroys data)
	@echo -e "$(RED)This will destroy all data. Are you sure? [y/N]$(NC)"
	@read -r response && [[ $$response =~ ^[Yy]$$ ]]
	docker-compose down -v
	docker-compose up -d postgres
	@sleep 5
	@make migrations

clean: ## Clean up build artifacts
	@echo -e "$(GREEN)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	docker system prune -f

install-pre-commit: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install

security-scan: ## Run security scans
	@echo -e "$(GREEN)Running security scans...$(NC)"
	cd backend && source venv/bin/activate && bandit -r app/
	cd frontend && npm audit
	docker run --rm -v $(PWD):/src clair-scanner

performance-test: ## Run performance tests
	@echo -e "$(GREEN)Running performance tests...$(NC)"
	# Add k6 or artillery performance tests

docs: ## Generate documentation
	@echo -e "$(GREEN)Generating documentation...$(NC)"
	cd backend && source venv/bin/activate && sphinx-build -b html docs/ docs/_build/
	cd frontend && npm run build:docs

backup: ## Backup database and files
	@echo -e "$(GREEN)Creating backup...$(NC)"
	docker exec triware_postgres_1 pg_dump -U triware triware_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore: ## Restore from backup
	@echo -e "$(YELLOW)Enter backup file name:$(NC)"
	@read -r backup_file && docker exec -i triware_postgres_1 psql -U triware triware_db < $$backup_file
