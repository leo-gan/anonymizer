"""Keep-list and deny-list gazetteers."""

from pathlib import Path

from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.gazetteers import (
    apply_deny_list,
    apply_keep_list,
    load_phrase_list,
)


def test_load_phrase_list_skips_comments(tmp_path: Path) -> None:
    path = tmp_path / "keep.txt"
    path.write_text("# comment\nApple\n\nAcme Inc.\n", encoding="utf-8")
    assert load_phrase_list(str(path)) == ["Apple", "Acme Inc."]


def test_keep_list_drops_matching_entity() -> None:
    entities = [
        {"text": "Apple", "type": "ORGANIZATION", "base_form": "Apple"},
        {"text": "Ada", "type": "PERSON", "base_form": "Ada"},
    ]
    kept = apply_keep_list(entities, ["apple"])
    assert [e["text"] for e in kept] == ["Ada"]


def test_deny_list_adds_missing_phrase() -> None:
    text = "Please call the night desk at Acme."
    entities = [{"text": "Ada", "type": "PERSON", "base_form": "Ada"}]
    out = apply_deny_list(text, entities, ["acme"])
    assert any(e["text"] == "Acme" and e["type"] == "CUSTOM" for e in out)


def test_keep_wins_over_deny() -> None:
    text = "Apple released a new phone."
    entities = [{"text": "Apple", "type": "ORGANIZATION", "base_form": "Apple"}]
    with_deny = apply_deny_list(text, entities, ["Apple"])
    kept = apply_keep_list(with_deny, ["Apple"])
    assert kept == []


def test_anonymize_respects_keep_and_deny(mocker) -> None:
    mocker.patch("os.path.getsize", return_value=0)
    text = "Ada met Apple in Boston."
    mocker.patch(
        "pdf_anonymizer_core.core.load_and_extract_text_from_file",
        return_value=(text, [text]),
    )
    mocker.patch(
        "pdf_anonymizer_core.core.identify_entities_with_llm",
        return_value=[
            {"text": "Ada", "type": "PERSON", "base_form": "Ada"},
            {"text": "Apple", "type": "ORGANIZATION", "base_form": "Apple"},
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
        keep_list=["Apple"],
        deny_list=["Boston"],
    )
    assert "Ada" not in anonymized
    assert "Apple" in anonymized
    assert "Boston" not in anonymized
    assert "PERSON_1" in anonymized
    assert mapping.get("Boston") == "CUSTOM_1"
    assert "Apple" not in mapping
