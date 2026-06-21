"""Core anonymization engine.

This module provides the primary high-level entry point for anonymizing
documents (PDF, Markdown, or plain text) using a hybrid Regex + LLM approach
with support for large files via chunking, entity consolidation, and reversible
placeholder mapping.

The first stage (regex) now uses the RE2 engine (google-re2) and ships with
a large library of patterns covering emails, phones, URLs, credit cards,
cryptocurrency addresses, IBANs/BICs, VINs, MACs, IPs, dates, plus
country-specific government IDs, tax IDs, driver licences, national IDs,
VAT/business numbers etc. for 30+ jurisdictions (see conf.DEFAULT_REGEX_PATTERNS
and regex_ner docs for the full partitioned list).
"""

import logging
import os
import re
import time
from typing import Dict, List, Optional, Tuple

from pdf_anonymizer_core.call_llm import identify_entities_with_llm
from pdf_anonymizer_core.conf import DEFAULT_CHUNK_OVERLAP, DEFAULT_REGEX_PATTERNS
from pdf_anonymizer_core.load_and_extract import load_and_extract_text_from_file
from pdf_anonymizer_core.regex_ner import extract_entities_via_regex


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
    """Anonymize a file by processing its text content.

    Performs a two-stage entity detection (fast regex first pass followed by
    LLM-based semantic detection), deduplicates, consolidates base forms for
    coreference (e.g. "Dr. Smith" / "Smith"), generates typed placeholders
    (PERSON_1, ORGANIZATION_3.v_1, ...), and performs length-descending safe
    replacement to produce reversible anonymized output.

    The function streams large inputs via chunking (Markdown-aware for PDF/MD)
    so that very large files (hundreds of MB) can be processed without
    exhausting context windows or memory.

    Args:
        file_path: Path to the file to anonymize (.pdf, .md, or .txt).
        characters_to_anonymize: Target character size of each chunk sent to the LLM.
        prompt_template: The full prompt template string (use one from
            pdf_anonymizer_core.prompts or supply your own).
        model_name: Model identifier or "provider/model" string
            (e.g. "gemini-2.5-flash", "ollama/phi4-mini", "google/gemini-2.0-flash-exp").
        anonymized_entities: Optional whitelist of entity *types* (e.g. ["PERSON", "ORGANIZATION"]).
            When provided, only matching entities are replaced.
        chunk_overlap: Number of characters of overlap between consecutive chunks.
        regex_patterns: Custom first-stage regex map. Defaults to the large built-in
            collection in DEFAULT_REGEX_PATTERNS (see conf.py). The collection covers
            universal PII (email, URLs, credit cards, crypto wallets, IBANs, VIN, MAC,
            IPv4/IPv6, dates) plus country-partitioned national IDs, tax IDs, driver
            licenses, VAT/business numbers, passports etc. for 30+ countries
            (mandatory: US, CA, GB, ES, IT, FR, IN, CN plus DE, JP, BR, AU, NL, ...).
            Keys become entity TYPEs (IPV4_ADDRESS, SSN_US, IBAN, CRYPTO_ETH, ...).
            All patterns are RE2 (google-re2) safe.
        max_retries: Maximum LLM call attempts per chunk (with exponential backoff).
        base_retry_delay: Base delay in seconds for retry backoff.
        max_retry_delay: Maximum delay cap for retry backoff.

    Returns:
        A tuple (anonymized_text, mapping) where:
            - anonymized_text is the masked document (or None on failure)
            - mapping is a dict of original_value -> placeholder (or None on failure)

    Note:
        The returned mapping is in original -> placeholder direction.
        The CLI later converts it to placeholder -> original for deanonymization.
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
            text_page,
            prompt_template,
            model_name,
            max_retries=max_retries,
            base_retry_delay=base_retry_delay,
            max_retry_delay=max_retry_delay,
        )

        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        logging.info(f"   NER stage duration (Regex + LLM): {minutes}:{seconds:02d}")
        logging.info(
            f"   Found {len(regex_entities)} via Regex, {len(llm_entities)} via LLM."
        )

        collected_entities.extend(regex_entities)
        collected_entities.extend(llm_entities)

    # Deduplicate entities by text, prioritizing more specific types if matched multiple times.
    # Higher numbers win. Financial, government ID, crypto, and network identifiers
    # receive elevated priority because they are high-risk and unambiguous.
    type_priority = {
        # Highest sensitivity / unambiguous structured PII (regex-first wins)
        "CREDIT_CARD": 15,
        "IBAN": 14,
        "CRYPTO_BTC": 13,
        "CRYPTO_ETH": 13,
        "EMAIL": 12,
        "SSN": 11,
        "SSN_US": 11,
        "SIN_CA": 11,
        "NINO_GB": 11,
        "INSEE_FR": 11,
        "AADHAAR_IN": 11,
        "RESIDENT_ID_CN": 11,
        "EIN_US": 10,
        "VAT_GB": 10,
        "VAT_FR": 10,
        "VAT_ES": 10,
        "VAT_IT": 10,
        "VAT_DE": 10,
        "PAN_IN": 10,
        "GSTIN_IN": 10,
        "UNIFIED_SOCIAL_CREDIT_CODE_CN": 10,
        "IPV4_ADDRESS": 9,
        "IP_ADDRESS": 9,  # legacy
        "IPV6_ADDRESS": 9,
        "MAC_ADDRESS": 8,
        "VIN": 8,
        "MEDICAL_NPI_US": 8,
        "PASSPORT": 7,
        "US_PASSPORT": 7,
        "GB_PASSPORT": 7,
        "DRIVERS_LICENSE_US": 6,
        "DRIVERS_LICENSE_GB": 6,
        "DRIVERS_LICENSE_FR": 6,
        "DRIVERS_LICENSE_CA": 6,
        "DATE_ISO": 5,
        "CURRENCY_AMOUNT": 5,
        "BIC_SWIFT": 5,
        "PHONE": 4,
        "URL": 4,
        # LLM-detected semantic types (lower than strong regex matches)
        "PERSON": 3,
        "ORGANIZATION": 2,
        "LOCATION": 1,
        "ADDRESS": 1,
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
            e
            for e in deduped_entities
            if e["type"].upper() in anonymized_entities_upper
        ]

    logging.info(
        f"Collected {len(collected_entities)} total entities. "
        f"Deduplicated to {len(deduped_entities)}. "
        f"Processing {len(entities_to_process)} filtered entities."
    )

    # Consolidate base forms to handle variations like "John" vs "John Doe"
    base_forms = {e.get("base_form") for e in entities_to_process if e.get("base_form")}
    sorted_base_forms = sorted(list(base_forms), key=len, reverse=True)
    for entity in entities_to_process:
        base_form = entity.get("base_form")
        if not base_form:
            continue
        for potential_full_form in sorted_base_forms:
            if base_form != potential_full_form and base_form in potential_full_form:
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
            current_variation_count = variation_counters.get(main_placeholder, 0) + 1
            variation_counters[main_placeholder] = current_variation_count
            variation_placeholder = f"{main_placeholder}.v_{current_variation_count}"
            final_mapping[entity_text] = variation_placeholder
        else:
            final_mapping[entity_text] = main_placeholder

    anonymized_text = full_text
    if entities_to_process:
        # Sort entities by length descending to match longer strings first
        entities_to_process.sort(key=lambda e: len(e["text"]), reverse=True)

        # Build selective boundary checks to prevent partial matching (e.g. "John" inside "Johnson")
        def make_boundary_pattern(text: str) -> str:
            prefix = r"\b" if text[0].isalnum() or text[0] == "_" else ""
            suffix = r"\b" if text[-1].isalnum() or text[-1] == "_" else ""
            return f"{prefix}{re.escape(text)}{suffix}"

        pattern = re.compile(
            "|".join(make_boundary_pattern(e["text"]) for e in entities_to_process)
        )
        anonymized_text = pattern.sub(
            lambda m: final_mapping[m.group(0)], anonymized_text
        )

    return anonymized_text, final_mapping
