"""Utilities for mapping consolidation, result saving, and deanonymization.

These helpers are used by both the CLI and direct SDK consumers. They handle
the reversible placeholder mapping contract, output file layout conventions,
and post-deanonymization auditing statistics.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from pdf_anonymizer_core.conf import (
    DEFAULT_ANONYMIZED_DIR,
    DEFAULT_DEANONYMIZED_DIR,
    DEFAULT_MAPPINGS_DIR,
    DEFAULT_STATS_DIR,
)
from pdf_anonymizer_core.mapping_crypto import (
    encrypt_mapping,
    load_mapping_payload,
    sha256_file,
)
from pdf_anonymizer_core.secure_io import write_private_json
from pdf_anonymizer_core.tables import (
    flatten_table_for_review,
    is_tabular_path,
    iter_cells,
    load_table,
    save_table,
    unneutralize_csv_equals,
    write_anonymized_table,
)
from pdf_anonymizer_core.word import (
    flatten_docx_for_review,
    is_word_path,
    load_docx,
    save_docx,
    write_anonymized_docx,
    write_block_text,
)

_PLACEHOLDER_PATTERN = re.compile(r"^[A-Z_]+_[0-9]+(?:\.v_[0-9]+)?$")


def looks_like_placeholder(text: str) -> bool:
    """True if ``text`` is a stand-in label such as PERSON_1 or IBAN_LIKE_2."""
    return bool(text and _PLACEHOLDER_PATTERN.match(text.strip()))


_PLACEHOLDER_PARSE = re.compile(r"^([A-Z][A-Z0-9_]*)_([0-9]+)(?:\.v_([0-9]+))?$")


def mapping_to_original_to_written(raw: Dict[str, str]) -> Dict[str, str]:
    """Accept either placeholder→original or original→placeholder."""
    keys_ph = sum(
        1 for key in raw if isinstance(key, str) and looks_like_placeholder(key)
    )
    vals_ph = sum(
        1
        for val in raw.values()
        if isinstance(val, str) and looks_like_placeholder(val)
    )
    if keys_ph >= vals_ph:
        out: Dict[str, str] = {}
        for placeholder, original in raw.items():
            if isinstance(original, str) and isinstance(placeholder, str):
                out.setdefault(original, placeholder)
        return out
    return {str(k): str(v) for k, v in raw.items()}


def load_seed_mapping(
    mapping_path: str, mapping_passphrase: Optional[str] = None
) -> Dict[str, str]:
    """Load a mapping file as original → written form (placeholder or fake)."""
    with open(mapping_path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    loaded = load_mapping_payload(raw, mapping_passphrase)
    return mapping_to_original_to_written(loaded)


def seed_placeholder_state(
    orig_to_written: Dict[str, str],
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, int], Dict[str, int]]:
    """Turn an existing original→written map into placeholder assignment state."""
    mapping = dict(orig_to_written)
    base_placeholders: Dict[str, str] = {}
    counts: Dict[str, int] = {}
    variation_counts: Dict[str, int] = {}
    for original, written in mapping.items():
        if not isinstance(written, str):
            continue
        parsed = _PLACEHOLDER_PARSE.match(written)
        if not parsed:
            base_placeholders[original] = written
            continue
        type_name, number, variation = (
            parsed.group(1),
            int(parsed.group(2)),
            parsed.group(3),
        )
        counts[type_name] = max(counts.get(type_name, 0), number)
        main = f"{type_name}_{number}"
        if variation is None:
            base_placeholders[original] = main
        else:
            variation_counts[main] = max(variation_counts.get(main, 0), int(variation))
    return mapping, base_placeholders, counts, variation_counts


def consolidate_mapping(
    anonymized_text: str, mapping: Dict[str, str]
) -> Tuple[str, Dict[str, str]]:
    """
    Consolidates the mapping to ensure one-to-one correspondence and updates the text.

    Args:
        anonymized_text: The text with anonymized placeholders.
        mapping: The dictionary mapping placeholders to original PII.

    Returns:
        A tuple containing the updated anonymized text and the consolidated mapping.
    """
    # Invert the mapping to find duplicates
    value_to_keys: Dict[str, list] = {}
    for key, value in mapping.items():
        if value not in value_to_keys:
            value_to_keys[value] = []
        value_to_keys[value].append(key)

    consolidation_map = {}
    consolidated_mapping = mapping.copy()

    for value, keys in value_to_keys.items():
        if len(keys) > 1:
            canonical_key = keys[0]
            for key_to_replace in keys[1:]:
                consolidation_map[key_to_replace] = canonical_key
                if key_to_replace in consolidated_mapping:
                    del consolidated_mapping[key_to_replace]

    # Update the anonymized text in a single pass
    if consolidation_map:
        # Use word boundaries to avoid replacing parts of other words
        # Replace by longest keys first to ensure correct matching
        sorted_keys = sorted(consolidation_map.keys(), key=len, reverse=True)
        pattern = re.compile(
            r"\b(" + "|".join(re.escape(key) for key in sorted_keys) + r")\b"
        )
        anonymized_text = pattern.sub(
            lambda m: consolidation_map[m.group(1)], anonymized_text
        )

    return anonymized_text, consolidated_mapping


def save_results(
    full_anonymized_text: str,
    final_mapping: dict[str, str],
    file_path: str,
    mapping_passphrase: str | None = None,
    *,
    ephemeral_mapping: bool = False,
    entity_texts: Optional[Iterable[str]] = None,
    orig_to_written: Optional[Dict[str, str]] = None,
) -> tuple[str, str]:
    """
    Save the anonymized text and the mapping to files.

    Args:
        full_anonymized_text (str): The anonymized text.
        final_mapping (dict[str, str]): Mapping written to the mapping file
            (CLI invert: placeholder → original).
        file_path (str): The path to the original file.
        mapping_passphrase: If set, write ``*.mapping.json.enc`` (AES-256-GCM
            + Argon2id) instead of plaintext JSON.
        ephemeral_mapping: If true, never write a mapping file. The second
            return value is an empty string. The caller already holds
            ``final_mapping`` in memory.
        entity_texts: Detected ``entity["text"]`` values used to apply the
            mapping. Required for table and Word paths; ignored for text.
        orig_to_written: Engine original → written map used to re-apply on
            tables and Word files. Required for colliding mask/generalize/fake
            forms; when omitted, ``mapping_to_original_to_written(final_mapping)``
            is used.

    Returns:
        tuple[str, str]: The paths to the anonymized text file and the mapping
        file. The mapping path is ``""`` when ``ephemeral_mapping`` is true.
    """
    original_path = Path(file_path)
    file_stem = original_path.stem
    file_extension = original_path.suffix.lower()

    anonymized_dir = DEFAULT_ANONYMIZED_DIR
    mappings_dir = DEFAULT_MAPPINGS_DIR
    os.makedirs(anonymized_dir, exist_ok=True)

    if file_extension == ".pdf":
        output_extension = ".md"
    else:
        output_extension = file_extension

    anonymized_output_file = (
        f"{anonymized_dir}/{file_stem}.anonymized{output_extension}"
    )
    structured = is_tabular_path(file_path) or is_word_path(file_path)
    if structured:
        if entity_texts is None:
            raise ValueError(
                "save_results() on a table or Word document requires "
                "entity_texts= (the same entity['text'] list the engine applied)."
            )
        apply_map = (
            orig_to_written
            if orig_to_written is not None
            else mapping_to_original_to_written(final_mapping)
        )
        texts = [text for text in entity_texts if text]
        if texts and not any(text in apply_map for text in texts):
            raise ValueError(
                "save_results() entity_texts are not keys of orig_to_written. "
                "Pass the engine original→written map as orig_to_written=."
            )
        if is_word_path(file_path):
            write_anonymized_docx(
                file_path, anonymized_output_file, apply_map, texts
            )
        else:
            write_anonymized_table(
                file_path, anonymized_output_file, apply_map, texts
            )
    else:
        with open(anonymized_output_file, "w", encoding="utf-8") as f:
            f.write(full_anonymized_text)

    if ephemeral_mapping:
        return anonymized_output_file, ""

    source_digest = ""
    if original_path.is_file():
        source_digest = sha256_file(original_path)

    if mapping_passphrase:
        mapping_file = f"{mappings_dir}/{file_stem}.mapping.json.enc"
        payload = encrypt_mapping(
            final_mapping,
            mapping_passphrase,
            source_sha256=source_digest or None,
        )
        write_private_json(mapping_file, payload)
    else:
        mapping_file = f"{mappings_dir}/{file_stem}.mapping.json"
        # Persist mapping as placeholder -> original for correct deanonymization
        write_private_json(mapping_file, final_mapping)

    return anonymized_output_file, mapping_file


def restore_placeholders_in_text(
    text: str, placeholder_to_original: Dict[str, str]
) -> tuple[str, set[str]]:
    """Replace longest-first ``PLACEHOLDER`` / ``PLACEHOLDER.v_n`` tokens."""
    used_placeholders: set[str] = set()
    sorted_placeholders = sorted(
        placeholder_to_original.keys(), key=len, reverse=True
    )
    if not sorted_placeholders:
        return text, used_placeholders

    pattern = re.compile(
        r"\b("
        + "|".join(re.escape(placeholder) for placeholder in sorted_placeholders)
        + r")(?:\.v_\d+)?\b"
    )

    def replace_match(match: re.Match[str]) -> str:
        full_match = match.group(0)
        base_placeholder = match.group(1)
        used_placeholders.add(full_match)
        return placeholder_to_original[base_placeholder]

    return pattern.sub(replace_match, text), used_placeholders


def deanonymize_file(
    anonymized_file_path: str,
    mapping_file_path: str,
    mapping_passphrase: str | None = None,
    *,
    expected_source_sha256: str | None = None,
) -> tuple[str, str]:
    """Deanonymize a file using a mapping file.

    Restores original PII values from placeholders. Supports both current
    (placeholder -> original) and legacy (original -> placeholder) mapping
    directions via auto-detection.

    The implementation correctly handles variation placeholders (PERSON_1.v_2
    etc.) by falling back to the base placeholder's original value.

    After processing it also produces an audit statistics JSON file.

    Args:
        anonymized_file_path: Path to the previously anonymized document.
        mapping_file_path: Path to the JSON mapping file (plaintext or ``.enc``).
        mapping_passphrase: Required when the mapping file is encrypted.
        expected_source_sha256: Optional SHA-256 of the original source
            document. When set, an encrypted mapping locked to a different
            file is rejected (AAD mismatch).

    Returns:
        A tuple (deanonymized_file_path, stats_file_path).
        The stats file contains:
            - unused_mappings: placeholders in the map that did not appear in text
            - not_found_mappings: placeholders seen in text but missing from the map
    """
    with open(mapping_file_path, "r", encoding="utf-8") as f:
        raw_mapping = json.load(f)

    raw_mapping = load_mapping_payload(
        raw_mapping,
        mapping_passphrase,
        source_sha256=expected_source_sha256,
    )

    # Detect mapping direction and normalize to placeholder -> original
    # Heuristic: if most keys look like placeholders (e.g., PERSON_1), treat as placeholder->original
    placeholder_key_pattern = _PLACEHOLDER_PATTERN
    keys_look_like_placeholders = sum(
        1
        for k in raw_mapping.keys()
        if isinstance(k, str) and placeholder_key_pattern.match(k)
    )
    values_look_like_placeholders = sum(
        1
        for v in raw_mapping.values()
        if isinstance(v, str) and placeholder_key_pattern.match(v)
    )

    if keys_look_like_placeholders >= values_look_like_placeholders:
        placeholder_to_original = dict(raw_mapping)
    else:
        # Legacy: invert original -> placeholder to placeholder -> original
        placeholder_to_original = {}
        for original, placeholder in raw_mapping.items():
            if isinstance(placeholder, str):
                placeholder_to_original.setdefault(placeholder, original)

    sorted_placeholders = sorted(placeholder_to_original.keys(), key=len, reverse=True)
    tabular = is_tabular_path(anonymized_file_path)
    word = is_word_path(anonymized_file_path)
    deanonymized_text = ""

    if tabular:
        doc = load_table(anonymized_file_path)
        anonymized_text = flatten_table_for_review(doc, anonymized=True)
        used_placeholders: set[str] = set()
        for cell in iter_cells(doc):
            if not cell.search_text:
                continue
            restored, cell_used = restore_placeholders_in_text(
                cell.search_text, placeholder_to_original
            )
            used_placeholders |= cell_used
            if doc.kind == "csv":
                restored = unneutralize_csv_equals(restored)
            if restored != cell.search_text:
                cell.search_text = restored
    elif word:
        word_doc = load_docx(anonymized_file_path)
        anonymized_text = flatten_docx_for_review(word_doc, anonymized=True)
        used_placeholders = set()
        for block in word_doc.blocks:
            if not block.search_text:
                continue
            restored, block_used = restore_placeholders_in_text(
                block.search_text, placeholder_to_original
            )
            used_placeholders |= block_used
            if restored != block.search_text:
                write_block_text(block, restored)
    else:
        with open(anonymized_file_path, "r", encoding="utf-8") as f:
            anonymized_text = f.read()
        deanonymized_text, used_placeholders = restore_placeholders_in_text(
            anonymized_text, placeholder_to_original
        )

    # Gather stats
    all_placeholders_in_text = set(
        re.findall(r"[A-Z_]+_[0-9]+(?:\.v_[0-9]+)?", anonymized_text)
    )

    not_found_mappings = sorted(list(all_placeholders_in_text - used_placeholders))

    # Unused mappings: base placeholders that never occurred (neither base nor any variation)
    used_bases = {p.split(".v_")[0] for p in used_placeholders}
    unused_mappings = sorted([p for p in sorted_placeholders if p not in used_bases])

    anonymized_path = Path(anonymized_file_path)
    file_stem = anonymized_path.name.replace(f".anonymized{anonymized_path.suffix}", "")
    output_extension = anonymized_path.suffix

    deanonymized_dir = DEFAULT_DEANONYMIZED_DIR
    stats_dir = DEFAULT_STATS_DIR
    os.makedirs(deanonymized_dir, exist_ok=True)
    os.makedirs(stats_dir, exist_ok=True)

    deanonymized_file = f"{deanonymized_dir}/{file_stem}.deanonymized{output_extension}"
    if tabular:
        save_table(doc, deanonymized_file)
    elif word:
        save_docx(word_doc, deanonymized_file)
    else:
        with open(deanonymized_file, "w", encoding="utf-8") as f:
            f.write(deanonymized_text)

    stats_file = f"{stats_dir}/{file_stem}.deanonymization_stat.json"
    stats = {
        "anonymized_file": anonymized_file_path,
        "mapping_file": mapping_file_path,
        "deanonymized_file": deanonymized_file,
        "unused_mappings": unused_mappings,
        "not_found_mappings": not_found_mappings,
    }
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)

    # Drop in-process references to recovered PII. Python strings cannot be
    # reliably overwritten; clearing the dicts is the explicit protocol.
    raw_mapping.clear()
    placeholder_to_original.clear()

    return deanonymized_file, stats_file
