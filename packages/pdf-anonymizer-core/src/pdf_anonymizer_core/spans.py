"""Locate and apply non-overlapping replacement intervals.

Entity texts are found in the full document with the same word-boundary
rules as before. Longer intervals win when two hits overlap, so
``John Doe`` is replaced and the inner ``John`` is left alone.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Sequence, Tuple

Span = Tuple[int, int, str]


def make_boundary_pattern(text: str) -> str:
    """Word-boundary wrap when the first/last character is alphanumeric."""
    prefix = r"\b" if text[0].isalnum() or text[0] == "_" else ""
    suffix = r"\b" if text[-1].isalnum() or text[-1] == "_" else ""
    return f"{prefix}{re.escape(text)}{suffix}"


def locate_spans(full_text: str, entity_texts: Iterable[str]) -> List[Span]:
    """Find every bounded occurrence of each entity text in ``full_text``."""
    spans: List[Span] = []
    seen = set()
    for text in entity_texts:
        if not text or text in seen:
            continue
        seen.add(text)
        pattern = re.compile(make_boundary_pattern(text))
        for match in pattern.finditer(full_text):
            spans.append((match.start(), match.end(), text))
    return spans


def _overlaps(start: int, end: int, taken: Sequence[Tuple[int, int]]) -> bool:
    for taken_start, taken_end in taken:
        if not (end <= taken_start or start >= taken_end):
            return True
    return False


def pick_non_overlapping(spans: Sequence[Span]) -> List[Span]:
    """Keep longest spans first; drop any that overlap an accepted span."""
    ordered = sorted(spans, key=lambda item: (item[1] - item[0], -item[0]), reverse=True)
    accepted: List[Span] = []
    taken: List[Tuple[int, int]] = []
    for start, end, text in ordered:
        if _overlaps(start, end, taken):
            continue
        accepted.append((start, end, text))
        taken.append((start, end))
    return accepted


def apply_spans(full_text: str, spans: Sequence[Span], mapping: Dict[str, str]) -> str:
    """Write replacements from the end of the string so earlier offsets stay valid."""
    pieces = list(full_text)
    # Walk right-to-left so later slices do not shift earlier indexes.
    for start, end, text in sorted(spans, key=lambda item: item[0], reverse=True):
        replacement = mapping.get(text)
        if replacement is None:
            continue
        pieces[start:end] = list(replacement)
    return "".join(pieces)


def replace_entities(full_text: str, entity_texts: Iterable[str], mapping: Dict[str, str]) -> str:
    """Locate, resolve overlaps, and replace. Empty entity list is a no-op."""
    texts = [text for text in entity_texts if text]
    if not texts:
        return full_text
    spans = pick_non_overlapping(locate_spans(full_text, texts))
    return apply_spans(full_text, spans, mapping)
