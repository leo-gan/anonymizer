import json
from pathlib import Path


def save_mapping(final_mapping: dict, original_pdf_path: Path) -> str:
    """
    Save the mapping dictionary to a JSON file.

    Args:
        final_mapping (dict): The dictionary containing the PII mapping.
        original_pdf_path (Path): The path to the original PDF file, used for naming.

    Returns:
        The path to the saved mapping file.
    """
    pdf_file_name = original_pdf_path.stem
    mapping_file_path = original_pdf_path.parent / f"{pdf_file_name}.mapping.json"

    # fix some glitch:
    final_mapping = {k: v for k, v in final_mapping.items() if k != v}

    with open(mapping_file_path, "w", encoding="utf-8") as f:
        json.dump(final_mapping, f, indent=4)

    return str(mapping_file_path)
