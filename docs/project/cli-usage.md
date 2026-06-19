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
*   `FILE_PATH`: Space-separated list of paths to files (PDF, Markdown, or plain text).

### Options

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--config-profile` / `-p` | `best-quality` \| `best-speed` \| `best-cost` | `best-speed` | Predefined bundle of model, prompt, chunk size, overlap, and retry settings (see below). |
| `--characters-to-anonymize` | `INTEGER` | `100000` | The character size of each chunk sent to the LLM (overrides profile). |
| `--prompt-name` | `simple` \| `detailed` | `detailed` | The type of instruction prompt sent to the LLM (overrides profile). |
| `--model-name` | `TEXT` | `gemini-2.5-flash` | The identifier of the model to execute (overrides profile). |
| `--anonymized-entities` | `PATH` | *None* | Path to a text file containing custom entities to search for and anonymize. |

### Configuration Profiles

The `--config-profile` (or `-p`) flag is the recommended way to select quality/speed/cost trade-offs. It sets a bundle of model, prompt, chunk size, overlap, and retry settings. Any of `--model-name`, `--prompt-name`, or `--characters-to-anonymize` act as **overrides** on top of the chosen profile.

| Profile        | Default Model           | Prompt   | Chunk Size | Overlap | Retries | Best For                          |
|----------------|-------------------------|----------|------------|---------|---------|-----------------------------------|
| `best-quality` | `gemini-2.5-pro`        | detailed | 15,000     | 2,000   | 5       | Highest accuracy (slower/costlier)|
| `best-speed`   | `gemini-2.5-flash`      | simple   | 30,000     | 1,000   | 3       | Balanced (default)                |
| `best-cost`    | `gemini-2.5-flash-lite` | simple   | 60,000     | 3,000   | 3       | Cheap & fast on long documents    |

**Examples**

```bash
# High accuracy on an important contract
pdf-anonymizer run contract.pdf -p best-quality

# Fast + cheap batch of notes with a local model
pdf-anonymizer run notes/*.md -p best-cost --model-name "ollama/phi4-mini"
```

See the [Recipes & Common Workflows](recipes.md) page for more profile usage patterns.

---

## Models & Providers

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

## The `deanonymize` Command (Reversal)

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

## Operational Examples

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

---

## Output Files & Auditing

Both commands write results under conventional directories (created automatically):

*   `data/anonymized/<stem>.anonymized.md` (or `.txt`)
*   `data/mappings/<stem>.mapping.json`
*   `data/deanonymized/<stem>.deanonymized.md` (or `.txt`)
*   `data/stats/<stem>.deanonymization_stat.json`

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
- **[SDK & API Usage](api-usage.md)** — programmatic usage of the same core functions.
- **[API Reference (auto)](api-reference.md)** — auto-generated function signatures.
- **[Architecture Design](architecture.md)** — how chunking, hybrid detection, mapping, and reversal work internally.
- **[Installation & Setup](installation.md)** — provider extras and environment setup.