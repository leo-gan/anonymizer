# PDF Anonymizer CLI

A command-line interface for anonymizing PDF, Markdown, and plain text files using LLMs.

## Installation

This project uses `uv` and is structured as a monorepo. The dependencies for the CLI and its core library are managed at the root of the project.

1.  **Install `uv`**: Follow the [official installation instructions](https://astral.sh/docs/uv#installation).
2.  **Install dependencies from the repository root**:
    ```bash
    # From the repository root
    uv sync
    ```
    This installs the `pdf-anonymizer` executable.

## Environment Variables

The CLI will automatically load a `.env` file from the current directory or any parent directory. For consistency, it's recommended to place a single `.env` file at the root of the repository.

- `GOOGLE_API_KEY`: Required when using Google's Gemini models.
- `OLLAMA_HOST`: Optional, defaults to `http://localhost:11434` when using local Ollama models.
- `HUGGING_FACE_TOKEN`: Required when using Hugging Face models.

Example `.env` file:
```env
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
HUGGING_FACE_TOKEN="YOUR_HF_TOKEN_HERE"
```

## Usage

### Anonymize

The `run` command anonymizes one or more files.

```bash
pdf-anonymizer run FILE_PATH [FILE_PATH ...] \
  [--characters-to-anonymize INTEGER] \
  [--prompt-name {simple|detailed}] \
  [--model-name TEXT] \
  [--anonymized-entities PATH]
```

**Arguments**:
- `FILE_PATH`: Path to one or several PDF, Markdown, or text files for anonymization.

**Options**:
- `--characters-to-anonymize INTEGER`: Number of characters to process in each chunk (default: `100000`).
- `--prompt-name [simple|detailed]`: The prompt template to use (default: `detailed`).
- `--model-name TEXT`: The language model to use.
- `--anonymized-entities PATH`: Path to a file with a list of entities to anonymize.

**Models**:
- **Google**: `gemini-2.5-pro`, `gemini-2.5-flash` (default), `gemini-2.5-flash-lite`.
- **Ollama**: `gemma:7b`, `phi4-mini`.
- **Hugging Face**: `mistralai/Mistral-7B-Instruct-v0.1`, `HuggingFaceH4/zephyr-7b-beta`.

### Examples

**Basic anonymization**:
```bash
pdf-anonymizer run document.pdf
```

**Custom model and prompt**:
```bash
pdf-anonymizer run notes.md --model-name phi4-mini --prompt-name simple
```

### Deanonymize

The `deanonymize` command reverts anonymization using a mapping file.

```bash
pdf-anonymizer deanonymize ANONYMIZED_FILE MAPPING_FILE
```

**Arguments**:
- `ANONYMIZED_FILE`: Path to the anonymized text file.
- `MAPPING_FILE`: Path to the JSON mapping file.

**Example**:
```bash
pdf-anonymizer deanonymize \
    data/anonymized/document.anonymized.md \
    data/mappings/document.mapping.json
```

This will create a deanonymized version of the file at `data/deanonymized/document.deanonymized.md`.