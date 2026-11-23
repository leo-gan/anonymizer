---
description: Anonymization Handbook — an open academic reference on statistical disclosure control, formal privacy models, document leakage, benchmarks, and the companion pdf-anonymizer and id-extract packages.
---

# Anonymization Handbook & Reference Implementation

An open, academic-style reference on **data anonymization, pseudonymization, and disclosure risk** — paired with a 38-country statute-cited identifier atlas (`id-extract`), empirical text-anonymization benchmarks, and a reversible open-source document pseudonymizer (`pdf-anonymizer`).

---

## 1. The Anonymization Handbook

The core reference track is vendor-neutral and grounded in peer-reviewed research and international standards (ISO/IEC 20889, NIST SP 800-188, GDPR, HIPAA):

| Resource | Contents |
|---|---|
| **[Curriculum (Lectures 1–9)](101/index.md)** | Threat models and privacy law; historical chronology; $k$-anonymity, $\ell$-diversity, $t$-closeness, and $(\varepsilon, \delta)$-DP; attacker models and risk metrics; PDF/DOCX/spreadsheet leakage; cryptographic pseudonymization; evaluation benchmarks; method decision framework; and a system case study. |
| **[Failure Compendium](101/failure-compendium.md)** | Nine canonical real-world privacy failures (GIC/Weld, AOL, Netflix, mobility/card metadata, NYC Taxi MD5, PDF overlays, LLM memorization and attribute inference) with primary citations. |
| **[Reading List & Standards](101/reading-list.md)** | Annotated guide to ISO/NIST/EU/HHS standards, foundational papers, public corpora (TAB, i2b2, MIMIC, MAPA, Gretel), and the open-source tooling ecosystem. |
| **[Standards-Aligned Glossary](project/terminology.md)** | Cross-standard comparison of privacy terminology (ISO/IEC 20889, NIST SP 800-188, GDPR, HIPAA) alongside software definitions. |
| **[Identifier Atlas (`id-extract`)](id-extract/index.md)** | 38-country catalog of structured national and payment identifiers with official issuing-agency and statutory citations, plus [Check-Digit Algorithms](id-extract/checksums.md). |
| **[Essays](essays/index.md)** | Short conceptual notes on serialization, copying, and privacy boundaries. |

---

## 2. Companion Open-Source Software

This repository also ships two modular Python tools that serve as a practical reference implementation and empirical testbed for the concepts in the handbook. Neither tool is a legal compliance certificate.

- **[`pdf-anonymizer`](project/index.md)** — Reversible, context-aware document pseudonymizer for PDF, Markdown, plain text, Word (`.docx`), CSV, and Excel (`.xlsx`). Combines RE2 pattern matching, optional local span NER (GLiNER), and local (Ollama) or remote LLMs with typed placeholders (`PERSON_1`), optional AES-256-GCM + Argon2id mapping encryption, optional CSV/Excel $k$-anonymity (`--k`), and post-masking residual/risk audits.
- **[`id-extract`](id-extract/index.md)** — Standalone RE2 and check-digit detector (`pip install id-extract`) returning character offsets without modifying text.
- **[Empirical Evaluation Results](project/eval-results.md)** — Measured mention $F_1$ and leftover rates across 6,761 public documents (Gretel, Presidio synthetic, TAB ECHR court judgments, and domain fixtures).

### Quick Start

```bash
git clone https://github.com/leo-gan/anonymizer.git
cd anonymizer
uv sync --group dev

# Anonymize (pass --no-llm for offline regex-only, or --model-name "ollama/phi4-mini" for local LLM)
pdf-anonymizer run data/sample.pdf

# Restore locally from the mapping file
pdf-anonymizer deanonymize \
  data/anonymized/sample.anonymized.md \
  data/mappings/sample.mapping.json
```
