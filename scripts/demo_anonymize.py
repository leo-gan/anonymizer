import sys
import os
from unittest.mock import patch, Mock
import json

# Ensure python can find our core package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "pdf-anonymizer-core", "src")))

from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.utils import save_results, deanonymize_file, consolidate_mapping

def run_demo():
    print("=" * 70)
    print("PDF Anonymizer Demo: Round-Trip Anonymization & Deanonymization")
    print("=" * 70)

    pdf_path = "data/arxiv_pii_sample.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} does not exist. Run prepare_demo_pdf.py first.")
        return

    # Mock the LLM provider to return the name "Alice Smith"
    # The Regex NER stage will automatically detect email, phone, IP, and SSN
    mock_provider = Mock()
    mock_provider.call.return_value = json.dumps({
        "entities": [
            {"text": "Alice Smith", "type": "PERSON", "base_form": "Alice Smith"}
        ]
    })

    print("Step 1: Running Hybrid NER on the PDF (Regex + LLM)...")
    with patch("pdf_anonymizer_core.call_llm.get_provider", return_value=mock_provider):
        anonymized_text, mapping = anonymize_file(
            file_path=pdf_path,
            characters_to_anonymize=50000,
            prompt_template="Identify PII: {text}",
            model_name="gemini-2.5-pro",
            chunk_overlap=1000,
        )

    if not anonymized_text or not mapping:
        print("Anonymization failed.")
        return

    print("\nHybrid NER Complete! Identified Entities:")
    for orig, placeholder in mapping.items():
        print(f"  - {orig} -> {placeholder}")

    # Standardize mapping to placeholder -> original and consolidate
    placeholder_to_original = {v: k for k, v in mapping.items()}
    anonymized_text, consolidated_map = consolidate_mapping(anonymized_text, placeholder_to_original)

    # Save outputs
    print("\nStep 2: Saving Anonymized text and Mapping vocabulary...")
    anonymized_output_file, mapping_file = save_results(
        anonymized_text, consolidated_map, pdf_path
    )
    print(f"  - Saved anonymized text to: {anonymized_output_file}")
    print(f"  - Saved mapping to: {mapping_file}")

    # Print a snippet of the anonymized output
    print("\nAnonymized Excerpt (First few lines of output):")
    print("-" * 50)
    lines = anonymized_text.splitlines()
    for line in lines[:10]:
        if any(p in line for p in ["PERSON", "EMAIL", "PHONE", "IP_ADDRESS", "SSN"]):
            print(f"\033[93m{line}\033[0m")  # highlight changes in yellow
        else:
            print(line)
    print("-" * 50)

    # Revert / Deanonymize
    print("\nStep 3: Performing Deanonymization (Round-Trip)...")
    deanonymized_file, stats_file = deanonymize_file(anonymized_output_file, mapping_file)
    print(f"  - Saved deanonymized text to: {deanonymized_file}")
    print(f"  - Saved stats to: {stats_file}")

    # Verify the roundtrip
    with open(deanonymized_file, "r") as f:
        reverted_text = f.read()

    print("\nDeanonymized Excerpt (Reverted back to original):")
    print("-" * 50)
    reverted_lines = reverted_text.splitlines()
    for line in reverted_lines[:10]:
        if any(pii in line for pii in ["Alice Smith", "alice.smith", "555-0199", "10.0.0.1", "123-45"]):
            print(f"\033[92m{line}\033[0m")  # highlight reverted text in green
        else:
            print(line)
    print("-" * 50)

    # Quick validation checks to ensure correctness
    assert "Alice Smith" in reverted_text
    assert "alice.smith@example.com" in reverted_text
    assert "+1-555-0199" in reverted_text
    assert "10.0.0.1" in reverted_text
    assert "123-45-6789" in reverted_text

    print("\nDemo Round-Trip Completed Successfully!")
    print("=" * 70)

if __name__ == "__main__":
    run_demo()
