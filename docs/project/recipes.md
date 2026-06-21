# Recipes & Common Workflows

This page contains practical, end-to-end examples for common real-world usage patterns with PDF Anonymizer.

Use these recipes as starting points and adapt the commands or code to your environment.

---

## Fully Local & Private Anonymization (Ollama)

Run everything on your own machine so no document data ever leaves your computer.

**Prerequisites**

- Ollama installed and running (`ollama serve`)
- A model pulled, e.g. `ollama pull phi4-mini` or `gemma:7b`

**CLI**

```bash
pdf-anonymizer run contract.pdf \
  -p best-speed \
  --model-name "ollama/phi4-mini"
```

**SDK (Python)**

```python
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.prompts import detailed
from pdf_anonymizer_core.conf import get_config_for_profile, ConfigProfile

config = get_config_for_profile(ConfigProfile.BEST_SPEED, model_name="ollama/phi4-mini")

anonymized, mapping = anonymize_file(
    file_path="contract.pdf",
    characters_to_anonymize=config.chunk_size,
    prompt_template=detailed.prompt_template,
    model_name=config.model_name,
    chunk_overlap=config.chunk_overlap,
    max_retries=config.max_retries,
    base_retry_delay=config.base_retry_delay,
    max_retry_delay=config.max_retry_delay,
)
```

**Notes**
- The `ollama` extra must be installed: `pip install "pdf-anonymizer-core[ollama]"` (or use the dev workspace).
- `OLLAMA_HOST` can be set in your `.env` if Ollama is not on the default localhost:11434.
- All processing (including LLM calls) is local.

---

## Anonymize → Send to External AI / Service → Deanonymize Locally

The classic reversible workflow: protect the original data, let an untrusted system (public ChatGPT, Claude, a third-party analysis service, translation pipeline, etc.) work on the masked version, then recover the real values locally.

**Step-by-step**

1. Anonymize locally (or with a trusted key):

   ```bash
   pdf-anonymizer run sensitive-report.pdf -p best-quality
   ```

   This produces:
   - `data/anonymized/sensitive-report.anonymized.md`
   - `data/mappings/sensitive-report.mapping.json` (keep this file very secure)

2. Send **only** the `.anonymized.md` file (never the mapping) to the external system or paste it into a public LLM.

3. Receive the processed result (still containing placeholders such as `PERSON_1`, `ORGANIZATION_3.v_1`, etc.).

4. Deanonymize locally:

   ```bash
   pdf-anonymizer deanonymize \
     data/anonymized/sensitive-report.anonymized.md \
     data/mappings/sensitive-report.mapping.json
   ```

   The final restored document appears under `data/deanonymized/`.

You can repeat step 4 any time you receive new output from the external system as long as you still have the original mapping file.

**Tip**: The mapping file is the "key". Treat it like a password or cryptographic material.

---

## Batch Processing Multiple Files

The CLI accepts multiple input paths.

```bash
pdf-anonymizer run \
  reports/q1.pdf \
  notes/meeting-2025-06.md \
  archive/transcript.txt \
  -p best-cost
```

Each file is processed independently. Results are written using the original stem name into the conventional output directories (`data/anonymized/`, `data/mappings/`, etc.).

For very large batch jobs you may want to:
- Use the faster/cheaper profile (`best-cost` or `best-speed`)
- Monitor `app.log` (written to the current working directory)
- Run inside a script that collects exit codes

---

## Anonymize Only Specific Entity Types

Use a text file containing the entity types you care about (one per line, uppercase).

Example filter file (`only-people-orgs.txt`):

```
PERSON
ORGANIZATION
```

Run:

```bash
pdf-anonymizer run document.pdf --anonymized-entities only-people-orgs.txt
```

Only entities whose `type` matches one of the listed values (after the hybrid Regex + LLM stage) will be replaced. Everything else stays in clear text.

This is useful when you want to protect names and companies but leave dates, addresses, or other categories untouched.

See the example file at `packages/pdf-anonymizer-cli/entities.example.txt`.

---

## Choose and Override Configuration Profiles

Profiles are the recommended way to select a quality/speed/cost tradeoff (see also the table in the [CLI Reference](cli-usage.md)).

**Quick introspection (Python)**

```python
from pdf_anonymizer_core.conf import get_config_for_profile, ConfigProfile

cfg = get_config_for_profile(ConfigProfile.BEST_QUALITY)
print(cfg.model_dump())   # see exactly what the profile resolved to
```

Any scalar override (`model_name`, `prompt_name`, `chunk_size`) takes precedence.

---

## Use the Python SDK in Pipelines / Applications

Minimal end-to-end example using the helper that mirrors the CLI:

```python
import json
from pdf_anonymizer_core.conf import get_config_for_profile, ConfigProfile
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.prompts import detailed
from pdf_anonymizer_core.utils import deanonymize_file

# 1. Configure like the CLI would
cfg = get_config_for_profile(ConfigProfile.BEST_SPEED)

# 2. Anonymize
anonymized_text, raw_mapping = anonymize_file(
    file_path="data/contract.pdf",
    characters_to_anonymize=cfg.chunk_size,
    prompt_template=detailed.prompt_template,
    model_name=cfg.model_name,
    chunk_overlap=cfg.chunk_overlap,
    max_retries=cfg.max_retries,
    base_retry_delay=cfg.base_retry_delay,
    max_retry_delay=cfg.max_retry_delay,
)

# 3. (Optional) Save the artifacts yourself
with open("contract.anonymized.md", "w", encoding="utf-8") as f:
    f.write(anonymized_text)

placeholder_to_original = {v: k for k, v in raw_mapping.items()}
with open("contract.mapping.json", "w", encoding="utf-8") as f:
    json.dump(placeholder_to_original, f, indent=2)

# 4. Later: restore
deanonymized_file_path, stats_file_path = deanonymize_file(
    "contract.anonymized.md",
    "contract.mapping.json",
)
print("Deanonymized file saved to:", deanonymized_file_path)
print("Stats file saved to:", stats_file_path)
```

You can also pass a custom list for `anonymized_entities` or supply your own `regex_patterns` dict for the first-stage NER.

---

## Working with Mapping Files and Deanonymization Statistics

After deanonymization the tool always writes a stats file:

`data/stats/<stem>.deanonymization_stat.json`

Example contents:

```json
{
  "anonymized_file": "...",
  "mapping_file": "...",
  "deanonymized_file": "...",
  "unused_mappings": ["PERSON_7"],
  "not_found_mappings": []
}
```

- `unused_mappings`: placeholders that existed in the map but were never present in the anonymized text (harmless).
- `not_found_mappings`: placeholders found in the anonymized text that had no entry in the map (usually indicates a corrupted or partial map).

These stats are useful for audit/compliance pipelines.

The mapping file format is `placeholder → original` (the direction used at deanonymization time). The CLI and `deanonymize_file` also accept the legacy `original → placeholder` direction and auto-detect.

---

## LLM Response Caching

By default the core caches successful LLM responses (keyed by model + prompt hash) to `data/cache/llm_responses.json`.

Benefits:
- Re-running the same document (or very similar chunks) is dramatically faster and cheaper.
- Helps during development and iterative prompt tuning.

**Disable or relocate the cache (SDK)**

```python
from pdf_anonymizer_core.llm_provider import configure_cache
from pdf_anonymizer_core.conf import get_config_for_profile, ConfigProfile

cfg = get_config_for_profile(ConfigProfile.BEST_SPEED)

configure_cache(
    enabled=False,                    # or True
    cache_dir=cfg.cache_dir,
    cache_file=cfg.cache_file,
)
```

The CLI always enables caching according to the profile's `AppConfig`. Delete or move the cache directory for a cold run.

---

## Processing Very Large Documents

PDF Anonymizer is designed for files up to ~1 GB thanks to streaming chunking.

**Practical tips**

- Start with the `best-cost` profile (larger chunks, fewer LLM calls).
- Increase `--characters-to-anonymize` further if your model has a large context window:

  ```bash
  pdf-anonymizer run huge-book.pdf -p best-cost --characters-to-anonymize 120000
  ```

- Use Markdown-aware splitting (automatic for `.pdf` and `.md`). Plain `.txt` falls back to recursive character splitting.
- Watch the log output: each chunk is logged (`Identifying entities in part X/Y...`).
- The `chunk_overlap` (profile-driven) helps the model see context across chunk boundaries for coreference.
- If you hit rate limits, the built-in retry logic with exponential backoff (and jitter) will help on transient errors.

---

## Advanced: Custom First-Stage Regex (SDK only)

The hybrid approach runs a fast deterministic RE2 (google-re2) regex pass before every LLM call.
You can supply your own set (or a filtered slice of the built-in collection):

```python
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.conf import get_config_for_profile, ConfigProfile, DEFAULT_REGEX_PATTERNS
from pdf_anonymizer_core.prompts import detailed

# Option A: completely custom
custom_regex = {
    "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "EMPLOYEE_ID": r"\bEMP-\d{6}\b",
    # ...
}

# Option B: use the built-in library (RE2-powered, 30+ countries)
# It includes: EMAIL, URL, CREDIT_CARD, IBAN, CRYPTO_*, VIN, MAC, IPV4/6,
# DATE_ISO, CURRENCY_AMOUNT, BIC_SWIFT + country partitioned IDs:
# SSN_US / SIN_CA / NINO_GB / INSEE_FR / DNI_ES / CODICE_FISCALE_IT / AADHAAR_IN / RESIDENT_ID_CN / ...
# VAT_*/EIN_*/business numbers, DRIVERS_LICENSE_*, PASSPORT_*, MEDICAL_* etc.
country_focused = {
    k: v for k, v in DEFAULT_REGEX_PATTERNS.items()
    if k in ("EMAIL", "CREDIT_CARD", "IBAN", "SSN_US", "SIN_CA", "NINO_GB", "INSEE_FR",
             "RESIDENT_ID_CN", "PAN_IN", "VAT_FR", "VAT_DE", "DRIVERS_LICENSE_US")
}

cfg = get_config_for_profile(ConfigProfile.BEST_SPEED)

text, mapping = anonymize_file(
    file_path="internal-log.txt",
    characters_to_anonymize=cfg.chunk_size,
    prompt_template=detailed.prompt_template,
    model_name=cfg.model_name,
    regex_patterns=country_focused,   # or custom_regex or DEFAULT_REGEX_PATTERNS
    # ... other config fields
)
```

All regex patterns are RE2-safe (linear time, no ReDoS). Entity type keys (upper-cased) become the
placeholder prefixes (IBAN_3, SSN_US_2, CRYPTO_ETH_1 ...). The LLM stage still runs afterwards and
adds semantic detections the regex stage could not catch. See `conf.py` (the giant docstring on
`DEFAULT_REGEX_PATTERNS`) and `regex_ner.py` for the full catalogue and country partitioning rules.

The default collection already covers the mandatory countries (USA, Canada, UK, Spain, Italy,
France, India, China) plus 25+ more via dedicated national/tax/driver/VAT/business patterns plus
universals that apply everywhere (credit cards, IBANs used across Europe, crypto, VIN, MAC, etc.).

---

## Debugging, Logs & Observability

The CLI always configures logging to both the console (INFO level) and a file:

- `app.log` in the current working directory (or wherever the process starts)
- Real-time progress per chunk: "Identifying entities in part X/Y...", timing, regex vs LLM counts, cache hits, retry messages, etc.

When things go wrong the log is the first place to look (rate-limit errors, provider auth problems, JSON parse failures from the LLM, empty extraction, etc.).

You can also delete or move `data/cache/llm_responses.json` to force a cold run with no cached LLM responses.

---

## See Also

- **[CLI Reference](cli-usage.md)** — complete flag reference, model aliases, and the profiles table.
- **[SDK & API Usage](api-usage.md)** — lower-level function signatures and returns.
- **[API Reference (auto)](api-reference.md)** — living signature documentation generated from source docstrings.
- **[Architecture Design](architecture.md)** — how chunking, consolidation, mapping, and reversal actually work.
- **[Installation & Setup](installation.md)** — provider extras and environment variables.
- **[Troubleshooting](troubleshooting.md)** — solutions to common problems encountered when following these recipes.

For conceptual background see the [Privacy & Anonymization 101](../101/index.md) track.
