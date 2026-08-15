"""Atomic, owner-only writes for mapping files.

Plain ``open(path, "w")`` applies the process umask (often ``0o022``), so the
resulting file is ``0644`` and readable by every local account. Temporary
files created the same way can also linger after a crash.

This helper:

* creates the parent directory with mode ``0700``
* opens a same-directory temp file with ``O_CREAT | O_EXCL`` and mode ``0600``
* ``fchmod``s to ``0600`` so umask cannot reopen the file
* writes, ``fsync``s, then ``os.replace`` (atomic on POSIX)
* unlinks the temp file if anything fails
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Union

from pdf_anonymizer_core.secure_memory import wipe_mutable

PathLike = Union[str, os.PathLike[str]]

PRIVATE_FILE_MODE = 0o600
PRIVATE_DIR_MODE = 0o700


def ensure_private_dir(path: PathLike) -> Path:
    """Create ``path`` as a ``0700`` directory (best-effort chmod if it exists)."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    try:
        os.chmod(directory, PRIVATE_DIR_MODE)
    except OSError:
        pass
    return directory


def write_private_bytes(path: PathLike, data: bytes | bytearray | memoryview) -> None:
    """Write ``data`` to ``path`` atomically with mode ``0600``."""
    dest = Path(path)
    ensure_private_dir(dest.parent)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{dest.name}.",
        suffix=".tmp",
        dir=str(dest.parent),
    )
    try:
        try:
            os.fchmod(fd, PRIVATE_FILE_MODE)
        except OSError:
            pass
        written = 0
        view = memoryview(data)
        while written < len(view):
            n = os.write(fd, view[written:])
            if n == 0:
                raise OSError("short write while persisting a mapping file")
            written += n
        os.fsync(fd)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    else:
        os.close(fd)

    try:
        os.replace(tmp_name, dest)
        try:
            os.chmod(dest, PRIVATE_FILE_MODE)
        except OSError:
            pass
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def write_private_json(path: PathLike, payload: Any) -> None:
    """Serialize ``payload`` as UTF-8 JSON and write it with ``write_private_bytes``.

    The encoded buffer is wiped after the write so plaintext PII does not
    linger in a leftover ``bytes`` object from this helper.
    """
    raw = bytearray(json.dumps(payload, ensure_ascii=False, indent=4).encode("utf-8"))
    try:
        write_private_bytes(path, raw)
    finally:
        wipe_mutable(raw)
