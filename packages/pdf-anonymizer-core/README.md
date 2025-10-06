# 🦉🫥 PDF Anonymizer Core

This package provides the core functionality for the PDF/Text anonymizer, including text extraction, LLM-driven anonymization, and deanonymization logic. It is used by `pdf-anonymizer-cli`.

## Installation

Install the base package with your favorite package manager:

```bash
pip install pdf-anonymizer-core
```

To use a specific LLM provider, you must install the corresponding extra. This helps to keep the installation lightweight by only downloading the libraries you need.

- **Google**: `pip install "pdf-anonymizer-core[google]"`
- **Ollama**: `pip install "pdf-anonymizer-core[ollama]"`
- **Hugging Face**: `pip install "pdf-anonymizer-core[huggingface]"`
- **OpenRouter**: `pip install "pdf-anonymizer-core[openrouter]"`
- **OpenAI**: `pip install "pdf-anonymizer-core[openai]"`
- **Anthropic**: `pip install "pdf-anonymizer-core[anthropic]"`

You can also install multiple extras at once:

```bash
pip install "pdf-anonymizer-core[google,ollama]"
```

## Environment Variables

The core library itself does not load `.env` files. Environment variables must be loaded by the application that uses this library (e.g., `pdf-anonymizer-cli`) or set in your shell.

- `GOOGLE_API_KEY`: Required when using Google models.
- `HUGGING_FACE_TOKEN`: Required when using Hugging Face models.
- `OPENROUTER_API_KEY`: Required when using OpenRouter models.
- `OPENAI_API_KEY`: Required when using OpenAI models.
- `ANTHROPIC_API_KEY`: Required when using Anthropic models.
- `OLLAMA_HOST`: Optional, defaults to `http://localhost:11434` when using Ollama models.

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
    model_name="gemini-2.5-pro"  # Can also be a new model like "google/gemini-flash-latest"
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
print(f"Available Google models: {[m.value for m in ModelName if m.provider == 'google']}")
```