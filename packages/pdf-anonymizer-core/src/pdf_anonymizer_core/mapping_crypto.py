"""Encrypt and decrypt mapping files (AES-256-GCM).

The mapping file is the key to the original names. With a passphrase the
JSON is locked so a leaked file is not an instant deanonymization.

Envelope is still JSON so you can tell an encrypted map from a plaintext one
without a special file type, though we write ``*.mapping.json.enc`` by default.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
from typing import Any, Dict

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAPPING_KEY_ENV = "ANONYMIZER_MAPPING_KEY"

FORMAT = "pdf-anonymizer-mapping"
VERSION = 1
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_KEY_LEN = 32
_SALT_LEN = 16
_NONCE_LEN = 12


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        passphrase.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_LEN,
    )


def is_encrypted_mapping(payload: Any) -> bool:
    """True if ``payload`` looks like our encrypted envelope, not a name map."""
    return (
        isinstance(payload, dict)
        and payload.get("format") == FORMAT
        and "ciphertext" in payload
    )


def encrypt_mapping(mapping: Dict[str, str], passphrase: str) -> Dict[str, Any]:
    """Return a JSON-serializable encrypted envelope."""
    if not passphrase:
        raise ValueError("A non-empty passphrase is required to encrypt a mapping.")
    salt = secrets.token_bytes(_SALT_LEN)
    nonce = secrets.token_bytes(_NONCE_LEN)
    key = _derive_key(passphrase, salt)
    plaintext = json.dumps(mapping, ensure_ascii=False).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return {
        "format": FORMAT,
        "v": VERSION,
        "kdf": "scrypt",
        "cipher": "AES-256-GCM",
        "salt": _b64(salt),
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext),
    }


def decrypt_mapping(payload: Dict[str, Any], passphrase: str) -> Dict[str, str]:
    """Decrypt an envelope back to placeholder -> original."""
    if not passphrase:
        raise ValueError("A passphrase is required to open an encrypted mapping.")
    if not is_encrypted_mapping(payload):
        raise ValueError("This file is not an encrypted mapping.")
    try:
        salt = _unb64(payload["salt"])
        nonce = _unb64(payload["nonce"])
        ciphertext = _unb64(payload["ciphertext"])
        key = _derive_key(passphrase, salt)
        raw = AESGCM(key).decrypt(nonce, ciphertext, None)
        data = json.loads(raw.decode("utf-8"))
    except (KeyError, ValueError, InvalidTag, json.JSONDecodeError) as exc:
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


def load_mapping_payload(raw_mapping: Any, passphrase: str | None) -> Dict[str, str]:
    """Load plaintext or encrypted mapping JSON already parsed from disk."""
    if is_encrypted_mapping(raw_mapping):
        if not passphrase:
            raise ValueError(
                "This mapping is encrypted. Pass --mapping-passphrase or set "
                "ANONYMIZER_MAPPING_KEY."
            )
        return decrypt_mapping(raw_mapping, passphrase)
    if not isinstance(raw_mapping, dict):
        raise ValueError("Mapping file must be a JSON object.")
    return {str(k): str(v) for k, v in raw_mapping.items()}
