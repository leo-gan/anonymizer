# PDF Anonymizer Core

Core Python SDK for reversible, context-aware document and table pseudonymization across PDF, Markdown, plain text, Word (`.docx`), CSV, and Excel (`.xlsx`). Used by `pdf-anonymizer-cli` and `pdf-anonymizer-api`.

It is a reversible pseudonymizer, not a legal compliance certificate. Full guides and the companion **Anonymization Handbook** live at **[leo-gan.github.io/anonymizer/](https://leo-gan.github.io/anonymizer/)**.

## Installation

```bash
# Base library (RE2 structured detection via id-extract; CSV supported)
pip install pdf-anonymizer-core

# Provider and format extras (combine as needed)
pip install "pdf-anonymizer-core[google]"
pip install "pdf-anonymizer-core[ollama]"
pip install "pdf-anonymizer-core[openai,anthropic]"
pip install "pdf-anonymizer-core[huggingface,openrouter]"
pip install "pdf-anonymizer-core[excel,docx,ner]"
```

Scanned PDF OCR requires the system `tesseract` binary on `PATH` (not a pip extra).

## Environment Variables

The core library does not automatically load `.env` files; set variables in your process environment (or load them with `python-dotenv`):

- Provider keys (only for remote models you invoke): `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `HUGGING_FACE_TOKEN`, `OPENROUTER_API_KEY`
- `OLLAMA_HOST`: optional local Ollama URL (default `http://localhost:11434`)
- `ANONYMIZER_MAPPING_KEY`: optional passphrase to encrypt mappings as `*.mapping.json.enc` (Argon2id + AES-256-GCM + source-hash AAD)
- `ANONYMIZER_FAKE_SECRET`: required seed when using the `fake` operator
- `ANONYMIZER_ENCRYPT_SECRET`: required secret when using the `encrypt` operator (`ENC1_…` tokens)

## Quick Start

```python
from pdf_anonymizer_core.conf import ConfigProfile, get_config_for_profile
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.prompts import detailed
from pdf_anonymizer_core.utils import deanonymize_file, save_results

cfg = get_config_for_profile(ConfigProfile.BEST_SPEED, countries=["US", "GB"])

anonymized_text, mapping = anonymize_file(
    file_path="data/contract.pdf",
    characters_to_anonymize=cfg.chunk_size,
    prompt_template=detailed.prompt_template,
    model_name=cfg.model_name,
    chunk_overlap=cfg.chunk_overlap,
    regex_patterns=cfg.regex_patterns,
)

# Persist with atomic 0600 mapping permissions (optional mapping_passphrase / ephemeral_mapping)
anon_path, map_path = save_results(
    anonymized_text,
    {v: k for k, v in mapping.items()},
    "data/contract.pdf",
)

restored_path, stats_path = deanonymize_file(anon_path, map_path)
```

## Key Capabilities

- **Profiles (`ConfigProfile`):** `BEST_QUALITY` (`detailed` prompt, detects indirect identity clues), `BEST_SPEED` (default), `BEST_COST`, and `REGEX_ONLY` (`use_llm=False`, offline).
- **Hybrid detection & checksums:** RE2 patterns via `id-extract` (universal + 38 countries, `filter_regex_patterns`), 26 check-digit validators (`TYPE_LIKE` vs. strict drop), optional local GLiNER (`use_ner=True`), and multi-provider LLMs.
- **Span replacement & operators:** Character-interval longest-span replacement with per-type operators (`replace`, `mask`, `hash`, `generalize`, `shift`, `fake`, `encrypt`), `keep_list`/`deny_list`, `seed_mapping`, `min_confidence`, and `EntityProfile.HIPAA_SAFE_HARBOR`.
- **Tables & Word:** `anonymize_tabular_file` (`.csv`/`.xlsx`, plus optional `table_privacy` $k$-anonymity reporting) and `anonymize_docx_file` (`.docx`).
- **Verification & hygiene:** `verify_anonymized_text`, `apply_residuals`, `assess_linkage_risk`, `configure_cache` (off by default), and `purge_local_artifacts`.

## Documentation

- **[SDK & API Usage](https://leo-gan.github.io/anonymizer/project/api-usage/)** — Full programmatic signatures and table/Word workflows.
- **[API Reference (auto)](https://leo-gan.github.io/anonymizer/project/api-reference/)** — Module-level docstring reference.
- **[Recipes & Workflows](https://leo-gan.github.io/anonymizer/project/recipes/)** — End-to-end CLI and SDK patterns.
- **[Architecture](https://leo-gan.github.io/anonymizer/project/architecture/)** & **[Mapping Security](https://leo-gan.github.io/anonymizer/project/mapping-security/)** — Pipeline and cryptographic design notes.
- **[Anonymization Handbook](https://leo-gan.github.io/anonymizer/101/)** — Theory, threat models, file-format leakage, and benchmarks.
