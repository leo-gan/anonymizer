"""Optional local span NER (GLiNER extra)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from pdf_anonymizer_cli.cli import app
from pdf_anonymizer_core.conf import ConfigProfile, get_config_for_profile
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.span_ner import (
    NER_EXTRA_MESSAGE,
    extract_entities_via_ner,
    ner_available,
    resolve_semantic_stages,
)


class TestResolveStages:
    def test_default_without_extra_keeps_llm(self, monkeypatch) -> None:
        monkeypatch.setattr("pdf_anonymizer_core.span_ner.ner_available", lambda: False)
        run_ner, run_llm = resolve_semantic_stages(
            use_llm=True, use_ner=None, replace_llm_when_ner=True
        )
        assert run_ner is False
        assert run_llm is True

    def test_auto_with_extra_replaces_llm_on_speed(self, monkeypatch) -> None:
        monkeypatch.setattr("pdf_anonymizer_core.span_ner.ner_available", lambda: True)
        run_ner, run_llm = resolve_semantic_stages(
            use_llm=True, use_ner=None, replace_llm_when_ner=True
        )
        assert run_ner is True
        assert run_llm is False

    def test_auto_with_extra_keeps_llm_on_quality(self, monkeypatch) -> None:
        monkeypatch.setattr("pdf_anonymizer_core.span_ner.ner_available", lambda: True)
        run_ner, run_llm = resolve_semantic_stages(
            use_llm=True, use_ner=None, replace_llm_when_ner=False
        )
        assert run_ner is True
        assert run_llm is True

    def test_regex_only_auto_skips_ner(self, monkeypatch) -> None:
        monkeypatch.setattr("pdf_anonymizer_core.span_ner.ner_available", lambda: True)
        run_ner, run_llm = resolve_semantic_stages(
            use_llm=False, use_ner=None, replace_llm_when_ner=True
        )
        assert run_ner is False
        assert run_llm is False

    def test_explicit_ner_without_extra_raises(self, monkeypatch) -> None:
        monkeypatch.setattr("pdf_anonymizer_core.span_ner.ner_available", lambda: False)
        with pytest.raises(ValueError, match=r"pdf-anonymizer-core\[ner\]"):
            resolve_semantic_stages(
                use_llm=True, use_ner=True, replace_llm_when_ner=True
            )
        assert NER_EXTRA_MESSAGE


class TestExtractNer:
    def test_missing_extra_raises(self, monkeypatch) -> None:
        monkeypatch.setattr("pdf_anonymizer_core.span_ner.ner_available", lambda: False)
        with pytest.raises(ValueError, match="ner"):
            extract_entities_via_ner("Jane Doe works at Acme.")

    def test_predict_entities_are_mapped(self, monkeypatch) -> None:
        monkeypatch.setattr("pdf_anonymizer_core.span_ner.ner_available", lambda: True)

        class FakeModel:
            def predict_entities(self, text, labels):
                assert "person" in labels
                return [
                    {"text": "Jane Doe", "label": "person", "start": 0, "end": 8},
                    {"text": "Acme", "label": "organization", "start": 18, "end": 22},
                ]

        monkeypatch.setattr(
            "pdf_anonymizer_core.span_ner._load_model", lambda name: FakeModel()
        )
        entities = extract_entities_via_ner("Jane Doe works at Acme.")
        types = {item["type"]: item["text"] for item in entities}
        assert types["PERSON"] == "Jane Doe"
        assert types["ORGANIZATION"] == "Acme"


class TestAnonymizeFileNer:
    def test_sdk_default_does_not_call_ner(self, mocker, tmp_path) -> None:
        src = tmp_path / "note.txt"
        src.write_text("Contact Jane Doe at jane@acme.com", encoding="utf-8")
        ner = mocker.patch(
            "pdf_anonymizer_core.core.extract_entities_via_ner",
            return_value=[
                {"text": "Jane Doe", "type": "PERSON", "base_form": "Jane Doe"}
            ],
        )
        mocker.patch(
            "pdf_anonymizer_core.core.identify_entities_with_llm",
            return_value=[],
        )
        text, mapping = anonymize_file(
            str(src), 1000, "unused", "unused", use_llm=False
        )
        ner.assert_not_called()
        assert mapping is not None
        assert "jane@acme.com" in mapping
        assert "Jane Doe" not in (mapping or {})

    def test_use_ner_masks_names_without_llm(self, mocker, tmp_path) -> None:
        src = tmp_path / "note.txt"
        src.write_text("Contact Jane Doe at jane@acme.com", encoding="utf-8")
        mocker.patch(
            "pdf_anonymizer_core.core.extract_entities_via_ner",
            return_value=[
                {"text": "Jane Doe", "type": "PERSON", "base_form": "Jane Doe"}
            ],
        )
        llm = mocker.patch(
            "pdf_anonymizer_core.core.identify_entities_with_llm",
            return_value=[],
        )
        text, mapping = anonymize_file(
            str(src), 1000, "unused", "unused", use_llm=False, use_ner=True
        )
        llm.assert_not_called()
        assert mapping is not None
        assert mapping["Jane Doe"].startswith("PERSON_")
        assert "Jane Doe" not in (text or "")


class TestCliNer:
    def test_explicit_ner_without_extra_exits(
        self, tmp_path, monkeypatch, mocker
    ) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "note.txt"
        src.write_text("hello jane@acme.com", encoding="utf-8")
        mocker.patch(
            "pdf_anonymizer_cli.cli.resolve_semantic_stages",
            side_effect=ValueError(NER_EXTRA_MESSAGE),
        )
        result = CliRunner().invoke(app, ["run", str(src), "--ner", "--no-llm"])
        assert result.exit_code == 1
        assert "Traceback" not in (result.output or "")


def test_default_profile_still_uses_llm_without_extra() -> None:
    cfg = get_config_for_profile(ConfigProfile.BEST_SPEED)
    assert cfg.use_llm is True


def test_gitignore_lists_tool_caches() -> None:
    text = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(
        encoding="utf-8"
    )
    assert ".hypothesis/" in text
    assert ".pytest_cache/" in text
    assert ".ruff_cache/" in text
    assert ner_available() in (True, False)
