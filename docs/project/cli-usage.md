# CLI Usage & Command Reference

The `pdf-anonymizer-cli` package installs the `pdf-anonymizer` executable. This guide details command syntax, options, and usage examples.

---

## 1. The `run` Command (Anonymization)

The `run` command processes one or more files, masks PII, and outputs the anonymized document along with a mapping file.

### Syntax
```bash
pdf-anonymizer run FILE_PATH [FILE_PATH ...] [OPTIONS]
```

### Arguments
*   `FILE_PATH`: Space-separated list of paths to files (PDF, Markdown, or plain text).

### Options

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--characters-to-anonymize` | `INTEGER` | `100000` | The character size of each chunk sent to the LLM. |
| `--prompt-name` | `simple` \| `detailed` | `detailed` | The type of instruction prompt sent to the LLM. |
| `--model-name` | `TEXT` | `gemini-2.5-flash` | The identifier of the model to execute. |
| `--anonymized-entities` | `PATH` | *None* | Path to a text file containing custom entities to search for and anonymize. |

---

## 2. Models & Providers

You can select a model via the `--model-name` option. PDF Anonymizer can use pre-configured alias strings or dynamically resolve model paths using the format `provider/model-identifier`.

### Model Aliases

#### :simple-google: Google (Gemini)
*   `gemini-2.5-pro`
*   `gemini-2.5-flash` (Default)
*   `gemini-2.5-flash-lite`

#### :material-dns: Ollama (Local)
*   `gemma:7b`
*   `phi4-mini`

#### :simple-huggingface: Hugging Face
*   `openai/gpt-oss-20b`
*   `mistralai/Mistral-7B-Instruct-v0.1`
*   `HuggingFaceH4/zephyr-7b-beta`

#### :simple-openai: OpenAI
*   `gpt-4o`
*   `gpt-5`

#### :simple-anthropic: Anthropic (Claude)
*   `claude-4-sonet`
*   `claude-4.5-sonet`

#### :material-cloud-sync: OpenRouter
*   `openai/gpt-4o`
*   `google/gemini-pro`

### Dynamic Resolution Syntax
To use any model not listed in the aliases, pass the string as `provider/model-name`. E.g.:
```bash
pdf-anonymizer run doc.pdf --model-name "google/gemini-2.0-flash-exp"
```

---

## 3. The `deanonymize` Command (Reversal)

The `deanonymize` command reads an anonymized document, loads the JSON mapping file containing placeholders and original PII, restores the original text, and writes the output file.

### Syntax
```bash
pdf-anonymizer deanonymize ANONYMIZED_FILE MAPPING_FILE
```

### Arguments
*   `ANONYMIZED_FILE`: Path to the file that was previously anonymized.
*   `MAPPING_FILE`: Path to the JSON mapping file containing the original entity-to-placeholder pairings.

### Output Destination
This command creates a deanonymized version of the file. For example:
If `ANONYMIZED_FILE` is `data/anonymized/document.anonymized.md`, the output will be saved under `data/deanonymized/document.deanonymized.md`.

---

## 4. Operational Examples

### Example 1: Basic Anonymization
Anonymize a meeting transcript using the default Gemini model:
```bash
pdf-anonymizer run data/meeting_transcript.pdf
```
*   **Outputs created**:
    *   `data/meeting_transcript.anonymized.md` (the masked document)
    *   `data/meeting_transcript.mapping.json` (the cryptographic key map)

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
  data/meeting_transcript.anonymized.md \
  data/meeting_transcript.mapping.json
```
*   **Output created**:
    *   `data/meeting_transcript.deanonymized.md`
