# Makefile for Baggage Operations AI Agents

.PHONY: help install dev-install test lint format clean docker-up docker-down run

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make test          - Run tests with coverage"
	@echo "  make lint          - Run linters (ruff, mypy)"
	@echo "  make format        - Format code with black and isort"
	@echo "  make clean         - Clean up generated files"
	@echo "  make docker-up     - Start Docker services"
	@echo "  make docker-down   - Stop Docker services"
	@echo "  make run           - Run the API server locally"
	@echo "  make pre-commit    - Install pre-commit hooks"

install:
	pip install -r requirements.txt

dev-install: install
	pip install -e .
	pre-commit install

test:
	pytest --cov=agents --cov=utils --cov=api --cov-report=html --cov-report=term

test-verbose:
	pytest -vv --cov=agents --cov=utils --cov=api --cov-report=html --cov-report=term

lint:
	ruff check .
	mypy agents/ utils/ api/

format:
	black .
	isort .
	ruff check --fix .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	rm -rf build dist

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-build:
	docker-compose build

docker-restart: docker-down docker-up

run:
	python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run-dev:
	python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

pre-commit:
	pre-commit install
	pre-commit run --all-files

db-init:
	@echo "Initializing database..."
	psql -h localhost -U postgres -d baggage_operations -f scripts/init-db.sql

setup: dev-install pre-commit
	@echo "Setup complete! Copy .env.example to .env and add your API keys."
	@echo "Then run 'make docker-up' to start services."
