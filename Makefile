.PHONY: install lint format test

install:
	uv pip install -e ./packages/pdf-anonymizer-core --system
	uv pip install -e ./packages/pdf-anonymizer-cli --system
	uv pip install -e .[dev] --system

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check . --select I --fix

test:
	uv run pytest