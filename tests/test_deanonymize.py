import json
from pathlib import Path

from pdf_anonymizer_core.utils import deanonymize_file


def test_deanonymize_file(tmp_path: Path):
    # Create dummy anonymized file in temp dir
    anonymized_content = (
        "Hello PERSON_1, welcome to LOCATION_1. Your email is EMAIL_1. "
        "We don't know about PERSON_4."
    )
    anonymized_file = tmp_path / "test_anonymized.md"
    anonymized_file.write_text(anonymized_content, encoding="utf-8")

    # Create dummy mapping file (placeholder -> original)
    mapping_content = {
        "PERSON_1": "John Doe",
        "LOCATION_1": "New York",
        "EMAIL_1": "john.doe@example.com",
        "PERSON_37": "Unused Person",
        # PERSON_4 intentionally missing
    }
    mapping_file = tmp_path / "test_mapping.json"
    mapping_file.write_text(json.dumps(mapping_content), encoding="utf-8")

    # Run deanonymization
    deanonymized_output_file, stats_file = deanonymize_file(
        str(anonymized_file), str(mapping_file)
    )

    # Check deanonymized file
    expected_deanonymized_content = (
        "Hello John Doe, welcome to New York. "
        "Your email is john.doe@example.com. We don't know about PERSON_4."
    )
    deanonymized_content = Path(deanonymized_output_file).read_text(encoding="utf-8")
    assert deanonymized_content == expected_deanonymized_content

    # Check stats file
    stats_content = json.loads(Path(stats_file).read_text(encoding="utf-8"))

    assert stats_content["anonymized_file"] == str(anonymized_file)
    assert stats_content["mapping_file"] == str(mapping_file)
    assert stats_content["deanonymized_file"] == deanonymized_output_file
    assert stats_content["unused_mappings"] == ["PERSON_37"]
    assert stats_content["not_found_mappings"] == ["PERSON_4"]
