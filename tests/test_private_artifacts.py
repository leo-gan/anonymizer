"""Cache, output files, and purge stay owner-only."""

import stat

from pdf_anonymizer_cli.cli import app
from pdf_anonymizer_core.llm_provider import CACHE_TTL_SECONDS, LocalLLMCache
from pdf_anonymizer_core.purge import purge_local_artifacts
from typer.testing import CliRunner


def _mode(path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_cache_file_is_private_and_expires(tmp_path, monkeypatch) -> None:
    import pdf_anonymizer_core.llm_provider as llm

    now = 1_700_000_000.0
    monkeypatch.setattr(llm.time, "time", lambda: now)
    cache = LocalLLMCache(str(tmp_path), "llm_responses.json")
    cache.set("model", "prompt text", "secret-reply")
    cache.save()
    path = tmp_path / "llm_responses.json"
    assert _mode(path) == 0o600
    assert cache.get("model", "prompt text") == "secret-reply"
    assert LocalLLMCache._fresh_response("legacy-plain-string") is None

    monkeypatch.setattr(llm.time, "time", lambda: now + CACHE_TTL_SECONDS + 1)
    assert cache.get("model", "prompt text") is None


def test_anonymized_text_is_private(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "note.txt"
    source.write_text("Write to ada@example.com please.\n", encoding="utf-8")
    result = CliRunner().invoke(app, ["run", str(source), "--no-llm", "--no-ner"])
    assert result.exit_code == 0
    written = list((tmp_path / "data" / "anonymized").glob("*.anonymized.txt"))
    assert len(written) == 1
    assert _mode(written[0]) == 0o600
    assert "ada@example.com" not in written[0].read_text(encoding="utf-8")


def test_purge_removes_cache_maps_stats_and_log(tmp_path) -> None:
    cache = tmp_path / "data" / "cache"
    mappings = tmp_path / "data" / "mappings"
    stats = tmp_path / "data" / "stats"
    kept = tmp_path / "data" / "anonymized"
    for directory in (cache, mappings, stats, kept):
        directory.mkdir(parents=True)
    (cache / "llm_responses.json").write_text("{}", encoding="utf-8")
    (mappings / "note.mapping.json").write_text("{}", encoding="utf-8")
    (stats / "note.risk.json").write_text("{}", encoding="utf-8")
    (kept / "note.anonymized.md").write_text("kept", encoding="utf-8")
    (tmp_path / "app.log").write_text("log", encoding="utf-8")

    removed = purge_local_artifacts(tmp_path)
    assert len(removed) == 4
    assert not (cache / "llm_responses.json").exists()
    assert not (mappings / "note.mapping.json").exists()
    assert not (stats / "note.risk.json").exists()
    assert not (tmp_path / "app.log").exists()
    assert (kept / "note.anonymized.md").read_text(encoding="utf-8") == "kept"

    result = CliRunner().invoke(app, ["purge", "--root", str(tmp_path)])
    assert result.exit_code == 0
