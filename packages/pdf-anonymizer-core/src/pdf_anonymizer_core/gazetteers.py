"""Keep-lists and deny-lists (gazetteers).

Keep-list: never replace this phrase, even if regex or the model found it.
Deny-list: always replace this phrase, even if both stages missed it.

If a phrase is on both lists, keep wins (it stays visible).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


def load_phrase_list(path: str) -> List[str]:
    """Load one phrase per line. Blank lines and # comments are ignored."""
    phrases: List[str] = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        phrases.append(line)
    return phrases


def apply_keep_list(
    entities: Sequence[Dict[str, str]], phrases: Iterable[str]
) -> List[Dict[str, str]]:
    """Drop entities whose text or base form is on the keep-list (case-insensitive)."""
    skip = {phrase.lower() for phrase in phrases if phrase}
    if not skip:
        return list(entities)
    kept: List[Dict[str, str]] = []
    for entity in entities:
        text = (entity.get("text") or "").lower()
        base = (entity.get("base_form") or "").lower()
        if text in skip or base in skip:
            continue
        kept.append(entity)
    return kept


def apply_deny_list(
    text: str, entities: Sequence[Dict[str, str]], phrases: Iterable[str]
) -> List[Dict[str, str]]:
    """Add a CUSTOM entity for each deny-list phrase that appears in ``text``."""
    extra: List[Dict[str, str]] = []
    already = {(entity.get("text") or "").lower() for entity in entities}
    for phrase in phrases:
        if not phrase or phrase.lower() in already:
            continue
        match = re.search(re.escape(phrase), text, flags=re.IGNORECASE)
        if not match:
            continue
        found = match.group(0)
        extra.append({"text": found, "type": "CUSTOM", "base_form": found})
        already.add(found.lower())
    return list(entities) + extra
