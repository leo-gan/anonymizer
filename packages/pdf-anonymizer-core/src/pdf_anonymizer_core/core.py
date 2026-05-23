import logging
import os
import time
from typing import Dict, List, Optional, Tuple

from pdf_anonymizer_core.call_llm import identify_entities_with_llm
from pdf_anonymizer_core.load_and_extract import load_and_extract_text_from_file
from pdf_anonymizer_core.regex_ner import extract_entities_via_regex
from pdf_anonymizer_core.conf import DEFAULT_REGEX_PATTERNS, DEFAULT_CHUNK_OVERLAP


def anonymize_file(
    file_path: str,
    characters_to_anonymize: int,
    prompt_template: str,
    model_name: str,
    anonymized_entities: Optional[List[str]] = None,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    regex_patterns: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
    base_retry_delay: float = 1.0,
    max_retry_delay: float = 10.0,
) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    """
    Anonymize a file by processing its text content.

    Args:
        file_path: Path to the file to anonymize.
        characters_to_anonymize: Number of characters to process in each chunk.
        prompt_template: Template string for the anonymization prompt.
        model_name: Name of the language model to use for anonymization.
        anonymized_entities: A list of entities to anonymize.
        chunk_overlap: Number of characters overlapping between chunks.
        regex_patterns: Regular expression patterns for first-stage NER.
        max_retries: Max retries for LLM calls.
        base_retry_delay: Base delay for backoff.
        max_retry_delay: Max delay for backoff.

    Returns:
        A tuple containing the anonymized text and the mapping of original to anonymized entities,
        or (None, None) if processing fails.
    """
    if regex_patterns is None:
        regex_patterns = DEFAULT_REGEX_PATTERNS

    file_size = os.path.getsize(file_path)
    full_text, text_pages = load_and_extract_text_from_file(
        file_path, characters_to_anonymize, chunk_overlap
    )

    if not text_pages:
        logging.warning("No text could be extracted from the file.")
        return None, None

    logging.info(f"Extracted text pages: {text_pages[0][:50]} ...")
    extracted_text_size = len(full_text)

    logging.info(f"  - File size: {file_size / 1024:.2f} KB")
    logging.info(f"  - Extracted text size: {extracted_text_size / 1024:.2f} KB")

    # Accumulate all entities from all chunks
    collected_entities: List[dict] = []

    for i, text_page in enumerate(text_pages):
        logging.info(f"Identifying entities in part {i + 1}/{len(text_pages)}...")
        start_time = time.time()

        # 1st Stage: Regex NER
        regex_entities = extract_entities_via_regex(text_page, regex_patterns)

        # 2nd Stage: LLM NER
        llm_entities = identify_entities_with_llm(
            text_page, prompt_template, model_name,
            max_retries=max_retries,
            base_retry_delay=base_retry_delay,
            max_retry_delay=max_retry_delay
        )

        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        logging.info(f"   NER stage duration (Regex + LLM): {minutes}:{seconds:02d}")
        logging.info(f"   Found {len(regex_entities)} via Regex, {len(llm_entities)} via LLM.")

        collected_entities.extend(regex_entities)
        collected_entities.extend(llm_entities)

    # Deduplicate entities by text, prioritizing more specific types if matched multiple times
    type_priority = {
        "EMAIL": 10,
        "CREDIT_CARD": 9,
        "IP_ADDRESS": 8,
        "SSN": 7,
        "PHONE": 6,
        "PERSON": 5,
        "ORGANIZATION": 4,
        "LOCATION": 3,
        "ADDRESS": 2,
    }
    
    best_entities: Dict[str, dict] = {}
    for ent in collected_entities:
        text = ent["text"]
        ent_type = ent["type"].upper()
        if text not in best_entities:
            best_entities[text] = ent
        else:
            existing_type = best_entities[text]["type"].upper()
            if type_priority.get(ent_type, 0) > type_priority.get(existing_type, 0):
                best_entities[text] = ent
                
    deduped_entities = list(best_entities.values())

    entities_to_process = deduped_entities
    if anonymized_entities:
        anonymized_entities_upper = [e.upper() for e in anonymized_entities]
        entities_to_process = [
            e for e in deduped_entities if e["type"].upper() in anonymized_entities_upper
        ]

    logging.info(
        f"Collected {len(collected_entities)} total entities. "
        f"Deduplicated to {len(deduped_entities)}. "
        f"Processing {len(entities_to_process)} filtered entities."
    )

    # Consolidate base forms to handle variations like "John" vs "John Doe"
    base_forms = {
        e.get("base_form") for e in entities_to_process if e.get("base_form")
    }
    sorted_base_forms = sorted(list(base_forms), key=len, reverse=True)
    for entity in entities_to_process:
        base_form = entity.get("base_form")
        if not base_form:
            continue
        for potential_full_form in sorted_base_forms:
            if (
                base_form != potential_full_form
                and base_form in potential_full_form
            ):
                entity["base_form"] = potential_full_form
                break

    # Generate placeholders
    final_mapping: Dict[str, str] = {}
    placeholder_counts: Dict[str, int] = {}
    base_entity_placeholders: Dict[str, str] = {}
    variation_counters: Dict[str, int] = {}

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
            current_variation_count = (
                variation_counters.get(main_placeholder, 0) + 1
            )
            variation_counters[main_placeholder] = current_variation_count
            variation_placeholder = (
                f"{main_placeholder}.v_{current_variation_count}"
            )
            final_mapping[entity_text] = variation_placeholder
        else:
            final_mapping[entity_text] = main_placeholder

    # Sort entities by length descending to replace longer strings first
    entities_to_process.sort(key=lambda e: len(e["text"]), reverse=True)

    anonymized_text = full_text
    for entity in entities_to_process:
        placeholder = final_mapping.get(entity["text"])
        if placeholder:
            anonymized_text = anonymized_text.replace(entity["text"], placeholder)

    return anonymized_text, final_mapping
