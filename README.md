# PDF Anonymizer

This application anonymizes PDF files by finding and redacting Personally Identifiable Information (PII) using Large Language Models (LLMs). It generates a new, anonymized PDF that preserves the original layout, along with a mapping file of the changes.

## How it works

1.  **PDF Parsing**: The application loads the input PDF and processes it page by page.
2.  **Anonymization with LLMs**: For each page, the text is extracted and sent to an LLM (Google Gemini or a local Ollama model) with a prompt that instructs it to identify PII like names, locations, etc.
3.  **Redaction & Replacement**: The original PII on each page is securely redacted and replaced with a placeholder (e.g., "PERSON_1"). This process is done carefully to maintain the document's original formatting.
4.  **Consistent Mapping**: A mapping file is maintained throughout the process to ensure that the same entity is always replaced with the same placeholder.
5.  **Output**: The application generates two files:
    *   `{original_file_name}.anonymized.pdf`: A new PDF file with all PII redacted and replaced by placeholders.
    *   `{original_file_name}.mapping.json`: A JSON file containing the mapping of the original PII to the anonymized placeholders.

## Installation

This project is packaged and can be installed using `pip`.

```bash
pip install .
```
*(Note: Once published to PyPI, this will become `pip install pdf-anonymizer`)*

### Environment Setup

1.  **Install Ollama (optional)**: If you want to use a local model for anonymization, you need to install and run Ollama. You can find the instructions on the official website: [https://ollama.com/](https://ollama.com/)

2.  **Set up environment variables**: Create a `.env` file in the directory where you run the application.
    *   If you are using Google Gemini, add your Google API key:
        ```
        GOOGLE_API_KEY="YOUR_API_KEY_HERE"
        ```

## Privacy and Security

This tool is designed with your privacy in mind.

*   **Local Processing**: Your PDF files are processed entirely on your local machine. They are never uploaded to any server.
*   **API Usage**: The only time data leaves your machine is if you choose to use a model from Google Gemini. In this case, the text content of each page is sent to the Google Gemini API for anonymization. No data is sent when using local Ollama models.
*   **No Logging of PII**: The tool does not log or store any of the sensitive information it finds.

## Usage

For command-line usage, run the application and provide the path to the PDF file you want to anonymize.

```bash
pdf-anonymizer /path/to/your/document.pdf
```

You can also specify the model and prompt you want to use:
```bash
pdf-anonymizer /path/to/your/document.pdf --model-name phi4-mini --prompt-name detailed
```

## Example

**Input PDF page:**
> "John Joe, who lives at 2864, Holm st, Springfild, met Mary Smith yesterday."

**Output Anonymized PDF page:**
> "PERSON_1, who lives at 2864, Holm st, Springfild, met PERSON_2 yesterday."

**`mapping.json`:**
```json
{
    "John Joe": "PERSON_1",
    "Mary Smith": "PERSON_2"
}
```
