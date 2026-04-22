import json
import os
from pdf_anonymizer_core.utils import save_results

def test_save_results_pdf(tmp_path, monkeypatch):
    # Change to temp directory to avoid creating data/ in the repo
    monkeypatch.chdir(tmp_path)

    full_anonymized_text = "Anonymized text content"
    final_mapping = {"PERSON_1": "John Doe"}
    file_path = "test_document.pdf"

    anonymized_output_file, mapping_file = save_results(
        full_anonymized_text, final_mapping, file_path
    )

    # Check if directories were created
    assert os.path.exists("data/anonymized")
    assert os.path.exists("data/mappings")

    # Check if files were created with correct names and extensions
    expected_anonymized_file = "data/anonymized/test_document.anonymized.md"
    expected_mapping_file = "data/mappings/test_document.mapping.json"

    assert anonymized_output_file == expected_anonymized_file
    assert mapping_file == expected_mapping_file
    assert os.path.exists(expected_anonymized_file)
    assert os.path.exists(expected_mapping_file)

    # Check content of the anonymized file
    with open(expected_anonymized_file, "r", encoding="utf-8") as f:
        assert f.read() == full_anonymized_text

    # Check content of the mapping file
    with open(expected_mapping_file, "r", encoding="utf-8") as f:
        loaded_mapping = json.load(f)
        assert loaded_mapping == final_mapping

def test_save_results_txt(tmp_path, monkeypatch):
    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    full_anonymized_text = "Anonymized text content"
    final_mapping = {"PERSON_1": "John Doe"}
    file_path = "test_document.txt"

    anonymized_output_file, mapping_file = save_results(
        full_anonymized_text, final_mapping, file_path
    )

    # Check if file extension is preserved
    expected_anonymized_file = "data/anonymized/test_document.anonymized.txt"
    assert anonymized_output_file == expected_anonymized_file
    assert os.path.exists(expected_anonymized_file)
