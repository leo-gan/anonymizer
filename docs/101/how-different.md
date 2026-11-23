---
description: Architectural case study mapping anonymization theory (Lectures 1–8) onto pdf-anonymizer's hybrid detection, reversible mapping, file sanitization, and measured benchmarks.
---

# Lecture 9: System Case Study — `pdf-anonymizer`

Lectures 1–8 covered vendor-neutral privacy theory, threat models, file-format leakage, cryptographic hygiene, evaluation benchmarks, and method selection. This final lecture examines how one concrete open-source system — **`pdf-anonymizer`** — instantiates a **reversible hybrid document pseudonymizer**, mapping its design choices back to earlier lectures and stating its explicit boundaries.

---

## 1. Mapping Theory to System Scope

`pdf-anonymizer` is not a general statistical anonymizer and does not issue legal compliance certificates. Its concrete mapping onto Lectures 3–7 is:

| Concept (Lectures 3–7) | Implementation in `pdf-anonymizer` |
|---|---|
| **Deterministic patterns + checksums** | First-stage RE2 library (`id-extract`) covering universal identifiers and 38 national catalogs. Failed checks (Luhn, IBAN mod-97, Verhoeff, national checks) remain masked as `TYPE_LIKE` (e.g., `IBAN_LIKE_1`) or are dropped for bare digit runs; see [Check-Digit Algorithms](../id-extract/checksums.md). |
| **Span NER and LLM detection** | Optional local span NER (GLiNER) for names/organizations, plus multi-provider LLM NER (local Ollama or remote APIs) with `simple`, `detailed`, and `hipaa` prompt templates. |
| **Reversible pseudonymization** | Span-based replacement (longest-span-wins) producing typed, coreferent placeholders (`PERSON_1`, `PERSON_1.v_1`) and a separate mapping file (`*.mapping.json`, optional AES-256-GCM + Argon2id with source-hash AAD `*.mapping.json.enc`, or in-memory `--ephemeral-mapping`). |
| **Container sanitization** | Native PDF write (`--output-pdf` / `--redact`) excises glyphs, strips `/Info`, XMP, attachments, and annotations, and compacts without `/Prev` history; `.docx` joins runs and skips `w:del`; `.xlsx` writes cached values only. |
| **Operators** | Per-type overrides: `replace` (default), `mask`, `hash`, `generalize`, `shift`, `fake` (seeded), and `encrypt` (`ENC1_…` AES-256-GCM tokens omitted from the mapping file). |
| **Syntactic table privacy** | Optional CSV/Excel `--k` mode (`table_privacy.py`) that generalizes or suppresses quasi-identifier columns to satisfy $k$-anonymity and reports prosecutor risk, $\ell$-diversity, and $t$-closeness. Not applied to prose PDFs or Word documents. |
| **Differential privacy / mixnets** | Out of scope. Calibrated query noise is incompatible with reversible prose editing; network anonymity is a transport-layer problem. |
| **Empirical auditing** | Post-masking residual regex/LLM scan (`*.residual_pii.json`), heuristic linkage-risk report (`*.risk.json`), and a TAB-style gold-corpus evaluation suite (`tests/eval/`). |

---

## 2. Indirect Identifiers in Unstructured Text

Standard NER pipelines target explicit named spans (`PERSON`, `EMAIL`, `PHONE`). In prose, however, an individual can be uniquely identified without any proper name:

> *"We scheduled a meeting with the CEO of Tesla at his office in Austin."*

No personal name appears in the sentence, yet the combination of executive role, named company, and city uniquely identifies a single individual. Similar indirect identifiers include unique creative attribution (*"the author of the Harry Potter series"*) and singular organizational roles (*"Acme Inc.'s only in-house patent counsel"*).

The `detailed` prompt (enabled via `-p best-quality` or `--prompt-name detailed`) instructs the model to extract such **identity clues** alongside direct identifiers:

- When the model resolves the implied person, the phrase is consolidated under that entity's placeholder (`PERSON_1`, `PERSON_1.v_1`).
- When the referent cannot be named, the phrase is still masked under type `INDIRECT` (e.g., `INDIRECT_1`).
- Non-identifying generic phrases (*"a teacher in Austin"*, *"the CEO"* without an organization) are left untouched to preserve text utility.

The faster default profile (`best-speed`, using the `simple` prompt) does not search for indirect clues. Neither mode guarantees zero residual leakage; manual review remains necessary for high-stakes releases.

```bash
# Enable indirect-identifier detection
pdf-anonymizer run notes.pdf -p best-quality

# Or override only the prompt template
pdf-anonymizer run notes.pdf --prompt-name detailed
```

---

## 3. Reversible Pseudonymization and the Mapping Engine

Permanent redaction (`<REDACTED>`) destroys referential structure, making downstream summarization, translation, or analysis unreliable. Typed placeholders preserve grammatical roles and cross-sentence coreference:

1. **Base-form consolidation:** Coreferent mentions (*"Dr. John Smith"*, *"Dr. Smith"*, *"Smith"*) are grouped under a canonical base form so all variants receive a shared root (`PERSON_1`, `PERSON_1.v_1`).
2. **Span-based replacement:** Mentions are located by character interval `[start, end)`. Overlapping hits resolve longest-first (`John Doe` takes precedence over inner `John`), and slices are rewritten back-to-front so earlier offsets stay valid.
3. **Separated key custody:** The masked document can be sent to an external service or analyst while the mapping stays local. For sensitive environments, the mapping can be encrypted with AES-256-GCM + Argon2id bound via AAD to the source file SHA-256 (`--mapping-passphrase` / `ANONYMIZER_MAPPING_KEY`), or kept strictly in memory (`--ephemeral-mapping`). See [Mapping Security](../project/mapping-security.md).
4. **Audited restoration:** Running `pdf-anonymizer deanonymize` restores base placeholders and `.v_N` variants locally and emits `*.deanonymization_stat.json` recording `unused_mappings` and `not_found_mappings`.

---

## 4. Local Execution and Measured Trade-offs

Sending raw sensitive documents to a public cloud API solely to anonymize them shifts rather than removes trust exposure. `pdf-anonymizer` supports fully local execution through:

- **Offline deterministic pass (`--no-llm` / `-p regex-only`):** Structured identifiers only; zero network calls; misses names and prose context.
- **Local span NER (`[ner]` extra):** Local CPU GLiNER model for names, organizations, locations, and dates.
- **Local LLMs (`ollama/...`):** Runs models such as Gemma or Phi locally so document text never leaves the host.

Empirical trade-offs are published rather than assumed. On a 6,761-document benchmark combining Gretel, Presidio synthetic, TAB court cases, and domain fixtures ([Evaluation Results](../project/eval-results.md)):

- **Regex-only:** mention $F_1 = 0.262$, overall leftover rate $57.6\%$, structured leftover rate $3.9\%$.
- **RE2 + local Gemma 4 12B (`detailed`):** mention $F_1 = 0.564$, overall leftover rate $24.1\%$, structured leftover rate $0.1\%$, with leftovers under $7\%$ in every domain except TAB legal judgments (where unmasked dates and demographic quasi-identifiers dominate).

---

## 5. Architectural Comparison with Adjacent Tooling

| Dimension | Tabular Anonymizers (e.g., ARX) | Rule + Classical NER (e.g., Presidio) | Hybrid Document Pseudonymizer (`pdf-anonymizer`) |
|---|---|---|---|
| **Primary input** | Structured relational tables | Unstructured text strings | PDF, Markdown, text, DOCX, CSV, XLSX |
| **Formal privacy model** | $k$-anonymity, $\ell$-diversity, $t$-closeness, DP | Empirical NER detection | Empirical hybrid detection + optional tabular `--k` aid |
| **Indirect prose clues** | Not applicable | Generally missed | Supported via `detailed` LLM prompt (`INDIRECT`) |
| **Checksum validation** | Not applicable | Type-dependent (often dropped on fail) | Failed checksums preserved as `TYPE_LIKE` |
| **Reversibility** | Irreversible by design | Primarily redaction/replacement | Typed placeholders + optional encrypted mapping |
| **Local / offline operation** | Yes | Yes | Yes (regex-only, local GLiNER, or local Ollama) |
| **Memory & scale limits** | Bounded by table size | Streaming possible per record | Text chunked in memory; tables/DOCX capped at 50 MiB |

---

To install and run the software, continue to [Project Documentation](../project/index.md), or return to the [Course Syllabus](index.md).
