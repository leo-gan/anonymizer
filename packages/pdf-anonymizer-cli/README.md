# 🦉🫥 PDF Anonymizer CLI

A command-line interface for anonymizing PDF, Markdown, and plain text files using LLMs.

- **High-Quality Anonymization**: Leverages LLMs to identify and replace Personally Identifiable Information (PII) with high accuracy.
- **Identity clues**: With `-p best-quality` or `--prompt-name detailed`, the tool also hides phrases that point to one person without writing their name (for example "the CEO of Tesla"). The default `best-speed` profile does not.
- **Checksum labels**: After the fast number search, a real IBAN becomes `IBAN_1` and a mistyped one becomes `IBAN_LIKE_1`. Both are hidden. Same idea for cards, VINs, and a few national IDs.
- **Operators, reports, and lists**: `--operator TYPE=mask|hash|generalize|shift|fake`, leftover scan (`verify`), linkage-risk score (`report`), `--keep-list` / `--deny-list`, `--mapping-in`, optional locked maps, HIPAA coverage aid. See the [CLI History](https://leo-gan.github.io/anonymizer/project/cli-usage/#history).
- **Large File Support**: Consistently anonymizes large files (tested up to 1GB).
- **Multi-Provider & Cost-Effective**: Free to use with local [Ollama](https://ollama.com/) models. It also supports major providers like [OpenAI](https://openai.com/), [Anthropic](https://www.anthropic.com/), [Google](https://ai.google.com/), [Hugging Face](https://huggingface.co/), and [OpenRouter](https://openrouter.ai/).
- **Reversible**: Supports deanonymization to recover original data when needed.
- **Multi-Format**: Works with PDF, Markdown, plain text, CSV, Excel, and Word (`.docx`) files.


## Installation

Install the CLI with your favorite package manager. To use a specific LLM provider, you must install the corresponding extra.

- **Google**: `pip install "pdf-anonymizer-cli[google]"`
- **Ollama**: `pip install "pdf-anonymizer-cli[ollama]"`
- **Hugging Face**: `pip install "pdf-anonymizer-cli[huggingface]"`
- **OpenRouter**: `pip install "pdf-anonymizer-cli[openrouter]"`
- **OpenAI**: `pip install "pdf-anonymizer-cli[openai]"`
- **Anthropic**: `pip install "pdf-anonymizer-cli[anthropic]"`
- **Excel** (`.xlsx`): `pip install "pdf-anonymizer-cli[excel]"`
- **Word** (`.docx`): `pip install "pdf-anonymizer-cli[docx]"`

You can also install multiple extras at once:

```bash
pip install "pdf-anonymizer-cli[google,openrouter]"
```

This installs the `pdf-anonymizer` executable.


## Environment Variables

The CLI will automatically load a `.env` file from the current directory or any parent directory. For consistency, it's recommended to place a single `.env` file at the root of the repository.

- `GOOGLE_API_KEY`: Required when using Google models.
- `HUGGING_FACE_TOKEN`: Required when using Hugging Face models. You can get a token from [here](https://huggingface.co/docs/hub/security-tokens).
- `OPENROUTER_API_KEY`: Required when using OpenRouter models.
- `OPENAI_API_KEY`: Required when using OpenAI models.
- `ANTHROPIC_API_KEY`: Required when using Anthropic models.
- `OLLAMA_HOST`: Optional, defaults to `http://localhost:11434` when using Ollama models.
- `ANONYMIZER_MAPPING_KEY`: Optional. Same as `--mapping-passphrase` (writes `*.mapping.json.enc`).
- `ANONYMIZER_FAKE_SECRET`: Optional. Seed for `--operator TYPE=fake`.

Example `.env` file:
```env
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
HUGGING_FACE_TOKEN="YOUR_HF_TOKEN_HERE"
OPENROUTER_API_KEY="YOUR_OPENROUTER_KEY"
```

## Usage

### Anonymize

The `run` command anonymizes one or more files.

```bash
pdf-anonymizer run FILE_PATH [FILE_PATH ...] \
  [-p | --config-profile {best-quality|best-speed|best-cost|regex-only}] \
  [--no-llm] \
  [--characters-to-anonymize INTEGER] \
  [--prompt-name {simple|detailed}] \
  [--model-name TEXT] \
  [--anonymized-entities PATH] \
  [--countries US,GB] \
  [--verify / --no-verify] \
  [--verify-llm]
```

**Arguments**:
- `FILE_PATH`: Path to one or several PDF, Markdown, text, CSV, Excel (`.xlsx`), or Word (`.docx`) files for anonymization.

**Options**:
- `-p, --config-profile {best-quality|best-speed|best-cost|regex-only}`: The configuration profile to use. Profiles bundle sensible defaults for model, prompt, chunk size, overlap, and retries (default: `best-speed`). `regex-only` skips the language model. Individual flags (`--model-name`, `--prompt-name`, `--characters-to-anonymize`) act as overrides on top of the chosen profile.
- `--no-llm`: Skip the language model. Only the RE2 regex stage runs. Names and identity clues will be missed. Same as `-p regex-only`.
- `--characters-to-anonymize INTEGER`: Number of characters to process in each chunk (default: `100000`; overrides profile).
- `--prompt-name [simple|detailed]`: The prompt template to use (default: `detailed`; overrides profile).
- `--model-name TEXT`: The language model to use (overrides profile).
- `--anonymized-entities PATH`: Path to a file with a list of entities to anonymize.
- `--countries TEXT`: ISO-2 country codes for national-ID regexes, comma-separated (e.g. `US,GB`). Universal patterns (email, IBAN, cards, …) always stay. Default: all countries.
- `--verify / --no-verify`: After masking, scan for leftovers (default: on). Writes `data/stats/<stem>.residual_pii.json`. Does not rewrite the file.
- `--verify-llm`: Also ask the language model to hunt for leftovers.
- `--ocr`: If a PDF has no text layer, OCR it with Tesseract (must be on PATH). A scan with OCR off is an error.
- `--output-pdf`: Also write a sanitized native PDF. Markdown is still written.
- `--redact`: Irreversible native PDF (black boxes). Implies `--output-pdf`.
- `--mapping-passphrase TEXT`: Lock the mapping as `*.mapping.json.enc` (AES-256-GCM + Argon2id). Also `ANONYMIZER_MAPPING_KEY`. Default: plaintext JSON.
- `--ephemeral-mapping`: Do not write `data/mappings/`. The vocabulary stays in this process only.
- `--operator TYPE=op`: How to write a type (`replace`, `mask`, `hash`, `generalize`, `shift`, `fake`). Repeatable. Default is `replace`.
- `--fake-secret TEXT`: Seed for `fake`. Also `ANONYMIZER_FAKE_SECRET`.
- `--risk / --no-risk`: After masking, score identity-clue clumps (default: on). Writes `data/stats/<stem>.risk.json`.

`pdf-anonymizer report FILE` runs the same linkage-risk score on an already-masked file.

- `--entity-profile hipaa-safe-harbor`: coverage aid for the 18 Safe Harbor identifier classes (year-only dates, ZIP3, age 90+). **Not a compliance certificate.**
- `--mapping-in PATH`: reuse an existing mapping so the same person stays `PERSON_1` across files. Files in one `run` share the map automatically.
- `--keep-list PATH`: phrases to leave visible (one per line).
- `--deny-list PATH`: phrases that must be hidden even if detection missed them.

`pdf-anonymizer verify FILE` runs the same leftover scan on an already-masked file.

**Models**:
You can use any of the predefined models below, or specify a new model using the format `"provider/model-name"`. 
For example: `--model-name "google/gemini-flash-latest"`.

- **Google**: `gemini-2.5-pro`, `gemini-2.5-flash` (default), `gemini-2.5-flash-lite`.
- **Ollama**: `gemma:7b`, `phi4-mini`.
- **Hugging Face**: `openai/gpt-oss-20b`, `mistralai/Mistral-7B-Instruct-v0.1`, `HuggingFaceH4/zephyr-7b-beta`.
- **OpenRouter**: `openai/gpt-4o`, `google/gemini-pro`.
- **OpenAI**: `gpt-4o`, `gpt-5`.
- **Anthropic**: `claude-4-sonet`, `claude-4.5-sonet`.

### Examples

**Basic anonymization (uses the default `best-speed` profile)**:
```bash
pdf-anonymizer run document.pdf
```

**High-quality run on an important document**:
```bash
pdf-anonymizer run contract.pdf -p best-quality
```

**Fast & cheap batch processing with a local model (override profile defaults)**:
```bash
pdf-anonymizer run notes/*.md -p best-cost --model-name "ollama/phi4-mini"
```

**A new model (Google) and a simple prompt**:
```bash
pdf-anonymizer run notes.md --model-name "google/gemini-flash-latest" --prompt-name simple
```

**Using an OpenRouter model**:
```bash
pdf-anonymizer run report.pdf --model-name "openai/gpt-4o"
```

### Deanonymize

The `deanonymize` command reverts anonymization using a mapping file.

```bash
pdf-anonymizer deanonymize ANONYMIZED_FILE MAPPING_FILE [--mapping-passphrase TEXT]
```

**Arguments**:
- `ANONYMIZED_FILE`: Path to the anonymized text file.
- `MAPPING_FILE`: Path to the JSON mapping file (plaintext or `*.mapping.json.enc`).
- `--mapping-passphrase`: Required for an encrypted mapping. Also `ANONYMIZER_MAPPING_KEY`.
- `--source-sha256`: Optional. Expected SHA-256 of the original source file.

**Example**:
```bash
pdf-anonymizer deanonymize \
    data/anonymized/document.anonymized.md \
    data/mappings/document.mapping.json
```

This will create a deanonymized version of the file at `data/deanonymized/document.deanonymized.md`.

---

## See Also

- **[Main Documentation](https://leo-gan.github.io/anonymizer/)** — Full guides including the 101 course.
- **[Core Package README](../pdf-anonymizer-core/README.md)** — Details on the underlying library.
- **[Recipes & Common Workflows](https://leo-gan.github.io/anonymizer/project/recipes/)** — Practical CLI usage examples (profiles, batching, external workflows, etc.).
- **[CLI Reference (full)](https://leo-gan.github.io/anonymizer/project/cli-usage/)** — Complete command reference on the docs site.
- **[Troubleshooting](https://leo-gan.github.io/anonymizer/project/troubleshooting/)** — Help with common CLI problems.
- **[Architecture](https://leo-gan.github.io/anonymizer/project/architecture/)** — How the CLI and core work together.