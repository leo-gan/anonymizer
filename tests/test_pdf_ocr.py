"""OCR for scanned PDFs: loud fail, Tesseract gate, layout sidecar."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from pdf_anonymizer_cli.cli import app
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.load_and_extract import load_and_extract_text_from_file
from pdf_anonymizer_core.pdf_ocr import (
    OCR_EMPTY_MESSAGE,
    OCR_OFF_EMPTY_MESSAGE,
    TESSERACT_MISSING_MESSAGE,
    PdfWord,
    load_layout_sidecar,
    ocr_pdf,
    store_pdf_layout,
    take_pdf_layout,
    write_layout_sidecar,
)
from pdf_anonymizer_core.utils import save_results


def _blank_pdf(path: Path) -> Path:
    import pymupdf

    document = pymupdf.open()
    document.new_page(width=200, height=100)
    document.save(path)
    document.close()
    return path


def _text_pdf(path: Path, text: str = "Contact jane@acme.com") -> Path:
    import pymupdf

    document = pymupdf.open()
    page = document.new_page(width=400, height=200)
    page.insert_text((40, 80), text)
    document.save(path)
    document.close()
    return path


class TestLoudFail:
    def test_blank_pdf_without_ocr_raises(self, tmp_path) -> None:
        src = _blank_pdf(tmp_path / "scan.pdf")
        with pytest.raises(ValueError, match="no extractable text"):
            load_and_extract_text_from_file(str(src), 1000, 0, ocr=False)
        with pytest.raises(ValueError, match="no extractable text"):
            anonymize_file(str(src), 1000, "unused", "unused", use_llm=False)

    def test_cli_blank_pdf_exits_without_output(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = _blank_pdf(tmp_path / "scan.pdf")
        result = CliRunner().invoke(app, ["run", str(src), "--no-llm"])
        assert result.exit_code == 1
        assert (
            not list(Path("data/anonymized").glob("*"))
            if Path("data/anonymized").exists()
            else True
        )
        assert "Traceback" not in (result.output or "")

    def test_text_layer_pdf_still_extracts(self, tmp_path) -> None:
        src = _text_pdf(tmp_path / "letter.pdf")
        text, chunks = load_and_extract_text_from_file(str(src), 1000, 0, ocr=False)
        assert "jane@acme.com" in text
        assert chunks


class TestOcrGate:
    def test_ocr_without_tesseract_is_clear(self, tmp_path, monkeypatch) -> None:
        src = _blank_pdf(tmp_path / "scan.pdf")
        monkeypatch.setattr(
            "pdf_anonymizer_core.pdf_ocr.tesseract_available", lambda: False
        )
        with pytest.raises(ValueError, match="Tesseract"):
            load_and_extract_text_from_file(str(src), 1000, 0, ocr=True)
        assert TESSERACT_MISSING_MESSAGE

    def test_ocr_empty_after_engine_raises(self, tmp_path, monkeypatch) -> None:
        src = _blank_pdf(tmp_path / "scan.pdf")
        monkeypatch.setattr(
            "pdf_anonymizer_core.pdf_ocr.tesseract_available", lambda: True
        )
        monkeypatch.setattr(
            "pdf_anonymizer_core.load_and_extract.ocr_pdf",
            lambda path: ("", []),
        )
        with pytest.raises(ValueError, match="OCR ran and still found no text"):
            load_and_extract_text_from_file(str(src), 1000, 0, ocr=True)
        assert OCR_EMPTY_MESSAGE
        assert OCR_OFF_EMPTY_MESSAGE

    def test_ocr_text_is_used_and_layout_stashed(self, tmp_path, monkeypatch) -> None:
        src = _blank_pdf(tmp_path / "scan.pdf")
        words = [
            PdfWord(page=0, text="jane@acme.com", x0=10, y0=10, x1=80, y1=20),
        ]
        monkeypatch.setattr(
            "pdf_anonymizer_core.pdf_ocr.tesseract_available", lambda: True
        )
        monkeypatch.setattr(
            "pdf_anonymizer_core.load_and_extract.ocr_pdf",
            lambda path: ("Contact jane@acme.com", words),
        )
        text, chunks = load_and_extract_text_from_file(str(src), 1000, 0, ocr=True)
        assert "jane@acme.com" in text
        assert chunks
        source, stored = take_pdf_layout()
        assert source == str(src)
        assert stored == words


class TestLayoutSidecar:
    def test_save_results_writes_layout_next_to_markdown(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        src = _text_pdf(tmp_path / "letter.pdf")
        words = [PdfWord(page=0, text="jane@acme.com", x0=1, y0=2, x1=3, y1=4)]
        store_pdf_layout(str(src), words)
        out, _mapping = save_results(
            "Contact EMAIL_1",
            {"EMAIL_1": "jane@acme.com"},
            str(src),
        )
        layout = Path(out).with_suffix(".layout.json")
        assert layout.is_file()
        loaded = load_layout_sidecar(str(layout))
        assert loaded == words
        assert write_layout_sidecar(out, str(src), words) == str(layout)


class TestOcrPdfWords:
    def test_ocr_pdf_reads_word_boxes(self, tmp_path, monkeypatch) -> None:
        src = _blank_pdf(tmp_path / "scan.pdf")
        monkeypatch.setattr(
            "pdf_anonymizer_core.pdf_ocr.tesseract_available", lambda: True
        )

        class FakePage:
            def get_textpage_ocr(self, **_kwargs):
                return object()

            def get_text(self, mode, textpage=None):
                assert mode == "words"
                return [(10.0, 11.0, 40.0, 20.0, "Ada", 0, 0, 0)]

        class FakeDoc:
            def __iter__(self):
                return iter([FakePage()])

            def close(self):
                return None

        monkeypatch.setattr("pymupdf.open", lambda path: FakeDoc())
        text, words = ocr_pdf(str(src))
        assert text == "Ada"
        assert words == [PdfWord(page=0, text="Ada", x0=10, y0=11, x1=40, y1=20)]
