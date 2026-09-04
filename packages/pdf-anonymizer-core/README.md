# 🦉🫥 PDF Anonymizer Core

This package provides the core functionality for the PDF/Text anonymizer, including text extraction, LLM-driven anonymization, and deanonymization logic. It is used by `pdf-anonymizer-cli`.

- **Multi-Format**: Works with PDF, Markdown, plain text, CSV, Excel, and Word (`.docx`) files.

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
- **Excel** (`.xlsx`): `pip install "pdf-anonymizer-core[excel]"`
- **Word** (`.docx`): `pip install "pdf-anonymizer-core[docx]"`
- **Local NER**: `pip install "pdf-anonymizer-core[ner]"`

You can also install multiple extras at once:

```bash
pip install "pdf-anonymizer-core[google,ollama]"
```

Full documentation, including the Python SDK guide, CLI reference, recipes, and architecture, lives at **[leo-gan.github.io/anonymizer/](https://leo-gan.github.io/anonymizer/)** (especially the [Recipes & Common Workflows](https://leo-gan.github.io/anonymizer/project/recipes/) section).
## Environment Variables

The core library itself does not load `.env` files. Environment variables must be loaded by the application that uses this library (e.g., `pdf-anonymizer-cli`) or set in your shell.

- `GOOGLE_API_KEY`: Required when using Google models.
- `HUGGING_FACE_TOKEN`: Required when using Hugging Face models.
- `OPENROUTER_API_KEY`: Required when using OpenRouter models.
- `OPENAI_API_KEY`: Required when using OpenAI models.
- `ANTHROPIC_API_KEY`: Required when using Anthropic models.
- `OLLAMA_HOST`: Optional, defaults to `http://localhost:11434` when using Ollama models.
- `ANONYMIZER_MAPPING_KEY`: Optional passphrase for encrypted mapping files.
- `ANONYMIZER_FAKE_SECRET`: Optional seed for the `fake` operator.

## API Usage

### `anonymize_file()`

Anonymizes a single file and returns the anonymized text and a mapping of original entities to their placeholders.

```python
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.prompts import detailed

# Example of programmatic usage
# detailed.prompt_template also asks the model to hide identity clues:
# phrases that point to one person without writing their name
# (for example "the CEO of Tesla"). Use simple.prompt_template to skip that.
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

Reverts anonymization using a mapping file. The function writes the restored document and a stats file to conventional locations and returns their paths.

```python
from pdf_anonymizer_core.utils import deanonymize_file

# Assumes you have an anonymized file and a mapping file
deanonymized_file_path, stats_file_path = deanonymize_file(
    "path/to/anonymized.md",
    "path/to/mapping.json",
    # mapping_passphrase="secret",  # required for *.mapping.json.enc
    # expected_source_sha256="...",  # optional AAD check
)

print("Deanonymized file:", deanonymized_file_path)
print("Stats file:", stats_file_path)
```

### Configuration

You can import default configurations, profiles, and available models from the `conf` module.

```python
from pdf_anonymizer_core.conf import (
    DEFAULT_MODEL_NAME,
    ModelName,
    PromptEnum,
    ConfigProfile,
    get_config_for_profile,
    DEFAULT_REGEX_PATTERNS,
)

print(f"Default model: {DEFAULT_MODEL_NAME}")
print(f"Available Google models: {[m.value for m in ModelName if m.provider == 'google']}")
print("Regex first-stage covers:", sorted(DEFAULT_REGEX_PATTERNS.keys())[:10], "...")

# Recommended way to obtain bundled settings (used by the CLI's --config-profile / -p)
cfg = get_config_for_profile(ConfigProfile.BEST_SPEED)
print(cfg.model_name, cfg.chunk_size)
```

The CLI exposes `--config-profile` (short: `-p`) with the values `best-quality`, `best-speed` (default), and `best-cost`.  
These profiles control model, prompt, chunk size, overlap, retries, etc. You can override individual values when calling `get_config_for_profile(...)` or when using the CLI.

The first-stage regex (hybrid NER) is now powered by the RE2 engine (`google-re2` package).  
`DEFAULT_REGEX_PATTERNS` contains 70+ patterns partitioned by country (ISO-2 suffixes) covering
emails, phones, URLs, credit cards, crypto, IBAN/BIC, VIN, MAC, IPv4/6, dates plus national IDs,
tax IDs, driver licences, VAT/business numbers, passports, medical licenses etc. for 30+ countries
(mandatory: US, CA, GB, ES, IT, FR, IN, CN + many others). After a structural match, `validators.py` runs a cheap checksum (Luhn, IBAN mod-97,
VIN check digit, and a few national IDs). Failures are kept and labeled `TYPE_LIKE`
(for example `IBAN_LIKE_1`) so a mistyped number is still hidden. Types with no
check are unchanged. Listing `IBAN` in a type filter also includes `IBAN_LIKE`.
See `conf.py`, `regex_ner.py`, and `validators.py`.

Pass `keep_list=` / `deny_list=` phrase lists into `anonymize_file` (CLI: `--keep-list` / `--deny-list`). Keep wins if a phrase is on both.

Pass `seed_mapping=` (original → written) into `anonymize_file` so the same person stays `PERSON_1` across documents. The CLI `--mapping-in` flag loads that file (including encrypted maps).

`EntityProfile.HIPAA_SAFE_HARBOR` is a coverage aid for Safe Harbor identifier classes (year-only dates, ZIP3, age 90+). It is **not** a compliance certificate.

Per-type operators (`replace`, `mask`, `hash`, `generalize`, `shift`, `fake`) go in `operators={"PERSON": "fake"}` on `anonymize_file`. Pass `fake_secret=` so the same person always gets the same fake.

Replacement is span-based: mentions are located in the full document, the longer interval wins on overlap, and slices are written from the end.

To score a gold fixture (mention vs entity recall, direct vs quasi) run `uv run python scripts/eval_tab.py`. To install and score the public gold-corpus (TAB, Presidio, Gretel — not stored in git) see the site page **Gold corpus & eval**. Tests and scripts only.

To score identity-clue clumps in masked text (report only):

```python
from pdf_anonymizer_core.risk import assess_linkage_risk, write_risk_report

report = assess_linkage_risk(anonymized_text)
write_risk_report(report, "data/anonymized/note.anonymized.md")
```

To scan a masked string for leftovers (report only, no rewrite):

```python
from pdf_anonymizer_core.verify import verify_anonymized_text, write_residual_report

report = verify_anonymized_text(anonymized_text)
write_residual_report(report, "data/anonymized/note.anonymized.md")
```

To keep only some countries' national-ID regexes (plus every universal pattern):

```python
from pdf_anonymizer_core.conf import filter_regex_patterns, get_config_for_profile, ConfigProfile

only_us_gb = filter_regex_patterns(["US", "GB"])
cfg = get_config_for_profile(ConfigProfile.BEST_SPEED, countries=["US", "GB"])
```

---

## See Also

- **[Main Documentation](https://leo-gan.github.io/anonymizer/)** — Full project guides and 101 course.
- **[CLI Package README](../pdf-anonymizer-cli/README.md)** — Command line interface usage.
- **[Recipes & Common Workflows](https://leo-gan.github.io/anonymizer/project/recipes/)** — Practical SDK examples (including profiles, caching, and advanced usage).
- **[API Reference (auto)](https://leo-gan.github.io/anonymizer/project/api-reference/)** — Detailed function signatures.
- **[Troubleshooting](https://leo-gan.github.io/anonymizer/project/troubleshooting/)** — Common issues when using the core library.
- **[Architecture](https://leo-gan.github.io/anonymizer/project/architecture/)** — How the anonymization pipeline works internally.