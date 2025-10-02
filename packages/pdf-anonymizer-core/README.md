# PDF Anonymizer Core

This package provides the core functionality for the PDF/Text anonymizer, including text extraction, LLM-driven anonymization, and deanonymization logic. It is used by `pdf-anonymizer-cli`.

## Installation for Development

This project uses `uv` and is structured as a monorepo. To install the necessary dependencies for development, run the following command from the root of the repository:

```bash
# From the repository root
uv sync
```

This will install the `pdf-anonymizer-core` package in editable mode.

## Environment Variables

The core library itself does not load `.env` files. Environment variables must be loaded by the application that uses this library (e.g., `pdf-anonymizer-cli`) or set in your shell.

- `GOOGLE_API_KEY`: Required when using Google's Gemini models.
- `OLLAMA_HOST`: Optional, defaults to `http://localhost:11434` when using local Ollama models.

## API Usage

### `anonymize_file()`

Anonymizes a single file and returns the anonymized text and a mapping of original entities to their placeholders.

```python
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.prompts import detailed

# Example of programmatic usage
text, mapping = anonymize_file(
    file_path="/path/to/file.pdf",
    prompt_template=detailed.prompt_template,
    model_name="gemini-2.5-flash"
)

if text and mapping:
    print("Anonymized Text:", text)
    print("Mapping:", mapping)
```

### `deanonymize_file()`

Reverts anonymization using a mapping file.

```python
from pdf_anonymizer_core.utils import deanonymize_file

# Assumes you have an anonymized file and a mapping file
deanonymized_text, stats = deanonymize_file(
    anonymized_file="path/to/anonymized.md",
    mapping_file="path/to/mapping.json"
)

if deanonymized_text:
    print("Deanonymized Text:", deanonymized_text)
```

### Configuration

You can import default configurations and available models from the `conf` module.

```python
from pdf_anonymizer_core.conf import (
    DEFAULT_MODEL_NAME,
    ModelName,
    PromptEnum,
)

print(f"Default model: {DEFAULT_MODEL_NAME}")
print(f"Available Google models: {[m.value for m in ModelName if 'gemini' in m.value]}")
```