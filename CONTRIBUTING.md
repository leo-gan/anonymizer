# Contributing to PDF Anonymizer

Thank you for your interest in contributing! This document explains how to set up your environment and run the most common development tasks.

## Development Environment

This project uses [`uv`](https://docs.astral.sh/uv/) for fast dependency management and is organized as a workspace (monorepo) with two packages under `packages/`.

```bash
# 1. Install uv (see https://astral.sh/docs/uv#installation if you don't have it)
# 2. Clone and sync the full dev environment (includes all LLM provider extras + docs tools)
git clone https://github.com/leo-gan/anonymizer.git
cd anonymizer
uv sync --group dev

# Activate the virtualenv created by uv (optional but convenient)
source .venv/bin/activate   # or `.venv\Scripts\activate` on Windows
```

The dev group installs:
- Both `pdf-anonymizer-core` and `pdf-anonymizer-cli` in editable mode
- All provider extras (google, ollama, openai, anthropic, huggingface, openrouter)
- Testing, linting, and MkDocs tooling

Create a `.env` file in the project root (or inside `packages/pdf-anonymizer-cli`) with any API keys you plan to use for testing.

## Common Tasks

Use the `Makefile` for convenience (or run the underlying `uv run` commands directly).

| Task                    | Command                              | Notes |
|-------------------------|--------------------------------------|-------|
| Lint                    | `make lint` or `uv run ruff check .` |       |
| Format                  | `make format`                        | Also fixes imports |
| Run tests               | `make test` or `uv run pytest`       |       |
| Serve docs locally      | `make docs-serve` or `uv run mkdocs serve` | Live-reloads while you edit `docs/` |
| Build docs              | `make docs-build` or `uv run mkdocs build --strict` | Produces `site/` (ignored by git) |
| Build distribution packages | `make build-core` / `make build-cli` | Uses `uvx --from build ...` |
| Clean build artifacts   | `make clean-core` / `make clean-cli` |       |

### Running the CLI during development

```bash
uv run pdf-anonymizer --help
uv run pdf-anonymizer run data/sample.pdf --config-profile best-speed
uv run pdf-anonymizer deanonymize ...
```

### Running the SDK from Python

```bash
uv run python -c "
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.prompts import detailed
print(anonymize_file('data/sample.pdf', 50000, detailed.prompt_template, 'gemini-2.5-flash'))
"
```

## Documentation

- Source lives in `docs/`.
- The site is built with MkDocs + Material.
- New practical examples go in `docs/project/recipes.md`.
- Hand-written usage guidance lives in `docs/project/`.
- Auto-generated reference (via mkdocstrings) is at `docs/project/api-reference.md`.
- Please keep docstrings in the Python source reasonably complete — they feed the API reference.

After editing docs you can preview with `uv run mkdocs serve`.

## Pull Requests

1. Create a feature branch.
2. Make sure `uv run ruff check .` and `uv run pytest` pass.
3. If you touched docs, run `uv run mkdocs build --strict` locally.
4. Open a PR. CI will run lint + tests automatically.

## Questions?

Open an issue or discussion on GitHub. We're happy to help you get set up or discuss design ideas before you write code.

Thanks for contributing!
