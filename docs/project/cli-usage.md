# CLI Usage & Command Reference

The `pdf-anonymizer-cli` package installs the `pdf-anonymizer` executable. This guide details command syntax, options, and usage examples.

---

## The `run` Command (Anonymization)

The `run` command processes one or more files, masks PII, and outputs the anonymized document along with a mapping file.

### Syntax
```bash
pdf-anonymizer run FILE_PATH [FILE_PATH ...] [OPTIONS]
```

### Arguments
*   `FILE_PATH`: Space-separated list of paths to files (PDF, Markdown, plain text, CSV, Excel `.xlsx`, or Word `.docx`).

### Options

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--config-profile` / `-p` | `best-quality` \| `best-speed` \| `best-cost` \| `regex-only` | `best-speed` | Predefined bundle of model, prompt, chunk size, overlap, and retry settings (see below). `regex-only` skips the language model. |
| `--no-llm` | flag | off | Skip the language model. Only the RE2 regex stage runs. Names and identity clues will be missed. Same as `-p regex-only`. |
| `--characters-to-anonymize` | `INTEGER` | `100000` | The character size of each chunk sent to the LLM (overrides profile). |
| `--prompt-name` | `simple` \| `detailed` | `detailed` | Instruction style sent to the language model (overrides profile). `detailed` also hides identity clues. `simple` does not. |
| `--model-name` | `TEXT` | `gemini-2.5-flash` | The identifier of the model to execute (overrides profile). |
| `--anonymized-entities` | `PATH` | *None* | Path to a text file containing custom entities to search for and anonymize. |
| `--countries` | `TEXT` | *all* | ISO-2 codes for national-ID regexes, comma-separated (`US,GB`). Email, IBAN, cards, and other universal patterns always stay. |
| `--opt-in` | `TEXT` | *none* | State, provincial, and industry `id-extract` keys, comma-separated (`DL_FL_US,NAM_QC_CA`), or `all` for every selective key. |
| `--cache` / `--no-cache` | flag | off | Store language-model replies on disk (`data/cache/llm_responses.json`, mode `0600`, 24-hour TTL). Cached entries contain source chunks and extracted entities. |
| `--verify` / `--no-verify` | flag | on | After masking, scan the result for leftovers (cheap regex). Writes `data/stats/<stem>.residual_pii.json`. Does not change the file unless `--apply-residuals`. |
| `--verify-llm` | flag | off | Also ask the language model to hunt for leftovers. |
| `--apply-residuals` | flag | off | After the leftover scan, hide every leftover on this run. Implies `--verify`. |
| `--mapping-passphrase` | `TEXT` | *none* | Lock the mapping as `*.mapping.json.enc` (AES-256-GCM + Argon2id, source-file AAD). Also read from `ANONYMIZER_MAPPING_KEY`. Default: plaintext JSON. |
| `--ephemeral-mapping` / `--persist-mapping` | flag | persist | Keep the mapping only in this process. Nothing is written under `data/mappings/`. |
| `--operator` | `TYPE=op` | `replace` | Repeatable. How to write a type: `replace`, `mask`, `hash`, `generalize`, `shift`, `fake`, `encrypt`. |
| `--fake-secret` | `TEXT` | *none* | Required seed for `fake`. Also `ANONYMIZER_FAKE_SECRET`. |
| `--encrypt-secret` | `TEXT` | *none* | Required secret for `encrypt` (`ENC1_…` AES-256-GCM tokens). Also `ANONYMIZER_ENCRYPT_SECRET`. |
| `--risk` / `--no-risk` | flag | on | After masking, score identity-clue clumps. Writes `data/stats/<stem>.risk.json`. Does not change the file. |
| `--entity-profile` | `hipaa-safe-harbor` | *none* | Coverage aid for HIPAA Safe Harbor identifier classes. **Not a compliance certificate.** |
| `--mapping-in` | `PATH` | *none* | Seed stand-ins from an existing mapping so the same person stays `PERSON_1` across files. |
| `--keep-list` | `PATH` | *none* | Phrases to leave visible (one per line). Wins if also on the deny-list. |
| `--deny-list` | `PATH` | *none* | Phrases that must be hidden even if detection missed them. |
| `--ocr` / `--no-ocr` | flag | off | If a PDF has no text layer, OCR it with Tesseract (must be on PATH). A scan with OCR off is an error, not an empty success file. |
| `--output-pdf` / `--no-output-pdf` | flag | off | Also write a sanitized native PDF. Markdown is still written. PDF inputs only. Not a legal certificate. |
| `--redact` / `--no-redact` | flag | off | Irreversible native PDF (black boxes, no stand-in). Implies `--output-pdf`. |
| `--ner` / `--no-ner` | flag | auto | Local span NER (GLiNER extra) for names and organizations. Auto-on when the extra is installed (except regex-only). `best-speed` / `best-cost` then skip the language model. |
| `--min-confidence` | `0–1` | `0` | Drop spans whose [score](terminology.md#recognizer-source-and-score) is below this value. Default 0 keeps every hit. Not a calibrated probability. |
| `--k` | integer ≥ 2 | *none* | CSV/Excel only. Generalize or suppress quasi-identifier columns until each combination appears at least K times. Writes `data/stats/<stem>.table_privacy.json`. Does not rewrite PDFs. An aid, not a certificate. |
| `--quasi-columns` | `zip,gender` | header hints | Quasi-identifier headers for `--k`. Default matches zip, gender, age, birth date, city, and state. |
| `--sensitive-column` | header | *none* | With `--k`, report ℓ-diversity and t-closeness for this column. The column is not generalized. |

### Configuration Profiles

The `--config-profile` (or `-p`) flag is the recommended way to select quality/speed/cost trade-offs. It sets a bundle of model, prompt, chunk size, overlap, and retry settings. Any of `--model-name`, `--prompt-name`, or `--characters-to-anonymize` act as **overrides** on top of the chosen profile.

| Profile        | Default Model           | Prompt   | Chunk Size | Overlap | Retries | Best For                          |
|----------------|-------------------------|----------|------------|---------|---------|-----------------------------------|
| `best-quality` | `gemini-2.5-pro`        | detailed | 15,000     | 2,000   | 5       | Highest accuracy; also hides identity clues (slower/costlier)|
| `best-speed`   | `gemini-2.5-flash`      | simple   | 30,000     | 1,000   | 3       | Balanced (default); does not hunt for identity clues |
| `best-cost`    | `gemini-2.5-flash-lite` | simple   | 60,000     | 3,000   | 3       | Cheap & fast on long documents; no identity-clue hunt |
| `regex-only`   | none                    | simple   | 200,000    | 0       | 1       | Offline / air-gapped: regex only. Names and identity clues are missed |

**Examples**

```bash
# High accuracy on an important contract (also hides identity clues)
pdf-anonymizer run contract.pdf -p best-quality

# Fast + cheap batch of notes with a local model
pdf-anonymizer run notes/*.md -p best-cost --model-name "ollama/phi4-mini"

# Only US and UK national-ID patterns (email, IBAN, cards still run)
pdf-anonymizer run contract.pdf --countries US,GB
```

See the [Recipes & Common Workflows](recipes.md) page for more profile usage patterns.

The optional HTTP service is a separate package (`pdf-anonymizer-api`). It is not a CLI command. See [HTTP service and Docker](http-service.md).

---

## Models & Providers

You can select a model via the `--model-name` option. PDF Anonymizer can use pre-configured alias strings or dynamically resolve model paths using the format `provider/model-identifier`.

### Model Aliases

#### Google (Gemini)
*   `gemini-2.5-pro`
*   `gemini-2.5-flash` (Default)
*   `gemini-2.5-flash-lite`

#### Ollama (Local)
*   `gemma:7b`
*   `phi4-mini`

#### Hugging Face
*   `openai/gpt-oss-20b`
*   `mistralai/Mistral-7B-Instruct-v0.1`
*   `HuggingFaceH4/zephyr-7b-beta`

#### OpenAI
*   `gpt-4o`
*   `gpt-5`

#### Anthropic (Claude)
*   `claude-4-sonet`
*   `claude-4.5-sonet`

#### OpenRouter
*   `openai/gpt-4o`
*   `google/gemini-pro`

### Dynamic Resolution Syntax
To use any model not listed in the aliases, pass the string as `provider/model-name`. E.g.:
```bash
pdf-anonymizer run doc.pdf --model-name "google/gemini-2.0-flash-exp"
```

---

## The `report` Command (linkage risk)

Score identity-clue clumps in an already-masked file. Does not change the file.

```bash
pdf-anonymizer report data/anonymized/notes.anonymized.md
pdf-anonymizer report data/anonymized/roster.anonymized.xlsx
```

The report is `data/stats/<stem>.risk.json`. `run` already writes this unless you pass `--no-risk`.

---

## The `verify` Command (leftover check)

Scan an already-masked file. This only writes a report. It does not change the file.

```bash
pdf-anonymizer verify data/anonymized/notes.anonymized.md
pdf-anonymizer verify data/anonymized/people.anonymized.csv
pdf-anonymizer verify data/anonymized/notes.anonymized.md --verify-llm -p best-quality
```

The report is `data/stats/<stem>.residual_pii.json`. Stand-in labels such as `PERSON_1` are ignored. A leftover email or a mistyped IBAN is listed.

`run` already does the cheap regex scan unless you pass `--no-verify`.

---

## The `apply` Command (hide leftovers)

The leftover report does not rewrite the page. `apply` hides the leftovers you accept, using the same span engine as `run`.

```bash
# Hide every leftover in the report
pdf-anonymizer apply data/stats/notes.residual_pii.json --accept-all

# Hide only some phrases
pdf-anonymizer apply data/stats/notes.residual_pii.json --accept accept.json

# Leave some visible
pdf-anonymizer apply data/stats/notes.residual_pii.json --accept-all --skip skip.txt
```

`--accept` / `--skip` are a JSON list of strings, a JSON object with an `accept` or `skip` key, or one phrase per line. On a TTY, if you pass neither `--accept-all` nor `--accept`, the command asks about each leftover.

The anonymized file is rewritten in place. New stand-ins are added to the mapping. Native PDF output is not supported; apply the Markdown file instead.

`run --apply-residuals` does the same thing for leftovers found on that run.

---

## The `deanonymize` Command (Reversal)

The `deanonymize` command reads an anonymized document, loads the JSON mapping file containing placeholders and original PII, restores the original text, and writes the output file.

### Syntax
```bash
pdf-anonymizer deanonymize ANONYMIZED_FILE MAPPING_FILE \
  [--mapping-passphrase TEXT] [--source-sha256 HEX] [--encrypt-secret TEXT]
```

### Arguments
*   `ANONYMIZED_FILE`: Path to the file that was previously anonymized.
*   `MAPPING_FILE`: Path to the JSON mapping file (plaintext or `*.mapping.json.enc`).
*   `--mapping-passphrase`: Required for an encrypted mapping. Also read from `ANONYMIZER_MAPPING_KEY`.
*   `--source-sha256`: Optional. Expected SHA-256 of the original source document. Rejects a mapping locked for a different file.
*   `--encrypt-secret`: Required to reverse `--operator TYPE=encrypt` (`ENC1_…`) tokens. Also read from `ANONYMIZER_ENCRYPT_SECRET`.

### Output Destination
This command creates a deanonymized version of the file. For example:
If `ANONYMIZED_FILE` is `data/anonymized/document.anonymized.md`, the output will be saved under `data/deanonymized/document.deanonymized.md`.

---

## The `purge` Command (Remove Local Artifacts)

Removes local files that may contain personal data from prior runs (`data/cache/`, `data/mappings/`, `data/stats/`, and `app.log`). Anonymized and deanonymized output documents are left intact; symlinks are skipped.

```bash
pdf-anonymizer purge [--root PATH]
```

*   `--root`: Directory containing `data/` and `app.log` (default: current working directory).

---

## Operational Examples

### Example 1: Basic Anonymization
Anonymize a meeting transcript using the default Gemini model:
```bash
pdf-anonymizer run data/meeting_transcript.pdf
```
*   **Outputs created**:
    *   `data/anonymized/meeting_transcript.anonymized.md` (the masked document)
    *   `data/mappings/meeting_transcript.mapping.json` (the mapping file — treat it like a key)

### Example 2: Local Processing via Ollama
To ensure data does not leave your local machine, use a locally running model:
```bash
pdf-anonymizer run medical_note.txt --model-name "ollama/phi4-mini"
```

### Example 3: Customized Chunk Size & Prompt
Process a long book draft using smaller chunks and a simple redaction strategy:
```bash
pdf-anonymizer run book.md --characters-to-anonymize 50000 --prompt-name simple
```

### Example 4: Restoring the Original Document
Revert the anonymization performed in Example 1:
```bash
pdf-anonymizer deanonymize \
  data/anonymized/meeting_transcript.anonymized.md \
  data/mappings/meeting_transcript.mapping.json
```
*   **Output created**:
    *   `data/deanonymized/meeting_transcript.deanonymized.md`

### Example 5: Newer flags in one command

```bash
pdf-anonymizer run notes.pdf contract.pdf \
  -p best-quality \
  --countries US,GB \
  --operator CREDIT_CARD=mask \
  --operator DATE=generalize \
  --keep-list keep.txt \
  --mapping-passphrase 'a long secret'
```

Files in the same `run` share one growing map, so the same person stays `PERSON_1`. See [Recipes](recipes.md) for keep-lists, HIPAA coverage aid, fake names, and `--mapping-in`.

---

## Output Files & Auditing

`run`, `verify`, `report`, and `deanonymize` write under conventional directories (created automatically):

*   `data/anonymized/<stem>.anonymized.md` (or `.txt`, `.csv`, `.xlsx`, `.docx`; plus `.pdf` when `--output-pdf`)
*   `data/mappings/<stem>.mapping.json` (or `*.mapping.json.enc` when a passphrase is set)
*   `data/deanonymized/<stem>.deanonymized.md` (or `.txt`, `.csv`, `.xlsx`, `.docx`)
*   `data/stats/<stem>.residual_pii.json` — leftovers found after masking (from `run` or `verify`)
*   `data/stats/<stem>.risk.json` — identity-clue clumps (from `run` or `report`)
*   `data/stats/<stem>.deanonymization_stat.json` — written by `deanonymize`

The stats file contains:

```json
{
  "anonymized_file": "...",
  "mapping_file": "...",
  "deanonymized_file": "...",
  "unused_mappings": ["PERSON_7"],
  "not_found_mappings": []
}
```

*   `unused_mappings`: placeholders present in the map but never found in the anonymized text (usually harmless).
*   `not_found_mappings`: placeholders seen in the text with no corresponding entry in the map (may indicate a corrupted or partial mapping).

These are useful for compliance/audit pipelines. See the [Recipes & Common Workflows](recipes.md) page for more details on working with mappings and stats.

---

## See Also

- **[Recipes & Common Workflows](recipes.md)** — practical end-to-end examples (profiles, local models, external LLM workflows, caching, debugging).
- **[HTTP service and Docker](http-service.md)** — `pdf-anonymizer-api`, compose, and `source` / `score` on the JSON response.
- **[SDK & API Usage](api-usage.md)** — programmatic usage of the same core functions.
- **[API Reference (auto)](api-reference.md)** — auto-generated function signatures.
- **[Architecture Design](architecture.md)** — how chunking, hybrid detection, mapping, and reversal work internally.
- **[Installation & Setup](installation.md)** — provider extras and environment setup.