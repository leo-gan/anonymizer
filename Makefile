.PHONY: install lint format test build-core build-cli clean-core clean-cli publish-core publish-cli publish-core-test publish-cli-test

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

# -----------------------------
# Packaging & Publishing
# -----------------------------
CORE_PKG_DIR=packages/pdf-anonymizer-core
CLI_PKG_DIR=packages/pdf-anonymizer-cli

clean-core:
	rm -rf $(CORE_PKG_DIR)/dist $(CORE_PKG_DIR)/build $(CORE_PKG_DIR)/*.egg-info

clean-cli:
	rm -rf $(CLI_PKG_DIR)/dist $(CLI_PKG_DIR)/build $(CLI_PKG_DIR)/*.egg-info

# Build distributions (sdist+wheel)
build-core: clean-core
	cd $(CORE_PKG_DIR) && uvx --from build pyproject-build .

build-cli: clean-cli
	cd $(CLI_PKG_DIR) && uvx --from build pyproject-build .

# Publish to TestPyPI (set TWINE_USERNAME=__token__ and TWINE_PASSWORD to the TestPyPI token)
publish-core-test: build-core
	cd $(CORE_PKG_DIR) && uvx --from twine twine upload --repository testpypi dist/*

publish-cli-test: build-cli
	cd $(CLI_PKG_DIR) && uvx --from twine twine upload --repository testpypi dist/*

# Publish to PyPI (set TWINE_USERNAME=__token__ and TWINE_PASSWORD to the PyPI token)
publish-core: build-core
	cd $(CORE_PKG_DIR) && uvx --from twine twine upload dist/*

publish-cli: build-cli
	cd $(CLI_PKG_DIR) && uvx --from twine twine upload dist/*