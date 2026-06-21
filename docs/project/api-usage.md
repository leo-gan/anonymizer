# Programmatic API & SDK Reference

Developers can integrate `pdf-anonymizer-core` directly into their Python applications (e.g. data processing pipelines, web apps, or custom AI agent loops).

---

## `anonymize_file`

The `anonymize_file` function reads, extracts, chunks, and masks a file, returning the final anonymized string and the mapped PII dictionary.

### Import Signature
```python
from pdf_anonymizer_core.core import anonymize_file
```

### Parameters
*   `file_path` (`str`): The absolute or relative path to the input document (supports `.pdf`, `.md`, `.txt`).
*   `prompt_template` (`str`): The prompt template string containing instructions for entity masking.
*   `model_name` (`str`): The target model name (e.g. `"gemini-2.5-flash"`, `"google/gemini-2.5-pro"`, `"ollama/phi4-mini"`).

### Returns
*   `anonymized_text` (`str`): The fully processed text with placeholders in place of PII.
*   `mapping` (`dict[str, str]`): A dictionary mapping original entities to their assigned placeholders.

---

## `deanonymize_file`

The `deanonymize_file` function reads an anonymized file, loads the mapping (auto-detecting placeholder→original or legacy direction), replaces placeholders (including `.v_N` variants), writes the restored document to the conventional output directory (`data/deanonymized/`), writes a statistics JSON file (`data/stats/`), and returns the two output file paths.

### Import Signature
```python
from pdf_anonymizer_core.utils import deanonymize_file
```

### Parameters
*   `anonymized_file_path` (`str`): Path to the markdown or text file that has placeholders.
*   `mapping_file_path` (`str`): Path to the JSON mapping file containing the original entity-to-placeholder mapping dictionary.

### Returns
*   `deanonymized_file_path` (`str`): Path to the written restored document.
*   `stats_file_path` (`str`): Path to the written deanonymization statistics JSON file.

---

## Configuration & Prompts

The core library exposes configuration constants, model structures, and prompts in `conf` and `prompts` modules.

### Loading Models & Configuration
```python
from pdf_anonymizer_core.conf import (
    DEFAULT_MODEL_NAME,
    ModelName,
    PromptEnum,
)

# Print default model
print(f"Default: {DEFAULT_MODEL_NAME}")

# List preconfigured Google models
google_models = [m.value for m in ModelName if m.provider == 'google']
print("Google models:", google_models)
```

### Selecting a Prompt Template
The package provides two pre-configured prompt styles: `simple` and `detailed`.

```python
from pdf_anonymizer_core.prompts import simple, detailed

# Use the detailed prompt template (recommended)
prompt_text = detailed.prompt_template
```

---

## End-to-End Code Example

Here is a complete script demonstrating how to programmatically anonymize a document, print the details, and then programmatically restore the text.

```python
import os
import json
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.utils import deanonymize_file
from pdf_anonymizer_core.prompts import detailed

# 1. Anonymize the input file
input_document = "data/contract.pdf"
model = "gemini-2.5-flash"

print(f"Anonymizing {input_document} using {model}...")
anonymized_text, mapping = anonymize_file(
    file_path=input_document,
    prompt_template=detailed.prompt_template,
    model_name=model
)

# 2. Inspect the outputs
print("\n--- Masked Text Output ---")
print(anonymized_text[:500] + "\n...")

print("\n--- Extracted Mappings ---")
print(json.dumps(mapping, indent=2))

# Save outputs to disk
anonymized_path = "data/contract.anonymized.md"
mapping_path = "data/contract.mapping.json"

with open(anonymized_path, "w", encoding="utf-8") as f:
    f.write(anonymized_text)

with open(mapping_path, "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=2)

# 3. Deanonymize programmatically
print(f"\nRestoring file from {anonymized_path} using {mapping_path}...")
deanonymized_file_path, stats_file_path = deanonymize_file(
    anonymized_path,
    mapping_path,
)

print("Deanonymized file saved to:", deanonymized_file_path)
print("Stats file saved to:", stats_file_path)

# If you need the text content in memory:
with open(deanonymized_file_path, "r", encoding="utf-8") as f:
    restored_text = f.read()
print("\n--- Restored Text Output (first 500 chars) ---")
print(restored_text[:500] + "\n...")
```

You can also pass a custom list for `anonymized_entities` or supply your own `regex_patterns` dict for the first-stage NER (now RE2-powered with 70+ patterns for 30+ countries; see Recipes for examples and `conf.DEFAULT_REGEX_PATTERNS`).

### Advanced: Caching and Full Control

The library caches LLM responses by default (in `data/cache/llm_responses.json`). You can control it directly:

```python
from pdf_anonymizer_core.llm_provider import configure_cache
configure_cache(enabled=True, cache_dir="my-cache", cache_file="responses.json")
```

For the complete `anonymize_file` signature (including `chunk_overlap`, `regex_patterns`, `max_retries`, etc.) see the [auto-generated API Reference](api-reference.md) or the Recipes page.

---

## See Also

- **[Recipes & Common Workflows](recipes.md)** — practical SDK examples (local Ollama, external LLM round-trips, profiles, custom regex, cache control, large files).
- **[CLI Reference](cli-usage.md)** — the command-line surface that wraps the same core functions.
- **[API Reference (auto)](api-reference.md)** — auto-generated detailed signatures.
- **[Architecture Design](architecture.md)** — internals behind the functions documented here.
- **[Installation & Setup](installation.md)** — how to set up the environment for the SDK.
- **[Troubleshooting](troubleshooting.md)** — help with common SDK and CLI issues.
- **[Architecture Design](architecture.md)** — how the anonymization pipeline, consolidation, and deanonymization actually work internally.
