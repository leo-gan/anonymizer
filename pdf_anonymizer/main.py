import sys
import json
from pathlib import Path
import google.generativeai as genai
import os
from dotenv import load_dotenv
import argparse
import logging
import time

from pdf_anonymizer.call_gemini import anonymize_text_with_gemini
from pdf_anonymizer.load_and_extract_pdf import load_and_extract_text
from pdf_anonymizer.prompts import detailed, simple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)


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

    parser.add_argument(
        "--prompt_name",
        type=str,
        default="simple",
        help="Can be 'simple' or 'detailed'.",
    )
    args = parser.parse_args()

    pdf_path = args.pdf_path
    logging.info(f"  --pdf_path: {pdf_path}")
    pages_in_group = args.pages_in_group
    logging.info(f"  --pages_in_group: {pages_in_group}")

    prompt_mapping = {"simple": simple.prompt_template, "detailed": detailed.prompt_template}
    prompt_template = prompt_mapping[args.prompt_name]
    logging.info(f"  --prompt_name: {args.prompt_name}")

    # PDF file: chunk and convert to text
    pdf_file_size = os.path.getsize(pdf_path)
    text_pages = load_and_extract_text(pdf_path)

    if not text_pages:
        logging.warning("No text could be extracted from the PDF.")
        return

    extracted_text_size = sum(len(page) for page in text_pages)

    logging.info(f"Starting anonymization for: {pdf_path}")
    logging.info(f"  - PDF file size: {pdf_file_size / 1024:.2f} KB")
    logging.info(f"  - Extracted text size: {extracted_text_size / 1024:.2f} KB")

    # Anonymization:
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
        anonymized_text, final_mapping = anonymize_text_with_gemini(text_chunk, final_mapping, prompt_template)
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
    with open(anonymized_output_file, "w", encoding="utf-8") as f:
        f.write(full_anonymized_text)

    mapping_file = f"{pdf_file_name}.mapping.json"
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(final_mapping, f, indent=4)

    logging.info("Anonymization complete!")
    logging.info(f"Anonymized text saved into '{anonymized_output_file}'")
    logging.info(f"Mapping vocabulary saved into '{mapping_file}'")


if __name__ == "__main__":
    main()
