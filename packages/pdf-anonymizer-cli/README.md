# PDF Anonymizer CLI

Command-line interface (`pdf-anonymizer`) for reversible, context-aware anonymization and restoration of PDF, Markdown, plain text, Word (`.docx`), CSV, and Excel (`.xlsx`) files. Built on `pdf-anonymizer-core`.

This tool is a reversible document pseudonymizer, not a legal compliance certificate. Full CLI reference and the companion **Anonymization Handbook** live at **[leo-gan.github.io/anonymizer/](https://leo-gan.github.io/anonymizer/)**.

## Installation

Install with the provider and format extras you need:

```bash
pip install "pdf-anonymizer-cli[google]"
pip install "pdf-anonymizer-cli[ollama]"
pip install "pdf-anonymizer-cli[openai,anthropic]"
pip install "pdf-anonymizer-cli[huggingface,openrouter]"
pip install "pdf-anonymizer-cli[excel,docx,ner]"
```

Scanned PDF OCR (`--ocr`) requires the system `tesseract` binary on `PATH`.

## Environment Variables

The CLI loads a `.env` file automatically from the current working directory or any parent directory:

- Provider credentials (only for remote models): `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `HUGGING_FACE_TOKEN`, `OPENROUTER_API_KEY`
- `OLLAMA_HOST`: optional local Ollama URL (default `http://localhost:11434`)
- `ANONYMIZER_MAPPING_KEY`: optional passphrase for `--mapping-passphrase` (`*.mapping.json.enc`)
- `ANONYMIZER_FAKE_SECRET`: required seed for `--operator TYPE=fake`
- `ANONYMIZER_ENCRYPT_SECRET`: required secret for `--operator TYPE=encrypt`

## Commands

| Command | Purpose |
|---|---|
| `pdf-anonymizer run FILE [FILE ...]` | Mask one or more files, write anonymized outputs, mapping (`0600`), residual report, and risk report. |
| `pdf-anonymizer deanonymize FILE MAP` | Restore original values locally and write `*.deanonymization_stat.json`. |
| `pdf-anonymizer verify FILE` | Scan an already-masked file for leftover structured (or `--verify-llm`) PII. Report only. |
| `pdf-anonymizer report FILE` | Score identity-clue linkage clumps in an already-masked file. Report only. |
| `pdf-anonymizer apply REPORT.json` | Apply accepted leftover hits (`--accept-all`, `--accept`, `--skip`, or interactive TTY) back onto the masked file. |
| `pdf-anonymizer purge [--root PATH]` | Delete local `data/cache/`, `data/mappings/`, `data/stats/`, and `app.log` (preserves anonymized/deanonymized documents). |

## Common Examples

```bash
# Default run (best-speed)
pdf-anonymizer run document.pdf

# Careful profile (also masks indirect identity clues)
pdf-anonymizer run contract.pdf -p best-quality

# Fully local with Ollama (fail-closed via --offline) or regex-only
pdf-anonymizer run notes.md -p best-cost --model-name "ollama/phi4-mini" --offline
pdf-anonymizer run logs.txt --no-llm --offline

# Country filter, operators, keep/deny lists, and encrypted mapping
pdf-anonymizer run notes.pdf contract.pdf \
  -p best-quality \
  --countries US,GB \
  --opt-in all \
  --operator CREDIT_CARD=mask \
  --operator DATE=generalize \
  --keep-list keep.txt \
  --mapping-passphrase 'a long secret'

# Native sanitized PDF (reversible --output-pdf, or irreversible --redact) and scanned OCR
pdf-anonymizer run scan.pdf --ocr --output-pdf

# Optional CSV/Excel table k-anonymity + l-diversity / t-closeness report
pdf-anonymizer run roster.csv --no-llm --k 5 --quasi-columns zip,gender --sensitive-column diagnosis

# Restore locally (pass --mapping-passphrase / --source-sha256 / --encrypt-secret as needed)
pdf-anonymizer deanonymize \
  data/anonymized/document.anonymized.md \
  data/mappings/document.mapping.json
```

Notes: LLM response caching is **off by default** (pass `--cache` to opt in; cached files are mode `0600` with 24-hour TTL). Text and PDF are chunked in memory; CSV, Excel, and Word inputs are capped at 50 MiB (see [Large Documents](https://leo-gan.github.io/anonymizer/project/recipes/#processing-very-large-documents)).

## Documentation

- **[CLI Reference](https://leo-gan.github.io/anonymizer/project/cli-usage/)** — Complete option tables, profiles, and model aliases.
- **[Recipes & Workflows](https://leo-gan.github.io/anonymizer/project/recipes/)** — Practical end-to-end patterns.
- **[Troubleshooting](https://leo-gan.github.io/anonymizer/project/troubleshooting/)** — Common errors and fixes.
- **[Anonymization Handbook](https://leo-gan.github.io/anonymizer/101/)** — Formal privacy models, file-format leakage, and benchmarks.
