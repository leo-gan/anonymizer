"""Core anonymization engine.

This module provides the primary high-level entry point for anonymizing
documents (PDF, Markdown, plain text, CSV, Excel, or Word) using a hybrid
Regex + LLM approach
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
import time
from typing import Dict, Iterable, List, Optional, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter

from pdf_anonymizer_core.call_llm import identify_entities_with_llm
from pdf_anonymizer_core.conf import DEFAULT_CHUNK_OVERLAP, DEFAULT_REGEX_PATTERNS
from pdf_anonymizer_core.load_and_extract import load_and_extract_text_from_file
from pdf_anonymizer_core.gazetteers import apply_deny_list, apply_keep_list
from pdf_anonymizer_core.operators import apply_operator, operator_for_type
from pdf_anonymizer_core.regex_ner import extract_entities_via_regex
from pdf_anonymizer_core.span_ner import extract_entities_via_ner
from pdf_anonymizer_core.spans import locate_spans, replace_entities
from pdf_anonymizer_core.tables import (
    REGEX_CELL_KINDS,
    TableCell,
    TableDocument,
    TableSheet,
    apply_mapping_to_table,
    column_letter,
    flatten_table_for_review,
    header_labels,
    is_rejected_spreadsheet,
    is_tabular_path,
    iter_cells,
    load_table,
    rejected_spreadsheet_error,
)
from pdf_anonymizer_core.word import (
    apply_mapping_to_docx,
    flatten_docx_for_review,
    is_rejected_word,
    is_word_path,
    load_docx,
    rejected_word_error,
)
from pdf_anonymizer_core.utils import seed_placeholder_state
from pdf_anonymizer_core.validators import LIKE_SUFFIX, parent_type, type_matches_filter

_TYPE_PRIORITY = {
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
    "IP_ADDRESS": 9,
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
    "INDIRECT": 4,
    "PERSON": 3,
    "ORGANIZATION": 2,
    "LOCATION": 1,
    "ADDRESS": 1,
    "CUSTOM": 3,
}


def _type_priority(ent_type: str) -> int:
    upper = ent_type.upper()
    if upper.endswith(LIKE_SUFFIX):
        return _TYPE_PRIORITY.get(parent_type(upper), 0) - 1
    return _TYPE_PRIORITY.get(upper, 0)


def collect_entities_from_chunks(
    chunks: List[str],
    *,
    prompt_template: str,
    model_name: str,
    regex_patterns: Dict[str, str],
    max_retries: int,
    base_retry_delay: float,
    max_retry_delay: float,
    use_llm: bool,
    use_ner: bool = False,
) -> List[dict]:
    """Per chunk: regex, optional local span NER, optional LLM."""
    collected_entities: List[dict] = []

    if not use_llm and not use_ner:
        logging.info(
            "Regex-only / offline mode: skipping the language model. "
            "Names and identity clues will be missed."
        )
    elif use_ner and not use_llm:
        logging.info(
            "Local span NER: skipping the language model. "
            "Identity clues will be missed."
        )

    for i, text_page in enumerate(chunks):
        logging.info(f"Identifying entities in part {i + 1}/{len(chunks)}...")
        start_time = time.time()

        regex_entities = extract_entities_via_regex(text_page, regex_patterns)

        ner_entities: List[dict] = []
        if use_ner:
            ner_entities = extract_entities_via_ner(text_page)

        if use_llm:
            llm_entities = identify_entities_with_llm(
                text_page,
                prompt_template,
                model_name,
                max_retries=max_retries,
                base_retry_delay=base_retry_delay,
                max_retry_delay=max_retry_delay,
            )
        else:
            llm_entities = []

        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        if use_llm and use_ner:
            stage = "Regex + NER + LLM"
        elif use_llm:
            stage = "Regex + LLM"
        elif use_ner:
            stage = "Regex + NER"
        else:
            stage = "Regex only"
        logging.info(f"   NER stage duration ({stage}): {minutes}:{seconds:02d}")
        logging.info(
            f"   Found {len(regex_entities)} via Regex, "
            f"{len(ner_entities)} via NER, {len(llm_entities)} via LLM."
        )

        collected_entities.extend(regex_entities)
        collected_entities.extend(ner_entities)
        collected_entities.extend(llm_entities)

    return collected_entities


def finalize_entities(
    collected: List[dict],
    full_text: str,
    *,
    anonymized_entities: Optional[List[str]],
    keep_list: Optional[List[str]],
    deny_list: Optional[List[str]],
    apply_deny: bool = True,
    seed_mapping: Optional[Dict[str, str]] = None,
    min_confidence: float = 0.0,
) -> List[dict]:
    """Type-priority dedup, type filter, optional deny-list, keep-list, base-form merge."""
    best_entities: Dict[str, dict] = {}
    for ent in collected:
        text = ent["text"]
        ent_type = ent["type"].upper()
        ent.setdefault("score", 1.0)
        ent.setdefault("source", "regex")
        if text not in best_entities:
            best_entities[text] = ent
        else:
            existing = best_entities[text]
            existing_type = existing["type"].upper()
            if _type_priority(ent_type) > _type_priority(existing_type):
                best_entities[text] = ent
            elif _type_priority(ent_type) == _type_priority(existing_type):
                if float(ent.get("score", 1.0)) > float(existing.get("score", 1.0)):
                    best_entities[text] = ent

    deduped_entities = list(best_entities.values())

    entities_to_process = deduped_entities
    if anonymized_entities:
        entities_to_process = [
            e
            for e in deduped_entities
            if type_matches_filter(e["type"], anonymized_entities)
        ]

    # Filter before the deny-list so a required phrase is re-added at
    # score 1.0 even if regex only found a weak TYPE_LIKE hit.
    if min_confidence > 0:
        entities_to_process = [
            entity
            for entity in entities_to_process
            if float(entity.get("score", 1.0)) >= min_confidence
        ]
    if apply_deny and deny_list:
        entities_to_process = apply_deny_list(full_text, entities_to_process, deny_list)
    if keep_list:
        entities_to_process = apply_keep_list(entities_to_process, keep_list)

    logging.info(
        f"Collected {len(collected)} total entities. "
        f"Deduplicated to {len(deduped_entities)}. "
        f"Processing {len(entities_to_process)} filtered entities."
    )

    base_forms = {e.get("base_form") for e in entities_to_process if e.get("base_form")}
    if seed_mapping:
        base_forms.update(seed_mapping.keys())
    sorted_base_forms = sorted(list(base_forms), key=len, reverse=True)
    for entity in entities_to_process:
        base_form = entity.get("base_form")
        if not base_form:
            continue
        for potential_full_form in sorted_base_forms:
            if base_form != potential_full_form and base_form in potential_full_form:
                entity["base_form"] = potential_full_form
                break

    return entities_to_process


def build_mapping(
    entities: List[dict],
    *,
    seed_mapping: Optional[Dict[str, str]],
    operators: Optional[Dict[str, str]],
    fake_secret: Optional[str],
    encrypt_secret: Optional[str] = None,
) -> Dict[str, str]:
    """seed_placeholder_state, PERSON_n / .v_n, apply_operator."""
    if seed_mapping:
        (
            final_mapping,
            base_entity_placeholders,
            placeholder_counts,
            variation_counters,
        ) = seed_placeholder_state(seed_mapping)
    else:
        final_mapping = {}
        placeholder_counts = {}
        base_entity_placeholders = {}
        variation_counters = {}

    for entity in entities:
        entity_text = entity["text"]
        entity_type = entity["type"].upper()
        base_form = entity.get("base_form") or entity_text

        if entity_text in final_mapping:
            continue

        if base_form not in base_entity_placeholders:
            current_count = placeholder_counts.get(entity_type, 0) + 1
            placeholder_counts[entity_type] = current_count
            main_placeholder = f"{entity_type}_{current_count}"
            base_entity_placeholders[base_form] = main_placeholder
            if base_form not in final_mapping:
                final_mapping[base_form] = main_placeholder

        main_placeholder = base_entity_placeholders[base_form]

        if entity_text != base_form:
            current_variation_count = variation_counters.get(main_placeholder, 0) + 1
            variation_counters[main_placeholder] = current_variation_count
            variation_placeholder = f"{main_placeholder}.v_{current_variation_count}"
            final_mapping[entity_text] = variation_placeholder
        else:
            final_mapping[entity_text] = main_placeholder

    if operators:
        text_to_type: Dict[str, str] = {}
        text_to_base: Dict[str, str] = {}
        for entity in entities:
            entity_text = entity["text"]
            entity_type = entity["type"].upper()
            base_form = entity.get("base_form") or entity_text
            text_to_type[entity_text] = entity_type
            text_to_base[entity_text] = base_form
            if base_form not in text_to_type:
                text_to_type[base_form] = entity_type
                text_to_base[base_form] = base_form
        seeded_originals = set(seed_mapping) if seed_mapping else set()
        transformed: Dict[str, str] = {}
        for original, placeholder in final_mapping.items():
            if original in seeded_originals:
                transformed[original] = placeholder
                continue
            entity_type = text_to_type.get(original, "ID")
            transformed[original] = apply_operator(
                original,
                entity_type,
                placeholder,
                operator_for_type(entity_type, operators),
                text_to_base.get(original, original),
                fake_secret or "",
                encrypt_secret or "",
            )
        final_mapping = transformed

    return final_mapping


def anonymize_text_content(
    full_text: str,
    text_pages: List[str],
    *,
    prompt_template: str,
    model_name: str,
    anonymized_entities: Optional[List[str]] = None,
    regex_patterns: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
    base_retry_delay: float = 1.0,
    max_retry_delay: float = 10.0,
    operators: Optional[Dict[str, str]] = None,
    fake_secret: Optional[str] = None,
    encrypt_secret: Optional[str] = None,
    seed_mapping: Optional[Dict[str, str]] = None,
    keep_list: Optional[List[str]] = None,
    deny_list: Optional[List[str]] = None,
    use_llm: bool = True,
    use_ner: bool = False,
    min_confidence: float = 0.0,
) -> Tuple[str, Dict[str, str]]:
    if regex_patterns is None:
        regex_patterns = DEFAULT_REGEX_PATTERNS

    collected_entities = collect_entities_from_chunks(
        text_pages,
        prompt_template=prompt_template,
        model_name=model_name,
        regex_patterns=regex_patterns,
        max_retries=max_retries,
        base_retry_delay=base_retry_delay,
        max_retry_delay=max_retry_delay,
        use_llm=use_llm,
        use_ner=use_ner,
    )
    entities_to_process = finalize_entities(
        collected_entities,
        full_text,
        anonymized_entities=anonymized_entities,
        keep_list=keep_list,
        deny_list=deny_list,
        apply_deny=True,
        min_confidence=min_confidence,
        seed_mapping=seed_mapping,
    )

    final_mapping = build_mapping(
        entities_to_process,
        seed_mapping=seed_mapping,
        operators=operators,
        fake_secret=fake_secret,
        encrypt_secret=encrypt_secret,
    )

    anonymized_text = full_text
    if entities_to_process:
        anonymized_text = replace_entities(
            full_text,
            (entity["text"] for entity in entities_to_process),
            final_mapping,
        )
    return anonymized_text, final_mapping


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
    operators: Optional[Dict[str, str]] = None,
    fake_secret: Optional[str] = None,
    encrypt_secret: Optional[str] = None,
    seed_mapping: Optional[Dict[str, str]] = None,
    keep_list: Optional[List[str]] = None,
    deny_list: Optional[List[str]] = None,
    use_llm: bool = True,
    use_ner: bool = False,
    ocr: bool = False,
    min_confidence: float = 0.0,
) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    """Anonymize a file by processing its text content.

    Performs a two-stage entity detection (fast regex first pass followed by
    LLM-based semantic detection), deduplicates, consolidates base forms for
    coreference (e.g. "Dr. Smith" / "Smith"), generates typed placeholders
    (PERSON_1, ORGANIZATION_3.v_1, ...), and replaces non-overlapping spans
    (longest-first, written from the end) to produce reversible anonymized output.

    The function streams large inputs via chunking (Markdown-aware for PDF/MD)
    so that very large files (hundreds of MB) can be processed without
    exhausting context windows or memory.

    Args:
        file_path: Path to the file to anonymize (.pdf, .md, .txt, .csv,
            .xlsx, or .docx). ``.xlsx`` needs the ``[excel]`` extra.
            ``.docx`` needs the ``[docx]`` extra. ``.xls`` / ``.xlsm`` /
            ``.ods`` / ``.xlsb`` and ``.doc`` / ``.docm`` / ``.dot`` /
            ``.dotm`` / ``.dotx`` are rejected.
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
        operators: Optional map of entity type → operator (replace, mask, hash,
            generalize, shift, fake, encrypt). Types not listed keep ``replace``.
            ``CREDIT_CARD_LIKE`` follows ``CREDIT_CARD``.
        fake_secret: Optional seed material for the ``fake`` operator. Same
            person + type + secret always yields the same fake.
        encrypt_secret: Secret for the ``encrypt`` operator. Same text always
            yields the same token. Required when any type uses ``encrypt``.
        seed_mapping: Optional original → written map from a previous file so
            the same person keeps PERSON_1 (or the same fake) across documents.
        keep_list: Phrases that must stay visible even if detected.
        deny_list: Phrases that must be replaced even if detection missed them.
        use_llm: When False, skip ``identify_entities_with_llm``. Regex,
            checksums, operators, gazetteers, and span replacement still run.
            Names and identity clues will be missed. Default True.
        use_ner: When True, run local span NER (GLiNER extra) for names and
            organizations. Default False so the SDK never downloads a
            checkpoint unless the caller asks.
        min_confidence: Drop entities whose ``score`` is below this value
            (0–1). Default 0 keeps today's accept-all behaviour. Scores are
            recognizer hints, not calibrated probabilities.
        ocr: When True and a PDF has no text layer, run Tesseract via
            PyMuPDF and stash word boxes for a later native-PDF write.
            A scan with OCR off (or OCR that returns nothing) raises.

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

    if is_rejected_word(file_path):
        raise rejected_word_error(file_path)
    if is_word_path(file_path):
        review, mapping, _entity_texts = anonymize_docx_file(
            file_path,
            characters_to_anonymize,
            prompt_template,
            model_name,
            anonymized_entities=anonymized_entities,
            chunk_overlap=chunk_overlap,
            regex_patterns=regex_patterns,
            max_retries=max_retries,
            base_retry_delay=base_retry_delay,
            max_retry_delay=max_retry_delay,
            operators=operators,
            fake_secret=fake_secret,
            encrypt_secret=encrypt_secret,
            seed_mapping=seed_mapping,
            keep_list=keep_list,
            deny_list=deny_list,
            use_llm=use_llm,
            use_ner=use_ner,
            min_confidence=min_confidence,
        )
        return review, mapping

    if is_rejected_spreadsheet(file_path):
        raise rejected_spreadsheet_error(file_path)
    if is_tabular_path(file_path):
        review, mapping, _entity_texts = anonymize_tabular_file(
            file_path,
            characters_to_anonymize,
            prompt_template,
            model_name,
            anonymized_entities=anonymized_entities,
            chunk_overlap=chunk_overlap,
            regex_patterns=regex_patterns,
            max_retries=max_retries,
            base_retry_delay=base_retry_delay,
            max_retry_delay=max_retry_delay,
            operators=operators,
            fake_secret=fake_secret,
            encrypt_secret=encrypt_secret,
            seed_mapping=seed_mapping,
            keep_list=keep_list,
            deny_list=deny_list,
            use_llm=use_llm,
            use_ner=use_ner,
            min_confidence=min_confidence,
        )
        return review, mapping

    file_size = os.path.getsize(file_path)
    full_text, text_pages = load_and_extract_text_from_file(
        file_path, characters_to_anonymize, chunk_overlap, ocr=ocr
    )

    if not text_pages:
        logging.warning("No text could be extracted from the file.")
        return None, None

    logging.info(f"Extracted text pages: {text_pages[0][:50]} ...")
    extracted_text_size = len(full_text)

    logging.info(f"  - File size: {file_size / 1024:.2f} KB")
    logging.info(f"  - Extracted text size: {extracted_text_size / 1024:.2f} KB")

    return anonymize_text_content(
        full_text,
        text_pages,
        prompt_template=prompt_template,
        model_name=model_name,
        anonymized_entities=anonymized_entities,
        regex_patterns=regex_patterns,
        max_retries=max_retries,
        base_retry_delay=base_retry_delay,
        max_retry_delay=max_retry_delay,
        operators=operators,
        fake_secret=fake_secret,
        encrypt_secret=encrypt_secret,
        seed_mapping=seed_mapping,
        keep_list=keep_list,
        deny_list=deny_list,
        use_llm=use_llm,
        use_ner=use_ner,
        min_confidence=min_confidence,
    )


def _serialize_cell_line(sheet_name: str, cell: TableCell, label: str) -> str:
    address = f"{sheet_name}!{column_letter(cell.column)}{cell.row}"
    return f"[{address}] {label}: {cell.search_text}"


def _searchable_row_cells(sheet: TableSheet, row: int) -> List[TableCell]:
    return [cell for cell in sheet.cells if cell.row == row and cell.search_text]


def _cell_label(cell: TableCell, labels: Dict[int, str]) -> str:
    return labels.get(cell.column, f"Col {column_letter(cell.column)}")


def _split_oversized_row(
    sheet_name: str,
    row: int,
    cells: List[TableCell],
    labels: Dict[int, str],
    characters_to_anonymize: int,
    splitter: RecursiveCharacterTextSplitter,
) -> List[str]:
    blocks: List[str] = []
    row_header = f"## Row {row}"
    for cell in sorted(cells, key=lambda item: item.column):
        label = _cell_label(cell, labels)
        line = _serialize_cell_line(sheet_name, cell, label)
        if len(line) <= characters_to_anonymize:
            blocks.append(f"{row_header}\n{line}")
            continue
        chunks = splitter.split_text(cell.search_text)
        total = max(len(chunks), 1)
        address = f"{sheet_name}!{column_letter(cell.column)}{cell.row}"
        if not chunks:
            chunks = [cell.search_text]
            total = 1
        for index, chunk in enumerate(chunks, start=1):
            blocks.append(
                f"{row_header}\n[{address}] {label} (part {index}/{total}): {chunk}"
            )
    return blocks


def build_llm_batches(doc: TableDocument, characters_to_anonymize: int) -> List[str]:
    """Row-addressed LLM prompts. Overlap is not applied across rows."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max(characters_to_anonymize, 1),
        chunk_overlap=0,
    )
    batches: List[str] = []
    for sheet in doc.sheets:
        labels = header_labels(sheet)
        units: List[str] = []
        for row in range(1, sheet.max_row + 1):
            cells = _searchable_row_cells(sheet, row)
            if not cells:
                continue
            row_header = f"## Row {row}"
            lines = [
                _serialize_cell_line(sheet.name, cell, _cell_label(cell, labels))
                for cell in sorted(cells, key=lambda item: item.column)
            ]
            row_block = row_header + "\n" + "\n".join(lines)
            if len(row_block) > characters_to_anonymize:
                units.extend(
                    _split_oversized_row(
                        sheet.name,
                        row,
                        cells,
                        labels,
                        characters_to_anonymize,
                        splitter,
                    )
                )
            else:
                units.append(row_block)

        current: List[str] = [f"# Sheet: {sheet.name}"]
        current_len = len(current[0])
        for unit in units:
            extra = 1 + len(unit)
            if current_len + extra > characters_to_anonymize and len(current) > 1:
                batches.append("\n".join(current))
                current = [f"# Sheet: {sheet.name}"]
                current_len = len(current[0])
            current.append(unit)
            current_len += extra
        if len(current) > 1:
            batches.append("\n".join(current))
    return batches


def _llm_entity_in_cells(entity_text: str, cells: Iterable[TableCell]) -> bool:
    if not entity_text:
        return False
    for cell in cells:
        if cell.search_text and locate_spans(cell.search_text, [entity_text]):
            return True
    return False


def anonymize_tabular_file(
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
    operators: Optional[Dict[str, str]] = None,
    fake_secret: Optional[str] = None,
    encrypt_secret: Optional[str] = None,
    seed_mapping: Optional[Dict[str, str]] = None,
    keep_list: Optional[List[str]] = None,
    deny_list: Optional[List[str]] = None,
    use_llm: bool = True,
    use_ner: bool = False,
    min_confidence: float = 0.0,
) -> Tuple[str, Dict[str, str], Tuple[str, ...]]:
    """Anonymize a CSV/Excel file cell by cell.

    Returns ``(review_flatten, orig→written, entity_texts)``. ``entity_texts``
    is the same ``entity["text"]`` list the text engine passes to
    ``replace_entities``.
    """
    del chunk_overlap  # row boundaries replace chunk overlap
    if regex_patterns is None:
        regex_patterns = DEFAULT_REGEX_PATTERNS

    if is_rejected_spreadsheet(file_path):
        raise rejected_spreadsheet_error(file_path)

    doc = load_table(file_path)
    cells = list(iter_cells(doc))
    collected_entities: List[dict] = []

    for cell in cells:
        if not cell.search_text or cell.kind not in REGEX_CELL_KINDS:
            continue
        collected_entities.extend(
            extract_entities_via_regex(cell.search_text, regex_patterns)
        )
        if use_ner:
            collected_entities.extend(extract_entities_via_ner(cell.search_text))

    if use_llm:
        batches = build_llm_batches(doc, characters_to_anonymize)
        for i, batch in enumerate(batches):
            logging.info(
                f"Identifying entities in table batch {i + 1}/{len(batches)}..."
            )
            llm_entities = identify_entities_with_llm(
                batch,
                prompt_template,
                model_name,
                max_retries=max_retries,
                base_retry_delay=base_retry_delay,
                max_retry_delay=max_retry_delay,
            )
            for entity in llm_entities:
                text = entity.get("text") or ""
                if _llm_entity_in_cells(text, cells):
                    collected_entities.append(entity)
    else:
        logging.info(
            "Regex-only / offline mode: skipping the language model. "
            "Names and identity clues will be missed."
        )

    if deny_list:
        for cell in cells:
            if not cell.search_text:
                continue
            collected_entities.extend(apply_deny_list(cell.search_text, [], deny_list))

    entities_to_process = finalize_entities(
        collected_entities,
        "",
        anonymized_entities=anonymized_entities,
        keep_list=keep_list,
        deny_list=deny_list,
        apply_deny=False,
        seed_mapping=seed_mapping,
        min_confidence=min_confidence,
    )
    final_mapping = build_mapping(
        entities_to_process,
        seed_mapping=seed_mapping,
        operators=operators,
        fake_secret=fake_secret,
        encrypt_secret=encrypt_secret,
    )
    entity_texts = tuple(
        entity["text"] for entity in entities_to_process if entity.get("text")
    )
    apply_mapping_to_table(doc, final_mapping, entity_texts)
    review = flatten_table_for_review(doc, anonymized=True)
    return review, final_mapping, entity_texts


def _llm_entity_in_blocks(entity_text: str, blocks: Iterable) -> bool:
    if not entity_text:
        return False
    for block in blocks:
        if block.search_text and locate_spans(block.search_text, [entity_text]):
            return True
    return False


def anonymize_docx_file(
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
    operators: Optional[Dict[str, str]] = None,
    fake_secret: Optional[str] = None,
    encrypt_secret: Optional[str] = None,
    seed_mapping: Optional[Dict[str, str]] = None,
    keep_list: Optional[List[str]] = None,
    deny_list: Optional[List[str]] = None,
    use_llm: bool = True,
    use_ner: bool = False,
    min_confidence: float = 0.0,
) -> Tuple[str, Dict[str, str], Tuple[str, ...]]:
    """Anonymize a Word ``.docx`` file paragraph by paragraph.

    Returns ``(review_flatten, orig→written, entity_texts)``. ``entity_texts``
    is the same ``entity["text"]`` list the text engine passes to
    ``replace_entities``.
    """
    if regex_patterns is None:
        regex_patterns = DEFAULT_REGEX_PATTERNS

    if is_rejected_word(file_path):
        raise rejected_word_error(file_path)

    doc = load_docx(file_path)
    blocks = list(doc.blocks)
    collected_entities: List[dict] = []

    for block in blocks:
        if not block.search_text:
            continue
        collected_entities.extend(
            extract_entities_via_regex(block.search_text, regex_patterns)
        )
        if use_ner:
            collected_entities.extend(extract_entities_via_ner(block.search_text))

    full_text = flatten_docx_for_review(doc, anonymized=False)
    if use_llm:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=max(characters_to_anonymize, 1),
            chunk_overlap=max(chunk_overlap, 0),
        )
        chunks = splitter.split_text(full_text) if full_text.strip() else []
        for i, chunk in enumerate(chunks):
            logging.info(f"Identifying entities in Word chunk {i + 1}/{len(chunks)}...")
            llm_entities = identify_entities_with_llm(
                chunk,
                prompt_template,
                model_name,
                max_retries=max_retries,
                base_retry_delay=base_retry_delay,
                max_retry_delay=max_retry_delay,
            )
            for entity in llm_entities:
                text = entity.get("text") or ""
                if _llm_entity_in_blocks(text, blocks):
                    collected_entities.append(entity)
    else:
        logging.info(
            "Regex-only / offline mode: skipping the language model. "
            "Names and identity clues will be missed."
        )

    if deny_list:
        for block in blocks:
            if not block.search_text:
                continue
            collected_entities.extend(apply_deny_list(block.search_text, [], deny_list))

    entities_to_process = finalize_entities(
        collected_entities,
        full_text,
        anonymized_entities=anonymized_entities,
        keep_list=keep_list,
        deny_list=deny_list,
        apply_deny=False,
        seed_mapping=seed_mapping,
        min_confidence=min_confidence,
    )
    final_mapping = build_mapping(
        entities_to_process,
        seed_mapping=seed_mapping,
        operators=operators,
        fake_secret=fake_secret,
        encrypt_secret=encrypt_secret,
    )
    entity_texts = tuple(
        entity["text"] for entity in entities_to_process if entity.get("text")
    )
    apply_mapping_to_docx(doc, final_mapping, entity_texts)
    review = flatten_docx_for_review(doc, anonymized=True)
    return review, final_mapping, entity_texts
