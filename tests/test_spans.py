"""Span-based replacement: longest interval wins, no overlap."""

from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.spans import (
    apply_spans,
    locate_spans,
    pick_non_overlapping,
    replace_entities,
)


def test_longer_span_wins_over_inner_name() -> None:
    text = "John Doe met John."
    spans = locate_spans(text, ["John Doe", "John"])
    kept = pick_non_overlapping(spans)
    mapping = {"John Doe": "PERSON_1", "John": "PERSON_1.v_1"}
    out = apply_spans(text, kept, mapping)
    assert out == "PERSON_1 met PERSON_1.v_1."


def test_word_boundary_skips_partial() -> None:
    text = "Johnson saw John."
    out = replace_entities(text, ["John"], {"John": "PERSON_1"})
    assert out == "Johnson saw PERSON_1."


def test_anonymize_uses_spans(mocker) -> None:
    mocker.patch("os.path.getsize", return_value=0)
    text = "John Doe and John went to Johnson."
    mocker.patch(
        "pdf_anonymizer_core.core.load_and_extract_text_from_file",
        return_value=(text, [text]),
    )
    mocker.patch(
        "pdf_anonymizer_core.core.identify_entities_with_llm",
        return_value=[
            {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
            {"text": "John", "type": "PERSON", "base_form": "John Doe"},
        ],
    )
    mocker.patch(
        "pdf_anonymizer_core.core.extract_entities_via_regex",
        return_value=[],
    )
    anonymized, _mapping = anonymize_file("dummy.pdf", 1000, "dummy", "dummy")
    assert "John Doe" not in anonymized
    assert "Johnson" in anonymized
    assert anonymized.startswith("PERSON_1")
