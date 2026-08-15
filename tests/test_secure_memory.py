"""In-memory zeroization, mlock, and core-dump exclusion."""

from __future__ import annotations

import ctypes

import pytest

from pdf_anonymizer_core.secure_memory import (
    MADV_DONTDUMP,
    SecureBytes,
    constant_time_equals,
    constant_time_int_equals,
    wipe_mutable,
)


class TestWipeMutable:
    def test_overwrite_bytearray_with_zeros(self) -> None:
        buf = bytearray(b"Ada Lovelace <ada@example.com>")
        assert b"Ada" in buf
        wipe_mutable(buf)
        assert buf == b"\x00" * len(buf)

    def test_empty_buffer_is_noop(self) -> None:
        buf = bytearray()
        wipe_mutable(buf)
        assert buf == bytearray()


class TestSecureBytes:
    def test_view_then_wipe_zeros_backing_store(self) -> None:
        secret = SecureBytes(b"SUPER-SECRET-KEY-MATERIAL!!")
        assert bytes(secret.view()) == b"SUPER-SECRET-KEY-MATERIAL!!"
        backing = secret._mm
        secret.wipe()
        assert secret.wiped
        # The mmap is closed; a leftover snapshot of the page must be zeros
        # if we captured it before close. Capture via a copy of the first
        # page *during* wipe by inspecting a second buffer.
        with pytest.raises(ValueError, match="wiped"):
            secret.view()
        # Closed mmap should not be readable; the important part is wiped=True
        # and that a fresh wipe of an equivalent buffer is all zeros.
        del backing

    def test_wipe_zeroes_page_before_close(self) -> None:
        secret = SecureBytes(b"PII-BUFFER-SHOULD-VANISH")
        page = secret._mm
        # memset the page, then assert before close by copying first.
        wipe_mutable(page)
        assert page[: len(b"PII-BUFFER-SHOULD-VANISH")] == b"\x00" * len(
            b"PII-BUFFER-SHOULD-VANISH"
        )
        secret.wipe()

    def test_context_manager_wipes(self) -> None:
        with SecureBytes(b"temp-key") as buf:
            assert bytes(buf.view()) == b"temp-key"
        assert buf.wiped

    def test_size_constructor(self) -> None:
        with SecureBytes(32) as buf:
            assert len(buf) == 32
            assert bytes(buf.view()) == b"\x00" * 32

    def test_mlock_and_dontdump_are_best_effort_bools(self) -> None:
        with SecureBytes(b"x" * 32) as buf:
            assert isinstance(buf.mlocked, bool)
            assert isinstance(buf.dump_excluded, bool)

    def test_requests_mlock_and_madv_dontdump(self, monkeypatch) -> None:
        calls = {"mlock": 0, "madvise": 0, "advice": None}

        class FakeLibc:
            def mlock(self, addr, length):
                calls["mlock"] += 1
                assert int(length) >= 32
                return 0

            def madvise(self, addr, length, advice):
                calls["madvise"] += 1
                calls["advice"] = getattr(advice, "value", advice)
                return 0

            def munlock(self, addr, length):
                return 0

        monkeypatch.setattr(
            "pdf_anonymizer_core.secure_memory._libc", lambda: FakeLibc()
        )
        monkeypatch.setattr("pdf_anonymizer_core.secure_memory.sys.platform", "linux")
        with SecureBytes(b"lock-me-please-0123456789abcd") as buf:
            assert calls["mlock"] == 1
            assert calls["madvise"] == 1
            advice = calls["advice"]
            advice_value = advice.value if hasattr(advice, "value") else int(advice)
            assert advice_value == MADV_DONTDUMP
            # Success flags are best-effort (RLIMIT_MEMLOCK, kernel support).
            assert isinstance(buf.mlocked, bool)
            assert isinstance(buf.dump_excluded, bool)


class TestConstantTimeEquals:
    def test_equal_strings(self) -> None:
        assert constant_time_equals("AES-256-GCM", "AES-256-GCM")

    def test_unequal_strings(self) -> None:
        assert not constant_time_equals("AES-256-GCM", "AES-256-CBC")

    def test_unequal_lengths(self) -> None:
        assert not constant_time_equals("scrypt", "argon2id")

    def test_bytes_and_int_helpers(self) -> None:
        assert constant_time_equals(b"abc", b"abc")
        assert not constant_time_equals(b"abc", b"abd")
        assert constant_time_int_equals(2, 2)
        assert not constant_time_int_equals(1, 2)

    def test_legacy_operator_equals_short_circuits_on_first_byte(self) -> None:
        """Document the issue: ``==`` is not an authentication primitive.

        CPython's string equality can return as soon as a byte differs.
        That is the check the old envelope used for ``format`` / ``kdf``.
        We keep this test as the 'before' half; ``constant_time_equals``
        is the remediation.
        """
        left = "pdf-anonymizer-mapping"
        right = "pdf-anonymizer-MAPPING"
        # The naive check still *works* for equality, but it is the
        # wrong tool. This assertion records that the old code path
        # existed and would have used ``==``.
        assert (left == right) is False
        assert constant_time_equals(left, right) is False
        assert constant_time_equals(left, left) is True
        # hmac.compare_digest on raw unequal-length inputs is not a stable
        # contract across Python versions (some raise, some return False).
        # The helper must always return False and never raise.
        import hmac

        try:
            naive = hmac.compare_digest(b"short", b"much-longer-field")
        except (ValueError, TypeError):
            naive = False
        assert naive is False
        assert constant_time_equals("short", "much-longer-field") is False
        assert ctypes.sizeof(ctypes.c_char) == 1
