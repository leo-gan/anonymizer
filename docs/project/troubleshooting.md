# Troubleshooting

Common problems and how to resolve them.

## Authentication / Missing API Key

- **Symptom**: Errors like "GOOGLE_API_KEY not found", "HUGGING_FACE_TOKEN environment variable not set", or provider import failures.
- **Fix**:
  - Create a `.env` file in the directory where you run the command (or a parent directory).
  - The CLI automatically loads it. Example:

    ```env
    GOOGLE_API_KEY="AIza..."
    OPENAI_API_KEY="sk-..."
    ANTHROPIC_API_KEY="sk-ant-..."
    HUGGING_FACE_TOKEN="hf_..."
    OPENROUTER_API_KEY="sk-or-..."
    OLLAMA_HOST="http://localhost:11434"
    ANONYMIZER_MAPPING_KEY="a long secret"
    ANONYMIZER_FAKE_SECRET="another long secret"
    ```
  - `ANONYMIZER_MAPPING_KEY` locks mapping files as `*.mapping.json.enc`. `ANONYMIZER_FAKE_SECRET` seeds `--operator TYPE=fake`. Neither is required.
  - For the SDK, load the environment variables yourself (e.g. with `python-dotenv` or `os.environ`).

## Ollama Not Running or Model Not Found

- **Symptom**: Connection errors or "model not found" when using `ollama/...` models.
- **Fix**:
  - Start the Ollama server: `ollama serve`
  - Pull the model first: `ollama pull phi4-mini` or `ollama pull gemma:7b`
  - Check `OLLAMA_HOST` if Ollama is not on the default port.

## Rate Limits, Timeouts, or Retries

- **Symptom**: Intermittent failures, "rate limit", 429, or empty results on long documents.
- **Fix**:
  - Use a more generous profile: `-p best-quality` (more retries, smaller chunks).
  - Or override manually with a larger model / more retries via SDK `max_retries`.
  - The library uses exponential backoff + jitter for transient errors (rate limits, server errors, connection issues, JSON parse errors). Auth errors are not retried.

## Nothing Was Anonymized / Very Few Entities Found

- **Symptom**: Output looks almost identical to the input.
- **Possible causes & fixes**:
  - The document contains very little PII (or the LLM prompt style was too conservative).
  - A sentence may still point to one person without writing their name (an identity clue). The default `best-speed` profile does not hunt for those. Try `-p best-quality` (uses the `detailed` prompt and a stronger model by default).
  - Use `--anonymized-entities` only if you intentionally want to restrict the types.
  - Check `app.log` — it shows how many entities were found by Regex vs LLM per chunk.
  - A number that *looks* like a card, IBAN, VIN, or national ID but fails the extra check-digit is still hidden, as `IBAN_LIKE_1` / `CREDIT_CARD_LIKE_1` and so on. That is expected for typos and example numbers such as `1234-5678-9012-3456`.
  - After a run, check `data/stats/<stem>.residual_pii.json` (or `pdf-anonymizer verify …`). Leftover emails or numbers listed there were not hidden.
  - Check `data/stats/<stem>.risk.json` (or `pdf-anonymizer report …`). A **high** score means leftover identity clumps (job + company + place), not that names were missed.
  - A keep-list phrase stays visible on purpose. A deny-list phrase becomes `CUSTOM_n` even if regex and the model missed it.
  - Very short documents or unusual formatting can reduce recall.

## Encrypted mapping will not open

- **Symptom**: `deanonymize` fails on `*.mapping.json.enc`, or you only have a `.enc` file and no passphrase.
- **Fix**:
  - Pass the same `--mapping-passphrase` you used with `run`, or set `ANONYMIZER_MAPPING_KEY`.
  - If you passed `--source-sha256`, it must be the SHA-256 of the *original* source file that was locked, not the anonymized file.
  - There is no recovery path. The masked document plus a locked map without the passphrase cannot put names back.
  - Default `run` still writes plaintext `*.mapping.json` if you set no passphrase.
  - `--ephemeral-mapping` never wrote a map. That run cannot be reversed from disk.

## A date or ZIP cannot be restored uniquely

- **Symptom**: After `--operator DATE=generalize` (or HIPAA year-only dates), two different originals both became `2019`.
- **Fix**: That is expected. Generalize, mask, and hash are not always one-to-one. Use `replace` (the default `PERSON_1`) when you need a unique round-trip.

## `--entity-profile hipaa-safe-harbor` is not a certificate

- That flag is a **coverage aid** (broader identifier classes, year-only dates, ZIP3, age 90+).
- It does **not** mean the file is legally de-identified. It does not hide pixels in a photo. A person still has to read the result.

## LLM Returns Invalid JSON / Parsing Failures

- **Symptom**: Errors about JSON decode or Pydantic validation in the logs.
- **Fix**:
  - The library already retries on parsing errors (the LLM sometimes returns markdown fences or extra text).
  - If it keeps happening, switch to a stronger model (`-p best-quality`) or a model known to follow JSON instructions well.
  - The prompts are designed to return only a JSON object.

## Cache Problems or Stale Results

- **Symptom**: Changes to prompts or documents are ignored, or you want a completely fresh run.
- **Fix**:
  - Delete or rename `data/cache/llm_responses.json`.
  - Or disable caching programmatically:

    ```python
    from pdf_anonymizer_core.llm_provider import configure_cache
    configure_cache(enabled=False)
    ```

## Scanned PDF is refused

- **Symptom**: `This PDF has pages but no extractable text (likely a scan).`
- **Fix**: Install Tesseract on PATH and re-run with `--ocr`, or supply a PDF that already has a text layer. The tool will not write an empty “success” file.

## Tesseract missing

- **Symptom**: `OCR requires the Tesseract binary on PATH.`
- **Fix**: Install the Tesseract **system** package (`apt-get install tesseract-ocr` / `brew install tesseract`). There is no pip extra for this.

## Native PDF still shows a name in an image

- **Symptom**: A photo or letterhead still shows a name after `--output-pdf`.
- **Fix**: The digital path excises text glyphs. It does not OCR images. Delete image-only letterhead, or accept the residual.

## `--output-pdf` rejected on a text file

- **Symptom**: `--output-pdf only applies to PDF inputs.`
- **Fix**: That flag rewrites a PDF package. Use it on a `.pdf`.

## Large Files / Memory or Context Issues

- **Symptom**: Out of memory, context length errors, or very slow runs.
- **Fix**:
  - Use `-p best-cost` (larger chunks).
  - Manually increase `--characters-to-anonymize` (e.g. 120000 or higher) when using a model with a large context window.
  - The tool uses Markdown-aware splitting for PDFs and `.md` files to preserve structure.
  - CSV and Excel are **in-memory**. They are refused above 50 MiB or 500,000 non-empty cells. That is not the 1 GB text-chunking path.
  - Word `.docx` is **in-memory**. It is refused above 50 MiB or 100,000 non-empty paragraphs. That is not the 1 GB text-chunking path.

## Excel extra missing

- **Symptom**: `Excel support requires the extra: pip install "pdf-anonymizer-core[excel]"`
- **Fix**: `pip install "pdf-anonymizer-core[excel]"` or `pip install "pdf-anonymizer-cli[excel]"`. CSV does not need this extra.

## Word extra missing

- **Symptom**: `Word support requires the extra: pip install "pdf-anonymizer-core[docx]"`
- **Fix**: `pip install "pdf-anonymizer-core[docx]"` or `pip install "pdf-anonymizer-cli[docx]"`.

## Rejected Word formats

- **Symptom**: `.doc`, `.docm`, `.dot`, `.dotm`, or `.dotx` is rejected with a convert-to-docx message.
- **Fix**: Re-save as `.docx`. Macro-enabled documents are not supported (macros can re-derive PII).

## Rejected spreadsheet formats

- **Symptom**: `.xls`, `.xlsm`, `.ods`, or `.xlsb` is rejected with a convert-to-xlsx / export-CSV message.
- **Fix**: Re-save as `.xlsx` or export CSV. Macro-enabled workbooks are not supported (macros can re-derive PII).

## Formulas are dropped

- **Symptom**: An Excel formula is gone; a CSV cell that started with `=` now starts with `'`.
- **Fix**: That is intended. Excel writes cached values only so `=A1` cannot restore a replaced name. CSV prefixes `'` on cells whose raw value starts with `=`. `+1-555-0100` is a phone, not a formula, and is left untouched.

## Charts, comments, and other leftovers

- **Symptom**: A name still appears in a chart, comment, header/footer, data-validation list, defined name, or hyperlink.
- **Fix**: On **spreadsheets**, those surfaces are not walked. Delete charts and clear headers/comments before sharing, or accept the residual. On **Word**, headers, footers, comments, field codes, and hyperlink targets **are** walked. Images, alt text, core properties (author), charts, and embedded objects are not.

## Word formatting after the first run is gone

- **Symptom**: A sentence that was partly bold or a second color is now one style.
- **Fix**: Word splits one phrase across many runs. Replacement writes the new text into the first run and clears the rest, so later-run formatting is lost. Paragraph style is kept.

## Undashed numeric IDs missed on `--no-llm`

- **Symptom**: An Excel integer such as `123456789` is still the same integer after `--no-llm`.
- **Fix**: Regex does not run on number or date cells (it would shred employee IDs and quantities). Store the dashed form as text, use a deny-list, or keep the language model on. There is no “9-digit integer ⇒ SSN” rule.

## Stored value, not display format

- **Symptom**: A numeric cell formatted as `000-00-0000` was not treated as a dashed SSN.
- **Fix**: Detection uses the stored value (`123456789`), not Excel’s display format.

## Output Files Not Where Expected

- All artifacts are written relative to the current working directory:
  - `data/anonymized/`
  - `data/mappings/`
  - `data/deanonymized/`
  - `data/stats/`
- These directories are created automatically.

## Still Stuck?

1. Look at `app.log` (always written alongside console output).
2. Run with a small test file and `-p best-quality`.
3. Check the [Recipes & Common Workflows](recipes.md) page for working examples.
4. Open an issue on GitHub with the log output and the exact command you ran.

---

---

## See Also

- **[Recipes & Common Workflows](recipes.md)** — many of the issues here are demonstrated with working examples.
- **[CLI Reference](cli-usage.md)** — full command options and profiles.
- **[Architecture Design](architecture.md)** — deeper internals that can help understand error cases.
- **[SDK & API Usage](api-usage.md)** — programmatic usage.
