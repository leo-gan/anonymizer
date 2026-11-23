# Anonymization Handbook & PDF Anonymizer

[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue?style=flat-square)](https://leo-gan.github.io/anonymizer/)
[![CI Workflow](https://github.com/leo-gan/anonymizer/actions/workflows/lint.yml/badge.svg)](https://github.com/leo-gan/anonymizer/actions)

An open, academic-style reference on **data anonymization, pseudonymization, and disclosure risk** — paired with a 38-country statute-cited structured identifier atlas (`id-extract`), empirical benchmarks, and a reversible open-source document pseudonymizer (`pdf-anonymizer`).

The software hides personal details in documents and tables and can restore them locally from a mapping file. It is a reversible [pseudonymizer](https://leo-gan.github.io/anonymizer/project/terminology/), not a legal compliance certificate.

---

## The Anonymization Handbook

Read the full documentation site at **[leo-gan.github.io/anonymizer/](https://leo-gan.github.io/anonymizer/)**:

- **[Curriculum (Lectures 1–9)](https://leo-gan.github.io/anonymizer/101/)** — Threat models and GDPR/HIPAA/CCPA; historical chronology; $k$-anonymity, $\ell$-diversity, $t$-closeness, and $(\varepsilon, \delta)$-differential privacy; prosecutor/journalist/marketer risk and LLM attacks; PDF/DOCX/spreadsheet leakage surfaces; cryptographic pseudonymization; evaluation benchmarks; method decision framework; and a system case study.
- **[Compendium of Anonymization Failures](https://leo-gan.github.io/anonymizer/101/failure-compendium/)** — Nine canonical real-world breaches (GIC/Weld, AOL, Netflix, mobility/card metadata, NYC Taxi MD5, PDF overlays, LLM extraction and attribute inference).
- **[Reading List, Standards & Ecosystem](https://leo-gan.github.io/anonymizer/101/reading-list/)** — Curated guide to ISO/IEC 20889, NIST SP 800-188, NIST SP 800-38G, foundational papers, public corpora, and open-source tools.
- **[Standards-Aligned Glossary](https://leo-gan.github.io/anonymizer/project/terminology/)** — Cross-standard definitions (ISO/IEC 20889, NIST, GDPR, HIPAA) alongside product terms.
- **[Identifier Atlas (`id-extract`)](https://leo-gan.github.io/anonymizer/id-extract/)** — 38-country catalog with official agency/statutory citations and [Check-Digit Algorithms](https://leo-gan.github.io/anonymizer/id-extract/checksums/).
- **[Essays](https://leo-gan.github.io/anonymizer/essays/)** — Short conceptual notes on serialization, copying, and privacy boundaries.

---

## Companion Software Capabilities

| Feature | Summary |
|---|---|
| Reversible pseudonymization | Personal values become typed placeholders (`PERSON_1`) plus a separate mapping file (`0600`; optional AES-256-GCM + Argon2id lock or `--ephemeral-mapping`). Not irreversible anonymization. |
| Hybrid detection | Linear-time RE2 patterns (`id-extract`), optional local span NER (GLiNER), and multi-provider LLMs (local [Ollama](https://ollama.com/) or remote Gemini, OpenAI, Anthropic, Hugging Face, OpenRouter). |
| Checksums & `_LIKE` labels | 26 registered validators (Luhn, ISO 13616 mod-97, Verhoeff, weighted sums). Failed checks stay masked as `TYPE_LIKE` (e.g., `IBAN_LIKE`) or are dropped for bare digit runs. |
| Indirect identifiers | The `detailed` prompt (`-p best-quality`) hides identifying prose clues without explicit names (`INDIRECT`). |
| Operators & table privacy | Per-type operators (`replace`, `mask`, `hash`, `generalize`, `shift`, `fake`, `encrypt`), HIPAA Safe Harbor coverage aid, keep/deny lists, and optional CSV/Excel $k$-anonymity (`--k`). |
| Multi-format support | PDF (Markdown export, `--ocr` via Tesseract, or sanitized native `--output-pdf` / `--redact`), Markdown, plain text, Word (`.docx`), CSV, and Excel (`.xlsx`). |
| Verification & auditing | Post-masking residual leftover scan (`verify` / `apply`), linkage-risk report (`report`), deanonymization stats, and `purge` for local artifacts. |

## What Leaves This Machine

The program does not send usage data and does not upload logs. The CLI writes `app.log` in the working directory.

Document text leaves the machine only during a call to a remote language-model provider. The default profile is `best-speed` (`gemini-2.5-flash`). Without the `ner` extra, a normal run sends each chunk to Google when `GOOGLE_API_KEY` is set. With `[ner]`, `best-speed` uses local span NER and skips the remote call. `--no-llm`, `-p regex-only`, and an `ollama/` model name keep all text on this machine. The first local span-NER run downloads model weights from Hugging Face; an install without `[ner]` downloads no models.

Each GitHub Release ships wheels with `SHA256SUMS` and a signed build attestation; PyPI stores a publish attestation on each uploaded file.

## Measured Quality

On 6,761 public documents (Gretel, Presidio synthetic, TAB ECHR court cases, and domain fixtures):

- **Regex-only:** 57.6% leftover rate, mention $F_1$ 0.262, structured leftover 3.9%.
- **RE2 + local Gemma 4 12B (`detailed`):** 24.1% leftover rate, mention $F_1$ 0.564, structured leftover 0.1%. Leftovers stay under 7% in every domain except TAB legal judgments (56.4%, driven by dates and demographic quasi-identifiers rather than names).
- **82-document comparison:** Gemini 4 Argon leaves 43.8% vs. Gemma 4's 50.5%, with tighter direct-identifier precision from Gemma.

Full tables and charts: **[Evaluation Results](https://leo-gan.github.io/anonymizer/project/eval-results/)**.

---

## Monorepo Packages

| Package | Role | README |
|---|---|---|
| `packages/id-extract` | Standalone RE2 + checksum structured identifier detector (offsets only, 38 countries) | [README](./packages/id-extract/README.md) |
| `packages/pdf-anonymizer-core` | Core library: loaders, hybrid detection, operators, mapping crypto, table privacy, eval | [README](./packages/pdf-anonymizer-core/README.md) |
| `packages/pdf-anonymizer-cli` | Typer CLI (`run`, `deanonymize`, `verify`, `report`, `apply`, `purge`) | [README](./packages/pdf-anonymizer-cli/README.md) |
| `packages/pdf-anonymizer-api` | Optional local FastAPI HTTP service (core only, no authentication) | [README](./packages/pdf-anonymizer-api/README.md) |

---

## Quick Start

Install the development workspace with [uv](https://astral.sh/docs/uv):

```bash
git clone https://github.com/leo-gan/anonymizer.git
cd anonymizer
uv sync --group dev
```

Configure API keys in a root `.env` file only if using cloud providers (`GOOGLE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `HUGGING_FACE_TOKEN`, `OPENROUTER_API_KEY`, or optional `OLLAMA_HOST`, `ANONYMIZER_MAPPING_KEY`, `ANONYMIZER_FAKE_SECRET`, `ANONYMIZER_ENCRYPT_SECRET`).

```bash
# Default run (best-speed)
uv run pdf-anonymizer run document.pdf

# Careful profile (also masks indirect identity clues)
uv run pdf-anonymizer run contract.pdf -p best-quality

# Fully local with Ollama or offline regex-only
uv run pdf-anonymizer run notes.md --model-name "ollama/phi4-mini"
uv run pdf-anonymizer run logs.txt --no-llm

# Restore original values locally
uv run pdf-anonymizer deanonymize \
  data/anonymized/document.anonymized.md \
  data/mappings/document.mapping.json
```

### Round-Trip Demo & Tests

```bash
# Download an arXiv PDF, inject synthetic PII, anonymize, and verify restoration
uv run python scripts/prepare_demo_pdf.py
uv run python scripts/demo_anonymize.py

# Run test suite and strict docs validation
uv run pytest
uv run mkdocs build --strict
```

---

## Documentation & Citation

- **[Handbook & Full Docs](https://leo-gan.github.io/anonymizer/)** — Lectures, Failure Compendium, Reading List, Identifier Atlas, CLI/SDK/HTTP references, Recipes, Architecture, and Troubleshooting.
- **Citation:** See [`CITATION.cff`](./CITATION.cff) for machine-readable citation metadata.
