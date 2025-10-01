import json
import os
from pathlib import Path

from pdf_anonymizer_core.utils import deanonymize_file


def test_deanonymize_file():
    # Create dummy anonymized file
    anonymized_content = "Hello PERSON_1, welcome to LOCATION_1. Your email is EMAIL_1. We don't know about PERSON_4."
    anonymized_file = Path("test_anonymized.md")
    anonymized_file.write_text(anonymized_content)

    # Create dummy mapping file
    mapping_content = {
        "PERSON_1": "John Doe",
        "LOCATION_1": "New York",
        "EMAIL_1": "john.doe@example.com",
        "PERSON_37": "Unused Person",
    }
    mapping_file = Path("test_mapping.json")
    mapping_file.write_text(json.dumps(mapping_content))

    # Run deanonymization
    deanonymized_output_file, stats_file = deanonymize_file(
        str(anonymized_file), str(mapping_file)
    )

    # Check deanonymized file
    expected_deanonymized_content = "Hello John Doe, welcome to New York. Your email is john.doe@example.com. We don't know about PERSON_4."
    with open(deanonymized_output_file, "r") as f:
        deanonymized_content = f.read()
    assert deanonymized_content == expected_deanonymized_content

    # Check stats file
    with open(stats_file, "r") as f:
        stats_content = json.load(f)

    assert stats_content["anonymized_file"] == str(anonymized_file)
    assert stats_content["mapping_file"] == str(mapping_file)
    assert stats_content["deanonymized_file"] == deanonymized_output_file
    assert sorted(stats_content["unused_mappings"]) == ["PERSON_37"]
    assert sorted(stats_content["not_found_mappings"]) == ["PERSON_4"]

    # Cleanup
    os.remove(anonymized_file)
    os.remove(mapping_file)
    os.remove(deanonymized_output_file)
    os.remove(stats_file)
