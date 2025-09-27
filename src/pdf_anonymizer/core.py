import logging
import os
import time
from typing import Dict, List, Optional, Tuple

from pdf_anonymizer.call_llm import Entity, identify_entities_with_llm
from pdf_anonymizer.load_and_extract_pdf import load_and_extract_text


def anonymize_pdf(
    pdf_path: str,
    characters_to_anonymize: int,
    prompt_template: str,
    model_name: str,
    anonymized_entities: Optional[List[str]] = None,
) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    """
    Anonymize a PDF file by processing its text content.

    Args:
        pdf_path: Path to the PDF file to anonymize.
        characters_to_anonymize: Number of characters to process in each chunk.
        prompt_template: Template string for the anonymization prompt.
        model_name: Name of the language model to use for anonymization.
        anonymized_entities: A list of entities to anonymize.

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

    logging.info(f"Extracted text pages: {text_pages}")
    extracted_text_size = sum(len(page) for page in text_pages)

    logging.info(f"  - PDF file size: {pdf_file_size / 1024:.2f} KB")
    logging.info(f"  - Extracted text size: {extracted_text_size / 1024:.2f} KB")

    # Anonymization:
    anonymized_chunks: List[str] = []
    final_mapping: Dict[str, str] = {}
    placeholder_counts: Dict[str, int] = {}
    base_entity_placeholders: Dict[str, str] = {}
    variation_counters: Dict[str, int] = {}

    for i, text_page in enumerate(text_pages):
        logging.info(f"Identifying entities in part {i + 1}/{len(text_pages)}...")
        start_time = time.time()

        all_entities = identify_entities_with_llm(
            text_page, prompt_template, model_name
        )

        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        logging.info(f"   LLM call duration: {minutes}:{seconds:02d}")

        entities_to_process = all_entities
        if anonymized_entities:
            entities_to_process = [
                e for e in all_entities if e["type"] in anonymized_entities
            ]

        logging.info(
            f"Found {len(all_entities)} total entities. "
            f"Processing {len(entities_to_process)} entities."
        )

        # Consolidate base forms to handle variations like "John" vs "John Doe"
        base_forms = {e.get("base_form") for e in entities_to_process if e.get("base_form")}
        for entity in entities_to_process:
            base_form = entity.get("base_form")
            if not base_form:
                continue
            for potential_full_form in base_forms:
                if base_form != potential_full_form and base_form in potential_full_form:
                    entity["base_form"] = potential_full_form
                    break

        # Generate placeholders for all entities that need to be processed
        for entity in entities_to_process:
            entity_text = entity["text"]
            entity_type = entity["type"].upper()
            base_form = entity.get("base_form") or entity_text

            if entity_text in final_mapping:
                continue

            if base_form not in base_entity_placeholders:
                # New base entity, create main placeholder
                current_count = placeholder_counts.get(entity_type, 0) + 1
                placeholder_counts[entity_type] = current_count
                main_placeholder = f"{entity_type}_{current_count}"
                base_entity_placeholders[base_form] = main_placeholder
                if base_form not in final_mapping:
                    final_mapping[base_form] = main_placeholder

            main_placeholder = base_entity_placeholders[base_form]

            if entity_text != base_form:
                # It's a variation, create variation placeholder
                current_variation_count = variation_counters.get(main_placeholder, 0) + 1
                variation_counters[main_placeholder] = current_variation_count
                variation_placeholder = f"{main_placeholder}.v_{current_variation_count}"
                final_mapping[entity_text] = variation_placeholder
            else:
                final_mapping[entity_text] = main_placeholder

        # Sort entities by length descending to replace longer strings first
        entities_to_process.sort(key=lambda e: len(e["text"]), reverse=True)

        anonymized_text = text_page
        for entity in entities_to_process:
            placeholder = final_mapping.get(entity["text"])
            if placeholder:
                anonymized_text = anonymized_text.replace(entity["text"], placeholder)

        anonymized_chunks.append(anonymized_text)

    full_anonymized_text = "\n\n--- Page Break ---\n\n".join(anonymized_chunks)

    return full_anonymized_text, final_mapping
