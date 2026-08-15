"""Residual-PII scan: report leftovers, never rewrite."""

from pathlib import Path

from pdf_anonymizer_core.utils import looks_like_placeholder
from pdf_anonymizer_core.verify import (
    scan_residual_regex,
    verify_anonymized_text,
    write_residual_report,
)


class TestLooksLikePlaceholder:
    def test_typed_and_like_and_variation(self) -> None:
        assert looks_like_placeholder("PERSON_1")
        assert looks_like_placeholder("IBAN_LIKE_2")
        assert looks_like_placeholder("ORGANIZATION_3.v_1")
        assert not looks_like_placeholder("alice@example.com")
        assert not looks_like_placeholder("DE89370400440532013000")


class TestScanResidualRegex:
    def test_finds_leftover_email_and_ignores_placeholders(self) -> None:
        text = (
            "Write PERSON_1 at leftover@example.com or use EMAIL_1. "
            "IBAN_LIKE_1 is already masked."
        )
        hits = scan_residual_regex(text)
        emails = [h for h in hits if h["type"] == "EMAIL"]
        assert any(h["text"] == "leftover@example.com" for h in emails)
        assert not any(looks_like_placeholder(h["text"]) for h in hits)

    def test_finds_mistyped_iban_left_in_clear(self) -> None:
        text = "Please pay GB00WEST12345698765432"
        hits = scan_residual_regex(text)
        types = {h["type"] for h in hits}
        texts = {h["text"] for h in hits}
        assert "GB00WEST12345698765432" in texts
        assert "IBAN_LIKE" in types or "IBAN" in types


class TestVerifyReport:
    def test_report_does_not_rewrite_and_writes_json(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        text = "Contact leftover@example.com and PERSON_1"
        report = verify_anonymized_text(text, anonymized_file="note.anonymized.md")
        assert report["rewritten"] is False
        assert report["residual_count"] >= 1
        assert any(h["text"] == "leftover@example.com" for h in report["regex_hits"])
        assert report["llm_hits"] == []

        out = write_residual_report(report, "data/anonymized/note.anonymized.md")
        path = Path(out)
        assert path.name == "note.residual_pii.json"
        assert path.is_file()
        assert "leftover@example.com" in path.read_text(encoding="utf-8")
