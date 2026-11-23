---
description: Standards-aligned privacy glossary comparing ISO/IEC 20889, NIST SP 800-188, GDPR, and HIPAA definitions alongside canonical pdf-anonymizer product terms.
---

# Terminology

This glossary has two parts: **Part A** aligns general privacy terms across major international standards (ISO/IEC 20889, NIST SP 800-188, GDPR, and HIPAA), and **Part B** defines canonical **product** terms used across `pdf-anonymizer` and `id-extract`.

When a legal statute uses a word differently for compliance purposes, the governing statute controls.

---

## Part A: General Privacy Terminology Across Standards

Major frameworks use overlapping vocabulary with materially different legal and technical thresholds:

| Concept | ISO/IEC 20889:2018 | NIST SP 800-188 | EU GDPR (2016/679) | U.S. HIPAA (45 CFR § 164.514) |
|---|---|---|---|---|
| **Anonymization** | Process reducing re-identification risk to an acceptable threshold (often irreversible). | Distinguished from de-identification; reserves *anonymous* for data with effectively zero linkability. | **Recital 26:** Individuals are no longer identifiable by any means *reasonably likely to be used*. Falls outside GDPR scope. | Does not use *anonymization* as the primary statutory term (uses *de-identification*). |
| **De-identification** | General process of removing or altering association between identifying attributes and data subjects (umbrella term). | Process of removing identifying information from a dataset so remaining data cannot readily identify individuals. | Not a defined statutory term; often used informally. | Statutory term satisfied via **Safe Harbor** (18 identifier classes) or **Expert Determination**. |
| **Pseudonymization** | Replacing direct identifiers with pseudonyms while permitting authorized re-linking via separated information. | Specific de-identification technique replacing identifiers with pseudonyms; remains linkable with the key. | **Art. 4(5):** Security safeguard where additional information is kept separately. Result **remains personal data**. | Re-identification codes allowed under § 164.514(c) if not derived from PHI and not disclosed. |
| **Direct identifier** | Data element that uniquely identifies a principal without combining other attributes. | Information that directly identifies an individual (name, SSN, email, account ID). | Identifier directly naming or addressing a natural person. | Explicit identifiers among the 18 Safe Harbor classes (names, SSN, MRN, email, phone). |
| **Quasi-identifier** | Attribute that can identify a principal in combination with other attributes or auxiliary data. | Indirect identifier (ZIP, birth date, gender, occupation) enabling linkage attacks. | Indirect identifying factors (Recital 26 / Art. 4(1)). | Covered partially by Safe Harbor rules on dates (year only), geographic subdivisions (ZIP3), and ages $> 89$. |

Additional general terms defined in the [Anonymization Handbook](../101/index.md):

- **Singling out, linkability, and inference:** The three operational disclosure criteria in EU WP29 Opinion 05/2014 ([Lecture 4](../101/risk-and-attackers.md#2-regulatory-disclosure-criteria-wp29-edpb)).
- **Prosecutor, journalist, and marketer risk:** Quantitative re-identification risk models for tabular releases ([Lecture 4](../101/risk-and-attackers.md#1-the-three-classical-sdc-attacker-models)).
- **Re-identification (deanonymization) attack:** Adversarially recovering individual identities from masked data without access to the mapping key ([Failure Compendium](../101/failure-compendium.md)).

---

## Part B: `pdf-anonymizer` Product Terms

### What this product is

| Term | Meaning here |
|---|---|
| **Anonymization** | Colloquially, "hide who the person is." Under GDPR, true anonymization is irreversible. This tool does **not** claim irreversible anonymization. |
| **Pseudonymization** | Replace personal values with stand-ins and keep a way back. GDPR still treats the result as personal data while you hold the map. That is what this tool does. |
| **Reversible document pseudonymizer** | The product: typed stand-ins (`PERSON_1`) plus a separate mapping file. It is not a general statistical anonymizer. |
| **Deanonymization** | Restoring original values from the mapping file. (In privacy literature, also the name of an adversarial re-identification attack.) |
| **PII** | Personally identifiable information: data that can identify a person, alone or with other facts. |
| **PHI** | Protected health information under U.S. HIPAA — PII within clinical or healthcare records. |
| **Aid, not a certificate** | Flags such as `--entity-profile hipaa-safe-harbor` or tabular `--k` assist coverage; they are not legal certifications. |

Longer legal and theoretical context: [Lecture 1: Problem, Threats, and Law](../101/why-anonymization.md), [Lecture 2: Historical Development](../101/history.md), [Lecture 3: Formal Models and Methods](../101/techniques.md).

---

## Leftover

A **leftover** is a personal value that is still visible after anonymize. The job of the package is to make leftovers rare. The job of eval is to count them.

| Related term | Meaning here |
|---|---|
| **Leftover rate** | After anonymize, the share of gold mention strings still visible in the output. |
| **Structured leftover** | Leftover rate on [structured identifiers](#identifiers) only (email, phone, SSN, card, IBAN, IP, ISO date). Regex-only should keep this near zero. Names are not in this number. |
| **Residual scan** | A second cheap regex pass (optional LLM) on already-masked text. Writes `*.residual_pii.json`. It reports leftovers. It does not rewrite the page unless you opt in (`apply` / `--apply-residuals`). |
| **Apply leftovers** | Opt-in rewrite: hide accepted leftover texts with the same span engine. Default stays report-only. |
| **Red-team** | A test that fails the build if the residual file still contains structured leftovers. |

A leftover can be a gold mention we never hid, or a structured value the residual scan finds that the gold labels never listed.

---

## Gold-corpus

A **gold-corpus** (also written gold corpus) is a set of documents with labeled personal spans. We run the package on those documents and compare what it hid with what the labels say should be hidden.

The hyphenated form is the product name: `data/gold-corpus/`, `make gold-corpus`, `scripts/download_gold_corpus.py`.

| Related term | Meaning here |
|---|---|
| **Gold mention** | One labeled span: text, type, optional offsets, optional `base_form`. |
| **TAB** | Text Anonymization Benchmark (Pilán et al., 2022). The dedicated public legal gold-corpus, and the mention/entity, direct/quasi split we reuse. |
| **Domain pack** | Small committed pages for healthcare, legal, government, research, finance, and enterprise. Always in PR CI. |
| **Baseline** | A stored score for one profile so later changes can be compared. |

Workflows, sources, and commands: [Gold corpus & eval](gold-corpus.md).

---

## Identifiers

| Term | Meaning here |
|---|---|
| **Direct identifier** | A value that names or addresses one person by itself: a name, email, phone, SSN, card, IBAN, account, medical-record number. |
| **Quasi-identifier** | A value that is weak alone but strong in combination: city, date, job title, organization, age. TAB scores these separately so a high score on cities cannot hide a poor score on names. |
| **Identity clue** | Words that do not look like a name but still pick out one person, such as “the CEO of Tesla.” The `detailed` prompt asks for these. The `simple` prompt does not. The type is often `INDIRECT`. See [Lecture 9: System Case Study](../101/how-different.md#2-indirect-identifiers-in-unstructured-text). |
| **Structured identifier** | A value the regex stage is built to find: email, phone, SSN, card, IBAN, IP, ISO date. Completeness tests treat these as the leftover ceiling. |
| **`TYPE_LIKE`** | A regex hit that failed a cheap checksum (Luhn, IBAN, VIN, some national IDs). Example: `IBAN_LIKE_1`. It is still hidden so leftover digits do not stay on the page. |

The eval code’s type lists live in `tests/eval/metrics.py` (`DIRECT_TYPES`, `QUASI_TYPES`) and `tests/eval/gold.py` (`STRUCTURED_TYPES`, `RED_TEAM_TYPES`).

---

## What the tool writes

| Term | Meaning here |
|---|---|
| **Placeholder** / **stand-in** | The token written into the document, such as `PERSON_1`, `EMAIL_3.v_1`, or `IBAN_LIKE_2`. |
| **Mapping** | JSON from original string to placeholder. Default is plaintext `*.mapping.json`. |
| **Locked mapping** | `*.mapping.json.enc`: AES-256-GCM with an Argon2id passphrase. See [Mapping encryption](mapping-security.md). |
| **Ephemeral mapping** | The map is never written to disk (`--ephemeral-mapping`). |
| **Operator** | How a type is written: `replace` (default), `mask`, `hash`, `generalize`, `shift`, `fake`, `encrypt`. |
| **Linkage-risk report** | `*.risk.json`: identity-clue clumps (job + company + place). Report only. |

---

## How detection runs

| Term | Meaning here |
|---|---|
| **Regex stage** / **RE2** | The first pass: regular expressions with the RE2 engine (linear time, no catastrophic backtracking). |
| **Regex-only** | `--no-llm` / `-p regex-only`. No language model. Names and identity clues are missed. PR CI uses this so no API key is required. |
| **LLM NER** | The language-model pass that finds names and, in `detailed`, identity clues. |
| **NER** | Named-entity recognition. Optional local span model (GLiNER, `[ner]` extra) for names and organizations. |
| **Span** | A character interval `[start, end)` in the full document. Replacement is span-based: the longer interval wins when two hits overlap. |
| **Hybrid pipeline** | Regex first, then optional NER, then optional LLM, then merge and replace. |

---

## Recognizer, source, and score

Detection is not one function. Several **recognizers** look at the same text. Each one that fires writes a span, a type, a **source** (which recognizer it was), and a **score** (how strongly that recognizer believed the hit). `--min-confidence` can drop weak hits. Default `0` keeps every hit.

These scores are **hints for ranking**, not a legal or statistical probability that the span is truly personal data. Do not treat `0.85` as “85% chance this is PII.”

| Term | Meaning here |
|---|---|
| **Recognizer** | One detector that proposes spans. This product has four: regex, local span NER, the language model, and the deny-list. |
| **Source** | Which recognizer proposed the span. Stored on the entity as `source`. Values: `regex`, `ner`, `llm`, `deny-list`. |
| **Score** | A number from 0 to 1 that that recognizer assigned. Stored on the entity as `score`. |
| **`--min-confidence`** | Drop any span whose score is below this number. Applied after type merge and before the deny-list, so a deny-list phrase is still replaced. |
| **Checksum / verified hit** | A regex match that passed a cheap extra check (Luhn, IBAN, VIN, some national IDs). Score 0.95. |
| **`TYPE_LIKE`** | A regex match that failed that extra check. Still hidden. Score 0.55. Example: `IBAN_LIKE_1`. |

How each recognizer scores a hit:

| Source | Typical score | What it means |
|---|---|---|
| `deny-list` | 1.0 | You listed the phrase. It is always replaced (unless the keep-list also has it). |
| `regex` (checksum passed) | 0.95 | The shape matched and the extra digit check passed. |
| `regex` (no checksum for this type) | 0.85 | The shape matched (email, phone, URL, …). There is no extra digit check. |
| `ner` | model value, or 0.80 if the model omitted one | The local GLiNER model proposed a name, organization, place, address, or date. |
| `llm` | 0.70 | The language model’s JSON listed this span. That JSON is uncalibrated. |
| `regex` (`TYPE_LIKE`) | 0.55 | The shape matched and the extra digit check failed. Still hidden by default. |

Worked examples: [Drop low-score hits](recipes.md#drop-low-score-hits). HTTP response field: [HTTP service](http-service.md).

---

## How we measure

Score names used on a gold-corpus. Workflows: [Gold corpus & eval](gold-corpus.md).

| Term | Meaning here |
|---|---|
| **Mention-level score** | Precision, recall, and $F_1$ on individual spans. |
| **Entity-level score** | Did we find each person or value at least once, even if a later mention was missed? |
| **Precision** | Of the spans we marked, how many were in the gold labels? |
| **Recall** | Of the gold labels, how many did we mark? |
| **$F_1$** | The harmonic mean of precision and recall. One number when you need a single score. |
| **Public eval table** | Comparison of regex-only, local Gemma 4 (`detailed`), and Gemini 4 Argon on the gold corpus. See [Evaluation Results](eval-results.md). |

---

## Techniques this tool does not apply to prose

These words appear in the course and in scope boundaries. Formal definitions: [Lecture 3: Formal Models and Methods](../101/techniques.md).

| Term | In this product |
|---|---|
| **$k$-anonymity**, **$\ell$-diversity**, **$t$-closeness** | Table privacy models. Not used to rewrite prose PDFs or Word documents. Available as an optional aid for CSV/Excel tables via `--k` and `--sensitive-column` (`table_privacy.py`); default table mode stays cell-level pseudonymization. |
| **Differential privacy** | Noise on aggregate query answers or ML training. Not applied to document text. |
| **Synthetic data** | Whole-dataset generation with artificial records. The `fake` operator only replaces individual spans using a secret seed. |

---

## See also

- [Gold corpus & eval](gold-corpus.md) — workflows that use these measure words
- [Lecture 1: Problem, Threats, and Law](../101/why-anonymization.md) — threat models, domains, and legal definitions
- [Lecture 9: System Case Study](../101/how-different.md) — indirect identifiers and system scope
- [Mapping encryption](mapping-security.md) — locked maps
