"""Per-span score and recognizer source (item 21)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pdf_anonymizer_cli.cli import app
from pdf_anonymizer_core.call_llm import (
    IdentificationResult,
    identify_entities_with_llm,
)
from pdf_anonymizer_core.conf import DEFAULT_REGEX_PATTERNS
from pdf_anonymizer_core.core import anonymize_file, finalize_entities
from pdf_anonymizer_core.gazetteers import apply_deny_list
from pdf_anonymizer_core.regex_ner import extract_entities_via_regex

GOOD_IBAN = "DE89370400440532013000"
BAD_IBAN = "GB00WEST12345698765432"


class TestRegexScores:
    def test_verified_iban_scores_higher_than_like(self) -> None:
        entities = extract_entities_via_regex(
            f"Pay {GOOD_IBAN} or {BAD_IBAN}.",
            {"IBAN": DEFAULT_REGEX_PATTERNS["IBAN"]},
        )
        by_text = {item["text"]: item for item in entities}
        assert by_text[GOOD_IBAN]["type"] == "IBAN"
        assert by_text[BAD_IBAN]["type"] == "IBAN_LIKE"
        assert by_text[GOOD_IBAN]["source"] == "regex"
        assert by_text[BAD_IBAN]["source"] == "regex"
        assert by_text[GOOD_IBAN]["score"] > by_text[BAD_IBAN]["score"]
        assert by_text[GOOD_IBAN]["score"] >= 0.9
        assert by_text[BAD_IBAN]["score"] < 0.7

    def test_email_has_regex_source(self) -> None:
        entities = extract_entities_via_regex(
            "mail jane@acme.com",
            {"EMAIL": DEFAULT_REGEX_PATTERNS["EMAIL"]},
        )
        assert entities[0]["source"] == "regex"
        assert entities[0]["score"] == 0.85


class TestMinConfidence:
    def test_default_keeps_like_hits(self, tmp_path) -> None:
        src = tmp_path / "note.txt"
        src.write_text(f"Pay {GOOD_IBAN} or {BAD_IBAN}.", encoding="utf-8")
        _text, mapping = anonymize_file(
            str(src), 1000, "unused", "unused", use_llm=False
        )
        assert mapping is not None
        assert GOOD_IBAN in mapping
        assert BAD_IBAN in mapping

    def test_threshold_drops_like_keeps_verified(self, tmp_path) -> None:
        src = tmp_path / "note.txt"
        src.write_text(f"Pay {GOOD_IBAN} or {BAD_IBAN}.", encoding="utf-8")
        _text, mapping = anonymize_file(
            str(src),
            1000,
            "unused",
            "unused",
            use_llm=False,
            min_confidence=0.8,
        )
        assert mapping is not None
        assert GOOD_IBAN in mapping
        assert BAD_IBAN not in mapping

    def test_deny_list_survives_high_threshold(self) -> None:
        entities = apply_deny_list("hello Ada", [], ["Ada"])
        assert entities[0]["source"] == "deny-list"
        assert entities[0]["score"] == 1.0
        kept = finalize_entities(
            entities,
            "hello Ada",
            anonymized_entities=None,
            keep_list=None,
            deny_list=None,
            min_confidence=0.9,
        )
        assert kept[0]["text"] == "Ada"

    def test_deny_list_readds_dropped_like_hit(self, tmp_path) -> None:
        src = tmp_path / "note.txt"
        src.write_text(f"Pay {BAD_IBAN}.", encoding="utf-8")
        _text, mapping = anonymize_file(
            str(src),
            1000,
            "unused",
            "unused",
            use_llm=False,
            min_confidence=0.8,
            deny_list=[BAD_IBAN],
        )
        assert mapping is not None
        assert BAD_IBAN in mapping


class TestLlmSource:
    def test_llm_entities_get_source_and_score(self, mocker) -> None:
        mock_provider = mocker.Mock()
        mock_provider.call.return_value = IdentificationResult(
            entities=[{"text": "Jane Doe", "type": "PERSON"}]
        ).model_dump_json()
        mocker.patch(
            "pdf_anonymizer_core.call_llm.get_provider",
            return_value=mock_provider,
        )
        mocker.patch(
            "pdf_anonymizer_core.call_llm.get_provider_and_model_name",
            return_value=("google", "dummy"),
        )
        entities = identify_entities_with_llm("Jane Doe", "{text}", "dummy")
        assert entities[0]["source"] == "llm"
        assert entities[0]["score"] == 0.70
        assert entities[0]["base_form"] == "Jane Doe"


class TestCli:
    def test_min_confidence_flag(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "note.txt"
        src.write_text(f"Pay {GOOD_IBAN} or {BAD_IBAN}.", encoding="utf-8")
        result = CliRunner().invoke(
            app, ["run", str(src), "--no-llm", "--min-confidence", "0.8"]
        )
        assert result.exit_code == 0, result.output
        mapping = Path("data/mappings/note.mapping.json").read_text(encoding="utf-8")
        assert GOOD_IBAN in mapping
        assert BAD_IBAN not in mapping
