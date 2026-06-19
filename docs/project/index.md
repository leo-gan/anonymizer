# Project Documentation

Welcome to the technical developer documentation for **PDF Anonymizer**. 

This section covers everything you need to install, run, configure, and extend the codebase. PDF Anonymizer is built as a modular Python monorepo, designed to keep developer tooling lightweight and separate from core business logic.

---

## Monorepo Project Structure

The project separates the command-line application from the underlying core library using a monorepo setup:

```
anonymizer/
├── .github/workflows/          # CI/CD & Deploy workflows
├── data/                       # Local data directory for sample files
├── docs/                       # MkDocs documentation source files
├── packages/
│   ├── pdf-anonymizer-core/    # Core SDK package (logic, providers, prompts)
│   └── pdf-anonymizer-cli/     # CLI executable wrapper using Typer
├── tests/                      # Global pytest test suite
├── Makefile                    # Developer shortcut commands
├── pyproject.toml              # Workspace and dev dependencies config
└── mkdocs.yml                  # MkDocs site configuration
```

---

## The Packages

The project contains two decoupled Python packages inside `packages/`:

### `pdf-anonymizer-core`
Contains all the core engines, including:

*   Text extraction from PDF, Markdown, and plain text formats.
*   LLM router and adapters for various providers (Ollama, Gemini, OpenAI, etc.).
*   System prompt templates (simple and detailed layouts).
*   Streaming chunk utility to process large text files.
*   Mapping and restoration engine for deanonymization.

### `pdf-anonymizer-cli`
A CLI tool built on top of `pdf-anonymizer-core` that:

*   Exposes a command-line interface using `Typer` (supporting autocompletion, clean logs, and command help).
*   Handles loading local `.env` files automatically.
*   Manages output file paths for anonymized logs and mapping tables.

---

## Getting Started

To dive deeper into the technical details, navigate through the following guides:

- **[Installation & Setup](installation.md)**: Learn how to set up the development environment using `uv`, manage packages, and define environment variables.
- **[CLI Reference](cli-usage.md)**: Explore the command-line arguments, options (including `--config-profile`), custom model strings, and usage examples.
- **[SDK & API Usage](api-usage.md)**: Learn how to import PDF Anonymizer as a Python library in your own applications.
- **[API Reference (auto)](api-reference.md)**: Living signature reference generated from source docstrings.
- **[Recipes & Common Workflows](recipes.md)**: Practical end-to-end examples — fully local Ollama usage, safe external LLM workflows, batching, entity filtering, profiles, caching, debugging, and more.
- **[Troubleshooting](troubleshooting.md)**: Common errors (auth, rate limits, LLM parsing, empty results, large files) and solutions.
- **[Architecture Design](architecture.md)**: Understand the data flow, prompt styling, LLM adapters, and file splitting mechanisms.
