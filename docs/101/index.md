# Privacy & Anonymization 101

A concise, four-lecture introduction to statistical disclosure control, formal privacy models, and unstructured text de-identification. No prior background in privacy engineering is assumed.

Lectures 1–3 cover general concepts from the research literature and privacy law. Lecture 4 examines how this project (`pdf-anonymizer`) applies a specific subset of those methods to documents and spreadsheets — and where its guarantees stop.

Canonical product terms (*pseudonymization*, *quasi-identifier*, *leftover*, *gold corpus*) are defined once in [Terminology](../project/terminology.md).

## Syllabus

| Lecture | Topic | Scope |
|---|---|---|
| [1. Problem, Threats, and Law](why-anonymization.md) | Why naive redaction fails | Direct vs. quasi-identifiers, re-identification attacks, regulatory definitions, application domains. |
| [2. Historical Development](history.md) | Evolution of disclosure control | Chronology from 1970s statistical disclosure control to differential privacy and text benchmarks. |
| [3. Formal Models and Methods](techniques.md) | Privacy mechanisms and metrics | Structural transforms, $k$-anonymity / $\ell$-diversity / $t$-closeness, differential privacy, NLP de-identification, and evaluation metrics. |
| [4. Unstructured Text Case Study](how-different.md) | System design of `pdf-anonymizer` | Indirect identifiers in prose, span-based reversible pseudonymization, verification reports, and honest scope limits. |

Related reading:

- [Terminology](../project/terminology.md) — project glossary and score definitions.
- [Evaluation Results](../project/eval-results.md) — measured mention $F_1$ and leftover rates on 6,761 public documents.
- [Essays](../essays/index.md) — conceptual notes outside the lecture sequence.
