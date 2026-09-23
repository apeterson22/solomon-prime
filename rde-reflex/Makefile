.PHONY: install test lint run dev

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check src tests

run:
	python -m rde_reflex

dev:
	uvicorn rde_reflex.api:app --host 127.0.0.1 --port 8787 --reload
