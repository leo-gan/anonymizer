# 🦉🫥 PDF Anonymizer CLI

A command-line interface for anonymizing PDF, Markdown, and plain text files using LLMs.

## Installation

Install the CLI with your favorite package manager. To use a specific LLM provider, you must install the corresponding extra.

- **Google**: `pip install "pdf-anonymizer-cli[google]"`
- **Ollama**: `pip install "pdf-anonymizer-cli[ollama]"`
- **Hugging Face**: `pip install "pdf-anonymizer-cli[huggingface]"`
- **OpenRouter**: `pip install "pdf-anonymizer-cli[openrouter]"`

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
- `OLLAMA_HOST`: Optional, defaults to `http://localhost:11434` when using Ollama models.

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
- **Google**: `google_gemini_2_5_pro`, `google_gemini_2_5_flash` (default), `google_gemini_2_5_flash_lite`.
- **Ollama**: `ollama_gemma`, `ollama_phi`.
- **Hugging Face**: `huggingface_openai_gpt_oss_20b`, `huggingface_mistral_7b_instruct`, `huggingface_zephyr_7b_beta`.
- **OpenRouter**: `openrouter_gpt_4o`, `openrouter_gemini_pro`.

### Examples

**Basic anonymization with the default model (Google)**:
```bash
pdf-anonymizer run document.pdf
```

**Custom model and prompt (Ollama)**:
```bash
pdf-anonymizer run notes.md --model-name ollama_phi --prompt-name simple
```

**Using an OpenRouter model**:
```bash
pdf-anonymizer run report.pdf --model-name openrouter_gpt_4o
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