import sys
import json
from pathlib import Path
from PyPDF2 import PdfReader
import google.generativeai as genai
import os
from dotenv import load_dotenv
import argparse
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)


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
        logging.error(f"Error: The file at {pdf_path} was not found.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred while reading the PDF: {e}")
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
        logging.error(f"An error occurred during anonymization: {e}")
        # In case of error, return the original text and existing mapping
        return text, existing_mapping

def main():
    """
    Main function to run the PDF anonymization process.
    """
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logging.error("Error: GOOGLE_API_KEY not found. Please set it in the .env file.")
        sys.exit(1)

    genai.configure(api_key=api_key)

    parser = argparse.ArgumentParser(description="Anonymize a PDF file.")
    parser.add_argument("pdf_path", help="The path to the PDF file to anonymize.")
    parser.add_argument(
        "--pages_in_group",
        type=int,
        default=100,
        help="Number of pages to group together for anonymization.",
    )
    args = parser.parse_args()

    pdf_path = args.pdf_path
    pages_in_group = args.pages_in_group

    pdf_file_size = os.path.getsize(pdf_path)
    text_pages = load_and_extract_text(pdf_path)

    if not text_pages:
        logging.warning("No text could be extracted from the PDF.")
        return

    extracted_text_size = sum(len(page) for page in text_pages)

    logging.info(f"Starting anonymization for: {pdf_path}")
    logging.info(f"  - PDF file size: {pdf_file_size / 1024:.2f} KB")
    logging.info(f"  - Extracted text size: {extracted_text_size / 1024:.2f} KB")

    anonymized_chunks = []
    final_mapping = {}
    num_pages = len(text_pages)

    for i in range(0, num_pages, pages_in_group):
        start_page = i + 1
        end_page = min(i + pages_in_group, num_pages)
        logging.info(f"Anonymizing pages {start_page}-{end_page}/{num_pages}...")

        page_group = text_pages[i:end_page]
        # The separator is added here to delineate pages within a chunk for the LLM.
        text_chunk = "\n\n--- Page Break ---\n\n".join(page_group)

        start_time = time.time()
        anonymized_text, final_mapping = anonymize_text_with_gemini(text_chunk, final_mapping)
        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        logging.info(f"   duration: {minutes}:{seconds:02d}")

        anonymized_chunks.append(anonymized_text)

    # Save the results
    # Each chunk is already a block of text. We join these blocks.
    # The separator used here will now separate the processed chunks.
    full_anonymized_text = "\n\n--- Page Break ---\n\n".join(anonymized_chunks)

    pdf_file_name = Path(pdf_path).stem
    anonymized_output_file = f"{pdf_file_name}.anonymized_output.txt"
    with open(anonymized_output_file, "w") as f:
        f.write(full_anonymized_text)

    mapping_file = f"{pdf_file_name}.mapping.json"
    with open(mapping_file, "w") as f:
        json.dump(final_mapping, f, indent=4)

    logging.info("Anonymization complete!")
    logging.info(f"Anonymized text saved into '{anonymized_output_file}'")
    logging.info(f"Mapping vocabulary saved into '{mapping_file}'")


if __name__ == "__main__":
    main()
