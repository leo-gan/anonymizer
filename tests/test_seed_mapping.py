"""Cross-document placeholder seeding."""

import json
from pathlib import Path

from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.mapping_crypto import encrypt_mapping
from pdf_anonymizer_core.utils import load_seed_mapping, seed_placeholder_state


def test_seed_state_reads_counts_and_variations() -> None:
    orig_to_written = {
        "Ada Lovelace": "PERSON_1",
        "Ada": "PERSON_1.v_1",
        "Acme Inc.": "ORGANIZATION_3",
    }
    mapping, bases, counts, variations = seed_placeholder_state(orig_to_written)
    assert mapping["Ada Lovelace"] == "PERSON_1"
    assert bases["Ada Lovelace"] == "PERSON_1"
    assert counts["PERSON"] == 1
    assert counts["ORGANIZATION"] == 3
    assert variations["PERSON_1"] == 1


def test_load_seed_mapping_accepts_placeholder_to_original(tmp_path: Path) -> None:
    path = tmp_path / "m.json"
    path.write_text(json.dumps({"PERSON_1": "Ada Lovelace"}), encoding="utf-8")
    loaded = load_seed_mapping(str(path))
    assert loaded == {"Ada Lovelace": "PERSON_1"}


def test_load_seed_mapping_encrypted(tmp_path: Path) -> None:
    path = tmp_path / "m.json.enc"
    path.write_text(
        json.dumps(encrypt_mapping({"PERSON_1": "Ada Lovelace"}, "secret")),
        encoding="utf-8",
    )
    loaded = load_seed_mapping(str(path), "secret")
    assert loaded == {"Ada Lovelace": "PERSON_1"}


def test_second_file_reuses_person_1(mocker) -> None:
    mocker.patch("os.path.getsize", return_value=0)
    text = "Ada Lovelace met Jane Smith."
    mocker.patch(
        "pdf_anonymizer_core.core.load_and_extract_text_from_file",
        return_value=(text, [text]),
    )
    mocker.patch(
        "pdf_anonymizer_core.core.identify_entities_with_llm",
        return_value=[
            {"text": "Ada Lovelace", "type": "PERSON", "base_form": "Ada Lovelace"},
            {"text": "Jane Smith", "type": "PERSON", "base_form": "Jane Smith"},
        ],
    )
    mocker.patch(
        "pdf_anonymizer_core.core.extract_entities_via_regex",
        return_value=[],
    )
    anonymized, mapping = anonymize_file(
        "dummy.pdf",
        1000,
        "dummy",
        "dummy",
        seed_mapping={"Ada Lovelace": "PERSON_1"},
    )
    assert mapping["Ada Lovelace"] == "PERSON_1"
    assert mapping["Jane Smith"] == "PERSON_2"
    assert anonymized == "PERSON_1 met PERSON_2."
