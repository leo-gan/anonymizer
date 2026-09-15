"""RE2 scan plus checksum relabel. Returns placements, never replacements."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

import re2 as re

from id_extract.checksums import has_checksum, passes_checksum
from id_extract.plugins import patterns as load_patterns
from id_extract.types import Entity, like_type


def extract(
    text: str,
    patterns: Optional[Dict[str, str]] = None,
    *,
    countries: Optional[Iterable[str] | str] = "all",
) -> List[Entity]:
    """Scan ``text`` for structured identifiers.

    ``patterns``, when given, is used as-is. Otherwise the bundled map for
    ``countries`` is loaded. The default is every bundled country plus the
    universal patterns.

    Matches that fail a registered checksum are kept and labeled
    ``<TYPE>_LIKE`` (for example ``IBAN_LIKE``). Offsets are character
    indexes in ``text``.
    """
    compiled = patterns if patterns is not None else load_patterns(countries)
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

    return entities
