"""Value-level encrypt operator (item 24)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pdf_anonymizer_cli.cli import app
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.operators import (
    ENCRYPT_PREFIX,
    decrypt_value,
    encrypt_value,
    looks_like_encrypt_token,
    mapping_without_encrypt_plaintexts,
    parse_operator_specs,
    restore_encrypt_tokens,
)
from pdf_anonymizer_core.utils import deanonymize_file

SECRET = "test-encrypt-secret"
EMAIL = "ada@example.com"


class TestEncryptRoundTrip:
    def test_stable_and_reversible(self) -> None:
        a = encrypt_value(EMAIL, SECRET)
        b = encrypt_value(EMAIL, SECRET)
        assert a == b
        assert a.startswith(ENCRYPT_PREFIX)
        assert looks_like_encrypt_token(a)
        assert decrypt_value(a, SECRET) == EMAIL
        assert encrypt_value("other@x.com", SECRET) != a

    def test_requires_secret(self) -> None:
        with pytest.raises(ValueError, match="encrypt-secret"):
            encrypt_value(EMAIL, "")

    def test_wrong_secret_stays_in_restore(self) -> None:
        token = encrypt_value(EMAIL, SECRET)
        text = f"Write {token}."
        assert EMAIL not in restore_encrypt_tokens(text, "other-secret")
        assert EMAIL in restore_encrypt_tokens(text, SECRET)

    def test_mapping_omits_encrypt_plaintexts(self) -> None:
        token = encrypt_value(EMAIL, SECRET)
        cleaned = mapping_without_encrypt_plaintexts({token: EMAIL, "PERSON_1": "Ada"})
        assert cleaned == {"PERSON_1": "Ada"}


class TestParseEncrypt:
    def test_accepts_encrypt(self) -> None:
        assert parse_operator_specs(["EMAIL=encrypt"]) == {"EMAIL": "encrypt"}


class TestAnonymizeEncrypt:
    def test_file_round_trip_without_plaintext_in_map(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "note.txt"
        src.write_text(f"mail {EMAIL}", encoding="utf-8")
        anonymized, mapping = anonymize_file(
            str(src),
            1000,
            "unused",
            "unused",
            use_llm=False,
            operators={"EMAIL": "encrypt"},
            encrypt_secret=SECRET,
        )
        assert anonymized is not None
        assert mapping is not None
        assert EMAIL not in anonymized
        assert ENCRYPT_PREFIX in anonymized
        assert mapping[EMAIL].startswith(ENCRYPT_PREFIX)

        from pdf_anonymizer_core.utils import save_results

        out, map_path = save_results(
            anonymized, {v: k for k, v in mapping.items()}, str(src)
        )
        stored = json.loads(Path(map_path).read_text(encoding="utf-8"))
        assert EMAIL not in stored
        assert EMAIL not in json.dumps(stored)

        restored, _stats = deanonymize_file(out, map_path, encrypt_secret=SECRET)
        assert EMAIL in Path(restored).read_text(encoding="utf-8")


class TestCliEncrypt:
    def test_run_and_deanonymize(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "note.txt"
        src.write_text(f"mail {EMAIL}", encoding="utf-8")
        run = CliRunner().invoke(
            app,
            [
                "run",
                str(src),
                "--no-llm",
                "--no-risk",
                "--operator",
                "EMAIL=encrypt",
                "--encrypt-secret",
                SECRET,
            ],
        )
        assert run.exit_code == 0, run.output
        masked = Path("data/anonymized/note.anonymized.txt").read_text(encoding="utf-8")
        assert EMAIL not in masked
        assert ENCRYPT_PREFIX in masked
        mapping = json.loads(Path("data/mappings/note.mapping.json").read_text())
        assert EMAIL not in json.dumps(mapping)

        back = CliRunner().invoke(
            app,
            [
                "deanonymize",
                "data/anonymized/note.anonymized.txt",
                "data/mappings/note.mapping.json",
                "--encrypt-secret",
                SECRET,
            ],
        )
        assert back.exit_code == 0, back.output
        text = Path("data/deanonymized/note.deanonymized.txt").read_text(
            encoding="utf-8"
        )
        assert EMAIL in text

    def test_encrypt_without_secret_fails(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "note.txt"
        src.write_text(f"mail {EMAIL}", encoding="utf-8")
        result = CliRunner().invoke(
            app, ["run", str(src), "--no-llm", "--operator", "EMAIL=encrypt"]
        )
        assert result.exit_code == 1
