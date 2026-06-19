# 🦉🫥 PDF Anonymizer

This application anonymizes large PDF, Markdown, or Text files using LLMs.

[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blue?style=flat-square)](https://leo-gan.github.io/anonymizer/)
[![CI Workflow](https://github.com/leo-gan/anonymizer/actions/workflows/lint.yml/badge.svg)](https://github.com/leo-gan/anonymizer/actions)

- **High-Quality Anonymization**: Leverages LLMs to identify and replace Personally Identifiable Information (PII) with high accuracy.
- **Large File Support**: Consistently anonymizes large files (tested up to 1GB).
- **Multi-Provider & Cost-Effective**: Free to use with local [Ollama](https://ollama.com/) models. It also supports major providers like [OpenAI](https://openai.com/), [Anthropic](https://www.anthropic.com/), [Google](https://ai.google.com/), [Hugging Face](https://huggingface.co/), and [OpenRouter](https://openrouter.ai/).
- **Reversible**: Supports deanonymization to recover original data when needed.
- **Multi-Format**: Works with PDF, Markdown, and plain text files.

## 📖 Documentation

A comprehensive documentation site is available at **[leo-gan.github.io/anonymizer/](https://leo-gan.github.io/anonymizer/)**.

The documentation includes:
- **[Anonymization 101](https://leo-gan.github.io/anonymizer/101/)**: A guide on data anonymization and deanonymization techniques.
- **[Installation Guide](https://leo-gan.github.io/anonymizer/project/installation/)**: System requirements, package extras, and setup.
- **[CLI Usage](https://leo-gan.github.io/anonymizer/project/cli-usage/)**: Reference manual for `pdf-anonymizer run` and `pdf-anonymizer deanonymize` (including configuration profiles).
- **[API Usage](https://leo-gan.github.io/anonymizer/project/api-usage/)**: Programmatic usage guide for the core SDK.
- **[API Reference (auto)](https://leo-gan.github.io/anonymizer/project/api-reference/)**: Auto-generated function signatures and details.
- **[Recipes & Common Workflows](https://leo-gan.github.io/anonymizer/project/recipes/)**: Practical patterns (local Ollama, external LLM round-trips, batching, profiles, caching, debugging, etc.).
- **[Troubleshooting](https://leo-gan.github.io/anonymizer/project/troubleshooting/)**: Common issues and solutions.
- **[Architecture](https://leo-gan.github.io/anonymizer/project/architecture/)**: Understanding how the anonymizer operates.

## Project Structure

This project is a monorepo containing two main packages:

- **`packages/pdf-anonymizer-core`**: The core library containing the anonymization and deanonymization logic. See the [core README](./packages/pdf-anonymizer-core/README.md) for more details.
- **`packages/pdf-anonymizer-cli`**: A command-line interface for using the anonymizer. See the [CLI README](./packages/pdf-anonymizer-cli/README.md) for detailed usage instructions.

## Development Installation

1.  **Install `uv`**: This project uses `uv` for package management. Follow the [official installation instructions](https://astral.sh/docs/uv#installation).

2.  **Clone the repository**:
    ```bash
    git clone https://github.com/leo-gan/anonymizer.git
    cd anonymizer
    ```

3.  **Install dependencies**:
    ```bash
    uv sync --group dev
    ```

4.  **Install Ollama (optional)**: If you want to use a local model for anonymization, install [Ollama](https://ollama.com/).

5.  **Set up environment variables**: Create a `.env` file in the root directory of the repository (or in the `packages/pdf-anonymizer-cli` directory) and add the necessary API keys for the providers you want to use. For example:
    ```env
    # For Google models
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"

    # For OpenAI models
    OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

    # For Anthropic models
    ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY"

    # For Hugging Face models
    HUGGING_FACE_TOKEN="YOUR_HF_TOKEN"

    # For OpenRouter models
    OPENROUTER_API_KEY="YOUR_OPENROUTER_KEY"
    ```

## Quick Start

To anonymize a file, run the `pdf-anonymizer` CLI tool using `uv run`:

```bash
uv run pdf-anonymizer run document.pdf
```

To deanonymize the file later:

```bash
uv run pdf-anonymizer deanonymize document.anonymized.md document.mapping.json
```

For detailed command-line options and examples, please refer to the [**CLI README**](./packages/pdf-anonymizer-cli/README.md) or the [**CLI Usage Docs**](https://leo-gan.github.io/anonymizer/project/cli-usage/).

## Demo: Anonymization & Deanonymization Example

To demonstrate the hybrid NER (Regex + LLM) and the complete round-trip process on a real document, we have provided a demo script:

1. **Prepare the Demo Document**: This script downloads an open-access arXiv research paper PDF and injects synthetic PII (name, email, phone, IP, SSN) onto the first page:
   ```bash
   uv run python scripts/prepare_demo_pdf.py
   ```

2. **Run the Demo**: This script runs the hybrid NER on the PDF, anonymizes the PII to structured placeholders, saves the mapping vocabulary, and performs a complete round-trip deanonymization:
   ```bash
   uv run python scripts/demo_anonymize.py
   ```

You will see colorized console logs showing the exact matched entities, the anonymized text, and the fully-reverted deanonymized output.

## Testing

To run the test suite:

```bash
uv run pytest
```

---

## See Also

- **[Documentation Site](https://leo-gan.github.io/anonymizer/)** — Full guides, 101 course, and API reference.
- **[Core Package README](./packages/pdf-anonymizer-core/README.md)** — SDK details and installation.
- **[CLI Package README](./packages/pdf-anonymizer-cli/README.md)** — Command-line specifics.
- **[Recipes & Common Workflows](https://leo-gan.github.io/anonymizer/project/recipes/)** — Practical usage examples.
- **[Troubleshooting](https://leo-gan.github.io/anonymizer/project/troubleshooting/)** — Solutions to common problems.