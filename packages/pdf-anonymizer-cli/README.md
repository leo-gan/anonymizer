# pdf-anonymizer-cli

CLI for anonymizing PDF, Markdown, and plain text files using LLMs. Supports Google Gemini and local Ollama models. Produces anonymized text plus a mapping JSON for consistent entity replacement. Also supports deanonymization.

## Install

Using uv (recommended):

```bash
# From the repository root
uv pip install -e ./packages/pdf-anonymizer-core
uv pip install -e ./packages/pdf-anonymizer-cli
```

Using pip:

```bash
pip install -e ./packages/pdf-anonymizer-core
pip install -e ./packages/pdf-anonymizer-cli
```

This installs the `pdf-anonymizer` executable entrypoint.

## Environment

The CLI will auto-load a `.env` file located at:

- `packages/pdf-anonymizer-cli/.env`

You can also export variables in your shell instead of using a `.env` file.

Variables:

- `GOOGLE_API_KEY` — required for Google Gemini models
- `OLLAMA_HOST` — optional, defaults to `http://localhost:11434`

Example `.env`:

```env
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
# OLLAMA_HOST="http://localhost:11434"
```

## Usage

Basic help:

```bash
pdf-anonymizer --help
```

### Anonymize

```bash
pdf-anonymizer run FILE_PATH [FILE_PATH ...] \
  [--characters-to-anonymize INT] \
  [--prompt-name {simple|detailed}] \
  [--model-name MODEL] \
  [--anonymized-entities PATH]
```

- `FILE_PATH ...` — one or more files (PDF, .md, .txt)
- `--characters-to-anonymize` — chunk size per LLM call (default from core config)
- `--prompt-name` — `simple` or `detailed` (default: `detailed`)
- `--model-name` — e.g. `gemini-2.5-flash` (default) or local models like `gemma:7b`, `phi4-mini`
- `--anonymized-entities` — path to a newline-delimited list of entities to anonymize

Outputs per input file:

- `data/anonymized/<name>.anonymized.{md|txt}`
- `data/mappings/<name>.mapping.json`

### Deanonymize

```bash
pdf-anonymizer deanonymize ANONYMIZED_FILE MAPPING_FILE
```

Outputs:

- `data/deanonymized/<name>.deanonymized.md`
- `data/stats/<name>.deanonymization_stat.json`

## Examples

```bash
# Minimal
pdf-anonymizer run document.pdf

# Custom model and prompt
pdf-anonymizer run notes.md --model-name phi4-mini --prompt-name simple

# Custom chunk size
pdf-anonymizer run document.txt --characters-to-anonymize 50000

# Deanonymize
pdf-anonymizer deanonymize \
  data/anonymized/document.anonymized.md \
  data/mappings/document.mapping.json
```

## Notes

- For Google models, ensure `GOOGLE_API_KEY` is set; otherwise the command will exit with an error.
- Logs are written to `app.log` alongside console output.
