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
        final_mapping (dict[str, str]): The mapping.
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

    anonymized_output_file = f"{anonymized_dir}/{file_stem}.anonymized{output_extension}"
    with open(anonymized_output_file, "w", encoding="utf-8") as f:
        f.write(full_anonymized_text)

    mapping_file = f"{mappings_dir}/{file_stem}.mapping.json"
    # fix some glitch:
    final_mapping = {k: v for k, v in final_mapping.items() if k != v}
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(final_mapping, f, indent=4)

    return anonymized_output_file, mapping_file


def deanonymize_file(
    anonymized_file_path: str, mapping_file_path: str
) -> tuple[str, str]:
    """
    Deanonymize a file using a mapping file.

    Args:
        anonymized_file_path (str): Path to the anonymized file.
        mapping_file_path (str): Path to the mapping file.

    Returns:
        A tuple containing the path to the deanonymized file and the statistics file.
    """
    with open(anonymized_file_path, "r", encoding="utf-8") as f:
        anonymized_text = f.read()

    with open(mapping_file_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    deanonymized_text = anonymized_text
    used_mappings = set()

    # Sort placeholders by length in descending order to avoid partial replacements
    sorted_placeholders = sorted(mapping.keys(), key=len, reverse=True)

    for placeholder in sorted_placeholders:
        if placeholder in deanonymized_text:
            deanonymized_text = deanonymized_text.replace(
                placeholder, mapping[placeholder]
            )
            used_mappings.add(placeholder)

    all_placeholders_in_text = set(
        re.findall(r"[A-Z_]+_[0-9]+(?:\.v_[0-9]+)?", anonymized_text)
    )

    not_found_mappings = sorted(list(all_placeholders_in_text - set(mapping.keys())))
    unused_mappings = sorted(list(set(mapping.keys()) - used_mappings))

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
