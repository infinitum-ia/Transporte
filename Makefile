.PHONY: help setup install test test-unit test-integration test-e2e test-bdd run docker-up docker-down docker-logs lint format coverage clean

help:
	@echo "Transformas Medical Transport Agent - Available Commands:"
	@echo ""
	@echo "  make setup          - Create virtual environment and install dependencies"
	@echo "  make install        - Install dependencies only"
	@echo "  make test           - Run all tests with coverage"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-e2e       - Run end-to-end tests only"
	@echo "  make test-bdd       - Run BDD tests only"
	@echo "  make run            - Run the application locally"
	@echo "  make docker-up      - Start Docker containers"
	@echo "  make docker-down    - Stop Docker containers"
	@echo "  make docker-logs    - View Docker logs"
	@echo "  make lint           - Run linting checks"
	@echo "  make format         - Format code with black and isort"
	@echo "  make coverage       - Generate coverage report and open in browser"
	@echo "  make clean          - Remove generated files and caches"

setup:
	python -m venv venv
	@echo "Virtual environment created. Activate it with:"
	@echo "  Windows: venv\\Scripts\\activate"
	@echo "  Unix:    source venv/bin/activate"
	@echo "Then run: make install"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

test-e2e:
	pytest tests/e2e/ -v -m e2e

test-bdd:
	pytest tests/bdd/ -v

run:
	uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-build:
	docker-compose build

lint:
	flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

coverage:
	pytest --cov=src --cov-report=html --cov-report=term
	@echo "Opening coverage report..."
	@python -m webbrowser htmlcov/index.html || start htmlcov\\index.html

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/ dist/ build/ 2>/dev/null || true
	@echo "Cleaned up generated files and caches"
