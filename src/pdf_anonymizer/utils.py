import json
import os
import re
from pathlib import Path


def save_results(
    full_anonymized_text: str, final_mapping: dict[str, str], pdf_path: str
) -> tuple[str, str]:
    """
    Save the anonymized text and the mapping to files.

    Args:
        full_anonymized_text (str): The anonymized text.
        final_mapping (dict[str, str]): The mapping.
        pdf_path (str): The path to the original PDF file.

    Returns:
        tuple[str, str]: The paths to the anonymized text file and the mapping file.
    """
    pdf_file_name = Path(pdf_path).stem

    anonymized_dir = "data/anonymized"
    mappings_dir = "data/mappings"
    os.makedirs(anonymized_dir, exist_ok=True)
    os.makedirs(mappings_dir, exist_ok=True)

    anonymized_output_file = f"{anonymized_dir}/{pdf_file_name}.anonymized.md"
    with open(anonymized_output_file, "w", encoding="utf-8") as f:
        f.write(full_anonymized_text)

    mapping_file = f"{mappings_dir}/{pdf_file_name}.mapping.json"
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

    file_stem = Path(anonymized_file_path).stem.replace(".anonymized", "")

    deanonymized_dir = "data/deanonymized"
    stats_dir = "data/stats"
    os.makedirs(deanonymized_dir, exist_ok=True)
    os.makedirs(stats_dir, exist_ok=True)

    deanonymized_file = f"{deanonymized_dir}/{file_stem}.deanonymized.md"
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
