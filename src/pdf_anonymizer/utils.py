import json
import os
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
