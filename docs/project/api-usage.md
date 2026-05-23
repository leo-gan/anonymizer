# Programmatic API & SDK Reference

Developers can integrate `pdf-anonymizer-core` directly into their Python applications (e.g. data processing pipelines, web apps, or custom AI agent loops).

---

## 1. `anonymize_file`

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

## 2. `deanonymize_file`

The `deanonymize_file` function reads an anonymized file, loads the entity placeholders dictionary from a JSON file, replaces placeholders with their original values, and returns the result.

### Import Signature
```python
from pdf_anonymizer_core.utils import deanonymize_file
```

### Parameters
*   `anonymized_file` (`str`): Path to the markdown or text file that has placeholders.
*   `mapping_file` (`str`): Path to the JSON mapping file containing the original entity-to-placeholder mapping dictionary.

### Returns
*   `deanonymized_text` (`str`): The restored text containing original PII.
*   `stats` (`dict`): Processing metadata, including entity counts.

---

## 3. Configuration & Prompts

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

## 4. End-to-End Code Example

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
restored_text, stats = deanonymize_file(
    anonymized_file=anonymized_path,
    mapping_file=mapping_path
)

print("\n--- Restored Text Output ---")
print(restored_text[:500] + "\n...")
print("Stats:", stats)
```
