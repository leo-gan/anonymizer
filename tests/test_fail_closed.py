"""A failed language-model call must not look like a finished anonymization."""

import logging

from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_cli.cli import app
from typer.testing import CliRunner


def test_log_file_omits_document_text(tmp_path) -> None:
    sentence = "ZephyrQuillock sat in the margin of the page."
    source = tmp_path / "note.txt"
    source.write_text(sentence, encoding="utf-8")
    log_path = tmp_path / "app.log"
    root = logging.getLogger()
    previous = root.level
    root.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    root.addHandler(handler)
    try:
        anonymize_file(
            file_path=str(source),
            characters_to_anonymize=1000,
            prompt_template="{text}",
            model_name="none",
            use_llm=False,
        )
    finally:
        handler.close()
        root.removeHandler(handler)
        root.setLevel(previous)

    recorded = log_path.read_text(encoding="utf-8")
    assert "ZephyrQuillock" not in recorded
    assert "Extracted text pages: 1" in recorded


def test_cli_stops_when_the_model_rejects_the_key(tmp_path, monkeypatch, caplog) -> None:
    source = tmp_path / "note.txt"
    sentence = "Ada Lovelace lives on State Street."
    source.write_text(sentence, encoding="utf-8")

    class Rejected:
        def call(self, *args, **kwargs):
            raise RuntimeError("401 unauthorized")

    monkeypatch.setattr(
        "pdf_anonymizer_core.call_llm.get_provider",
        lambda _name: Rejected(),
    )
    with caplog.at_level(logging.ERROR):
        result = CliRunner().invoke(app, ["run", str(source), "--no-ner"])
    assert result.exit_code == 1
    assert "AUTHENTICATION_ERROR" in caplog.text
    assert sentence not in caplog.text
