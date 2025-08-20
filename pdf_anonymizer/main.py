import sys
import json
from pathlib import Path
from PyPDF2 import PdfReader
import google.generativeai as genai
import os
from dotenv import load_dotenv
import argparse

def load_and_extract_text(pdf_path):
    """
    Loads a PDF file and extracts text from each page.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        list: A list of strings, where each string is the text of a page.
    """
    try:
        reader = PdfReader(pdf_path)
        text_pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_pages.append(text)
        return text_pages
    except FileNotFoundError:
        print(f"Error: The file at {pdf_path} was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
        sys.exit(1)


def anonymize_text_with_gemini(text, existing_mapping):
    """
    Anonymizes a text chunk using Google Gemini and updates the mapping.

    Args:
        text (str): The text to anonymize.
        existing_mapping (dict): The existing mapping of original to anonymized entities.

    Returns:
        tuple: A tuple containing the anonymized text and the updated mapping.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    You are an expert in text anonymization. Your task is to identify and replace Personally Identifiable Information (PII) in the given text.
    PII includes names, locations, organizations, phone numbers, email addresses, etc.

    Instructions:
    1.  Read the text and the provided JSON mapping of existing anonymized entities.
    2.  Identify all PII in the text.
    3.  If a PII entity is already in the mapping, replace it with its existing anonymized value.
    4.  If a new PII entity is found, create a new anonymized placeholder for it (e.g., PERSON_1, LOCATION_1). The number should be incremented for each new entity of the same type.
    5.  Update the mapping with any new entities you find.
    6.  Return a single JSON object with two keys:
        - "anonymized_text": The text with all PII replaced by placeholders.
        - "mapping": The complete and updated JSON mapping.

    Existing mapping:
    {json.dumps(existing_mapping)}

    Text to anonymize:
    ---
    {text}
    ---

    Respond with ONLY the JSON object.
    """

    try:
        response = model.generate_content(prompt)
        # It's better to clean the response from markdown code block markers
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
        result = json.loads(cleaned_response)
        return result.get("anonymized_text", ""), result.get("mapping", {})
    except Exception as e:
        print(f"An error occurred during anonymization: {e}")
        # In case of error, return the original text and existing mapping
        return text, existing_mapping

def main():
    """
    Main function to run the PDF anonymization process.
    """
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found. Please set it in the .env file.")
        sys.exit(1)

    genai.configure(api_key=api_key)

    parser = argparse.ArgumentParser(description="Anonymize a PDF file.")
    parser.add_argument("pdf_path", help="The path to the PDF file to anonymize.")
    args = parser.parse_args()

    pdf_path = args.pdf_path
    text_pages = load_and_extract_text(pdf_path)

    if not text_pages:
        print("No text could be extracted from the PDF.")
        return

    anonymized_pages = []
    final_mapping = {}

    for i, page_text in enumerate(text_pages):
        print(f"Anonymizing page {i+1}/{len(text_pages)}...")
        anonymized_text, final_mapping = anonymize_text_with_gemini(page_text, final_mapping)
        anonymized_pages.append(anonymized_text)

    # Save the results
    full_anonymized_text = "\n\n--- Page Break ---\n\n".join(anonymized_pages)

    pdf_file_name = Path(pdf_path).stem
    anonymized_output_file = f"{pdf_file_name}.anonymized_output.txt"
    with open(anonymized_output_file, "w") as f:
        f.write(full_anonymized_text)

    mapping_file = f"{pdf_file_name}.sample.2506.16406v1.mapping.json"
    with open(mapping_file, "w") as f:
        json.dump(final_mapping, f, indent=4)

    print("\nAnonymization complete!")
    print(f"Anonymized text saved to '{anonymized_output_file}'")
    print(f"Mapping vocabulary saved to '{mapping_file}'")


if __name__ == "__main__":
    main()
