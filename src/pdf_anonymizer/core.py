import logging
import os
import time
from typing import Dict, List, Optional, Tuple

from pdf_anonymizer.call_llm import anonymize_text_with_llm
from pdf_anonymizer.exceptions import AnonymizationError
from pdf_anonymizer.load_and_extract_pdf import load_and_extract_text


from pdf_anonymizer.conf import ModelName


def anonymize_pdf(
    pdf_path: str,
    characters_to_anonymize: int,
    prompt_template: str,
    model_name: ModelName,
) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    """
    Anonymize a PDF file by processing its text content.

    Args:
        pdf_path: Path to the PDF file to anonymize.
        characters_to_anonymize: Number of characters to process in each chunk.
        prompt_template: Template string for the anonymization prompt.
        model_name: Name of the language model to use for anonymization.

    Returns:
        A tuple containing the anonymized text and the mapping of original to anonymized entities,
        or (None, None) if processing fails.
    """
    # PDF file: chunk and convert to text
    pdf_file_size = os.path.getsize(pdf_path)
    text_pages: List[str] = load_and_extract_text(pdf_path, characters_to_anonymize)

    if not text_pages:
        logging.warning("No text could be extracted from the PDF.")
        return None, None

    extracted_text_size = sum(len(page) for page in text_pages)

    logging.info(f"  - PDF file size: {pdf_file_size / 1024:.2f} KB")
    logging.info(f"  - Extracted text size: {extracted_text_size / 1024:.2f} KB")

    # Anonymization:
    anonymized_chunks: List[str] = []
    final_mapping: Dict[str, str] = {}

    for i, text_page in enumerate(text_pages):
        logging.info(f"Anonymizing part {i + 1}/{len(text_pages)}...")
        start_time = time.time()

        try:
            anonymized_text, final_mapping = anonymize_text_with_llm(
                text_page, final_mapping, prompt_template, model_name
            )
        except AnonymizationError as e:
            logging.error(
                f"Anonymization failed for {pdf_path} on chunk {i + 1}: {e}"
            )
            return None, None

        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        logging.info(f"   duration: {minutes}:{seconds:02d}")

        anonymized_chunks.append(anonymized_text)

    full_anonymized_text = "\n\n--- Page Break ---\n\n".join(anonymized_chunks)

    return full_anonymized_text, final_mapping
