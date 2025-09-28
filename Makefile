.PHONY: install lint format

install:
	uv pip install -e .[dev]

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check . --select I --fix