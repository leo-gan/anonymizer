---
description: End-to-end local-first guide for academic researchers, qualitative interview transcripts, survey tables, IRB protocols, and Open Science repository archiving (OSF, Zenodo, QDR).
---

# Academic Research & IRB Workflow

Qualitative researchers, clinical/legal NLP labs, and research data stewards routinely need to de-identify interview transcripts (`.docx`, `.pdf`) and survey exports (`.csv`, `.xlsx`) under strict Institutional Review Board (IRB) protocols while preparing materials for Open Science repositories (OSF, Zenodo, Qualitative Data Repository, Dataverse).

This guide documents a **100% local workflow** using `pdf-anonymizer-cli` so raw human-subject data never leaves the research workstation.

!!! warning "Engineering aid, not IRB certification"
    Automated de-identification accelerates the first pass; it never replaces human review. Under IRB and GDPR/HIPAA rules, reversible pseudonymization produces **pseudonymized personal data** while the mapping key exists ([Lecture 1](../101/why-anonymization.md)). Always review masked transcripts and container metadata before sharing or depositing data.

---

## 1. Local-Only Installation (No Cloud API Calls)

Choose one of two strictly local execution paths depending on available hardware:

=== "Path A: CPU-only laptop (RE2 + local GLiNER NER)"

    Best for standard university laptops without a GPU. Detects structured identifiers (RE2 + checksums) plus names, organizations, locations, and dates locally on CPU.

    ```bash
    pip install "pdf-anonymizer-cli[ner,docx,excel]"
    ```

    *Note:* The `[ner]` extra installs PyTorch and downloads the `urchade/gliner_small-v2.1` checkpoint from Hugging Face on first run. Once cached locally, runs require no internet access.

=== "Path B: Workstation with local LLM (Ollama — catches indirect clues)"

    Best when interview prose contains **indirect contextual clues** (e.g., *"as the only pediatric neurologist in my county..."*). Runs entirely on localhost via [Ollama](https://ollama.com/).

    ```bash
    pip install "pdf-anonymizer-cli[ollama,docx,excel]"
    ollama serve
    ollama pull gemma4:12b-it-qat   # or a smaller model such as phi4-mini
    ```

*Network guarantee:* `pdf-anonymizer` sends zero telemetry and uploads no logs. Text leaves the host only if you invoke a remote cloud model. Pass **`--offline`** on every IRB command to fail closed before any byte is sent if a profile or environment variable would ever resolve to a remote provider or non-localhost `OLLAMA_HOST`.

---

## 2. Qualitative Interview Transcripts (`.docx` / `.pdf`)

### Protect speaker labels and force study-specific redactions

Create two plain-text lists (one phrase per line) to prevent speaker roles from being masked and to catch study-specific sites or project codenames:

```text
# keep.txt (never mask these structural labels)
Interviewer
Moderator
Participant
```

```text
# deny.txt (always hide these study-specific terms as CUSTOM_n)
Northside Community Clinic
Project Lighthouse
```

### Run locally with longitudinal consistency and encrypted key custody

Multi-wave qualitative studies require the same participant to keep the same stand-in (`PERSON_1`) across Wave 1, Wave 2, and follow-up field notes:

```bash
# Wave 1 — files in one run automatically share a growing mapping
# --offline refuses any remote provider; --countries scopes national-ID regexes
pdf-anonymizer run transcripts/wave1/*.docx \
  -p best-quality \
  --model-name "ollama/gemma4:12b-it-qat" \
  --offline \
  --countries US \
  --keep-list keep.txt \
  --deny-list deny.txt \
  --mapping-passphrase "$ANONYMIZER_MAPPING_KEY"

# Wave 2 — seed stand-ins from Wave 1's encrypted mapping
pdf-anonymizer run transcripts/wave2/*.docx \
  -p best-quality \
  --model-name "ollama/gemma4:12b-it-qat" \
  --offline \
  --countries US \
  --keep-list keep.txt \
  --deny-list deny.txt \
  --mapping-in data/mappings/interview_01.mapping.json.enc \
  --mapping-passphrase "$ANONYMIZER_MAPPING_KEY"
```

*CPU-only alternative (without Ollama):* replace `-p best-quality --model-name "ollama/..."` with `-p best-speed --no-llm --ner`.

Key custody options for your IRB Data Management Plan:

- **Longitudinal studies (re-linking allowed by IRB):** Encrypt mapping files with `--mapping-passphrase` / `ANONYMIZER_MAPPING_KEY` (`*.mapping.json.enc`, Argon2id + AES-256-GCM + source-hash AAD, atomic mode `0600`) and move them to a separate encrypted institutional drive before sharing masked files ([Mapping Security](mapping-security.md)).
- **One-way archiving (no re-linking permitted):** Pass `--ephemeral-mapping` so no mapping file is written to disk.

### Format-specific container checks before sharing

- **Word (`.docx`):** The engine joins split XML runs (`w:t`), walks body, tables, headers, footers, footnotes, comments, field codes, and external hyperlinks, and skips tracked-change deletions (`w:del`). **Still inspect/remove manually:** embedded images, alt text, charts, and document core properties (author name in `docProps/core.xml`). See [Lecture 5: Document Leakage](../101/document-leakage.md).
- **PDF (`.pdf`):** Default output is Markdown (`.anonymized.md`), which strips PDF binary metadata automatically. If you need a sanitized native PDF, pass `--output-pdf` (or irreversible `--redact`); scanned PDFs require Tesseract on `PATH` and `--ocr`.

---

## 3. Survey and Demographic Tables (`.csv` / `.xlsx`)

For participant rosters or survey tables combining free-text open responses with demographic columns:

```bash
# Cell-level pseudonymization + optional k-anonymity on quasi-identifier columns
pdf-anonymizer run survey_responses.csv \
  --no-llm --ner \
  --countries US \
  --k 5 \
  --quasi-columns zip,gender,age \
  --sensitive-column diagnosis
```

- Direct identifiers and free-text cells are pseudonymized per cell; Excel formulas are dropped (cached values only).
- Quasi-identifier columns are generalized or suppressed until every combination occurs at least $k = 5$ times, and `data/stats/survey_responses.anonymized.table_privacy.json` records prosecutor linkage risk ($1/|E|$), $\ell$-diversity, and $t$-closeness.
- *Boundary:* If your study requires journalist risk estimation, global multi-attribute generalization lattices, or formal differential privacy on large relational tables, use [ARX Data Anonymizer](https://arx.deidentifier.org/) or `sdcMicro` ([Tool Comparison](tool-comparison.md)).

---

## 4. Mandatory Human Review and Local Cleanup

Every `run` writes two audit files under `data/stats/` without silently rewriting your documents:

1. **`data/stats/<stem>.residual_pii.json`** — Structured leftovers (emails, phone numbers, IDs) still visible after masking. Review and mask accepted hits interactively or in batch:
   ```bash
   pdf-anonymizer apply data/stats/interview_01.residual_pii.json --accept-all
   ```
2. **`data/stats/<stem>.risk.json`** — Heuristic linkage-risk clumps (`high` / `medium` / `low`, such as job title + organization + city in one passage). Read every `high`-risk passage manually to confirm no participant can be inferred from context.
3. **Manual full read-through:** Read the masked transcript end-to-end before deposit (checking rare life events, unique workplace descriptions, and indirect geographical references).
4. **Clean up temporary artifacts:** Once your encrypted mapping is safely archived (or if you used `--ephemeral-mapping`), purge local logs, stats, cache, and mapping directories:
   ```bash
   pdf-anonymizer purge
   ```
   `purge` removes `data/cache/`, `data/mappings/`, `data/stats/`, and `app.log` while leaving `data/anonymized/` intact.

---

## 5. Open-Science Archiving & IRB Methods Template

When qualitative narratives remain rich even after pseudonymization, consider **tiered repository access** (OSF, Zenodo, QDR, Dataverse): publish codebooks and summary code openly, and place de-identified transcripts under controlled access requiring a Data Use Agreement (DUA).

### Adaptable IRB Protocol / Methods Paragraph

> *Direct and indirect personal identifiers in interview transcripts and survey tables were first processed locally on an offline workstation using `pdf-anonymizer` (RE2 structured pattern matching with check-digit validation paired with [local GLiNER span NER / local Ollama model name], with zero cloud data transmission). Speaker labels were preserved via a keep-list, and cross-wave consistency was maintained through an AES-256-GCM encrypted mapping file stored separately from the transcripts under owner-only permissions (`0600`) [or: no mapping file was retained (`--ephemeral-mapping`)]. Automated residual-PII and contextual linkage-risk reports were generated for every file, followed by a complete manual review by the research team to catch subtle indirect identifiers prior to [analysis / controlled-access archiving]. Automated tooling served strictly as a first-pass aid rather than a compliance guarantee.*

### Citing the Handbook and Software

Citation metadata for papers, syllabi, and data-management plans is provided in [`CITATION.cff`](https://github.com/leo-gan/anonymizer/blob/main/CITATION.cff).

---

## See Also

- [Tool Comparison](tool-comparison.md) — when to choose `pdf-anonymizer` vs. Textwash, ARX, Presidio, or MAT2
- [Anonymization Handbook](../101/index.md) — course notes and exercises suitable for methods seminars
- [Evaluation Results](eval-results.md) — empirical leftover rates across 6,761 public documents
- [Mapping Security](mapping-security.md) — cryptographic design note for IRB security reviews
