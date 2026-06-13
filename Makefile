.PHONY: help install dev run test lint fmt docker up down logs

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install:  ## Install runtime deps
	pip install -r requirements.txt

dev:  ## Install with dev extras (editable)
	pip install -e ".[dev]"

run:  ## Run the bot locally (long polling)
	python -m bot

test:  ## Run the test suite
	pytest -q

lint:  ## Lint with ruff
	ruff check bot/ tests/

fmt:  ## Auto-fix lint issues
	ruff check --fix bot/ tests/

docker:  ## Build the Docker image
	docker build -t getmem-telegram-bot:latest .

up:  ## Start with docker compose (polling)
	docker compose up -d --build

down:  ## Stop docker compose
	docker compose down

logs:  ## Tail bot logs
	docker compose logs -f bot
