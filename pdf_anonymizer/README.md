# PDF Anonymizer

This application anonymizes large PDF files by splitting them into smaller pieces, converting them to text, and using Google Gemini to anonymize the text. It generates an anonymized version of the text and a mapping vocabulary of the original entities to their anonymized replacements.

## How it works

1.  **Splitting and Text Extraction**: The input PDF is split page by page, and the text content of each page is extracted.
2.  **Anonymization with Google Gemini**: Each page's text is sent to the Google Gemini API with a prompt that instructs it to identify and replace Personally Identifiable Information (PII) like names, locations, etc.
3.  **Consistent Mapping**: A mapping vocabulary is maintained throughout the process. This ensures that the same entity is replaced with the same placeholder (e.g., "John Smith" is always replaced with "PERSON_1").
4.  **Output**: The application generates two files:
    *   `anonymized_output.txt`: The full text of the PDF with all PII replaced by placeholders.
    *   `mapping.json`: A JSON file containing the one-to-one mapping of the original PII to the anonymized placeholders.

## Installation

1.  Clone the repository or download the source code.
2.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
3.  Create a `.env` file inside the `pdf_anonymizer` directory and add your Google API key:
    ```
    GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```

## Usage

Run the application from the command line, providing the path to the PDF file you want to anonymize:

```bash
python pdf_anonymizer/main.py /path/to/your/document.pdf
```

The output files (`anonymized_output.txt` and `mapping.json`) will be created in the root directory of the project.

## Example

**Input Text (from a PDF page):**
> "John Smith, CEO of Acme Corp, can be reached at john.smith@example.com."

**`anonymized_output.txt`:**
> "PERSON_1, CEO of ORGANIZATION_1, can be reached at EMAIL_1."

**`mapping.json`:**
```json
{
    "John Smith": "PERSON_1",
    "Acme Corp": "ORGANIZATION_1",
    "john.smith@example.com": "EMAIL_1"
}
```

## Testing

The project includes a test suite to verify the functionality of the core components. To run the tests, navigate to the `pdf_anonymizer` directory and run:

```bash
python -m unittest discover tests
```
This will discover and run all the tests in the `tests` directory.
