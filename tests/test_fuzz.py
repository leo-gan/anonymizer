"""Hypothesis fuzz for regex NER, mapping envelopes, and loaders."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from pdf_anonymizer_core.conf import DEFAULT_REGEX_PATTERNS
from pdf_anonymizer_core.load_and_extract import load_and_extract_text_from_file
from pdf_anonymizer_core.mapping_crypto import decrypt_mapping, validate_envelope
from pdf_anonymizer_core.regex_ner import extract_entities_via_regex
from pdf_anonymizer_core.tables import load_csv, load_table
from pdf_anonymizer_core.word import load_docx

_FUZZ = settings(max_examples=40, deadline=2000)


@_FUZZ
@given(st.text(max_size=400))
def test_regex_ner_returns_well_formed_spans(text: str) -> None:
    entities = extract_entities_via_regex(text, DEFAULT_REGEX_PATTERNS)
    assert isinstance(entities, list)
    for entity in entities:
        assert entity["text"]
        assert entity["type"]
        start = entity["start"]
        end = entity["end"]
        assert 0 <= start < end <= len(text)
        assert text[start:end] == entity["text"]


@_FUZZ
@given(
    st.recursive(
        st.none() | st.booleans() | st.integers() | st.text(max_size=40),
        lambda children: st.lists(children, max_size=4)
        | st.dictionaries(st.text(max_size=16), children, max_size=8),
        max_leaves=12,
    )
)
def test_validate_envelope_never_hangs_or_crashes(payload: object) -> None:
    try:
        validate_envelope(payload)
    except ValueError:
        return


@_FUZZ
@given(st.dictionaries(st.text(max_size=20), st.text(max_size=40), max_size=8))
def test_decrypt_garbage_mapping_raises(payload: dict) -> None:
    with pytest.raises(ValueError):
        decrypt_mapping(payload, "passphrase")


@_FUZZ
@given(st.binary(max_size=2048))
def test_malformed_pdf_does_not_succeed_empty(data: bytes) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fuzz.pdf"
        path.write_bytes(data)
        try:
            text, chunks = load_and_extract_text_from_file(str(path), 1000, 0)
        except (ValueError, OSError, RuntimeError):
            return
        except Exception as exc:
            if type(exc).__name__ in {
                "FileDataError",
                "EmptyFileError",
                "FzErrorFormat",
            }:
                return
            raise
        assert (text or "").strip() != "" or chunks


@_FUZZ
@given(st.binary(max_size=2048))
def test_csv_loader_does_not_hang(data: bytes) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fuzz.csv"
        path.write_bytes(data)
        try:
            document = load_csv(str(path))
        except (ValueError, UnicodeError, OSError):
            return
        assert document.kind == "csv"
        load_table(str(path))


@_FUZZ
@given(st.binary(max_size=2048))
def test_docx_loader_does_not_hang(data: bytes) -> None:
    pytest.importorskip("docx")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fuzz.docx"
        path.write_bytes(data)
        try:
            document = load_docx(str(path))
        except (ValueError, OSError):
            return
        assert document.kind == "docx"


def test_zero_page_pdf_is_not_success(tmp_path: Path) -> None:
    path = tmp_path / "empty_pages.pdf"
    path.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n")
    with pytest.raises(ValueError, match="no pages|not readable|empty"):
        load_and_extract_text_from_file(str(path), 1000, 0)
