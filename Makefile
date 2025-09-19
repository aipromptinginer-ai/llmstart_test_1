.PHONY: build run test test-coverage clean install docker-build docker-run docker-compose-up docker-compose-down

install:
	uv sync

build:
	uv run python -m py_compile src/main.py

run:
	uv run python src/main.py

test:
	uv run pytest

test-coverage:
	uv run pytest --cov=src --cov-report=html --cov-report=term

test-verbose:
	uv run pytest -v

clean:
	find . -type d -name __pycache__ -delete
	find . -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -rf .coverage

dev:
	uv run python src/main.py

# Docker команды
docker-build:
	docker build -t llm-learning-goals-bot .

docker-run:
	docker run -d --name llm-bot --restart=always --env-file .env llm-learning-goals-bot

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

docker-logs:
	docker-compose logs -f llm-bot

# Интеграционные тесты
test-integration:
	@echo "Запуск интеграционных тестов..."
	@echo "Убедитесь что бот запущен и переменные окружения настроены"
	uv run python -c "import sys; sys.path.append('src'); from tests.integration.test_bot import run_integration_tests; run_integration_tests()"
