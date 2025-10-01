# PDF Anonymizer

This application anonymizes large PDF, Markdown or Text files using LLMs.
- LLM anonymizes text with `high quality`.
- It anonymizes `large files consistently`. I've tried 1GB files.
- Anonymizes for `free`, if you use an open-source LLM (It uses hashtag#Ollama underhood for OS LLMs)
- Can do `Deanonymization`. It's helpful when you allow untrusted parties to edit your sensitive documents.
- Anonymizes `PDF`, `Markdown`, and `text` files.


## How it works

1.  **Input**: The input can be a PDF, Markdown or Text file. It can be several files.
2.  **Anonymization with LLMs**: Each text is sent to an LLM (Google Gemini or a local Ollama model) with an instruction
    to identify and replace `Personally Identifiable Information` (`PII`) like names, locations, etc.
3.  **Consistent Mapping**: A mapping vocabulary is maintained throughout the process. This ensures that
    the same entity is replaced with the same placeholder (e.g., "John Smith" is always replaced with "PERSON_1").
4.  **Large files**: Large files are split into smaller chunks to be anonymized.
4.  **Output**: The application generates two files:
    *   `data/anonymized/{original_file_name}.anonymized.{md,txt}`: The anonymized text with all PII replaced by placeholders. For PDF inputs, the output is a Markdown file. For other file types, the original extension is preserved.
    *   `data/mappings/{original_file_name}.mapping.json`: A JSON file containing the one-to-one mapping of the original PII to the anonymized placeholders.

### Design Considerations

- LLMs can anonymize text with very good quality, much better than other tools, like Grammar rule engines.
- LLM can anonymize text directly from the PDF. But LLM can't edit the PDF file directly.
  So, the Anonymizer saves the anonymized text only as a text.
- Anonymized text and mapping are stored separately in different directories because of **security** reasons.
- The anonymized file name compounded as the original file name and with `.anonymized` suffix and the mapping file name with `.mapping` suffix for easy identification and security reasons.
- The anonymized text is stored in Markdown format so it saves the document structure information.
- **Large files** are split into smaller chunks to be anonymized since LLMs can't handle large texts in one go.
- **Mapping** is needed to make anonymization consistent between anonymized text chunks. Mapping also used to deanonymize the text.

## Installation

1.  **Install `uv`**: This project uses `uv` for package management. Follow the [official installation instructions](https://astral.sh/docs/uv#installation).

2.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd pdf-anonymizer
    ```

3.  **Install dependencies**:
    ```bash
    uv sync
    ```

4.  **Install Ollama (optional)**: If you want to use a local model for anonymization, install Ollama. Follow the [official installation instructions](https://ollama.com/)

5.  **Set up environment variables**: Create a `.env` file inside the `pdf_anonymizer` directory. Use the `.env.template` as a template.
    *   If you are using Google Gemini, add your Google API key:
        ```
        GOOGLE_API_KEY="YOUR_API_KEY_HERE"
        ```

## Environment Variables

- `GOOGLE_API_KEY`: Required when using Google's Gemini models
- `OLLAMA_HOST`: Optional, defaults to `http://localhost:11434` when using local Ollama models

## Models

### Google Models:
- the `gemini-2.5-flash` model (default) is recommended
- the `gemini-2.5-flash-lite` model performs well only on small files!

### Ollama models:
Using Ollama models you perform anonymization locally for free.
See a [list of available models](https://ollama.com/search).
If you are using Ollama, you need to download the models you want to use.
You can do this from the command line. For example, to download the `phi` model:

```bash
ollama pull phi
```


## Anonymization

### Usage

```bash
pdf-anonymizer --help
```

2. **Deanonymize a file**:
```bash
pdf-anonymizer deanonymize \
    data/anonymized/document.anonymized.md \
    data/mappings/document.mapping.json
```

### `run` command
Anonymize one or more files.

```bash
pdf-anonymizer run FILE_PATH [FILE_PATH ...] \
  [--characters-to-anonymize INTEGER] \
  [--prompt-name {simple|detailed}] \
  [--model-name TEXT] \
  [--anonymized-entities PATH]
```

#### Arguments:
- `FILE_PATH`: Path to one or several PDF, Markdown, or text files for anonymization.

#### Options:
- `--characters-to-anonymize INTEGER`
  Number of characters to send to the model for anonymization in one go.
  Default: `100000`

- `--prompt-name [simple|detailed]`
  The prompt template to use for anonymization.
  Choices: `simple`, `detailed`
  Default: `detailed`

- `--model-name TEXT`
  The language model to use for anonymization.
  Available models:
  - Google models (require GOOGLE_API_KEY):
    - `gemini-2.5-pro`
    - `gemini-2.5-flash` (default)
    - `gemini-2.5-flash-lite`
  - Local Ollama models:
    - `gemma:7b`
    - `phi4-mini`

### Examples

1. **Basic anonymization**:
```bash
pdf-anonymizer run document.pdf
```

2. **Custom model and prompt**:
```bash
pdf-anonymizer run notes.md --model-name phi4-mini --prompt-name simple
```

3. **Custom character chunk size**:
Models have a specific limit on the number of characters/tokens they can process in one go.
You can find this limit in the model's documentation.
The models can have different performance with different chunk sizes.

```bash
pdf-anonymizer run document.txt --characters-to-anonymize 50000
```

### Anonymization results

**Input Text: `sample.pdf`:**
> "John Smith, CEO of Acme Corp, can be reached at john.smith@example.com."

**Anonymized Output Markdown text: `sample.anonymized.md`**
> "PERSON_1, CEO of ORGANIZATION_1, can be reached at EMAIL_1."

**Entity Mapping: `sample.mapping.json`**
```json
{
  "PERSON_1": "John Smith",
  "ORGANIZATION_1": "Acme Corp",
  "EMAIL_1": "john.smith@example.com"
}
```

## Deanonymization

**Anonymizer** supports reversing the anonymization process using the `deanonymize` command. This can be useful if you need to recover the original text from an anonymized document.

### Usage

To deanonymize a file, you'll need both the anonymized text and its corresponding mapping file:

```bash
pdf-anonymizer deanonymize data/anonymized/document.anonymized.md data/mappings/document.mapping.json
```

This will create a deanonymized version of the file at `data/deanonymized/document.deanonymized.md`
and a deanonymization statistics file at `data/stats/document.deanonymization_stat.json`.

### `deanonymize` command
Revert anonymization using a mapping file.

```bash
pdf-anonymizer deanonymize ANONYMIZED_FILE MAPPING_FILE
```

#### Arguments:
- `ANONYMIZED_FILE`: Path to the anonymized text file
- `MAPPING_FILE`: Path to the JSON mapping file

### Deanonymization results

**Anonymized Text: `sample.anonymized.md`**
> "PERSON_1, CEO of ORGANIZATION_1, can be reached at EMAIL_1."

**Deanonymized Output: `sample.deanonymized.md`**
> "John Smith, CEO of Acme Corp, can be reached at john.smith@example.com."


## Testing

The project includes a test suite to verify the functionality of the core components.

```bash
uv run pytest
```
This will discover and run all the tests in the `tests` directory.