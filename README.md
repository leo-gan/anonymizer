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

Run the application from the command line, providing the path to the PDF file you want to anonymize.

Using `uv`:
```bash
uv run python pdf_anonymizer/main.py /path/to/your/document.pdf
```

You can also specify the model and prompt you want to use:
```bash
uv run python pdf_anonymizer/main.py /path/to/your/document.pdf --model-name phi --prompt-name detailed
```

The output files (`data/anonymized/{original_file_name}.anonymized_output.md` and `data/mappings/{original_file_name}.mapping.json`) will be created in the `/data` directory of the project.

## Example

**Input Text from a `sample.pdf`:**
> "John Smith, CEO of Acme Corp, can be reached at john.smith@example.com."

**Anonymized Output Markdown text: `sample.anonymized_output.md`**
> "PERSON_1, CEO of ORGANIZATION_1, can be reached at EMAIL_1."

**Entity Mapping: `sample.mapping.json`**
```json
{
  "PERSON_1": "John Smith",
  "ORGANIZATION_1": "Acme Corp",
  "EMAIL_1": "john.smith@example.com"
}
```

## Testing

The project includes a test suite to verify the functionality of the core components. To run the tests, navigate to the `pdf_anonymizer` directory and run:

```bash
uv run python -m unittest discover tests
```
This will discover and run all the tests in the `tests` directory.
