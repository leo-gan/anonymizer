"""Native PDF write: reversible placeholders, irreversible redact, sanitize."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from pdf_anonymizer_cli.cli import app
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.pdf_output import (
    OUTPUT_PDF_NOT_PDF_MESSAGE,
    write_anonymized_pdf,
)
from pdf_anonymizer_core.utils import deanonymize_file, save_results


def _pdf_text(path: Path) -> str:
    import pymupdf

    document = pymupdf.open(path)
    try:
        return "\n".join(page.get_text() or "" for page in document)
    finally:
        document.close()


def _pdf_meta(path: Path) -> dict:
    import pymupdf

    document = pymupdf.open(path)
    try:
        return dict(document.metadata or {})
    finally:
        document.close()


def _make_letter(path: Path) -> Path:
    import pymupdf

    document = pymupdf.open()
    page = document.new_page(width=400, height=200)
    page.insert_text((40, 80), "Contact jane@acme.com today.")
    document.set_metadata({"author": "Jane Doe", "title": "Secret letter"})
    document.embfile_add("note.txt", b"hidden jane@acme.com")
    document.save(path)
    document.close()
    return path


class TestNativePdfWrite:
    def test_replaces_text_and_wipes_metadata(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = _make_letter(tmp_path / "letter.pdf")
        review, mapping = anonymize_file(
            str(src), 1000, "unused", "unused", use_llm=False
        )
        assert mapping is not None
        assert "jane@acme.com" in mapping
        out, mapping_path = save_results(
            review or "",
            {written: original for original, written in mapping.items()},
            str(src),
            orig_to_written=mapping,
            output_pdf=True,
        )
        assert out.endswith(".anonymized.pdf")
        assert Path(out).is_file()
        assert Path("data/anonymized/letter.anonymized.md").is_file()
        text = _pdf_text(Path(out))
        assert "jane@acme.com" not in text
        assert "EMAIL_" in text
        meta = _pdf_meta(Path(out))
        assert not (meta.get("author") or "").strip()
        assert not (meta.get("title") or "").strip()

        import pymupdf

        opened = pymupdf.open(out)
        try:
            assert opened.embfile_count() == 0
        finally:
            opened.close()

        restored, _stats = deanonymize_file(out, mapping_path)
        assert restored.endswith(".deanonymized.pdf")
        assert "jane@acme.com" in _pdf_text(Path(restored))

    def test_redact_is_irreversible(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = _make_letter(tmp_path / "letter.pdf")
        review, mapping = anonymize_file(
            str(src), 1000, "unused", "unused", use_llm=False
        )
        out, mapping_path = save_results(
            review or "",
            {written: original for original, written in mapping.items()},
            str(src),
            orig_to_written=mapping,
            redact=True,
        )
        text = _pdf_text(Path(out))
        assert "jane@acme.com" not in text
        assert "EMAIL_" not in text
        restored, _stats = deanonymize_file(out, mapping_path)
        assert "jane@acme.com" not in _pdf_text(Path(restored))

    def test_output_pdf_rejects_non_pdf(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "note.txt"
        src.write_text("jane@acme.com", encoding="utf-8")
        with pytest.raises(ValueError, match="only applies to PDF"):
            save_results(
                "EMAIL_1",
                {"EMAIL_1": "jane@acme.com"},
                str(src),
                output_pdf=True,
            )
        assert OUTPUT_PDF_NOT_PDF_MESSAGE


class TestNativePdfCli:
    def test_run_output_pdf(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = _make_letter(tmp_path / "letter.pdf")
        result = CliRunner().invoke(app, ["run", str(src), "--no-llm", "--output-pdf"])
        assert result.exit_code == 0, result.output
        out = Path("data/anonymized/letter.anonymized.pdf")
        assert out.is_file()
        assert "jane@acme.com" not in _pdf_text(out)

    def test_output_pdf_on_txt_exits(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "note.txt"
        src.write_text("hello jane@acme.com", encoding="utf-8")
        result = CliRunner().invoke(app, ["run", str(src), "--no-llm", "--output-pdf"])
        assert result.exit_code == 1
        assert "Traceback" not in (result.output or "")


def test_write_anonymized_pdf_direct(tmp_path) -> None:
    src = _make_letter(tmp_path / "letter.pdf")
    dest = tmp_path / "out.pdf"
    write_anonymized_pdf(
        str(src),
        str(dest),
        {"jane@acme.com": "EMAIL_1"},
        ["jane@acme.com"],
        redact=False,
    )
    assert "EMAIL_1" in _pdf_text(dest)
    assert "jane@acme.com" not in _pdf_text(dest)
