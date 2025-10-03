# 🦉🫥 PDF Anonymizer

This application anonymizes large PDF, Markdown or Text files using LLMs.

- **High-Quality Anonymization**: Leverages LLMs to identify and replace Personally Identifiable Information (PII) with high accuracy.
- **Large File Support**: Consistently anonymizes large files (tested up to 1GB).
- **Cost-Effective**: Free to use with local [Ollama](https://ollama.com/) models or cheap [Hugging Face hosted](https://huggingface.co/) and [OpenRouter](https://openrouter.ai/) models.
- **Reversible**: Supports deanonymization to recover original data when needed.
- **Multi-Format**: Works with PDF, Markdown, and plain text files.

## Project Structure

This project is a monorepo containing two main packages:

- **`packages/pdf-anonymizer-core`**: The core library containing the anonymization and deanonymization logic. See the [core README](./packages/pdf-anonymizer-core/README.md) for more details.
- **`packages/pdf-anonymizer-cli`**: A command-line interface for using the anonymizer. See the [CLI README](./packages/pdf-anonymizer-cli/README.md) for detailed usage instructions.

## Development Installation

1.  **Install `uv`**: This project uses `uv` for package management. Follow the [official installation instructions](https://astral.sh/docs/uv#installation).

2.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd anonymizer
    ```

3.  **Install dependencies**:
    ```bash
    uv sync --group dev
    ```

4.  **Install Ollama (optional)**: If you want to use a local model for anonymization, install [Ollama](https://ollama.com/).

5.  **Set up environment variables**: Create a `.env` file in the `packages/pdf-anonymizer-cli` directory. If you are using Google Gemini, add your Google API key:
    ```
    GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```

## Quick Start

To anonymize a file, use the `pdf-anonymizer` command:

```bash
pdf-anonymizer run document.pdf
```

For detailed command-line options and examples, please refer to the [**CLI README**](./packages/pdf-anonymizer-cli/README.md).

## Testing

To run the test suite:

```bash
uv run pytest
```