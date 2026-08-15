"""Encrypt and decrypt mapping files (AES-256-GCM + Argon2id).

The mapping file is the key to the original names. With a passphrase the
JSON is locked so a leaked file is not an instant deanonymization.

Envelope v2 (current):

* AES-256-GCM authenticated encryption
* Argon2id key derivation (OWASP interactive parameters by default)
* Document SHA-256 and mapping schema version bound as AEAD AAD
* Envelope fields validated *before* any KDF or decrypt
* Authentication checks use constant-time compares
* Derived keys and plaintext PII live in wipeable buffers

Envelope v1 (legacy, decrypt only): scrypt, no AAD. Still accepted so
existing ``*.mapping.json.enc`` files keep working.

Envelope is still JSON so you can tell an encrypted map from a plaintext
one without a special file type. We write ``*.mapping.json.enc`` by default.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

from pdf_anonymizer_core.secure_memory import (
    SecureBytes,
    constant_time_equals,
    constant_time_int_equals,
    wipe_mutable,
)

MAPPING_KEY_ENV = "ANONYMIZER_MAPPING_KEY"

FORMAT = "pdf-anonymizer-mapping"
VERSION = 2
LEGACY_VERSION = 1
MAPPING_SCHEMA_VERSION = 1

CIPHER_NAME = "AES-256-GCM"
KDF_ARGON2ID = "argon2id"
KDF_SCRYPT = "scrypt"

# OWASP 2023 interactive Argon2id: 19 MiB, 2 iterations, 1 lane.
DEFAULT_ARGON2_ITERATIONS = 2
DEFAULT_ARGON2_LANES = 1
DEFAULT_ARGON2_MEMORY = 19_456

# Hard caps so a crafted envelope cannot turn decrypt into a memory DoS.
_MAX_ARGON2_ITERATIONS = 10
_MAX_ARGON2_LANES = 8
_MAX_ARGON2_MEMORY = 1_048_576  # 1 GiB
_MIN_ARGON2_MEMORY_PER_LANE = 8

_KEY_LEN = 32
_SALT_LEN = 16
_NONCE_LEN = 12
_MAX_CIPHERTEXT_LEN = 32 * 1024 * 1024

# Legacy v1 scrypt parameters (fixed; v1 did not store them).
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(text: str) -> bytes:
    if not isinstance(text, str):
        raise ValueError("Envelope field is not base64 text.")
    try:
        return base64.b64decode(text.encode("ascii"), validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Envelope field is not valid base64.") from exc


def sha256_file(path: str | os.PathLike[str]) -> str:
    """Return the lowercase hex SHA-256 of a file, streamed in 1 MiB chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def encode_aad(
    source_sha256: str,
    schema_version: int,
    envelope_version: int = VERSION,
) -> bytes:
    """Canonical AAD bytes bound into AES-GCM.

    Newline-delimited, not JSON: callers cannot change the binding by
    adding spaces or reordering keys.
    """
    return (
        f"{FORMAT}\n"
        f"v={envelope_version}\n"
        f"schema={schema_version}\n"
        f"sha256={source_sha256}\n"
    ).encode("utf-8")


def _normalize_sha256(value: Optional[str]) -> str:
    if value is None:
        return ""
    text = value.strip().lower()
    if text == "":
        return ""
    if len(text) != 64 or any(c not in "0123456789abcdef" for c in text):
        raise ValueError("source_sha256 must be a 64-character hex SHA-256 digest.")
    return text


def is_encrypted_mapping(payload: Any) -> bool:
    """True if ``payload`` looks like our encrypted envelope, not a name map."""
    if not isinstance(payload, dict):
        return False
    if not constant_time_equals(str(payload.get("format", "")), FORMAT):
        return False
    return "ciphertext" in payload


@dataclass(frozen=True)
class EnvelopeMeta:
    """Validated envelope fields. Built *before* any KDF or AEAD call."""

    version: int
    kdf: str
    cipher: str
    salt: bytes
    nonce: bytes
    ciphertext: bytes
    source_sha256: str
    schema_version: int
    kdf_params: Dict[str, int]
    aad: Optional[bytes]


def _require_dict(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Encrypted mapping envelope must be a JSON object.")
    return payload


def validate_envelope(payload: Any) -> EnvelopeMeta:
    """Strict metadata checks. Raises ``ValueError`` before any crypto work."""
    data = _require_dict(payload)
    if not constant_time_equals(str(data.get("format", "")), FORMAT):
        raise ValueError("This file is not an encrypted mapping.")

    version_raw = data.get("v")
    if not isinstance(version_raw, int) or isinstance(version_raw, bool):
        raise ValueError("Envelope version is missing or not an integer.")
    is_v1 = constant_time_int_equals(version_raw, LEGACY_VERSION)
    is_v2 = constant_time_int_equals(version_raw, VERSION)
    if not (is_v1 or is_v2):
        raise ValueError("Unsupported mapping envelope version.")
    version = LEGACY_VERSION if is_v1 else VERSION

    kdf = str(data.get("kdf", ""))
    cipher = str(data.get("cipher", ""))
    expected_kdf = KDF_SCRYPT if version == LEGACY_VERSION else KDF_ARGON2ID
    if not constant_time_equals(kdf, expected_kdf):
        raise ValueError("Envelope key-derivation algorithm is not allowed.")
    if not constant_time_equals(cipher, CIPHER_NAME):
        raise ValueError("Envelope cipher is not allowed.")

    salt = _unb64(data.get("salt", ""))
    nonce = _unb64(data.get("nonce", ""))
    ciphertext = _unb64(data.get("ciphertext", ""))
    if len(salt) != _SALT_LEN:
        raise ValueError("Envelope salt has an unexpected length.")
    if len(nonce) != _NONCE_LEN:
        raise ValueError("Envelope nonce has an unexpected length.")
    if not ciphertext:
        raise ValueError("Envelope ciphertext is empty.")
    if len(ciphertext) > _MAX_CIPHERTEXT_LEN:
        raise ValueError("Envelope ciphertext is larger than the allowed maximum.")

    kdf_params = _validate_kdf_params(version, data.get("kdf_params"))
    source_sha256 = ""
    schema_version = MAPPING_SCHEMA_VERSION
    aad: Optional[bytes] = None
    if version == VERSION:
        aad_block = data.get("aad")
        if not isinstance(aad_block, dict):
            raise ValueError("Envelope AAD metadata is missing.")
        source_sha256 = _normalize_sha256(str(aad_block.get("source_sha256", "")))
        schema_raw = aad_block.get("schema_version", MAPPING_SCHEMA_VERSION)
        if not isinstance(schema_raw, int) or isinstance(schema_raw, bool):
            raise ValueError("Envelope schema_version is not an integer.")
        if schema_raw < 1 or schema_raw > 16:
            raise ValueError("Envelope schema_version is out of range.")
        schema_version = schema_raw
        aad = encode_aad(source_sha256, schema_version, version)

    return EnvelopeMeta(
        version=version,
        kdf=kdf,
        cipher=cipher,
        salt=salt,
        nonce=nonce,
        ciphertext=ciphertext,
        source_sha256=source_sha256,
        schema_version=schema_version,
        kdf_params=kdf_params,
        aad=aad,
    )


def _validate_kdf_params(version: int, raw: Any) -> Dict[str, int]:
    if version == LEGACY_VERSION:
        if raw is not None and raw != {}:
            raise ValueError("Legacy scrypt envelopes do not accept kdf_params.")
        return {"n": _SCRYPT_N, "r": _SCRYPT_R, "p": _SCRYPT_P}

    if raw is None:
        raise ValueError("Argon2id envelopes must include kdf_params.")
    if not isinstance(raw, dict):
        raise ValueError("kdf_params must be an object.")
    try:
        iterations = int(raw["iterations"])
        lanes = int(raw["lanes"])
        memory_cost = int(raw["memory_cost"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "kdf_params must include iterations, lanes, and memory_cost."
        ) from exc
    if iterations < 1 or iterations > _MAX_ARGON2_ITERATIONS:
        raise ValueError("Argon2id iterations are out of the allowed range.")
    if lanes < 1 or lanes > _MAX_ARGON2_LANES:
        raise ValueError("Argon2id lanes are out of the allowed range.")
    min_memory = _MIN_ARGON2_MEMORY_PER_LANE * lanes
    if memory_cost < min_memory or memory_cost > _MAX_ARGON2_MEMORY:
        raise ValueError("Argon2id memory_cost is out of the allowed range.")
    return {"iterations": iterations, "lanes": lanes, "memory_cost": memory_cost}


def _derive_key_argon2id(
    passphrase: SecureBytes,
    salt: bytes,
    params: Mapping[str, int],
    key_out: SecureBytes,
) -> None:
    kdf = Argon2id(
        salt=salt,
        length=_KEY_LEN,
        iterations=params["iterations"],
        lanes=params["lanes"],
        memory_cost=params["memory_cost"],
    )
    kdf.derive_into(passphrase.view(), key_out.view())


def _derive_key_scrypt(
    passphrase: SecureBytes, salt: bytes, key_out: SecureBytes
) -> None:
    # hashlib.scrypt writes into a new bytes object; copy into our buffer and
    # wipe the temporary as far as we can (the bytes object itself is immutable).
    derived = hashlib.scrypt(
        bytes(passphrase.view()),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_LEN,
    )
    key_out.view()[:] = derived
    # ``derived`` cannot be wiped; it is a short-lived bytes object.


def encrypt_mapping(
    mapping: Dict[str, str],
    passphrase: str,
    *,
    source_sha256: str | None = None,
    schema_version: int | None = None,
    kdf_params: Mapping[str, int] | None = None,
) -> Dict[str, Any]:
    """Return a JSON-serializable encrypted envelope.

    Extra keyword arguments are optional so existing callers
    ``encrypt_mapping(mapping, passphrase)`` keep working. When
    ``source_sha256`` is omitted the AAD still binds an empty hash so the
    field cannot be filled in later without breaking the tag.
    """
    if not passphrase:
        raise ValueError("A non-empty passphrase is required to encrypt a mapping.")
    if not isinstance(mapping, dict):
        raise ValueError("Mapping must be a JSON object.")

    digest = _normalize_sha256(source_sha256)
    schema = MAPPING_SCHEMA_VERSION if schema_version is None else int(schema_version)
    if schema < 1 or schema > 16:
        raise ValueError("schema_version is out of range.")

    params = {
        "iterations": DEFAULT_ARGON2_ITERATIONS,
        "lanes": DEFAULT_ARGON2_LANES,
        "memory_cost": DEFAULT_ARGON2_MEMORY,
    }
    if kdf_params:
        params.update({k: int(v) for k, v in kdf_params.items()})
    params = _validate_kdf_params(VERSION, params)

    salt = secrets.token_bytes(_SALT_LEN)
    nonce = secrets.token_bytes(_NONCE_LEN)
    aad = encode_aad(digest, schema, VERSION)

    plaintext = bytearray(
        json.dumps(mapping, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    try:
        with SecureBytes(passphrase.encode("utf-8")) as password:
            with SecureBytes(_KEY_LEN) as key:
                _derive_key_argon2id(password, salt, params, key)
                ciphertext = AESGCM(bytes(key.view())).encrypt(
                    nonce, bytes(plaintext), aad
                )
    finally:
        wipe_mutable(plaintext)

    return {
        "format": FORMAT,
        "v": VERSION,
        "kdf": KDF_ARGON2ID,
        "cipher": CIPHER_NAME,
        "kdf_params": params,
        "salt": _b64(salt),
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext),
        "aad": {
            "source_sha256": digest,
            "schema_version": schema,
        },
    }


def decrypt_mapping(
    payload: Dict[str, Any],
    passphrase: str,
    *,
    source_sha256: str | None = None,
    schema_version: int | None = None,
) -> Dict[str, str]:
    """Decrypt an envelope back to placeholder -> original.

    Envelope metadata is validated first. If the caller supplies an expected
    source hash or schema version those values are compared in constant time
    against the authenticated AAD *before* the KDF runs. GCM then
    re-authenticates the same AAD so a swapped or replayed mapping fails
    the tag check.
    """
    if not passphrase:
        raise ValueError("A passphrase is required to open an encrypted mapping.")

    meta = validate_envelope(payload)
    expected_hash = (
        _normalize_sha256(source_sha256) if source_sha256 is not None else None
    )
    if expected_hash is not None:
        if not constant_time_equals(meta.source_sha256, expected_hash):
            raise ValueError(
                "Could not decrypt the mapping. Check the passphrase and the file."
            )
    if schema_version is not None:
        if not constant_time_int_equals(meta.schema_version, int(schema_version)):
            raise ValueError(
                "Could not decrypt the mapping. Check the passphrase and the file."
            )

    try:
        with SecureBytes(passphrase.encode("utf-8")) as password:
            with SecureBytes(_KEY_LEN) as key:
                if meta.version == LEGACY_VERSION:
                    _derive_key_scrypt(password, meta.salt, key)
                else:
                    _derive_key_argon2id(password, meta.salt, meta.kdf_params, key)
                raw = AESGCM(bytes(key.view())).decrypt(
                    meta.nonce, meta.ciphertext, meta.aad
                )
        plaintext = bytearray(raw)
        try:
            data = json.loads(bytes(plaintext).decode("utf-8"))
        finally:
            wipe_mutable(plaintext)
    except (ValueError, InvalidTag, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(
            "Could not decrypt the mapping. Check the passphrase and the file."
        ) from exc

    if not isinstance(data, dict):
        raise ValueError("Decrypted mapping is not a JSON object.")
    return {str(k): str(v) for k, v in data.items()}


def resolve_mapping_passphrase(explicit: str | None = None) -> str | None:
    """CLI flag wins; otherwise ``ANONYMIZER_MAPPING_KEY``."""
    if explicit:
        return explicit
    value = os.getenv(MAPPING_KEY_ENV)
    return value or None


def load_mapping_payload(
    raw_mapping: Any,
    passphrase: str | None,
    *,
    source_sha256: str | None = None,
    schema_version: int | None = None,
) -> Dict[str, str]:
    """Load plaintext or encrypted mapping JSON already parsed from disk."""
    if is_encrypted_mapping(raw_mapping):
        if not passphrase:
            raise ValueError(
                "This mapping is encrypted. Pass --mapping-passphrase or set "
                "ANONYMIZER_MAPPING_KEY."
            )
        return decrypt_mapping(
            raw_mapping,
            passphrase,
            source_sha256=source_sha256,
            schema_version=schema_version,
        )
    if not isinstance(raw_mapping, dict):
        raise ValueError("Mapping file must be a JSON object.")
    return {str(k): str(v) for k, v in raw_mapping.items()}
