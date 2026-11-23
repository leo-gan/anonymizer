# PDF Anonymizer Documentation

`pdf-anonymizer` is a reversible, context-aware document [pseudonymizer](project/terminology.md) for PDF, Markdown, plain text, Word (`.docx`), CSV, and Excel (`.xlsx`) files. It combines linear-time RE2 pattern matching (`id-extract`), optional local span NER (GLiNER), and multi-provider language models (local Ollama or remote APIs) to replace personal identifiers with typed placeholders (`PERSON_1`, `EMAIL_1`) alongside a separate mapping file. It is an engineering aid, not a legal compliance certificate.

---

## Documentation Sections

| Section | Contents |
|---|---|
| **[Privacy & Anonymization 101](101/index.md)** | Four-lecture course covering threat models, legal definitions, disclosure-control history, formal privacy models ($k$-anonymity, $\ell$-diversity, $t$-closeness, differential privacy), and an architectural case study. |
| **[Project Docs](project/index.md)** | Installation, CLI and Python SDK references, HTTP service, practical workflows, architecture, mapping encryption design, and gold-corpus evaluation results. |
| **[id-extract](id-extract/index.md)** | Standalone RE2 and checksum detector for structured identifiers across 30+ countries, with official agency and statutory citations. |
| **[Essays](essays/index.md)** | Conceptual essays on serialization, copying, and privacy boundaries. |

---

## Quick Start

Install the development workspace with [uv](https://astral.sh/docs/uv):

```bash
git clone https://github.com/leo-gan/anonymizer.git
cd anonymizer
uv sync --group dev
```

Anonymize a document (uses `best-speed` by default; pass `--no-llm` for offline regex-only mode, or `--model-name "ollama/phi4-mini"` for local inference):

```bash
pdf-anonymizer run data/sample.pdf
```

Restore the original values locally from the mapping file:

```bash
pdf-anonymizer deanonymize \
  data/anonymized/sample.anonymized.md \
  data/mappings/sample.mapping.json
```

---

## Round-Trip Demo

Two scripts demonstrate hybrid detection (RE2 + LLM) and round-trip verification on an open-access arXiv paper injected with synthetic PII:

```bash
uv run python scripts/prepare_demo_pdf.py
uv run python scripts/demo_anonymize.py
```

For empirical accuracy and leftover-rate benchmarks across 6,761 public documents, see [Evaluation Results](project/eval-results.md).
