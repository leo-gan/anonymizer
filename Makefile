.PHONY: install lint format

install:
	pip install -e .[dev]

lint:
	ruff check .

format:
	ruff format .