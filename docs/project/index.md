---
description: Developer documentation, CLI and Python SDK references, HTTP service, architecture, mapping encryption design, and evaluation benchmarks for pdf-anonymizer.
---

# Project Documentation

Technical reference, guides, and design notes for `pdf-anonymizer`. The repository is structured as a Python monorepo separating structured extraction, core anonymization logic, the CLI wrapper, and an optional HTTP service.

---

## Monorepo Layout

```text
anonymizer/
├── .github/workflows/          # CI, lint, release, and docs workflows
├── data/                       # Local data directory for sample inputs and outputs
├── docs/                       # MkDocs documentation sources
├── packages/
│   ├── id-extract/             # RE2 + checksum detector (span placements only)
│   ├── pdf-anonymizer-core/    # Core SDK (loaders, recognizers, operators, crypto, eval)
│   ├── pdf-anonymizer-cli/     # Typer CLI wrapper (pdf-anonymizer)
│   └── pdf-anonymizer-api/     # Optional FastAPI service (depends on core only)
├── tests/                      # Pytest suite, fuzz tests, and gold-corpus eval harness
├── Makefile                    # Developer task targets
├── pyproject.toml              # Workspace and dependency configuration
└── mkdocs.yml                  # Documentation site configuration
```

---

## Packages

- **`id-extract`** — Deterministic RE2 and checksum detector returning character offsets without modifying text. Ships every bundled country; filter at call time via `countries=` or `--countries`. See [id-extract](../id-extract/index.md).
- **`pdf-anonymizer-core`** — Document loaders (PDF via `pymupdf4llm` or Tesseract OCR, Markdown, plain text, `.docx`, `.csv`, `.xlsx`), hybrid detection (RE2, optional local GLiNER NER, multi-provider LLM router), prompt templates (`simple`, `detailed`, `hipaa`), span-based replacement, per-type operators, optional CSV/Excel $k$-anonymity (`table_privacy`), mapping encryption, residual verification, and linkage-risk reporting.
- **`pdf-anonymizer-cli`** — `Typer` CLI (`run`, `deanonymize`, `verify`, `report`, `apply`, `purge`) handling `.env` loading and standard output directories.
- **`pdf-anonymizer-api`** — Optional local FastAPI service depending only on `pdf-anonymizer-core`.

---

## Guide Index

### Guides
- [Installation](installation.md) — Workspace setup, PEP 508 extras, and environment variables.
- [Recipes & Workflows](recipes.md) — End-to-end CLI and SDK examples for common tasks.
- [Troubleshooting](troubleshooting.md) — Common failure modes and resolutions.

### Reference
- [CLI Reference](cli-usage.md) — Subcommands (`run`, `deanonymize`, `verify`, `report`, `apply`, `purge`), flags, profiles, and model aliases.
- [Python SDK](api-usage.md) — Programmatic entry points for text, tables, Word documents, and restoration.
- [HTTP Service & Docker](http-service.md) — Local FastAPI endpoints, Docker Compose, and AppArmor profile.
- [API Reference (auto)](api-reference.md) — Signature reference generated from source docstrings.
- [Terminology](terminology.md) — Canonical definitions for project terms and recognizer scores.

### Design & Evaluation
- [Architecture](architecture.md) — Processing pipeline, format-specific paths, and reversal internals.
- [Mapping Security](mapping-security.md) — Argon2id + AES-256-GCM envelope design, AAD binding, `0600` I/O, and memory hygiene.
- [Gold Corpus & Eval](gold-corpus.md) — Corpus sources, TAB-style metrics, and CI completeness gates.
- [Evaluation Results](eval-results.md) — Empirical leftover rates and $F_1$ scores on 6,761 public documents.
