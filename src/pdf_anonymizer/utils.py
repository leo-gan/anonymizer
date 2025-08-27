import json
from pathlib import Path
import os
from markdown_pdf import MarkdownPdf


def save_results(full_anonymized_text, final_mapping, pdf_path, output_format):
    """
    Save the anonymized text and the mapping to files.
    """
    pdf_file_name = Path(pdf_path).stem

    anonymized_dir = "data/anonymized"
    mappings_dir = "data/mappings"
    os.makedirs(anonymized_dir, exist_ok=True)
    os.makedirs(mappings_dir, exist_ok=True)

    if output_format == "pdf":
        anonymized_output_file = f"{anonymized_dir}/{pdf_file_name}.anonymized.pdf"
        pdf = MarkdownPdf()
        pdf.add_section(full_anonymized_text)
        pdf.save(anonymized_output_file)
    else:
        anonymized_output_file = f"{anonymized_dir}/{pdf_file_name}.anonymized.md"
        with open(anonymized_output_file, "w", encoding="utf-8") as f:
            f.write(full_anonymized_text)

    mapping_file = f"{mappings_dir}/{pdf_file_name}.mapping.json"
    # fix some glitch:
    final_mapping = {k: v for k, v in final_mapping.items() if k != v}
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(final_mapping, f, indent=4)

    return anonymized_output_file, mapping_file
