.PHONY: build run test clean install

install:
	uv sync

build:
	uv run python -m py_compile src/main.py

run:
	uv run python src/main.py

test:
	uv run pytest

clean:
	find . -type d -name __pycache__ -delete
	find . -name "*.pyc" -delete

dev:
	uv run python src/main.py

docker-build:
	docker build -f docker/Dockerfile -t llm-bot .

docker-run:
	docker run -d --name llm-bot --restart=always --env-file .env llm-bot
