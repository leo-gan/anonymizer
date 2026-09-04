# Terminology

This page is the single list of words this project uses. Course chapters still teach the ideas. Other pages should link here instead of inventing a second definition.

When a legal text uses the same word differently, that text wins for compliance. These are **product** meanings.

---

## What this product is

| Term | Meaning here |
|---|---|
| **Anonymization** | In everyday talk, “hide who the person is.” In GDPR, true anonymization is irreversible. This tool does **not** claim that. |
| **Pseudonymization** | Replace personal values with stand-ins and keep a way back. GDPR still treats the result as personal data while you hold the map. That is what this tool does. |
| **Reversible document pseudonymizer** | The product: typed stand-ins (`PERSON_1`) plus a separate mapping file. It is not a statistical anonymizer. |
| **Deanonymization** | Put the original values back from the mapping. Also the name of an attack that tries to recover people without the map. |
| **PII** | Personally identifiable information: data that can identify a person, alone or with other facts. |
| **PHI** | Protected health information under US HIPAA. A kind of PII in clinical text. |
| **Aid, not a certificate** | Flags such as `--entity-profile hipaa-safe-harbor` help you cover identifier classes. They are not a legal certification. |

Longer legal and history context: [Why Anonymize?](../101/why-anonymization.md), [History](../101/history.md), [Techniques](../101/techniques.md).

---

## Leftover

A **leftover** is a personal value that is still visible after anonymize. The job of the package is to make leftovers rare. The job of eval is to count them.

| Related term | Meaning here |
|---|---|
| **Leftover rate** | After anonymize, the share of gold mention strings still visible in the output. |
| **Structured leftover** | Leftover rate on [structured identifiers](#identifiers) only (email, phone, SSN, card, IBAN, IP, ISO date). Regex-only should keep this near zero. Names are not in this number. |
| **Residual scan** | A second cheap regex pass (optional LLM) on already-masked text. Writes `*.residual_pii.json`. It reports leftovers. It does not rewrite the page. |
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
| **Domain pack** | Tiny committed pages for healthcare, legal, government, research, finance, and enterprise. Always in PR CI. |
| **Baseline** | A stored score for one profile (today: regex-only) so later changes can be compared. |

Workflows, sources, and commands: [Gold corpus & eval](gold-corpus.md).

---

## Identifiers

| Term | Meaning here |
|---|---|
| **Direct identifier** | A value that names or addresses one person by itself: a name, email, phone, SSN, card, IBAN, account, medical-record number. |
| **Quasi-identifier** | A value that is weak alone but strong in combination: city, date, job title, organization, age. TAB scores these separately so a high score on cities cannot hide a poor score on names. |
| **Identity clue** | Words that do not look like a name but still pick out one person, such as “the CEO of Tesla.” The `detailed` prompt asks for these. The `simple` prompt does not. The type is often `INDIRECT`. See [How PDF Anonymizer is Different](../101/how-different.md). |
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
| **Operator** | How a type is written: `replace` (default), `mask`, `hash`, `generalize`, `shift`, `fake`. |
| **Linkage-risk report** | `*.risk.json`: identity-clue clumps (job + company + place). Report only. |

---

## How detection runs

| Term | Meaning here |
|---|---|
| **Regex stage** / **RE2** | The first pass: regular expressions with the RE2 engine (linear time, no catastrophic backtracking). |
| **Regex-only** | `--no-llm` / `-p regex-only`. No language model. Names and identity clues are missed. PR CI uses this so no API key is required. |
| **LLM NER** | The language-model pass that finds names and, in `detailed`, identity clues. |
| **NER** | Named-entity recognition. Item 20 (not shipped) is a local span model for `best-speed`. |
| **Span** | A character interval `[start, end)` in the full document. Replacement is span-based: the longer interval wins when two hits overlap. |
| **Hybrid pipeline** | Regex first, then LLM, then merge and replace. |

---

## How we measure

Score names used on a gold-corpus. Workflows: [Gold corpus & eval](gold-corpus.md).

| Term | Meaning here |
|---|---|
| **Mention-level score** | Precision, recall, and F1 on individual spans. |
| **Entity-level score** | Did we find each person or value at least once, even if a later mention was missed? |
| **Precision** | Of the spans we marked, how many were in the gold labels? |
| **Recall** | Of the gold labels, how many did we mark? |
| **F1** | The harmonic mean of precision and recall. One number when you need a single score. |
| **Public eval table** | Regex-only vs NER vs `detailed` LLM on the same gold set. NER and live LLM are placeholders until those stages exist. |

---

## Techniques this tool does not apply to prose

These words appear in the course and in “we do not do this.” Definitions: [Techniques](../101/techniques.md).

| Term | In this product |
|---|---|
| ***k*-anonymity**, ***ℓ*-diversity**, ***t*-closeness** | Table privacy models. Not used to rewrite PDFs. Cell-level CSV/Excel is still pseudonymization. |
| **Differential privacy** | Noise on query answers. Not applied to document text. |
| **Synthetic data** | Whole-document rewrite with fake people. The `fake` operator only replaces a value, with a seed. |

---

## See also

- [Gold corpus & eval](gold-corpus.md) — workflows that use these measure words
- [Why Anonymize?](../101/why-anonymization.md) — sectors and legal names
- [How PDF Anonymizer is Different](../101/how-different.md) — identity clues
- [Mapping encryption](mapping-security.md) — locked maps
