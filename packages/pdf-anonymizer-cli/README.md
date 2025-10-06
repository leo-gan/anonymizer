# 🦉🫥 PDF Anonymizer CLI

A command-line interface for anonymizing PDF, Markdown, and plain text files using LLMs.

- **High-Quality Anonymization**: Leverages LLMs to identify and replace Personally Identifiable Information (PII) with high accuracy.
- **Large File Support**: Consistently anonymizes large files (tested up to 1GB).
- **Multi-Provider & Cost-Effective**: Free to use with local [Ollama](https://ollama.com/) models. It also supports major providers like [OpenAI](https://openai.com/), [Anthropic](https://www.anthropic.com/), [Google](https://ai.google.com/), [Hugging Face](https://huggingface.co/), and [OpenRouter](https://openrouter.ai/).
- **Reversible**: Supports deanonymization to recover original data when needed.
- **Multi-Format**: Works with PDF, Markdown, and plain text files.


## Installation

Install the CLI with your favorite package manager. To use a specific LLM provider, you must install the corresponding extra.

- **Google**: `pip install "pdf-anonymizer-cli[google]"`
- **Ollama**: `pip install "pdf-anonymizer-cli[ollama]"`
- **Hugging Face**: `pip install "pdf-anonymizer-cli[huggingface]"`
- **OpenRouter**: `pip install "pdf-anonymizer-cli[openrouter]"`
- **OpenAI**: `pip install "pdf-anonymizer-cli[openai]"`
- **Anthropic**: `pip install "pdf-anonymizer-cli[anthropic]"`

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
You can use any of the predefined models below, or specify a new model using the format `"provider/model-name"`. 
For example: `--model-name "google/gemini-flash-latest"`.

- **Google**: `gemini-2.5-pro`, `gemini-2.5-flash` (default), `gemini-2.5-flash-lite`.
- **Ollama**: `gemma:7b`, `phi4-mini`.
- **Hugging Face**: `openai/gpt-oss-20b`, `mistralai/Mistral-7B-Instruct-v0.1`, `HuggingFaceH4/zephyr-7b-beta`.
- **OpenRouter**: `openai/gpt-4o`, `google/gemini-pro`.
- **OpenAI**: `gpt-4o`, `gpt-5`.
- **Anthropic**: `claude-4-sonet`, `claude-4.5-sonet`.

### Examples

**Basic anonymization with the default model (Google)**:
```bash
pdf-anonymizer run document.pdf
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