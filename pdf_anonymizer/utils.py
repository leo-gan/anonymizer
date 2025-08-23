import json
from pathlib import Path


def save_results(full_anonymized_text, final_mapping, pdf_path):
    """
    Save the anonymized text and the mapping to files.
    """
    pdf_file_name = Path(pdf_path).stem
    anonymized_output_file = f"{pdf_file_name}.anonymized_output.txt"
    with open(anonymized_output_file, "w", encoding="utf-8") as f:
        f.write(full_anonymized_text)

    mapping_file = f"{pdf_file_name}.mapping.json"
    # fix some glitch:
    final_mapping = {k: v for k, v in final_mapping.items() if k != v}
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(final_mapping, f, indent=4)

    return anonymized_output_file, mapping_file
