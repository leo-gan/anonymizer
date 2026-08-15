"""Mutable secret buffers with wipe, mlock, and core-dump exclusion.

Python ``str`` / ``bytes`` are immutable and can be interned or copied by
the runtime. Anything we treat as key material or plaintext PII is held in
a mutable buffer we own, then overwritten with zeros as soon as the
operation finishes.

``mlock`` and ``MADV_DONTDUMP`` are best-effort. They are Linux/POSIX
features and may fail (unprivileged ``RLIMIT_MEMLOCK``, missing libc
symbols, non-Linux). Failure is recorded, never raised, so the crypto
path still works.
"""

from __future__ import annotations

import ctypes
import hashlib
import hmac
import mmap
import sys
from typing import Optional

# Linux madvise: do not include pages in a core dump.
MADV_DONTDUMP = 16

_LIBC: Optional[ctypes.CDLL] = None
_LIBC_READY = False


def _configure_libc(libc: ctypes.CDLL) -> None:
    """Best-effort ctypes signatures. Fake/test objects skip this."""
    for name, argtypes in (
        ("mlock", [ctypes.c_void_p, ctypes.c_size_t]),
        ("munlock", [ctypes.c_void_p, ctypes.c_size_t]),
        ("madvise", [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]),
    ):
        func = getattr(libc, name, None)
        if func is None:
            continue
        try:
            func.argtypes = argtypes
            func.restype = ctypes.c_int
        except (AttributeError, TypeError):
            pass


def _libc() -> Optional[ctypes.CDLL]:
    global _LIBC, _LIBC_READY
    if _LIBC_READY:
        return _LIBC
    _LIBC_READY = True
    if sys.platform == "win32":
        _LIBC = None
        return None
    try:
        _LIBC = ctypes.CDLL(None, use_errno=True)
        _configure_libc(_LIBC)
    except OSError:
        _LIBC = None
    return _LIBC


def _buffer_address(buf) -> int:
    """Return the raw address of a writable contiguous buffer."""
    view = (ctypes.c_char * len(buf)).from_buffer(buf)
    return ctypes.addressof(view)


def wipe_mutable(buf) -> None:
    """Overwrite a mutable buffer with zeros (memset, then a Python loop).

    ``memset`` is the preferred wipe: it is one syscall-level store and is
    harder for a compiler to treat as a dead store. The Python loop is a
    fallback if the object does not support the buffer protocol.
    """
    n = len(buf)
    if n == 0:
        return
    try:
        addr = _buffer_address(buf)
        ctypes.memset(addr, 0, n)
    except (TypeError, ValueError, BufferError):
        for i in range(n):
            buf[i] = 0
    # Confirm; if anything remains, force a second pass.
    if hasattr(buf, "__getitem__") and n and buf[0] != 0:
        for i in range(n):
            buf[i] = 0


def constant_time_equals(left: bytes | str, right: bytes | str) -> bool:
    """Constant-time equality for authentication checks.

    ``hmac.compare_digest`` requires equal length. Different lengths are
    rejected after hashing both sides to a fixed-size digest so the
    comparison itself does not short-circuit on the first differing byte.
    Length is not treated as secret (envelope field sizes are public).
    """
    if isinstance(left, str):
        left_b = left.encode("utf-8")
    else:
        left_b = bytes(left)
    if isinstance(right, str):
        right_b = right.encode("utf-8")
    else:
        right_b = bytes(right)
    # Always run compare_digest on fixed-size SHA-256 so callers can pass
    # unequal-length strings (format / kdf names) without raising.
    digest_l = hashlib.sha256(left_b).digest()
    digest_r = hashlib.sha256(right_b).digest()
    same_len = hmac.compare_digest(
        len(left_b).to_bytes(8, "big"), len(right_b).to_bytes(8, "big")
    )
    same_body = hmac.compare_digest(digest_l, digest_r)
    return bool(same_len and same_body)


def constant_time_int_equals(left: int, right: int) -> bool:
    """Constant-time compare for small non-negative integers (schema version)."""
    if left < 0 or right < 0:
        return left == right
    return hmac.compare_digest(left.to_bytes(8, "big"), right.to_bytes(8, "big"))


class SecureBytes:
    """Page-aligned mutable secret with optional ``mlock`` + ``MADV_DONTDUMP``.

    Use as a context manager so wipe runs on every exit path::

        with SecureBytes(b"key-material") as buf:
            use(buf.view())
    """

    __slots__ = (
        "_mm",
        "_len",
        "_wiped",
        "_mlocked",
        "_dump_excluded",
        "_keepalive",
    )

    def __init__(self, data: bytes | bytearray | memoryview | int = 0) -> None:
        if isinstance(data, int):
            if data < 0:
                raise ValueError("SecureBytes size must be non-negative.")
            payload = b"\x00" * data
        else:
            payload = bytes(data)
        self._len = len(payload)
        page = mmap.PAGESIZE
        size = page if self._len == 0 else ((self._len + page - 1) // page) * page
        self._mm = mmap.mmap(-1, size)
        if self._len:
            self._mm[: self._len] = payload
        self._wiped = False
        self._mlocked = False
        self._dump_excluded = False
        # Keep the ctypes view alive so the address stays valid.
        self._keepalive = (ctypes.c_char * size).from_buffer(self._mm)
        self._try_mlock()
        self._try_dontdump()

    @property
    def wiped(self) -> bool:
        return self._wiped

    @property
    def mlocked(self) -> bool:
        return self._mlocked

    @property
    def dump_excluded(self) -> bool:
        return self._dump_excluded

    def __len__(self) -> int:
        return self._len

    def view(self) -> memoryview:
        if self._wiped:
            raise ValueError("SecureBytes has been wiped.")
        return memoryview(self._mm)[: self._len]

    def copy_out(self) -> bytes:
        """Return a ``bytes`` snapshot. Prefer ``view()`` so we can wipe later."""
        return bytes(self.view())

    def _address(self) -> int:
        return ctypes.addressof(self._keepalive)

    def _try_mlock(self) -> None:
        libc = _libc()
        if libc is None or not hasattr(libc, "mlock"):
            return
        try:
            rc = libc.mlock(
                ctypes.c_void_p(self._address()), ctypes.c_size_t(len(self._mm))
            )
            self._mlocked = rc == 0
        except (OSError, ValueError, AttributeError, TypeError):
            self._mlocked = False

    def _try_munlock(self) -> None:
        if not self._mlocked:
            return
        libc = _libc()
        if libc is None or not hasattr(libc, "munlock"):
            return
        try:
            libc.munlock(
                ctypes.c_void_p(self._address()), ctypes.c_size_t(len(self._mm))
            )
        except (OSError, ValueError, AttributeError, TypeError):
            pass
        self._mlocked = False

    def _try_dontdump(self) -> None:
        if sys.platform != "linux":
            return
        libc = _libc()
        if libc is None or not hasattr(libc, "madvise"):
            return
        try:
            rc = libc.madvise(
                ctypes.c_void_p(self._address()),
                ctypes.c_size_t(len(self._mm)),
                ctypes.c_int(MADV_DONTDUMP),
            )
            self._dump_excluded = rc == 0
        except (OSError, ValueError, AttributeError, TypeError):
            self._dump_excluded = False

    def wipe(self) -> None:
        if self._wiped:
            return
        try:
            wipe_mutable(self._mm)
        except (ValueError, BufferError):
            pass
        self._try_munlock()
        try:
            self._mm.close()
        except (BufferError, ValueError):
            pass
        self._keepalive = None
        self._wiped = True

    def __enter__(self) -> "SecureBytes":
        return self

    def __exit__(self, *exc: object) -> None:
        self.wipe()

    def __del__(self) -> None:
        try:
            self.wipe()
        except Exception:
            pass
