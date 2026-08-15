"""Encrypted mapping files: legacy issues vs the hardened workflow.

The first classes reconstruct the pre-hardening behaviour (scrypt, no AAD,
umask-dependent ``0644`` writes, no metadata checks) so the security bugs
are visible. Later classes assert the remediated results.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any, Dict

import pytest

from pdf_anonymizer_core.mapping_crypto import (
    CIPHER_NAME,
    FORMAT,
    KDF_ARGON2ID,
    LEGACY_VERSION,
    VERSION,
    decrypt_mapping,
    encrypt_mapping,
    is_encrypted_mapping,
    load_mapping_payload,
    resolve_mapping_passphrase,
    sha256_file,
    validate_envelope,
)
from pdf_anonymizer_core.secure_io import PRIVATE_FILE_MODE, write_private_json
from pdf_anonymizer_core.secure_memory import SecureBytes
from pdf_anonymizer_core.utils import deanonymize_file, save_results


# ---------------------------------------------------------------------------
# Legacy (pre-hardening) helpers — the insecure baseline.
# ---------------------------------------------------------------------------

_LEGACY_SCRYPT_N = 2**14
_LEGACY_SCRYPT_R = 8
_LEGACY_SCRYPT_P = 1
_LEGACY_KEY_LEN = 32
_LEGACY_SALT_LEN = 16
_LEGACY_NONCE_LEN = 12


def _legacy_b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


def _legacy_unb64(text: str) -> bytes:
    import base64

    return base64.b64decode(text.encode("ascii"))


def _legacy_derive_scrypt(passphrase: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        passphrase.encode("utf-8"),
        salt=salt,
        n=_LEGACY_SCRYPT_N,
        r=_LEGACY_SCRYPT_R,
        p=_LEGACY_SCRYPT_P,
        dklen=_LEGACY_KEY_LEN,
    )


def legacy_v1_encrypt(mapping: Dict[str, str], passphrase: str) -> Dict[str, Any]:
    """Reproduce the original envelope: scrypt, AES-GCM, *no* AAD."""
    import secrets

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    salt = secrets.token_bytes(_LEGACY_SALT_LEN)
    nonce = secrets.token_bytes(_LEGACY_NONCE_LEN)
    key = _legacy_derive_scrypt(passphrase, salt)
    plaintext = json.dumps(mapping, ensure_ascii=False).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return {
        "format": FORMAT,
        "v": LEGACY_VERSION,
        "kdf": "scrypt",
        "cipher": "AES-256-GCM",
        "salt": _legacy_b64(salt),
        "nonce": _legacy_b64(nonce),
        "ciphertext": _legacy_b64(ciphertext),
    }


def legacy_naive_write(path: Path, payload: Any) -> None:
    """The old ``open(..., "w")`` persist path. Permissions follow umask."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4)


# ---------------------------------------------------------------------------
# Existing public API (must stay stable).
# ---------------------------------------------------------------------------


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

    def test_new_envelopes_use_argon2id_and_v2(self) -> None:
        envelope = encrypt_mapping({"PERSON_1": "Ada"}, "secret")
        assert envelope["v"] == VERSION == 2
        assert envelope["kdf"] == KDF_ARGON2ID
        assert envelope["cipher"] == CIPHER_NAME
        assert "kdf_params" in envelope
        assert "aad" in envelope


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

        out, _stats = deanonymize_file(
            str(anon), str(mapping), mapping_passphrase="secret"
        )
        assert Path(out).read_text(encoding="utf-8") == "Hello Ada Lovelace"

    def test_deanonymize_encrypted_without_key_fails(
        self, tmp_path, monkeypatch
    ) -> None:
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


# ---------------------------------------------------------------------------
# Issue: no document binding. Remediation: AEAD AAD.
# ---------------------------------------------------------------------------


class TestLegacyMissingAad:
    def test_v1_envelope_has_no_aad_and_decrypts_for_any_document(self) -> None:
        envelope = legacy_v1_encrypt({"PERSON_1": "Ada Lovelace"}, "secret")
        assert "aad" not in envelope
        assert envelope["v"] == 1
        assert envelope["kdf"] == "scrypt"
        # The old file can be opened with no source check — that is the
        # transposition/replay hole: the same ciphertext is valid next to
        # any other anonymized document.
        assert decrypt_mapping(envelope, "secret") == {"PERSON_1": "Ada Lovelace"}

    def test_v2_binds_source_hash_as_aad(self) -> None:
        digest_a = "ab" * 32
        digest_b = "cd" * 32
        envelope = encrypt_mapping(
            {"PERSON_1": "Ada Lovelace"},
            "secret",
            source_sha256=digest_a,
        )
        assert envelope["aad"]["source_sha256"] == digest_a
        assert decrypt_mapping(envelope, "secret", source_sha256=digest_a) == {
            "PERSON_1": "Ada Lovelace"
        }
        with pytest.raises(ValueError, match="decrypt"):
            decrypt_mapping(envelope, "secret", source_sha256=digest_b)

    def test_aad_field_tamper_is_detected(self) -> None:
        envelope = encrypt_mapping(
            {"PERSON_1": "Ada"},
            "secret",
            source_sha256="11" * 32,
            schema_version=1,
        )
        envelope["aad"]["source_sha256"] = "22" * 32
        with pytest.raises(ValueError, match="decrypt"):
            decrypt_mapping(envelope, "secret")

    def test_schema_version_tamper_is_detected(self) -> None:
        envelope = encrypt_mapping(
            {"PERSON_1": "Ada"},
            "secret",
            source_sha256="33" * 32,
            schema_version=1,
        )
        envelope["aad"]["schema_version"] = 2
        with pytest.raises(ValueError, match="decrypt"):
            decrypt_mapping(envelope, "secret")

    def test_ciphertext_moved_onto_other_document_aad_fails(self) -> None:
        env_a = encrypt_mapping({"PERSON_1": "Ada"}, "secret", source_sha256="aa" * 32)
        env_b = encrypt_mapping(
            {"PERSON_1": "Grace"}, "secret", source_sha256="bb" * 32
        )
        # Classic transposition: reuse A's ciphertext under B's metadata.
        env_b["ciphertext"] = env_a["ciphertext"]
        env_b["salt"] = env_a["salt"]
        env_b["nonce"] = env_a["nonce"]
        with pytest.raises(ValueError, match="decrypt"):
            decrypt_mapping(env_b, "secret", source_sha256="bb" * 32)

    def test_save_results_binds_source_file_hash(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "contract.txt"
        src.write_text("Ada Lovelace", encoding="utf-8")
        anon_path, mapping_path = save_results(
            "PERSON_1",
            {"PERSON_1": "Ada Lovelace"},
            str(src),
            mapping_passphrase="secret",
        )
        payload = json.loads(Path(mapping_path).read_text(encoding="utf-8"))
        assert payload["aad"]["source_sha256"] == sha256_file(src)
        assert payload["aad"]["schema_version"] == 1

        with pytest.raises(ValueError, match="decrypt"):
            deanonymize_file(
                anon_path,
                mapping_path,
                mapping_passphrase="secret",
                expected_source_sha256="00" * 32,
            )
        out, _stats = deanonymize_file(
            anon_path,
            mapping_path,
            mapping_passphrase="secret",
            expected_source_sha256=payload["aad"]["source_sha256"],
        )
        assert Path(out).read_text(encoding="utf-8") == "Ada Lovelace"


# ---------------------------------------------------------------------------
# Issue: metadata not checked before crypto. Remediation: validate_envelope.
# ---------------------------------------------------------------------------


class TestEnvelopeValidationBeforeCrypto:
    def test_unknown_kdf_does_not_run_argon2(self, monkeypatch) -> None:
        calls = {"n": 0}

        class Boom:
            def __init__(self, *args, **kwargs):
                calls["n"] += 1
                raise AssertionError("Argon2id must not run on a rejected envelope")

        envelope = encrypt_mapping({"PERSON_1": "Ada"}, "secret")
        monkeypatch.setattr("pdf_anonymizer_core.mapping_crypto.Argon2id", Boom)
        envelope["kdf"] = "pbkdf2"
        with pytest.raises(ValueError, match="key-derivation"):
            decrypt_mapping(envelope, "secret")
        assert calls["n"] == 0

    def test_huge_memory_cost_rejected_before_kdf(self, monkeypatch) -> None:
        calls = {"n": 0}

        class Boom:
            def __init__(self, *args, **kwargs):
                calls["n"] += 1
                raise AssertionError("Argon2id must not run")

        envelope = encrypt_mapping({"PERSON_1": "Ada"}, "secret")
        monkeypatch.setattr("pdf_anonymizer_core.mapping_crypto.Argon2id", Boom)
        envelope["kdf_params"]["memory_cost"] = 10**12
        with pytest.raises(ValueError, match="memory_cost"):
            decrypt_mapping(envelope, "secret")
        assert calls["n"] == 0

    def test_wrong_nonce_length_rejected(self) -> None:
        import base64

        envelope = encrypt_mapping({"PERSON_1": "Ada"}, "secret")
        envelope["nonce"] = base64.b64encode(b"short").decode("ascii")
        with pytest.raises(ValueError, match="nonce"):
            decrypt_mapping(envelope, "secret")

    def test_missing_aad_block_rejected(self) -> None:
        envelope = encrypt_mapping({"PERSON_1": "Ada"}, "secret")
        del envelope["aad"]
        with pytest.raises(ValueError, match="AAD"):
            validate_envelope(envelope)

    def test_unsupported_version_rejected(self) -> None:
        envelope = encrypt_mapping({"PERSON_1": "Ada"}, "secret")
        envelope["v"] = 99
        with pytest.raises(ValueError, match="version"):
            decrypt_mapping(envelope, "secret")

    def test_legacy_v1_still_decrypts(self) -> None:
        envelope = legacy_v1_encrypt({"PERSON_1": "Ada Lovelace"}, "secret")
        assert decrypt_mapping(envelope, "secret") == {"PERSON_1": "Ada Lovelace"}


# ---------------------------------------------------------------------------
# Issue: umask 0644 mapping files. Remediation: atomic 0600 writes.
# ---------------------------------------------------------------------------


class TestMappingFilePermissions:
    def test_legacy_open_write_is_group_or_world_readable(self, tmp_path) -> None:
        previous = os.umask(0o022)
        try:
            path = tmp_path / "legacy.mapping.json"
            legacy_naive_write(path, {"PERSON_1": "Ada Lovelace"})
            mode = stat.S_IMODE(path.stat().st_mode)
            assert mode & 0o044, f"expected the old leak, got {oct(mode)}"
        finally:
            os.umask(previous)

    def test_write_private_json_is_0600_even_with_permissive_umask(
        self, tmp_path
    ) -> None:
        previous = os.umask(0o000)
        try:
            path = tmp_path / "private.mapping.json"
            write_private_json(path, {"PERSON_1": "Ada Lovelace"})
            mode = stat.S_IMODE(path.stat().st_mode)
            assert mode == PRIVATE_FILE_MODE
        finally:
            os.umask(previous)

    def test_save_results_plaintext_and_encrypted_are_0600(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        previous = os.umask(0o000)
        try:
            src = tmp_path / "note.txt"
            src.write_text("hi", encoding="utf-8")
            _anon, plain = save_results("hello PERSON_1", {"PERSON_1": "Ada"}, str(src))
            _anon, locked = save_results(
                "hello PERSON_1",
                {"PERSON_1": "Ada"},
                str(src),
                mapping_passphrase="secret",
            )
            assert stat.S_IMODE(Path(plain).stat().st_mode) == 0o600
            assert stat.S_IMODE(Path(locked).stat().st_mode) == 0o600
        finally:
            os.umask(previous)

    def test_atomic_write_leaves_no_temp_file(self, tmp_path) -> None:
        path = tmp_path / "note.mapping.json"
        write_private_json(path, {"PERSON_1": "Ada"})
        leftovers = [
            p for p in tmp_path.iterdir() if p.suffix == ".tmp" or ".tmp" in p.name
        ]
        assert leftovers == []
        assert path.is_file()

    def test_failed_write_unlinks_temp(self, tmp_path, monkeypatch) -> None:
        def boom(fd, data):
            raise OSError("disk full")

        monkeypatch.setattr("pdf_anonymizer_core.secure_io.os.write", boom)
        path = tmp_path / "note.mapping.json"
        with pytest.raises(OSError, match="disk full"):
            write_private_json(path, {"PERSON_1": "Ada"})
        assert not path.exists()
        leftovers = list(tmp_path.glob(".*")) + list(tmp_path.glob("*.tmp"))
        leftovers = [p for p in leftovers if p.name != path.name]
        assert leftovers == []


# ---------------------------------------------------------------------------
# Issue: keys and plaintext linger. Remediation: SecureBytes wipe.
# ---------------------------------------------------------------------------


class TestMemoryWiping:
    def test_encrypt_wipes_secure_buffers(self, monkeypatch) -> None:
        wiped = {"n": 0}
        original_wipe = SecureBytes.wipe

        def tracking_wipe(self):
            wiped["n"] += 1
            return original_wipe(self)

        monkeypatch.setattr(SecureBytes, "wipe", tracking_wipe)
        encrypt_mapping({"PERSON_1": "Ada Lovelace"}, "correct horse")
        # passphrase buffer + derived key (context managers, both exit paths)
        assert wiped["n"] >= 2

    def test_decrypt_wipes_secure_buffers(self, monkeypatch) -> None:
        envelope = encrypt_mapping({"PERSON_1": "Ada"}, "secret")
        wiped = {"n": 0}
        original_wipe = SecureBytes.wipe

        def tracking_wipe(self):
            wiped["n"] += 1
            return original_wipe(self)

        monkeypatch.setattr(SecureBytes, "wipe", tracking_wipe)
        decrypt_mapping(envelope, "secret")
        assert wiped["n"] >= 2

    def test_plaintext_bytearray_is_zeros_after_encrypt(self, monkeypatch) -> None:
        captured: list[bytearray] = []
        real_dumps = json.dumps

        def spy_dumps(*args, **kwargs):
            text = real_dumps(*args, **kwargs)
            return text

        monkeypatch.setattr("pdf_anonymizer_core.mapping_crypto.json.dumps", spy_dumps)
        # Spy on bytearray construction of the plaintext by wrapping wipe_mutable.
        from pdf_anonymizer_core import mapping_crypto as mc

        original_wipe = mc.wipe_mutable

        def spy_wipe(buf):
            captured.append(bytearray(buf))
            return original_wipe(buf)

        monkeypatch.setattr(mc, "wipe_mutable", spy_wipe)
        encrypt_mapping({"PERSON_1": "Ada Lovelace"}, "secret")
        assert captured, "expected the plaintext buffer to be wiped"
        # After wipe_mutable the live buffer is zeros; the spy copied first.
        assert any(b"Ada Lovelace" in chunk for chunk in captured)


# ---------------------------------------------------------------------------
# Ephemeral in-memory mode.
# ---------------------------------------------------------------------------


class TestEphemeralMapping:
    def test_save_results_writes_no_mapping_file(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "note.txt"
        src.write_text("hi", encoding="utf-8")
        anon, mapping_path = save_results(
            "hello PERSON_1",
            {"PERSON_1": "Ada Lovelace"},
            str(src),
            mapping_passphrase="secret",
            ephemeral_mapping=True,
        )
        assert mapping_path == ""
        assert Path(anon).is_file()
        mappings_dir = tmp_path / "data" / "mappings"
        assert not mappings_dir.exists() or list(mappings_dir.iterdir()) == []

    def test_ephemeral_without_passphrase_still_skips_disk(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "note.txt"
        src.write_text("hi", encoding="utf-8")
        _anon, mapping_path = save_results(
            "hello",
            {"PERSON_1": "Ada"},
            str(src),
            ephemeral_mapping=True,
        )
        assert mapping_path == ""
        assert not (tmp_path / "data/mappings/note.mapping.json").exists()
