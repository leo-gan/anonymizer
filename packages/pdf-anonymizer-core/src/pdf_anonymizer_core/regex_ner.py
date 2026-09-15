"""Compatibility wrapper around ``id_extract.extract``.

The hybrid pipeline still calls this name. Detection lives in the
``id-extract`` package. This module does not replace text.
"""

from __future__ import annotations

from typing import Dict, List

from id_extract import extract
from id_extract.types import Entity as EntityDict


def extract_entities_via_regex(text: str, patterns: Dict[str, str]) -> List[EntityDict]:
    """Scan ``text`` with the given RE2 map. See ``id_extract.extract``."""
    return extract(text, patterns=patterns)
