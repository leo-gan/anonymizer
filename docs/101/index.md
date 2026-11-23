---
description: Anonymization Handbook — an open, academic-style curriculum on statistical disclosure control, formal privacy models, document leakage, cryptography, benchmarks, and failure case studies.
---

# Anonymization Handbook

A concise, academic-style reference and nine-lecture curriculum covering statistical disclosure control, formal privacy models, file-format leakage, cryptographic pseudonymization, and unstructured text evaluation. No prior background in privacy engineering is assumed.

**Lectures 1–8** and the reference compendia are **vendor-neutral**, grounded in peer-reviewed literature and international standards (ISO/IEC 20889, NIST SP 800-188, GDPR, HIPAA). **Lecture 9** examines how the companion open-source tool (`pdf-anonymizer`) implements a specific subset of these methods — and where its guarantees stop.

---

## Curriculum

### Part I — Foundations & Formal Theory

| Lecture | Topic | Key Concepts |
|---|---|---|
| [1. Problem, Threats, and Law](why-anonymization.md) | Why naive redaction fails | Direct vs. quasi-identifiers, anonymization vs. pseudonymization, GDPR / HIPAA / CCPA, application domains. |
| [2. Historical Development](history.md) | Evolution of disclosure control | Chronology from Fellegi (1972) and Dalenius (1977) to differential privacy and TAB (2022). |
| [3. Formal Models and Methods](techniques.md) | Privacy mechanisms | Deterministic transforms, $k$-anonymity, $\ell$-diversity, $t$-closeness, $(\varepsilon, \delta)$-differential privacy, synthetic data, NLP de-identification. |
| [4. Attacker Models and Risk](risk-and-attackers.md) | Formalizing disclosure risk | Prosecutor, journalist, and marketer risk; WP29 criteria (*singling out*, *linkability*, *inference*); ML/LLM membership and attribute inference. |

### Part II — Systems, Cryptography & Evaluation

| Lecture | Topic | Key Concepts |
|---|---|---|
| [5. Document & File-Format Leakage](document-leakage.md) | Hidden container surfaces | PDF content streams vs. overlay boxes, `/Prev` history, XMP/`/Info`; OOXML `w:del` and split runs; spreadsheet formulas and display formats. |
| [6. Pseudonymization & Crypto](pseudonymization-crypto.md) | Key hygiene and reversibility | Unsalted hash failure, keyed HMAC, NIST SP 800-38G FPE (FF1 vs. FF3-1), Argon2id + AES-256-GCM + AAD mapping custody. |
| [7. Evaluation & Benchmarks](evaluation-and-benchmarks.md) | Measuring leakage honestly | Direct vs. quasi recall, mention vs. entity $F_1$, leftover rate vs. utility, public corpora (TAB, i2b2, Gretel), and the synthetic gap. |
| [8. Choosing a Method](decision-framework.md) | Decision framework | Selection flowchart and matrix across data modalities, release contexts, open-source tooling classes, and engineering anti-patterns. |

### Part III — Reference Implementation

| Lecture | Topic | Key Concepts |
|---|---|---|
| [9. Case Study: `pdf-anonymizer`](how-different.md) | Concrete system design | Mapping Lectures 1–8 onto hybrid RE2 + GLiNER + LLM detection, indirect identifiers, span replacement, and measured quality. |

---

## Reference Compendia

- **[Compendium of Anonymization Failures](failure-compendium.md)** — Real-world privacy breaches organized by root cause (linkage, high-dimensional uniqueness, broken hashing, file-format leaks, LLM extraction).
- **[Reading List, Standards & Ecosystem](reading-list.md)** — Curated bibliography of technical standards (ISO/IEC 20889, NIST SP 800-188), foundational papers, public corpora, and open-source tools.
- **[Standards-Aligned Glossary](../project/terminology.md)** — Cross-standard comparison (ISO/IEC 20889, NIST, GDPR, HIPAA) plus project terms.
- **[Identifier Atlas (`id-extract`)](../id-extract/index.md)** — 38-country statute-cited catalog of structured identifiers and [Check-Digit Algorithms](../id-extract/checksums.md).
- **[Empirical Evaluation Results](../project/eval-results.md)** — Measured mention $F_1$ and leftover rates on 6,761 public documents.
- **[Essays](../essays/index.md)** — Conceptual notes outside the lecture sequence.

---

## Citing This Handbook

Machine-readable citation metadata is provided in [`CITATION.cff`](https://github.com/leo-gan/anonymizer/blob/main/CITATION.cff) at the repository root.
