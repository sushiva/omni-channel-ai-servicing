.PHONY: install test test-cov test-unit test-integration lint format run-api run-email run-mock docker-build docker-up clean help

# Colors for terminal output
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install package and dependencies
	uv pip install -e ".[dev]"

test: ## Run all tests
	pytest tests/unit tests/integration -v

test-unit: ## Run unit tests only
	pytest tests/unit -v

test-integration: ## Run integration tests only
	pytest tests/integration -v

test-cov: ## Run tests with coverage report
	pytest tests/ --cov=omni_channel_ai_servicing --cov-report=html --cov-report=term
	@echo "$(BLUE)Coverage report generated in htmlcov/index.html$(NC)"

lint: ## Run linting checks
	@echo "$(BLUE)Running ruff...$(NC)"
	ruff check omni_channel_ai_servicing tests
	@echo "$(BLUE)Running mypy...$(NC)"
	mypy omni_channel_ai_servicing --ignore-missing-imports

format: ## Format code with ruff
	ruff format omni_channel_ai_servicing tests

run-api: ## Start the FastAPI application
	python -m omni_channel_ai_servicing.app.main

run-email: ## Start the email IDLE poller
	python -m omni_channel_ai_servicing.services.email_idle_poller

run-mock: ## Start mock services
	cd mock_services && python main.py

docker-build: ## Build Docker image
	docker build -f infra/docker/Dockerfile -t omni-channel-ai:latest .

docker-up: ## Start services with docker-compose
	docker-compose -f infra/docker/docker-compose.yaml up

docker-down: ## Stop docker-compose services
	docker-compose -f infra/docker/docker-compose.yaml down

clean: ## Clean up temporary files
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	@echo "$(BLUE)Done!$(NC)"

clean-all: clean ## Clean everything including virtual environment
	rm -rf .venv
