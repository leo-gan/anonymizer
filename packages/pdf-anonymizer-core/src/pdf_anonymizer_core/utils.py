import json
import os
import re
from pathlib import Path
from typing import Dict, Tuple


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

    # Update the anonymized text
    for old_key, new_key in consolidation_map.items():
        # Use word boundaries to avoid replacing parts of other words
        anonymized_text = re.sub(
            r"\b" + re.escape(old_key) + r"\b", new_key, anonymized_text
        )

    return anonymized_text, consolidated_mapping


def save_results(
    full_anonymized_text: str, final_mapping: dict[str, str], file_path: str
) -> tuple[str, str]:
    """
    Save the anonymized text and the mapping to files.

    Args:
        full_anonymized_text (str): The anonymized text.
        final_mapping (dict[str, str]): Mapping of original text -> placeholder.
        file_path (str): The path to the original file.

    Returns:
        tuple[str, str]: The paths to the anonymized text file and the mapping file.
    """
    original_path = Path(file_path)
    file_stem = original_path.stem
    file_extension = original_path.suffix.lower()

    anonymized_dir = "data/anonymized"
    mappings_dir = "data/mappings"
    os.makedirs(anonymized_dir, exist_ok=True)
    os.makedirs(mappings_dir, exist_ok=True)

    if file_extension == ".pdf":
        output_extension = ".md"
    else:
        output_extension = file_extension

    anonymized_output_file = (
        f"{anonymized_dir}/{file_stem}.anonymized{output_extension}"
    )
    with open(anonymized_output_file, "w", encoding="utf-8") as f:
        f.write(full_anonymized_text)

    mapping_file = f"{mappings_dir}/{file_stem}.mapping.json"
    # Persist mapping as placeholder -> original for correct deanonymization
    placeholder_to_original: dict[str, str] = {}
    for original, placeholder in final_mapping.items():
        # Prefer the first original we saw for a given placeholder
        if placeholder not in placeholder_to_original:
            placeholder_to_original[placeholder] = original
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(placeholder_to_original, f, indent=4)

    return anonymized_output_file, mapping_file


def deanonymize_file(
    anonymized_file_path: str, mapping_file_path: str
) -> tuple[str, str]:
    """
    Deanonymize a file using a mapping file.

    The mapping file can be either:
    - placeholder -> original (preferred), or
    - original -> placeholder (legacy). In this case it will be inverted.

    Variations like "PERSON_1.v_1" will be mapped to the base placeholder's
    original value if only the base (e.g., "PERSON_1") exists in the mapping.

    Args:
        anonymized_file_path (str): Path to the anonymized file.
        mapping_file_path (str): Path to the mapping file.

    Returns:
        A tuple containing the path to the deanonymized file and the statistics file.
    """
    with open(anonymized_file_path, "r", encoding="utf-8") as f:
        anonymized_text = f.read()

    with open(mapping_file_path, "r", encoding="utf-8") as f:
        raw_mapping = json.load(f)

    # Detect mapping direction and normalize to placeholder -> original
    # Heuristic: if most keys look like placeholders (e.g., PERSON_1), treat as placeholder->original
    placeholder_key_pattern = re.compile(r"^[A-Z_]+_[0-9]+(?:\.v_[0-9]+)?$")
    keys_look_like_placeholders = sum(
        1 for k in raw_mapping.keys() if isinstance(k, str) and placeholder_key_pattern.match(k)
    )
    values_look_like_placeholders = sum(
        1 for v in raw_mapping.values() if isinstance(v, str) and placeholder_key_pattern.match(v)
    )

    if keys_look_like_placeholders >= values_look_like_placeholders:
        placeholder_to_original = dict(raw_mapping)
    else:
        # Legacy: invert original -> placeholder to placeholder -> original
        placeholder_to_original = {}
        for original, placeholder in raw_mapping.items():
            if isinstance(placeholder, str):
                placeholder_to_original.setdefault(placeholder, original)

    deanonymized_text = anonymized_text
    used_placeholders = set()  # track actual placeholders (including variations) found

    # Replace placeholders by longest first to avoid partial overlaps
    sorted_placeholders = sorted(placeholder_to_original.keys(), key=len, reverse=True)

    for base_placeholder in sorted_placeholders:
        original_value = placeholder_to_original[base_placeholder]
        # Match base and its variations: PERSON_1 and PERSON_1.v_1, PERSON_1.v_2, ...
        pattern = re.compile(rf"\b{re.escape(base_placeholder)}(?:\.v_\d+)?\b")

        # Record any matches before substitution
        matches = set(pattern.findall(deanonymized_text))
        if matches:
            used_placeholders.update(matches)
            deanonymized_text = pattern.sub(original_value, deanonymized_text)

    # Gather stats
    all_placeholders_in_text = set(
        re.findall(r"[A-Z_]+_[0-9]+(?:\.v_[0-9]+)?", anonymized_text)
    )

    not_found_mappings = sorted(list(all_placeholders_in_text - used_placeholders))

    # Unused mappings: base placeholders that never occurred (neither base nor any variation)
    used_bases = {p.split(".v_")[0] for p in used_placeholders}
    unused_mappings = sorted([
        p for p in sorted_placeholders if p not in used_bases
    ])

    anonymized_path = Path(anonymized_file_path)
    file_stem = anonymized_path.name.replace(f".anonymized{anonymized_path.suffix}", "")
    output_extension = anonymized_path.suffix

    deanonymized_dir = "data/deanonymized"
    stats_dir = "data/stats"
    os.makedirs(deanonymized_dir, exist_ok=True)
    os.makedirs(stats_dir, exist_ok=True)

    deanonymized_file = f"{deanonymized_dir}/{file_stem}.deanonymized{output_extension}"
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

    return deanonymized_file, stats_file
