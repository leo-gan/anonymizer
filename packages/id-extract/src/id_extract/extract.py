"""RE2 scan plus checksum relabel. Returns placements, never replacements."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

import re2 as re

from id_extract.checksums import has_checksum, passes_checksum, strict_checksum
from id_extract.plugins import patterns as load_patterns
from id_extract.types import Entity, like_type

# Same span: drop the broader label when the specific one also matched.
_PREFERRED_OVER = {
    "ITIN_US": ("SSN_US", "SSN"),
    "ATIN_US": ("SSN_US", "SSN"),
    "DEA_US": ("MEDICAL_LICENSE_US",),
    "PTIN_US": ("MEDICAL_LICENSE_US",),
    "A_NUMBER_US": ("MEDICAL_LICENSE_US",),
    "DL_FL_US": ("DRIVERS_LICENSE_US",),
    "DL_ON_CA": ("DRIVERS_LICENSE_CA",),
    "USCIS_RECEIPT_US": ("DOS_CASE_US",),
    "PHN_BC_CA": ("MEDICAL_NPI_US", "MEDICAL_NPI_US_LIKE"),
    "CLABE_MX": ("CREDIT_CARD", "CREDIT_CARD_LIKE"),
}


def extract(
    text: str,
    patterns: Optional[Dict[str, str]] = None,
    *,
    countries: Optional[Iterable[str] | str] = "all",
    opt_in: Optional[Iterable[str] | str | bool] = None,
) -> List[Entity]:
    """Scan ``text`` for structured identifiers.

    ``patterns``, when given, is used as-is and ``countries`` / ``opt_in``
    are ignored. Otherwise the bundled map for ``countries`` is loaded.
    The default is every bundled country plus the universal patterns, and
    no state, provincial, or industry pattern.

    Matches that fail a registered checksum are kept and labeled
    ``<TYPE>_LIKE`` (for example ``IBAN_LIKE``), unless the type is strict.
    A strict failure is dropped. Offsets are character indexes in ``text``.
    """
    compiled = (
        patterns if patterns is not None else load_patterns(countries, opt_in=opt_in)
    )
    entities: List[Entity] = []

    for entity_type, pattern_str in compiled.items():
        try:
            compiled_pattern = re.compile(pattern_str)
            for match in compiled_pattern.finditer(text):
                matched_text = match.group(0)
                if not matched_text.strip():
                    continue

                entity_type_upper = entity_type.upper()
                if has_checksum(entity_type_upper) and not passes_checksum(
                    entity_type_upper, matched_text
                ):
                    if strict_checksum(entity_type_upper):
                        continue
                    like = like_type(entity_type_upper)
                    logging.debug(
                        "Checksum failed for %s %r; labeling as %s",
                        entity_type_upper,
                        matched_text,
                        like,
                    )
                    entity_type_upper = like
                    score = 0.55
                elif has_checksum(entity_type_upper):
                    score = 0.95
                else:
                    score = 0.85

                entities.append(
                    {
                        "text": matched_text,
                        "type": entity_type_upper,
                        "base_form": matched_text,
                        "start": match.start(),
                        "end": match.end(),
                        "score": score,
                        "source": "regex",
                    }
                )
        except re.error as e:
            logging.error("Invalid regex pattern configured for %s: %s", entity_type, e)

    return _drop_broader_labels(entities)


def _drop_broader_labels(entities: List[Entity]) -> List[Entity]:
    """Keep the specific type when it occupies the same span as a broader one."""
    by_span: Dict[tuple[int, int], set[str]] = {}
    for entity in entities:
        span = (entity["start"], entity["end"])
        by_span.setdefault(span, set()).add(entity["type"])
    dropped: Dict[tuple[int, int], set[str]] = {}
    for span, types in by_span.items():
        losers = {
            loser
            for winner, broader in _PREFERRED_OVER.items()
            if winner in types
            for loser in broader
            if loser in types
        }
        if losers:
            dropped[span] = losers
    if not dropped:
        return entities
    return [
        entity
        for entity in entities
        if entity["type"] not in dropped.get((entity["start"], entity["end"]), ())
    ]
