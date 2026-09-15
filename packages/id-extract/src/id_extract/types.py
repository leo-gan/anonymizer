"""Entity record and type-name helpers shared with the anonymizer."""

from __future__ import annotations

from typing import List, Set, TypedDict


class Entity(TypedDict):
    text: str
    type: str
    base_form: str
    start: int
    end: int
    score: float
    source: str


LIKE_SUFFIX = "_LIKE"


def like_type(entity_type: str) -> str:
    """``IBAN`` -> ``IBAN_LIKE``."""
    return f"{entity_type.upper()}{LIKE_SUFFIX}"


def parent_type(entity_type: str) -> str:
    """``IBAN_LIKE`` -> ``IBAN``; ``IBAN`` -> ``IBAN``."""
    upper = entity_type.upper()
    if upper.endswith(LIKE_SUFFIX) and len(upper) > len(LIKE_SUFFIX):
        return upper[: -len(LIKE_SUFFIX)]
    return upper


def type_matches_filter(entity_type: str, allowed: List[str] | Set[str]) -> bool:
    """True if the type is listed, is a ``_LIKE`` sibling, or matches a prefix.

    A listed ``DRIVERS_LICENSE`` matches ``DRIVERS_LICENSE_US``.
    A listed ``DATE`` matches ``DATE_ISO``.
    """
    allowed_upper = {item.upper() for item in allowed}
    upper = entity_type.upper()
    parent = parent_type(upper)
    if upper in allowed_upper or parent in allowed_upper:
        return True
    for item in allowed_upper:
        if upper.startswith(item + "_") or parent.startswith(item + "_"):
            return True
        if upper.endswith("_" + item) or parent.endswith("_" + item):
            return True
    return False
