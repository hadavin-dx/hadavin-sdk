.PHONY: help install install-dev test test-unit test-integration test-e2e test-chaos test-perf test-security lint format typecheck coverage clean build publish

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install package
	pip install -e .

install-dev: ## Install package with dev dependencies
	pip install -e ".[dev,all]"

test: ## Run all tests
	pytest tests/ -v --timeout=30

test-unit: ## Run unit tests only
	pytest tests/unit/ -v --timeout=10

test-integration: ## Run integration tests
	pytest tests/integration/ -v --timeout=30

test-e2e: ## Run end-to-end tests
	pytest tests/e2e/ -v --timeout=60

test-chaos: ## Run chaos/fault-injection tests
	pytest tests/chaos/ -v --timeout=30

test-perf: ## Run performance tests
	pytest tests/performance/ -v --timeout=60

test-security: ## Run security tests
	pytest tests/security/ -v --timeout=30

lint: ## Run linter
	ruff check src/ tests/

format: ## Format code
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck: ## Run type checker
	mypy src/agent_killswitch/

coverage: ## Run tests with coverage
	pytest tests/ -v --cov=agent_killswitch --cov-report=html --cov-report=term-missing --timeout=30

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info src/*.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

build: clean ## Build distribution packages
	python -m build

publish: build ## Publish to PyPI
	twine upload dist/*
