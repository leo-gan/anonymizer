"""Apply leftover hits from a residual report (item 23)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from pdf_anonymizer_cli.cli import app
from pdf_anonymizer_core.apply_residuals import (
    NATIVE_PDF_APPLY_MESSAGE,
    apply_residual_hits,
    load_decision_list,
    select_residual_hits,
)
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.verify import verify_anonymized_text, write_residual_report

LEFTOVER = "leftover@example.com"


class TestSelectHits:
    def test_accept_all_except_skip(self) -> None:
        hits = [
            {"text": "a@x.com", "type": "EMAIL"},
            {"text": "b@x.com", "type": "EMAIL"},
        ]
        accepted, skipped = select_residual_hits(
            hits, accept_all=True, skip=["b@x.com"]
        )
        assert [h["text"] for h in accepted] == ["a@x.com"]
        assert [h["text"] for h in skipped] == ["b@x.com"]

    def test_accept_list_only(self) -> None:
        hits = [
            {"text": "a@x.com", "type": "EMAIL"},
            {"text": "b@x.com", "type": "EMAIL"},
        ]
        accepted, skipped = select_residual_hits(hits, accept=["a@x.com"])
        assert [h["text"] for h in accepted] == ["a@x.com"]
        assert [h["text"] for h in skipped] == ["b@x.com"]


class TestLoadDecisionList:
    def test_json_array(self, tmp_path) -> None:
        path = tmp_path / "accept.json"
        path.write_text(json.dumps([LEFTOVER]), encoding="utf-8")
        assert load_decision_list(str(path)) == [LEFTOVER]

    def test_one_per_line(self, tmp_path) -> None:
        path = tmp_path / "accept.txt"
        path.write_text(f"# comment\n{LEFTOVER}\n", encoding="utf-8")
        assert load_decision_list(str(path)) == [LEFTOVER]


class TestApplyResidualHits:
    def test_rewrites_text_and_updates_mapping(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        masked = tmp_path / "note.anonymized.md"
        masked.write_text(f"Write {LEFTOVER} and PERSON_1.\n", encoding="utf-8")
        result = apply_residual_hits(
            str(masked),
            [{"text": LEFTOVER, "type": "EMAIL", "base_form": LEFTOVER}],
            seed_mapping={"Ada": "PERSON_1"},
        )
        text = masked.read_text(encoding="utf-8")
        assert LEFTOVER not in text
        assert "EMAIL_1" in text
        assert result["rewritten"] is True
        mapping = json.loads((tmp_path / "data/mappings/note.mapping.json").read_text())
        assert mapping["EMAIL_1"] == LEFTOVER
        assert mapping["PERSON_1"] == "Ada"

    def test_rejects_native_pdf(self, tmp_path) -> None:
        pdf = tmp_path / "note.anonymized.pdf"
        pdf.write_bytes(b"%PDF-1.4")
        try:
            apply_residual_hits(str(pdf), [{"text": LEFTOVER, "type": "EMAIL"}])
        except ValueError as exc:
            assert str(exc) == NATIVE_PDF_APPLY_MESSAGE
        else:
            raise AssertionError("expected ValueError")


class TestCliApply:
    def test_accept_all_hides_leftover(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "note.txt"
        src.write_text(f"mail {LEFTOVER}", encoding="utf-8")
        _text, mapping = anonymize_file(
            str(src), 1000, "unused", "unused", use_llm=False
        )
        assert mapping is not None
        # Force a leftover the first pass would have hidden: write it back.
        out = Path("data/anonymized/note.anonymized.txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f"still {LEFTOVER} and PERSON_1", encoding="utf-8")
        report = verify_anonymized_text(
            out.read_text(encoding="utf-8"), anonymized_file=str(out)
        )
        report_path = write_residual_report(report, str(out))
        result = CliRunner().invoke(app, ["apply", report_path, "--accept-all"])
        assert result.exit_code == 0, result.output
        assert LEFTOVER not in out.read_text(encoding="utf-8")
        assert "EMAIL_" in out.read_text(encoding="utf-8")

    def test_run_apply_residuals(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "note.txt"
        # A name is missed on --no-llm, then apply-residuals cannot find it
        # (regex-only residual scan). Use a leftover the scan will see:
        # hide email first by writing a file that still contains a second email
        # after regex? Simpler: run with --no-llm on text that has only
        # leftover-shaped content if we inject after...
        # Use --apply-residuals on a file whose first pass misses nothing
        # extra, then a second leftover is not there.
        # Instead: text with a LIKE IBAN at min-confidence 0.8 so LIKE stays,
        # then apply-residuals hides it.
        good = "DE89370400440532013000"
        bad = "GB00WEST12345698765432"
        src.write_text(f"Pay {good} or {bad}.", encoding="utf-8")
        result = CliRunner().invoke(
            app,
            [
                "run",
                str(src),
                "--no-llm",
                "--min-confidence",
                "0.8",
                "--apply-residuals",
                "--no-risk",
            ],
        )
        assert result.exit_code == 0, result.output
        out = Path("data/anonymized/note.anonymized.txt").read_text(encoding="utf-8")
        assert good not in out
        assert bad not in out
        assert "IBAN_1" in out
        assert "IBAN_LIKE" in out

    def test_noninteractive_without_accept_fails(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        report = tmp_path / "note.residual_pii.json"
        masked = tmp_path / "note.anonymized.md"
        masked.write_text(f"mail {LEFTOVER}", encoding="utf-8")
        report.write_text(
            json.dumps(
                {
                    "anonymized_file": str(masked),
                    "regex_hits": [{"text": LEFTOVER, "type": "EMAIL"}],
                    "llm_hits": [],
                    "residual_count": 1,
                    "rewritten": False,
                }
            ),
            encoding="utf-8",
        )
        result = CliRunner().invoke(app, ["apply", str(report)])
        assert result.exit_code == 1
        assert LEFTOVER in masked.read_text(encoding="utf-8")
