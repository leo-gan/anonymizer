"""Per-type operators for how a found value is written into the masked file.

Default is ``replace`` (typed stand-ins such as PERSON_1). Other operators
change what the reader sees; the mapping still records original → written form
so deanonymize can reverse when the written form is unique.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, Optional

from pdf_anonymizer_core.validators import parent_type

OPERATOR_REPLACE = "replace"
OPERATOR_MASK = "mask"
OPERATOR_HASH = "hash"
OPERATOR_GENERALIZE = "generalize"
OPERATOR_SHIFT = "shift"

OPERATORS = frozenset(
    {
        OPERATOR_REPLACE,
        OPERATOR_MASK,
        OPERATOR_HASH,
        OPERATOR_GENERALIZE,
        OPERATOR_SHIFT,
    }
)

_ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
_US_ZIP = re.compile(r"^(\d{5})(?:-\d{4})?$")
_ZIP_IN_TEXT = re.compile(r"\b(\d{5})(-\d{4})?\b")
_DIGITS = re.compile(r"\d")


def parse_operator_specs(specs: Optional[Iterable[str]]) -> Dict[str, str]:
    """Parse ``TYPE=operator`` strings. Unknown operators raise ValueError."""
    result: Dict[str, str] = {}
    if not specs:
        return result
    for raw in specs:
        if not raw or "=" not in raw:
            raise ValueError(
                f"Invalid --operator {raw!r}. Use TYPE=operator, e.g. CREDIT_CARD=mask."
            )
        type_name, operator = raw.split("=", 1)
        type_name = type_name.strip().upper()
        operator = operator.strip().lower()
        if not type_name:
            raise ValueError(f"Invalid --operator {raw!r}. Missing type name.")
        if operator not in OPERATORS:
            raise ValueError(
                f"Unknown operator {operator!r} for {type_name}. "
                f"Use one of: {', '.join(sorted(OPERATORS))}."
            )
        result[type_name] = operator
    return result


def operator_for_type(entity_type: str, operators: Optional[Dict[str, str]]) -> str:
    """Resolve the operator for a type. ``CREDIT_CARD_LIKE`` follows ``CREDIT_CARD``."""
    if not operators:
        return OPERATOR_REPLACE
    upper = entity_type.upper()
    if upper in operators:
        return operators[upper]
    parent = parent_type(upper)
    if parent in operators:
        return operators[parent]
    if upper.startswith("DATE") and "DATE" in operators:
        return operators["DATE"]
    return OPERATOR_REPLACE


def apply_operator(
    original: str,
    entity_type: str,
    placeholder: str,
    operator: str,
    base_form: Optional[str] = None,
) -> str:
    """Return the string to write in place of ``original``."""
    if operator == OPERATOR_REPLACE:
        return placeholder
    if operator == OPERATOR_MASK:
        return mask_value(original, entity_type)
    if operator == OPERATOR_HASH:
        return hash_value(original)
    if operator == OPERATOR_GENERALIZE:
        return generalize_value(original, entity_type)
    if operator == OPERATOR_SHIFT:
        return shift_date_value(original, base_form or original)
    return placeholder


def hash_value(original: str) -> str:
    digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:16]
    return f"H_{digest}"


def mask_value(original: str, entity_type: str) -> str:
    """Keep a little shape; hide the rest."""
    kind = parent_type(entity_type)
    digits = _DIGITS.findall(original)
    if kind in {"CREDIT_CARD", "SSN", "SSN_US", "SIN_CA", "MEDICAL_NPI_US"} or (
        kind.startswith("SSN")
    ):
        return _mask_keep_last(original, 4)
    if kind == "IBAN" or kind.endswith("IBAN"):
        return _mask_keep_last(original, 4)
    if kind == "PHONE":
        return _mask_keep_last(original, 4)
    if kind == "EMAIL":
        return _mask_email(original)
    if digits and len(digits) >= 4:
        return _mask_keep_last(original, 4)
    return "".join("*" if ch.isalnum() else ch for ch in original) or "****"


def _mask_keep_last(original: str, keep: int) -> str:
    chars = list(original)
    digit_positions = [i for i, ch in enumerate(chars) if ch.isdigit()]
    hide = set(digit_positions[:-keep]) if len(digit_positions) > keep else set(digit_positions)
    for i in hide:
        chars[i] = "*"
    letter_positions = [i for i, ch in enumerate(chars) if ch.isalpha()]
    for i in letter_positions:
        chars[i] = "*"
    return "".join(chars)


def _mask_email(original: str) -> str:
    if "@" not in original:
        return "*" * max(len(original), 4)
    local, _, domain = original.partition("@")
    local_out = (local[0] + "***") if local else "***"
    if "." in domain:
        name, _, tld = domain.rpartition(".")
        domain_out = (name[0] + "***." + tld) if name else "***." + tld
    else:
        domain_out = (domain[0] + "***") if domain else "***"
    return f"{local_out}@{domain_out}"


def generalize_value(original: str, entity_type: str) -> str:
    """Coarser value: year, ZIP3, or age band. Falls back to the original shape."""
    kind = parent_type(entity_type)
    parsed = _parse_date(original)
    if parsed is not None and (
        kind.startswith("DATE") or kind == "DATE" or _ISO_DATE.match(original.strip())
    ):
        return str(parsed.year)

    zip_match = _US_ZIP.match(original.strip())
    if zip_match:
        return zip_match.group(1)[:3] + "**"

    if kind == "ADDRESS":
        return _ZIP_IN_TEXT.sub(lambda m: m.group(1)[:3] + "**", original)

    if kind == "AGE" or (
        kind in {"", "ID"} and original.strip().isdigit() and 1 <= int(original.strip()) <= 120
    ):
        return _age_band(int(original.strip()))

    if original.strip().isdigit() and kind.startswith("DATE"):
        # year-only already
        return original.strip()

    # Unknown shape: keep year if it looks like a date, else leave a coarse token
    if parsed is not None:
        return str(parsed.year)
    return original


def _age_band(age: int) -> str:
    if age > 89:
        return "90+"
    low = (age // 10) * 10
    return f"{low}-{low + 9}"


def _parse_date(text: str) -> Optional[date]:
    stripped = text.strip()
    match = _ISO_DATE.match(stripped)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    try:
        return datetime.fromisoformat(stripped.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def shift_date_value(original: str, base_form: str) -> str:
    """Shift a date by a stable offset derived from ``base_form``."""
    parsed = _parse_date(original)
    if parsed is None:
        return original
    digest = hashlib.sha256(f"pdf-anonymizer-date-shift:{base_form}".encode()).digest()
    offset = int.from_bytes(digest[:2], "big") % 365 - 182
    shifted = parsed + timedelta(days=offset)
    # Preserve a trailing time suffix if the original had ISO time.
    rest = original.strip()[10:] if len(original.strip()) > 10 else ""
    return shifted.isoformat() + rest
