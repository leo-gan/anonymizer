# pdf-anonymizer-core

Core functionality for the PDF/Text anonymizer. Provides text extraction, LLM-driven entity detection, anonymization mapping, consolidation, persistence, and deanonymization utilities. Used by `pdf-anonymizer-cli`.

## Install (for development)

Using uv (recommended):

```bash
uv pip install -e ./packages/pdf-anonymizer-core
```

Using pip:

```bash
pip install -e ./packages/pdf-anonymizer-core
```

## Features

- Load and extract text from PDF/Markdown/Text (`load_and_extract.py`)
- Identify entities via LLMs (Google Gemini or local Ollama) (`call_llm.py`)
- Chunking and consistent placeholder mapping (`core.py`)
- Mapping consolidation and file I/O (`utils.py`)
- Prompt templates (`prompts/`): `simple`, `detailed`
- Config and enums for models and prompts (`conf.py`)

## Environment

When using Google models you must set:

- `GOOGLE_API_KEY`

For local Ollama models (optional):

- `OLLAMA_HOST` (defaults to `http://localhost:11434`)

The core package itself does not auto-load a `.env`. If you use it programmatically, export variables in your shell or load them via `dotenv` in your application. The CLI package (`pdf-anonymizer-cli`) auto-loads a `.env` at `packages/pdf-anonymizer-cli/.env`.

## Public API (most common)

### `anonymize_file()`

```python
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.prompts import detailed, simple

text, mapping = anonymize_file(
    file_path="/path/to/file.pdf",
    characters_to_anonymize=100_000,
    prompt_template=detailed.prompt_template,
    model_name="gemini-2.5-flash",  # or local models like "gemma:7b", "phi4-mini"
    anonymized_entities=None,        # or list like ["PERSON", "EMAIL"]
)
```

- Returns a tuple `(full_anonymized_text: Optional[str], mapping: Optional[dict])`.

### `utils`

```python
from pdf_anonymizer_core.utils import consolidate_mapping, save_results, deanonymize_file

# Consolidate placeholders and save anonymization outputs
# Note: The mapping from anonymize_file is original->placeholder.
# We invert it for use with other utility functions.
placeholder_to_original = {v: k for k, v in mapping.items()}
anonymized_text, consolidated_mapping = consolidate_mapping(anonymized_text, placeholder_to_original)
# save_results now expects placeholder->original
md_path, json_path = save_results(anonymized_text, consolidated_mapping, original_file_path)

# Deanonymize using mapping
out_md, stats_json = deanonymize_file(
    anonymized_file=md_path,
    mapping_file=json_path,
)
```

### Configuration and Models

```python
from pdf_anonymizer_core.conf import (
    DEFAULT_CHARACTERS_TO_ANONYMIZE,
    DEFAULT_MODEL_NAME,
    DEFAULT_PROMPT_NAME,
    ModelName,
    PromptEnum,
)
```

- Default model: `gemini-2.5-flash`
- Prompts: `simple`, `detailed`
- Local models (via Ollama): `gemma:7b`, `phi4-mini`

## Notes

- PDF parsing relies on `pymupdf4llm`.
- Google models require `google-genai` and a valid `GOOGLE_API_KEY`.
- Local models use `ollama`. Ensure the model is pulled/running (e.g., `ollama pull phi`).
