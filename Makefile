.PHONY: dev-up dev-down prod-up prod-down frontend backend install-dev clean
SHELL := /bin/bash

# Development commands
dev-up:
	docker compose -f docker/docker-compose.dev.yml up -d
	@echo "Waiting for database to be ready..."
	@sleep 5  # Give PostgreSQL time to initialize
	cd backend && . .venv/bin/activate && python create_test_user.py
	cd backend && . .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload

dev-down:
	docker compose -f docker/docker-compose.dev.yml down

# Local development servers
frontend:
	cd frontend && npm run dev

backend:
	cd backend && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload

# Installation and setup
install-dev:
	cd frontend && npm install
	cd backend && pip install -r requirements.txt

# Production commands
prod-up:
	docker compose -f docker/docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker/docker-compose.prod.yml down

# Cleanup
clean:
	docker compose -f docker/docker-compose.dev.yml down -v
	docker compose -f docker/docker-compose.prod.yml down -v
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "node_modules" -exec rm -r {} +