# PDF Anonymizer

This application anonymizes large PDF files by splitting them into smaller pieces, converting them to text, and using Google Gemini or a local Ollama model to anonymize the text. It generates an anonymized version of the text and a mapping vocabulary of the original entities to their anonymized replacements.

## How it works

1.  **Splitting and Text Extraction**: The input PDF is split page by page, and the text content of each page is extracted.
2.  **Anonymization with LLMs**: Each page's text is sent to an LLM (Google Gemini or a local Ollama model) with a prompt that instructs it to identify and replace Personally Identifiable Information (PII) like names, locations, etc.
3.  **Consistent Mapping**: A mapping vocabulary is maintained throughout the process. This ensures that the same entity is replaced with the same placeholder (e.g., "John Smith" is always replaced with "PERSON_1").
4.  **Output**: The application generates two files:
    *   `{original_file_name}.anonymized_output.txt`: The full text of the PDF with all PII replaced by placeholders.
    *   `{original_file_name}.mapping.json`: A JSON file containing the one-to-one mapping of the original PII to the anonymized placeholders.

## Installation

1.  **Install `uv`**: This project uses `uv` for package management. You can install it by following the official instructions: [https://astral.sh/docs/uv#installation](https://astral.sh/docs/uv#installation)

2.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd pdf-anonymizer
    ```

3.  **Install dependencies**:
    ```bash
    uv sync
    ```

4.  **Install Ollama (optional)**: If you want to use a local model for anonymization, you need to install Ollama. You can find the installation instructions on the official website: [https://ollama.com/](https://ollama.com/)

5.  **Set up environment variables**: Create a `.env` file inside the `pdf_anonymizer` directory.
    *   If you are using Google Gemini, add your Google API key:
        ```
        GOOGLE_API_KEY="YOUR_API_KEY_HERE"
        ```

## Models

### Google Models:
- the `gemini-2.5-flash` model (default) is recommended
- the `gemini-2.5-flash-lite` model performs well only on small files!

### Ollama models:
Using Ollama models you can run anonymization locally for free.
If you are using Ollama, you need to download the models you want to use. 
You can do this from the command line. For example, to download the `phi` model:

```bash
ollama pull phi
```

You can see a list of available models on the Ollama website.

## Usage

### Basic Commands

1. **Anonymize a PDF**:
   ```bash
   uv run python pdf_anonymizer/main.py run /path/to/your/document.pdf
   ```

2. **Deanonymize a file**:
   ```bash
   uv run python pdf_anonymizer/main.py deanonymize \
       data/anonymized/document.anonymized.md \
       data/mappings/document.mapping.json
   ```

## Command Line Arguments

### `run` command
Anonymize one or more PDF files.

```bash
uv run python pdf_anonymizer/main.py run PDF_FILES [OPTIONS]
```

#### Arguments:
- `PDF_FILES`: Path to one or several PDF files for anonymization.

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
  Default: `gemini-2.5-flash`

### `deanonymize` command
Revert anonymization using a mapping file.

```bash
uv run python pdf_anonymizer/main.py deanonymize ANONYMIZED_FILE MAPPING_FILE
```

#### Arguments:
- `ANONYMIZED_FILE`: Path to the anonymized text file
- `MAPPING_FILE`: Path to the JSON mapping file

## Environment Variables

- `GOOGLE_API_KEY`: Required when using Google's Gemini models
- `OLLAMA_HOST`: Optional, defaults to `http://localhost:11434` when using local Ollama models

## Examples

1. **Basic anonymization**:
   ```bash
   uv run python pdf_anonymizer/main.py run document.pdf
   ```

2. **Custom model and prompt**:
   ```bash
   uv run python pdf_anonymizer/main.py run document.pdf --model-name phi4-mini --prompt-name simple
   ```

3. **Custom character chunk size**:
The models can have different performance with different chunk sizes.

   ```bash
   uv run python pdf_anonymizer/main.py run document.pdf --characters-to-anonymize 50000
   ```

## Anonymization

### Example

**Input Text from a `sample.pdf`:**
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

The tool also supports reversing the anonymization process using the `deanonymize` command. This can be useful if you need to recover the original text from an anonymized document.

### Usage

To deanonymize a file, you'll need both the anonymized text and its corresponding mapping file:

```bash
uv run python pdf_anonymizer/main.py deanonymize data/anonymized/document.anonymized.md data/mappings/document.mapping.json
```

This will create a deanonymized version of the file at `data/deanonymized/document.deanonymized.md`
and a deanonymization statistics file at `data/stats/document.deanonymization_stat.json`.

### Example

**Anonymized Text: `sample.anonymized.md`**
> "PERSON_1, CEO of ORGANIZATION_1, can be reached at EMAIL_1."

**Deanonymized Output: `sample.deanonymized.md`**
> "John Smith, CEO of Acme Corp, can be reached at john.smith@example.com."


## Testing

The project includes a test suite to verify the functionality of the core components. To run the tests, navigate to the `pdf_anonymizer` directory and run:

```bash
uv run python -m unittest discover tests
```
This will discover and run all the tests in the `tests` directory.
