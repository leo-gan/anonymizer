"""Encrypted mapping files (AES-256-GCM)."""

import json
from pathlib import Path

import pytest

from pdf_anonymizer_core.mapping_crypto import (
    decrypt_mapping,
    encrypt_mapping,
    is_encrypted_mapping,
    load_mapping_payload,
    resolve_mapping_passphrase,
)
from pdf_anonymizer_core.utils import deanonymize_file, save_results


class TestEncryptDecrypt:
    def test_round_trip(self) -> None:
        mapping = {"PERSON_1": "Ada Lovelace", "EMAIL_1": "ada@example.com"}
        envelope = encrypt_mapping(mapping, "correct horse")
        assert is_encrypted_mapping(envelope)
        assert "Ada" not in json.dumps(envelope)
        assert decrypt_mapping(envelope, "correct horse") == mapping

    def test_wrong_passphrase_fails(self) -> None:
        envelope = encrypt_mapping({"PERSON_1": "Ada"}, "secret")
        with pytest.raises(ValueError, match="decrypt"):
            decrypt_mapping(envelope, "wrong")

    def test_empty_passphrase_rejected(self) -> None:
        with pytest.raises(ValueError, match="passphrase"):
            encrypt_mapping({"PERSON_1": "Ada"}, "")

    def test_plaintext_payload_loads_without_key(self) -> None:
        raw = {"PERSON_1": "Ada"}
        assert load_mapping_payload(raw, None) == raw

    def test_encrypted_payload_requires_key(self) -> None:
        envelope = encrypt_mapping({"PERSON_1": "Ada"}, "secret")
        with pytest.raises(ValueError, match="encrypted"):
            load_mapping_payload(envelope, None)

    def test_resolve_passphrase_flag_beats_env(self, monkeypatch) -> None:
        monkeypatch.setenv("ANONYMIZER_MAPPING_KEY", "from-env")
        assert resolve_mapping_passphrase("from-flag") == "from-flag"
        assert resolve_mapping_passphrase(None) == "from-env"
        monkeypatch.delenv("ANONYMIZER_MAPPING_KEY")
        assert resolve_mapping_passphrase(None) is None


class TestSaveAndDeanonymizeEncrypted:
    def test_save_results_writes_enc_not_json(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "note.txt"
        src.write_text("hi", encoding="utf-8")
        _anon, mapping_path = save_results(
            "hello PERSON_1",
            {"PERSON_1": "Ada"},
            str(src),
            mapping_passphrase="secret",
        )
        assert mapping_path.endswith(".mapping.json.enc")
        assert Path(mapping_path).is_file()
        assert not (tmp_path / "data/mappings/note.mapping.json").exists()
        payload = json.loads(Path(mapping_path).read_text(encoding="utf-8"))
        assert is_encrypted_mapping(payload)

    def test_deanonymize_encrypted_mapping(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        anon = tmp_path / "note.anonymized.md"
        anon.write_text("Hello PERSON_1", encoding="utf-8")
        envelope = encrypt_mapping({"PERSON_1": "Ada Lovelace"}, "secret")
        mapping = tmp_path / "note.mapping.json.enc"
        mapping.write_text(json.dumps(envelope), encoding="utf-8")

        out, _stats = deanonymize_file(str(anon), str(mapping), mapping_passphrase="secret")
        assert Path(out).read_text(encoding="utf-8") == "Hello Ada Lovelace"

    def test_deanonymize_encrypted_without_key_fails(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        anon = tmp_path / "note.anonymized.md"
        anon.write_text("Hello PERSON_1", encoding="utf-8")
        mapping = tmp_path / "note.mapping.json.enc"
        mapping.write_text(
            json.dumps(encrypt_mapping({"PERSON_1": "Ada"}, "secret")),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="encrypted"):
            deanonymize_file(str(anon), str(mapping))
