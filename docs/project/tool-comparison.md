---
description: Neutral technical comparison of pdf-anonymizer and id-extract against Textwash, ARX Data Anonymizer, Microsoft Presidio, custom spaCy scripts, and MAT2.
---

# Tool Comparison

No single open-source tool covers every anonymization task. This page provides a neutral comparison to help researchers and engineers choose the right tool — including when another project is a better fit than `pdf-anonymizer`.

---

## Capability Overview

| Dimension | `pdf-anonymizer` & `id-extract` | Textwash | ARX Data Anonymizer | Microsoft Presidio | Custom `spaCy` Script | MAT2 |
|---|---|---|---|---|---|---|
| **Primary target** | Multi-format documents & tables (PDF, DOCX, CSV, XLSX, MD, TXT) | Qualitative/social-science plain text | Relational microdata tables | Text & image PII middleware (Python / Docker / Spark) | Custom NLP text pipelines | Binary file metadata scrubbing |
| **Structured IDs & checksums** | 38 countries, 26 check-digit validators, ReDoS-safe RE2 (`id-extract`) | Limited | Schema-based | Strong US/global recognizers; extensible | Manual regex | None |
| **Contextual / indirect clues** | `detailed` LLM prompt (`INDIRECT`) + linkage-risk report | Generalizes named categories | Quasi-identifier combinations ($Q$) | Standard NER + context words | Standard NER only | None |
| **Formal tabular privacy** | Optional CSV/Excel `--k` + $\ell$/$t$ report (basic aid) | None | Full $k$-anonymity, $\ell$-diversity, $t$-closeness, $(\varepsilon,\delta)$-DP, prosecutor/journalist/marketer risk | None | None | None |
| **Reversible pseudonymization** | Built-in typed coreferent placeholders (`PERSON_1.v_1`) + encrypted/ephemeral maps + audit stats | Consistent replacement tags | Irreversible by design | Requires custom session/vault wrapper for stateful restoration | DIY | Irreversible |
| **Native file containers** | PDF (Markdown or native redact + metadata wipe), DOCX, CSV, XLSX | Plain text / scripts | CSV / SQL tables | Text + image OCR (`presidio-image-redactor`); PDF layout requires external parsing | DIY | PDF, DOCX, images, audio, video |
| **Offline / local execution** | Yes (`--no-llm`, CPU GLiNER, or local Ollama) | Yes | Yes (Java desktop/library) | Yes (`spaCy` / transformer locally) | Yes | Yes |
| **Dependency footprint** | `id-extract`: only `google-re2`. Core: modular PEP 508 extras | Moderate (NLP weights) | JVM | Heavy (`spaCy` + models + optional transformers) | Moderate–heavy | Lightweight system tools |

---

## When to Choose Another Tool Instead

- **Choose [ARX Data Anonymizer](https://arx.deidentifier.org/) (or `sdcMicro`)** when publishing relational research or clinical microdata tables that require rigorous population/journalist risk estimation, multi-level generalization hierarchies, or formal differential privacy. `pdf-anonymizer --k` is a lightweight CSV/Excel aid, not a replacement for ARX.
- **Choose [Microsoft Presidio](https://microsoft.github.io/presidio/)** when you need a mature, Apache-2.0 enterprise text/image middleware with native PySpark UDFs, Kubernetes Helm charts, or existing LiteLLM guardrail integrations. *(You can also embed `id-extract` inside a custom Presidio `EntityRecognizer` — see [id-extract in Data & Security Pipelines](id-extract-pipelines.md).)*
- **Choose [OpenDP](https://opendp.org/) or [Tumult Analytics](https://www.tmlt.dev/)** when releasing aggregate statistics or query summaries with formal $(\varepsilon, \delta)$-differential privacy guarantees.
- **Choose [MAT2](https://0xacab.org/jvoisin/mat2)** when you only need to strip hidden metadata from images, audio, video, or binary office containers without modifying body text.
- **Choose `pdf-anonymizer`** when you need a **local-first, reversible multi-format workflow** across PDF, `.docx`, `.csv`, and `.xlsx` with built-in typed coreference (`PERSON_1.v_1`), encrypted mapping files, indirect contextual clue detection (`detailed` prompt), and auditable residual/risk JSON reports.
- **Choose `id-extract` standalone** when you need fast, ReDoS-safe, zero-ML-dependency structured identifier extraction across 38 countries with mathematical check-digit validation and statutory documentation.

---

## See Also

- [Lecture 8: Decision Framework](../101/decision-framework.md) — vendor-neutral method selection flowchart
- [Reading List, Standards & Ecosystem](../101/reading-list.md) — broader open-source ecosystem directory
- [Evaluation Results](eval-results.md) — empirical leftover rates and $F_1$ scores on 6,761 documents
