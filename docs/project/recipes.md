# Recipes & Common Workflows

This page contains practical, end-to-end examples for common real-world usage patterns with PDF Anonymizer.

Use these recipes as starting points and adapt the commands or code to your environment.

---

## Fully Local & Private Anonymization (Ollama)

Run everything on your own machine so no document data ever leaves your computer.

**Prerequisites**

- Ollama installed and running (`ollama serve`)
- A model pulled, e.g. `ollama pull phi4-mini` or `gemma:7b`

**CLI**

```bash
pdf-anonymizer run contract.pdf \
  -p best-speed \
  --model-name "ollama/phi4-mini"
```

**SDK (Python)**

```python
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.prompts import detailed
from pdf_anonymizer_core.conf import get_config_for_profile, ConfigProfile

config = get_config_for_profile(ConfigProfile.BEST_SPEED, model_name="ollama/phi4-mini")

anonymized, mapping = anonymize_file(
    file_path="contract.pdf",
    characters_to_anonymize=config.chunk_size,
    prompt_template=detailed.prompt_template,
    model_name=config.model_name,
    chunk_overlap=config.chunk_overlap,
    max_retries=config.max_retries,
    base_retry_delay=config.base_retry_delay,
    max_retry_delay=config.max_retry_delay,
)
```

**Notes**
- The `ollama` extra must be installed: `pip install "pdf-anonymizer-core[ollama]"` (or use the dev workspace).
- `OLLAMA_HOST` can be set in your `.env` if Ollama is not on the default localhost:11434.
- All processing (including LLM calls) is local.

---

## Regex-only / offline (no language model)

Air-gapped machines, structured logs, or a cheap first pass: skip the model. Only the RE2 regex stage runs. Checksums (`IBAN_LIKE_1`), `--countries`, `--operator`, leftover scan, and linkage-risk still run. **Names and identity clues will be missed.**

**CLI**

```bash
pdf-anonymizer run access.log --no-llm
# or
pdf-anonymizer run access.log -p regex-only
```

No API key is required. `--verify-llm` is ignored in this mode so the process stays offline.

**SDK (Python)**

```python
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.conf import get_config_for_profile, ConfigProfile

config = get_config_for_profile(ConfigProfile.REGEX_ONLY)
anonymized, mapping = anonymize_file(
    file_path="access.log",
    characters_to_anonymize=config.chunk_size,
    prompt_template="",
    model_name=config.model_name,
    chunk_overlap=config.chunk_overlap,
    regex_patterns=config.regex_patterns,
    use_llm=False,
)
```

`use_llm` defaults to True. Existing callers are unchanged.

---

## Anonymize → Send to External AI / Service → Deanonymize Locally

The classic reversible workflow: protect the original data, let an untrusted system (public ChatGPT, Claude, a third-party analysis service, translation pipeline, etc.) work on the masked version, then recover the real values locally.

**Step-by-step**

1. Anonymize locally (or with a trusted key):

   ```bash
   pdf-anonymizer run sensitive-report.pdf -p best-quality
   ```

   This produces:
   - `data/anonymized/sensitive-report.anonymized.md`
   - `data/mappings/sensitive-report.mapping.json` (keep this file very secure)

2. Send **only** the `.anonymized.md` file (never the mapping) to the external system or paste it into a public LLM.

3. Receive the processed result (still containing placeholders such as `PERSON_1`, `ORGANIZATION_3.v_1`, etc.).

4. Deanonymize locally:

   ```bash
   pdf-anonymizer deanonymize \
     data/anonymized/sensitive-report.anonymized.md \
     data/mappings/sensitive-report.mapping.json
   ```

   The final restored document appears under `data/deanonymized/`.

You can repeat step 4 any time you receive new output from the external system as long as you still have the original mapping file.

**Tip**: The mapping file is the "key". Anyone who has it can put the real names back. Treat it like a password.

### Lock the mapping file

By default the mapping is plain JSON. That is easy to use and easy to leak. You can lock it with a passphrase. The tool writes `*.mapping.json.enc` (AES-256-GCM, Argon2id, source-file AAD) instead of `*.mapping.json`. Both the locked file and a plaintext mapping are created atomically with mode `0600`.

```bash
pdf-anonymizer run sensitive-report.pdf --mapping-passphrase 'a long secret'
# or set ANONYMIZER_MAPPING_KEY in the environment

pdf-anonymizer deanonymize \
  data/anonymized/sensitive-report.anonymized.md \
  data/mappings/sensitive-report.mapping.json.enc \
  --mapping-passphrase 'a long secret'
```

Without a passphrase, behavior is unchanged: plaintext `*.mapping.json`. An encrypted file cannot be opened without the passphrase. The masked document is still not enough to recover the names.

Do not put the passphrase in the document, the mapping, or the log.

`--ephemeral-mapping` skips `data/mappings/` entirely. Use that when the process will discard the vocabulary and you will not deanonymize later.

`--source-sha256` on `deanonymize` rejects a map that was locked for a different source file (the hash is authenticated inside the envelope). `--mapping-in` does not require a matching hash, because that flag exists to reuse placeholders across documents.

The architecture, threat model, trade-offs, and the tests that demonstrate the old holes versus the fix are in [Mapping encryption](mapping-security.md).

---

## Keep some phrases, always hide others

A keep-list is a file of phrases that must stay visible, even if the tool found them. Use this for your own company name, or for “Apple” when you mean the fruit.

A deny-list is a file of phrases that must be hidden, even if regex and the model missed them.

One phrase per line. Lines starting with `#` are comments. If a phrase is on both lists, **keep wins**.

```text
# keep.txt
Apple
Acme Inc.
```

```bash
pdf-anonymizer run notes.pdf --keep-list keep.txt --deny-list must-hide.txt
```

Deny-list hits become `CUSTOM_1`, `CUSTOM_2`, and so on.

---

## Keep the same stand-in across files

Each file used to start counting at `PERSON_1`. In a batch, Ada could be `PERSON_1` in notes.md and `PERSON_7` in contract.pdf.

`--mapping-in` starts from an existing map. Files in the same `run` command also share the growing map, so Ada stays `PERSON_1` from the first file to the last.

```bash
pdf-anonymizer run day1.md day2.md
# day2 reuses the people found in day1

pdf-anonymizer run day3.md --mapping-in data/mappings/day2.mapping.json
```

Encrypted maps work if you also pass `--mapping-passphrase` (or `ANONYMIZER_MAPPING_KEY`). Each file's mapping file is the combined map up to that file.

---

## Batch Processing Multiple Files

The CLI accepts multiple input paths.

```bash
pdf-anonymizer run \
  reports/q1.pdf \
  notes/meeting-2025-06.md \
  archive/transcript.txt \
  -p best-cost
```

Files in the same `run` **share a growing map**, so Ada stays `PERSON_1` from the first file to the last. Results are written using the original stem name into the conventional output directories (`data/anonymized/`, `data/mappings/`, etc.). Use `--mapping-in` to continue a later batch from an earlier map.

For very large batch jobs you may want to:
- Use the faster/cheaper profile (`best-cost` or `best-speed`)
- Monitor `app.log` (written to the current working directory)
- Run inside a script that collects exit codes

---

## Use local span NER

Names such as “Jane Doe” are not a regex job. The default `best-speed` profile asks a language model. Install the optional extra to do that locally on CPU:

```bash
pip install "pdf-anonymizer-core[ner]"
# or
pip install "pdf-anonymizer-cli[ner]"
```

That extra pulls **PyTorch** and a GLiNER checkpoint (`urchade/gliner_small-v2.1` by default) on first use.

```bash
pdf-anonymizer run notes.md -p best-speed --no-llm --ner
```

`--ner` is implied on `best-speed`, `best-cost`, and `best-quality` once the extra is installed. Speed and cost then skip the language model. Identity clues (“the CEO of Tesla”) stay on the LLM path (`-p best-quality`).

`--no-ner` keeps the previous LLM `best-speed`. `--ner` without the extra is an error.

This is not a flip of the default extra-less install. Item 19’s gold leftover/recall numbers are how a later change would decide to make NER the default even without the extra.

---

## OCR a scanned PDF

A PDF that is only pictures of pages has no text layer. `pymupdf4llm` then returns empty Markdown. That used to look like a successful run. It is now a hard error: the CLI exits non-zero and writes no `*.anonymized.md`.

To recover words, install **Tesseract** (a system package, not a pip extra) and pass `--ocr`:

```bash
# Debian/Ubuntu
sudo apt-get install tesseract-ocr
# macOS
brew install tesseract

pdf-anonymizer run scan.pdf --ocr --no-llm
```

That writes the usual anonymized Markdown and mapping, plus `data/anonymized/scan.anonymized.layout.json`. The layout file lists each OCR word and its page box so a later native-PDF redact pass can find the same spans.

**Notes**

- OCR is slower and less accurate than a real text layer. Prefer a digitally created PDF when you have one.
- `--ocr` does nothing extra when the PDF already has extractable text.
- If Tesseract is missing, the error says to install the binary. There is no `[ocr]` wheel today.
- If OCR itself returns nothing, that is also an error, not an empty success file.

---

## Write a native PDF

The default output for a PDF input is still Markdown. That drops layout, fonts, and headers. `--output-pdf` writes a **sanitized native PDF** as well:

```bash
pdf-anonymizer run contract.pdf --no-llm --output-pdf
```

That writes:

- `data/anonymized/contract.anonymized.md` (review / verify / report)
- `data/anonymized/contract.anonymized.pdf` (shareable page)
- `data/mappings/contract.mapping.json`

```bash
pdf-anonymizer deanonymize \
  data/anonymized/contract.anonymized.pdf \
  data/mappings/contract.mapping.json
```

The native write uses PyMuPDF redaction annotations and then `apply_redactions`. That removes the old glyphs from the content stream. It is not a black rectangle drawn on top of selectable text.

`--redact` is a second, **irreversible** mode: the hit becomes a black box and there is no stand-in on the page. Deanonymize cannot put the original words back.

```bash
pdf-anonymizer run contract.pdf --no-llm --redact
```

Every native write also wipes `/Info`, XMP, attachments, leftover annotations, and optional-content groups, and saves a full rewrite (no incremental `/Prev` history).

**Notes**

- This is still reversible pseudonymization when you use `--output-pdf` without `--redact`. It is **not** a legal de-identification certificate.
- Images, form fields, and some drawings can still show a name. Delete those before sharing, or accept the residual.
- `--output-pdf` on a non-PDF input is an error.

---

## Anonymize a CSV or Excel roster

A roster, export, or clinic list is a table. The same engine walks **cells** and writes a same-format spreadsheet plus the usual mapping. This is the same reversible pseudonymization as a PDF. It is **not** *k*-anonymity: leftover columns are not crowd-hidden.

CSV works with the base install. Excel (`.xlsx`) needs the extra:

```bash
pip install "pdf-anonymizer-core[excel]"
# or
pip install "pdf-anonymizer-cli[excel]"
```

**CLI**

```bash
pdf-anonymizer run people.csv
pdf-anonymizer run roster.xlsx
```

That writes:

- `data/anonymized/people.anonymized.csv` (or `roster.anonymized.xlsx`)
- `data/mappings/people.mapping.json`

```bash
pdf-anonymizer deanonymize \
  data/anonymized/people.anonymized.csv \
  data/mappings/people.mapping.json

pdf-anonymizer verify data/anonymized/people.anonymized.csv
pdf-anonymizer report data/anonymized/roster.anonymized.xlsx
```

No new flags. `--no-llm`, `--operator`, `--keep-list` / `--deny-list`, `--mapping-in`, and the rest work the same way as on a PDF. Files in one `run` still share a growing map (`people.csv notes.md`).

**Notes**

- **Formulas are never written back.** Excel: cached values only. A leftover `=A1` would restore a replaced name. CSV: only a cell whose raw value starts with `=` is treated as formula-like and written with a leading `'`. Deanonymize strips that `'` when the remainder still starts with `=`. E.164 phones such as `+1-555-0100` are **not** formulas and are left untouched.
- **Size / RAM.** Hard limits: 50 MiB on disk, 500,000 non-empty cells. Spreadsheets load in memory. Peak for a large `.xlsx` is two live workbooks plus the cell table (hundreds of MiB possible at the cap). This is **not** the 1 GB text-chunking path.
- **Regex skips number and date cells.** Regex runs on text and formula-cached strings only. An undashed numeric ID stored as an Excel number is **missed** on `--no-llm`. Store the dashed form as text, use a deny-list, or keep the language model on. There is no “9-digit integer ⇒ SSN” rule.
- **Stored value, not display format.** A numeric `123456789` with format `000-00-0000` is still seen as `123456789`.
- **Leftover risk.** Charts, comments, headers/footers, data-validation lists, defined names, and hyperlinks are not rewritten. A chart series or a header can still show a name. Delete those before sharing, or accept the residual.
- `.xls`, `.xlsm`, `.ods`, and `.xlsb` are rejected. Re-save as `.xlsx` or export CSV.

**SDK (Python)**

`anonymize_file("people.csv")` still returns a 2-tuple. The string is a row-wise **review flatten** (for verify/risk), not spreadsheet bytes. To write a real `.csv` / `.xlsx`, call `anonymize_tabular_file` and pass `entity_texts` into `save_results`:

```python
from pdf_anonymizer_core.core import anonymize_tabular_file
from pdf_anonymizer_core.utils import save_results

review, mapping, entity_texts = anonymize_tabular_file(
    "people.csv",
    characters_to_anonymize=100000,
    prompt_template="",
    model_name="",
    use_llm=False,
)
# mapping is original → written. Pass the CLI invert into save_results.
save_results(
    review,
    {v: k for k, v in mapping.items()},
    "people.csv",
    entity_texts=entity_texts,
)
```

---

## Anonymize a Word document

A letter, contract, or report is a Word file. The same engine walks **paragraphs** (body, tables, headers, footers, footnotes, comments) and writes a `.docx` plus the usual mapping. This is the same reversible pseudonymization as a PDF.

Word (`.docx`) needs the extra:

```bash
pip install "pdf-anonymizer-core[docx]"
# or
pip install "pdf-anonymizer-cli[docx]"
```

**CLI**

```bash
pdf-anonymizer run letter.docx
```

That writes:

- `data/anonymized/letter.anonymized.docx`
- `data/mappings/letter.mapping.json`

```bash
pdf-anonymizer deanonymize \
  data/anonymized/letter.anonymized.docx \
  data/mappings/letter.mapping.json

pdf-anonymizer verify data/anonymized/letter.anonymized.docx
pdf-anonymizer report data/anonymized/letter.anonymized.docx
```

No new flags. `--no-llm`, `--operator`, `--keep-list` / `--deny-list`, `--mapping-in`, and the rest work the same way as on a PDF. Files in one `run` still share a growing map (`letter.docx notes.md`).

**Notes**

- **Runs are joined before detection.** Word often splits `jane@acme.com` across three runs. The loader concatenates visible `w:t` text in a paragraph so the email is one string. After replacement, the new text is written into the first run and later runs are cleared. Bold or color on those later runs is lost.
- **Headers, footers, comments, and field codes are walked.** External hyperlink targets (`mailto:…`) are rewritten too.
- **Size / RAM.** Hard limits: 50 MiB on disk, 100,000 non-empty paragraphs, fields, and hyperlink targets. The package loads in memory. This is **not** the 1 GB text-chunking path.
- **Leftover risk.** Images, picture alt text, core properties (author / last modified by), charts, and embedded objects are not rewritten. Delete those before sharing, or accept the residual.
- Tracked-change deletions (`w:del`) are skipped so rejected text is not treated as live PII.
- `.doc`, `.docm`, `.dot`, `.dotm`, and `.dotx` are rejected. Re-save as `.docx`. Macro-enabled files are not supported (macros can re-derive PII).

**SDK (Python)**

`anonymize_file("letter.docx")` still returns a 2-tuple. The string is a part-wise **review flatten** (for verify/risk), not Word bytes. To write a real `.docx`, call `anonymize_docx_file` and pass `entity_texts` into `save_results`:

```python
from pdf_anonymizer_core.core import anonymize_docx_file
from pdf_anonymizer_core.utils import save_results

review, mapping, entity_texts = anonymize_docx_file(
    "letter.docx",
    characters_to_anonymize=100000,
    prompt_template="",
    model_name="",
    use_llm=False,
)
save_results(
    review,
    {v: k for k, v in mapping.items()},
    "letter.docx",
    entity_texts=entity_texts,
)
```

---

## Wrong-looking numbers are not treated as found

A string of digits can *look* like a card number, a bank account, or a national ID and still be junk — a version number, an order id, or someone typing 1234-5678-9012-3456 as an example.

**Think of it like this.** Shops do not only check that a card has 16 digits. They also run a tiny extra sum (often called a Luhn check) to see if the number was mistyped. Bank accounts (IBAN), vehicle numbers (VIN), and some national IDs have the same kind of extra digit.

The first, fast search still looks only at *shape*. Right after a hit, the tool runs that extra sum when one exists.

- If the sum **passes**, the stand-in keeps the real name: `IBAN_1`, `CREDIT_CARD_2`.
- If the sum **fails**, the number is **still hidden**. The stand-in says so: `IBAN_LIKE_1`, `CREDIT_CARD_LIKE_1`. A mistyped IBAN does not stay on the page.

What gets this extra check today: credit cards, IBANs, vehicle identification numbers, US medical NPI, Canadian SIN, Spanish DNI/NIE, Chinese resident ID, Indian Aadhaar, Brazilian CPF, Italian tax code, and Polish PESEL.

What does **not**: emails, phones, names, and any type with no well-known extra digit. Those stay “shape only” and never get a `_LIKE` label.

You do not turn this on or off. It always runs on the regex stage. The search patterns themselves did not change.

If you pass a type list (`--anonymized-entities`) with `IBAN`, mistyped IBANs (`IBAN_LIKE`) are included. You do not have to list both.

---

## Anonymize Only Specific Entity Types

Use a text file containing the entity types you care about (one per line, uppercase).

Example filter file (`only-people-orgs.txt`):

```
PERSON
ORGANIZATION
```

Run:

```bash
pdf-anonymizer run document.pdf --anonymized-entities only-people-orgs.txt
```

Only entities whose `type` matches one of the listed values (after the hybrid Regex + LLM stage) will be replaced. Everything else stays in clear text. Listing `IBAN` also hides `IBAN_LIKE` (mistyped IBANs). You do not list the `_LIKE` name yourself unless you want only the look-alikes.

This is useful when you want to protect names and companies but leave dates, addresses, or other categories untouched.

If you also want to hide identity clues (phrases that point to one person without naming them), include `INDIRECT` on its own line. Those clues are only found when you use the **detailed** instructions (`-p best-quality` or `--prompt-name detailed`).

See the example file at `packages/pdf-anonymizer-cli/entities.example.txt`.

---

## Hide identity clues, not only names

A name is the easy case. A harder case is a sentence that never writes the name, but still points to one person.

**Think of it like this.** If you black out "Ada Lovelace" in a biography, that helps. If the next sentence still says "the person who wrote the first computer program in the 1840s", a careful reader can put the name back. That leftover sentence is an identity clue.

The careful instructions (`detailed`) now ask the language model to find three common shapes of clue:

| Everyday sentence | Why it still names someone | What should be hidden |
|---|---|---|
| "a meeting with the CEO of Tesla in Austin" | Job + famous company + city | the whole clue, plus the company and city |
| "the author of the 'Harry Potter' series" | "Author of …" a unique work | the whole author phrase |
| "Acme Inc.'s only in-house patent counsel" | A one-of-a-kind role at a named company | the whole role phrase |

Use the careful profile so those instructions are actually sent:

```bash
pdf-anonymizer run interview-notes.pdf -p best-quality
```

Or keep another profile and only switch the instructions:

```bash
pdf-anonymizer run interview-notes.pdf --prompt-name detailed
```

**What you should see.** A clue may become `PERSON_1` (when the model knows the name) or `INDIRECT_1` (when it does not). Either way, the identifying words should leave the page.

**What you should not expect.** The short instructions (`simple`, used by `best-speed` and `best-cost`) do not hunt for these clues. Vague words such as "the CEO" or "a teacher in Austin" should also stay, because they could be many people.

This is a helper, not a lock. Read the result before you share it.

A longer, slower explanation of the same idea lives in the 101 page [How PDF Anonymizer is Different](../101/how-different.md#identity-clues-when-the-name-is-missing-but-everyone-still-knows-who-it-is).

---

## Choose and Override Configuration Profiles

Profiles are the recommended way to select a quality/speed/cost tradeoff (see also the table in the [CLI Reference](cli-usage.md)).

**Quick introspection (Python)**

```python
from pdf_anonymizer_core.conf import get_config_for_profile, ConfigProfile

cfg = get_config_for_profile(ConfigProfile.BEST_QUALITY)
print(cfg.model_dump())   # see exactly what the profile resolved to
```

Any scalar override (`model_name`, `prompt_name`, `chunk_size`) takes precedence.

---

## Use the Python SDK in Pipelines / Applications

Minimal end-to-end example using the helper that mirrors the CLI:

```python
import json
from pdf_anonymizer_core.conf import get_config_for_profile, ConfigProfile
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.prompts import detailed
from pdf_anonymizer_core.utils import deanonymize_file

# 1. Configure like the CLI would
cfg = get_config_for_profile(ConfigProfile.BEST_SPEED)

# 2. Anonymize
anonymized_text, raw_mapping = anonymize_file(
    file_path="data/contract.pdf",
    characters_to_anonymize=cfg.chunk_size,
    prompt_template=detailed.prompt_template,
    model_name=cfg.model_name,
    chunk_overlap=cfg.chunk_overlap,
    max_retries=cfg.max_retries,
    base_retry_delay=cfg.base_retry_delay,
    max_retry_delay=cfg.max_retry_delay,
)

# 3. (Optional) Save the artifacts yourself
with open("contract.anonymized.md", "w", encoding="utf-8") as f:
    f.write(anonymized_text)

placeholder_to_original = {v: k for k, v in raw_mapping.items()}
with open("contract.mapping.json", "w", encoding="utf-8") as f:
    json.dump(placeholder_to_original, f, indent=2)

# 4. Later: restore
deanonymized_file_path, stats_file_path = deanonymize_file(
    "contract.anonymized.md",
    "contract.mapping.json",
)
print("Deanonymized file saved to:", deanonymized_file_path)
print("Stats file saved to:", stats_file_path)
```

You can also pass a custom list for `anonymized_entities` or supply your own `regex_patterns` dict for the first-stage NER.

---

## Working with Mapping Files and Deanonymization Statistics

After deanonymization the tool always writes a stats file:

`data/stats/<stem>.deanonymization_stat.json`

Example contents:

```json
{
  "anonymized_file": "...",
  "mapping_file": "...",
  "deanonymized_file": "...",
  "unused_mappings": ["PERSON_7"],
  "not_found_mappings": []
}
```

- `unused_mappings`: placeholders that existed in the map but were never present in the anonymized text (harmless).
- `not_found_mappings`: placeholders found in the anonymized text that had no entry in the map (usually indicates a corrupted or partial map).

These stats are useful for audit/compliance pipelines.

The mapping file format is `placeholder → original` (the direction used at deanonymization time). The CLI and `deanonymize_file` also accept the legacy `original → placeholder` direction and auto-detect.

---

## LLM Response Caching

By default the core caches successful LLM responses (keyed by model + prompt hash) to `data/cache/llm_responses.json`.

Benefits:
- Re-running the same document (or very similar chunks) is dramatically faster and cheaper.
- Helps during development and iterative prompt tuning.

**Disable or relocate the cache (SDK)**

```python
from pdf_anonymizer_core.llm_provider import configure_cache
from pdf_anonymizer_core.conf import get_config_for_profile, ConfigProfile

cfg = get_config_for_profile(ConfigProfile.BEST_SPEED)

configure_cache(
    enabled=False,                    # or True
    cache_dir=cfg.cache_dir,
    cache_file=cfg.cache_file,
)
```

The CLI always enables caching according to the profile's `AppConfig`. Delete or move the cache directory for a cold run.

---

## Processing Very Large Documents

PDF Anonymizer is designed for files up to ~1 GB thanks to streaming chunking.

**Spreadsheets and Word files are in-memory.** CSV, Excel, and `.docx` do **not** use this 1 GB streaming path. Spreadsheets are capped at 50 MiB / 500,000 non-empty cells. Word is capped at 50 MiB / 100,000 non-empty paragraphs. See [Anonymize a CSV or Excel roster](#anonymize-a-csv-or-excel-roster) and [Anonymize a Word document](#anonymize-a-word-document).

**Practical tips**

- Start with the `best-cost` profile (larger chunks, fewer LLM calls).
- Increase `--characters-to-anonymize` further if your model has a large context window:

  ```bash
  pdf-anonymizer run huge-book.pdf -p best-cost --characters-to-anonymize 120000
  ```

- Use Markdown-aware splitting (automatic for `.pdf` and `.md`). Plain `.txt` falls back to recursive character splitting.
- Watch the log output: each chunk is logged (`Identifying entities in part X/Y...`).
- The `chunk_overlap` (profile-driven) helps the model see context across chunk boundaries for coreference.
- If you hit rate limits, the built-in retry logic with exponential backoff (and jitter) will help on transient errors.

---

## HIPAA Safe Harbor coverage aid

Health notes mention more than names: visit dates, record numbers, small-area places, ages over 89.

`--entity-profile hipaa-safe-harbor` is a **coverage aid**. It:

- asks the careful prompt to look for the identifier *classes* that apply to text (the familiar list of 18 kinds: names, places smaller than a state, dates about a person, phones, emails, SSNs, record and plan numbers, licenses, vehicle and device IDs, URLs, IPs, and phrases for biometrics or face photos)
- writes dates as a **year**, ZIP codes as **first three digits**, and ages over 89 as **90+**
- does **not** hide pixels in a photo, and does **not** mean the file is legally de-identified

This is **not** a HIPAA Safe Harbor certification. A person still has to read the result. Expert Determination is a different path and is not this flag.

```bash
pdf-anonymizer run clinic-note.pdf --entity-profile hipaa-safe-harbor
```

You can still add `--operator` (your choice wins) or `--anonymized-entities` (extra types are kept, not used to shrink the list).

---

## Choose how a type is written (mask, year, hash)

By default every find becomes a stand-in such as `PERSON_1` or `CREDIT_CARD_2`. That is best for sending the page to another AI and putting names back later.

Sometimes you want a different mark:

| Operator | What the reader sees | Good for |
|---|---|---|
| `replace` | `PERSON_1` (default) | Reversible stand-ins |
| `mask` | `****-****-****-1111` | Cards, SSNs, phones (keep a little shape) |
| `generalize` | `2019`, `021**`, `40-49` | Dates, ZIP codes, ages |
| `hash` | `H_` plus a short fingerprint | Same value always looks the same, but not readable |
| `shift` | A nearby date | Dates that must stay dates, not just a year |
| `fake` | `Jane Alvarez`, `555-0103` | Looks real; same person always gets the same fake |

```bash
pdf-anonymizer run invoice.pdf \
  --operator CREDIT_CARD=mask \
  --operator DATE=generalize \
  --operator DATE_ISO=generalize

# Invent stable fake names (same person → same fake)
pdf-anonymizer run notes.pdf --operator PERSON=fake --operator EMAIL=fake
```

Types you do not list stay as stand-ins. `CREDIT_CARD_LIKE` follows `CREDIT_CARD`.

The mapping file still records how to put the original back when the written form is unique. Two dates that both become `2019` cannot both be restored uniquely.

---

## Score leftover identity clumps (linkage risk)

Hiding names is not the same as hiding *who it is*. If the masked page still says `JOB_TITLE_1 of ORGANIZATION_1 in LOCATION_1`, a reader can often put the name back.

After `run`, the tool scores those clumps (unless `--no-risk`). It **does not change the file**. It writes:

`data/stats/<stem>.risk.json`

Levels:

- **high** — job + company + place, or a nameless identity phrase (`INDIRECT_1`), or three identity clues in one passage
- **medium** — two clues together (person + city, person + company)
- **low** — only one kind of clue, or none

```bash
pdf-anonymizer run notes.pdf
pdf-anonymizer run notes.pdf --no-risk
pdf-anonymizer report data/anonymized/notes.anonymized.md
```

This is a warning light, not a proof of safety. A `low` score does not mean the page is safe to publish.

---

## Check the masked file for leftovers

Hiding names is a first pass. A leftover email or a mistyped IBAN can still sit in the masked page.

After `run`, the tool scans the result with the same cheap number/email search. It **does not rewrite** the file. It writes a report:

`data/stats/<stem>.residual_pii.json`

Stand-in labels such as `PERSON_1` or `IBAN_LIKE_1` are ignored. Real leftovers are listed.

```bash
# Default: regex scan after every run
pdf-anonymizer run notes.pdf

# Skip the scan
pdf-anonymizer run notes.pdf --no-verify

# Also ask the language model (slower)
pdf-anonymizer run notes.pdf --verify-llm

# Scan a file you already have
pdf-anonymizer verify data/anonymized/notes.anonymized.md
```

This is a helper, not a lock. Read the report (and the page) before you share.

---

## Limit national-ID regexes to some countries

The first, fast search knows ID shapes for 30+ countries. On a US contract that is extra noise: a Polish PESEL or an Indian Aadhaar pattern can fire on a random digit string.

`--countries` keeps **every universal pattern** (email, phone, URL, card, IBAN, IP, MAC, crypto, VIN, dates, amounts) and only the national IDs for the codes you list.

```bash
pdf-anonymizer run contract.pdf --countries US,GB
```

That still finds emails and IBANs. It still finds a US SSN and a UK National Insurance number. It does **not** run the Polish, Indian, or Chinese national-ID patterns.

Use ISO-2 codes (`US`, `GB`, `FR`, …), comma-separated, any case. Unknown codes stop the run with an error.

**SDK**

```python
from pdf_anonymizer_core.conf import filter_regex_patterns, get_config_for_profile, ConfigProfile

# Same filter the CLI uses
only_us_gb = filter_regex_patterns(["US", "GB"])

cfg = get_config_for_profile(ConfigProfile.BEST_SPEED, countries=["US", "GB"])
# cfg.regex_patterns is already filtered
```

This is a regex-stage setting only. The language model still reads the whole page and can name an ID from another country if the text is clear.

---

## Replacement is by span, not a blind search

The tool does **not** walk the page and replace every copy of the letters `May`. It finds each mention as a *span* (a start and end character), keeps the longer span when two hits overlap (`John Doe` wins over the inner `John`), and writes replacements from the end of the string so earlier offsets stay valid.

You do not turn this on. It is how replacement always works now.

There is no extra CLI flag.

---

## Score a gold fixture (TAB-style eval)

Unit tests check regexes and mappings. They do not tell you “how many real names did we miss?”. Score names are defined on [Terminology](terminology.md#how-we-measure).

`tests/eval/` is a tiny gold page plus a scorer. It reports mention-level and entity-level precision / recall / F1, split by **direct** identifiers (email, SSN, person) versus **quasi** identifiers (city, date). That split matters: a high score on cities can hide a poor score on names.

```bash
# Run the regex stage on the built-in mini fixture
uv run python scripts/eval_tab.py

# Or score your own predictions JSON
uv run python scripts/eval_tab.py --fixture tests/eval/fixture.json --predictions pred.json
```

This is tests and scripts only. It does not change `run`. It is not a legal privacy proof.

---

## Gold-corpus benchmark

Goals, sources, metrics, and CI gates are on **[Gold corpus & eval](gold-corpus.md)**. The commands are:

```bash
make gold-corpus          # download TAB / Presidio / Gretel into data/gold-corpus/
make gold-bench           # regex-only baseline (no API key)
make gold-table           # public eval table
make test-cov             # PR suite: leftover gate, residual JSON, coverage, fuzz
```

This is tests and scripts only. It is not a legal privacy proof.

---

## Advanced: Custom First-Stage Regex (SDK only)

The hybrid approach runs a fast deterministic RE2 (google-re2) regex pass before every LLM call.
You can supply your own set (or a filtered slice of the built-in collection):

```python
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.conf import get_config_for_profile, ConfigProfile
from pdf_anonymizer_core.prompts import detailed

# Option A: completely custom
custom_regex = {
    "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "EMPLOYEE_ID": r"\bEMP-\d{6}\b",
    # ...
}

# Option B: built-in library, limited to some countries (plus all universal keys)
from pdf_anonymizer_core.conf import filter_regex_patterns

country_focused = filter_regex_patterns(["US", "CA", "GB", "FR", "IN", "CN", "DE"])

cfg = get_config_for_profile(ConfigProfile.BEST_SPEED)

text, mapping = anonymize_file(
    file_path="internal-log.txt",
    characters_to_anonymize=cfg.chunk_size,
    prompt_template=detailed.prompt_template,
    model_name=cfg.model_name,
    regex_patterns=country_focused,   # or custom_regex or DEFAULT_REGEX_PATTERNS
    # ... other config fields
)
```

All regex patterns are RE2-safe (linear time, no ReDoS). Entity type keys (upper-cased) become the
placeholder prefixes (IBAN_3, SSN_US_2, CRYPTO_ETH_1 ...). The LLM stage still runs afterwards and
adds semantic detections the regex stage could not catch. See `conf.py` (the giant docstring on
`DEFAULT_REGEX_PATTERNS`) and `regex_ner.py` for the full catalogue and country partitioning rules.

The default collection already covers the mandatory countries (USA, Canada, UK, Spain, Italy,
France, India, China) plus 25+ more via dedicated national/tax/driver/VAT/business patterns plus
universals that apply everywhere (credit cards, IBANs used across Europe, crypto, VIN, MAC, etc.).

---

## Debugging, Logs & Observability

The CLI always configures logging to both the console (INFO level) and a file:

- `app.log` in the current working directory (or wherever the process starts)
- Real-time progress per chunk: "Identifying entities in part X/Y...", timing, regex vs LLM counts, cache hits, retry messages, etc.

When things go wrong the log is the first place to look (rate-limit errors, provider auth problems, JSON parse failures from the LLM, empty extraction, etc.).

You can also delete or move `data/cache/llm_responses.json` to force a cold run with no cached LLM responses.

---

## See Also

- **[CLI Reference](cli-usage.md)** — complete flag reference, model aliases, and the profiles table.
- **[SDK & API Usage](api-usage.md)** — lower-level function signatures and returns.
- **[API Reference (auto)](api-reference.md)** — living signature documentation generated from source docstrings.
- **[Architecture Design](architecture.md)** — how chunking, consolidation, mapping, and reversal actually work.
- **[Installation & Setup](installation.md)** — provider extras and environment variables.
- **[Troubleshooting](troubleshooting.md)** — solutions to common problems encountered when following these recipes.

For conceptual background see the [Privacy & Anonymization 101](../101/index.md) track.
