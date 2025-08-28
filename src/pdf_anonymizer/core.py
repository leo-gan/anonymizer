import logging
import time
import os

from pdf_anonymizer.call_llm import anonymize_text_with_llm
from pdf_anonymizer.load_and_extract_pdf import load_and_extract_text


def anonymize_pdf(pdf_path, characters_to_anonymize, prompt_template, model_name):
    """
    Anonymize a PDF file.
    """
    # PDF file: chunk and convert to text
    pdf_file_size = os.path.getsize(pdf_path)
    text_pages = load_and_extract_text(pdf_path, characters_to_anonymize)

    if not text_pages:
        logging.warning("No text could be extracted from the PDF.")
        return None, None

    extracted_text_size = sum(len(page) for page in text_pages)

    logging.info(f"  - PDF file size: {pdf_file_size / 1024:.2f} KB")
    logging.info(f"  - Extracted text size: {extracted_text_size / 1024:.2f} KB")

    # Anonymization:
    anonymized_chunks = []
    final_mapping = {}

    for i, text_page in enumerate(text_pages):
        logging.info(f"Anonymizing part {i+1}/{len(text_pages)}...")
        start_time = time.time()

        anonymized_text, final_mapping = anonymize_text_with_llm(
            text_page,
            final_mapping,
            prompt_template,
            model_name
        )

        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        logging.info(f"   duration: {minutes}:{seconds:02d}")

        anonymized_chunks.append(anonymized_text)

    full_anonymized_text = "\n\n--- Page Break ---\n\n".join(anonymized_chunks)

    return full_anonymized_text, final_mapping
