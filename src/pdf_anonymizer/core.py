import logging
import time
from pathlib import Path

from pdf_anonymizer.call_llm import anonymize_text_with_llm
from pdf_anonymizer.load_and_extract_pdf import load_pdf


def anonymize_pdf(pdf_path: Path, prompt_template: str, model_name: str):
    """
    Anonymizes a PDF file by redacting PII and replacing it with placeholders.

    Args:
        pdf_path (Path): The path to the PDF file.
        prompt_template (str): The prompt template to use for anonymization.
        model_name (str): The name of the model to use for anonymization.

    Returns:
        A tuple containing the path to the anonymized PDF and the final mapping,
        or (None, None) if an error occurs.
    """
    doc = load_pdf(str(pdf_path))
    if not doc:
        return None, None

    final_mapping = {}
    total_redactions = 0

    logging.info(f"Starting PDF-to-PDF anonymization for: {pdf_path.name}")

    for i, page in enumerate(doc.pages()):
        logging.info(f"Anonymizing page {i+1}/{len(doc)}...")
        start_time = time.time()

        text_to_anonymize = page.get_text()
        if not text_to_anonymize.strip():
            logging.info(f"  - Page {i+1} is empty or has no text. Skipping.")
            continue

        # Store the state of the mapping before the LLM call
        mapping_before = final_mapping.copy()

        # Call the LLM to get anonymized text and updated mapping
        _, final_mapping = anonymize_text_with_llm(
            text_to_anonymize,
            final_mapping,
            prompt_template,
            model_name
        )

        # Identify the newly added PII from this page
        newly_found_pii = {
            k: v for k, v in final_mapping.items() if k not in mapping_before
        }

        if not newly_found_pii:
            logging.info(f"  - No new PII found on page {i+1}.")
            continue

        logging.info(f"  - Found {len(newly_found_pii)} PII elements to redact on page {i+1}.")

        # Redact each piece of PII found on the page
        for pii_text, anonymized_value in newly_found_pii.items():
            text_instances = page.search_for(pii_text)
            for inst in text_instances:
                # Add a redaction annotation. The `text` parameter replaces the
                # content with the anonymized value.
                page.add_redact_annot(inst, text=anonymized_value, fill=(1, 1, 1))
                total_redactions += 1

        # Apply all redactions for the current page
        page.apply_redactions()

        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        logging.info(f"   duration: {minutes}:{seconds:02d}")

    if total_redactions > 0:
        # Save the modified document
        output_path = pdf_path.parent / f"{pdf_path.stem}.anonymized.pdf"
        # garbage=4, deflate=True, clean=True are for optimization
        doc.save(str(output_path), garbage=4, deflate=True, clean=True)
        logging.info(f"Successfully created anonymized PDF: {output_path}")
        return output_path, final_mapping
    else:
        logging.warning("No PII was found to redact in the entire document.")
        return None, final_mapping
