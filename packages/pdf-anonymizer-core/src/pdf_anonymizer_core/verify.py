"""Residual-PII scan for already-anonymized text.

Re-runs the cheap regex pass on the masked document and optionally asks a
language model to look again. Hits that are only stand-in labels (PERSON_1,
IBAN_LIKE_2) are ignored. The scan reports; it does not rewrite the file.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pdf_anonymizer_core.call_llm import identify_entities_with_llm
from pdf_anonymizer_core.conf import DEFAULT_REGEX_PATTERNS, DEFAULT_STATS_DIR
from pdf_anonymizer_core.regex_ner import extract_entities_via_regex
from pdf_anonymizer_core.utils import looks_like_placeholder

RESIDUAL_LLM_PROMPT = """
    You are checking an already-masked document for leftover personal details.
    Ignore stand-in labels such as PERSON_1, ORGANIZATION_2, IBAN_LIKE_1, EMAIL_3.v_1.
    List only real leftover values still written in the clear (names, emails,
    phone numbers, IDs, addresses, identity clues).

    Return a single JSON object with one key: "entities".
    Each item must have "text", "type", and "base_form".

    Text to check:
    ---
    {text}
    ---

    Respond with ONLY the JSON object.
    """


def _public_hit(entity: Dict[str, Any]) -> Dict[str, str]:
    return {
        "text": entity.get("text", ""),
        "type": str(entity.get("type", "")).upper(),
        "base_form": entity.get("base_form") or entity.get("text", ""),
    }


def scan_residual_regex(
    text: str, regex_patterns: Optional[Dict[str, str]] = None
) -> List[Dict[str, str]]:
    """Return regex hits that are not stand-in labels."""
    patterns = DEFAULT_REGEX_PATTERNS if regex_patterns is None else regex_patterns
    hits: List[Dict[str, str]] = []
    seen = set()
    for entity in extract_entities_via_regex(text, patterns):
        raw = entity["text"].strip()
        if not raw or looks_like_placeholder(raw):
            continue
        key = (raw, entity["type"])
        if key in seen:
            continue
        seen.add(key)
        hits.append(_public_hit(entity))
    return hits


def scan_residual_llm(
    text: str,
    model_name: str,
    prompt_template: str = RESIDUAL_LLM_PROMPT,
    max_retries: int = 3,
    base_retry_delay: float = 1.0,
    max_retry_delay: float = 10.0,
) -> List[Dict[str, str]]:
    """Ask a language model for leftover personal details. May return []."""
    raw_entities = identify_entities_with_llm(
        text,
        prompt_template,
        model_name,
        max_retries=max_retries,
        base_retry_delay=base_retry_delay,
        max_retry_delay=max_retry_delay,
    )
    hits: List[Dict[str, str]] = []
    seen = set()
    for entity in raw_entities:
        raw = (entity.get("text") or "").strip()
        if not raw or looks_like_placeholder(raw):
            continue
        key = (raw, str(entity.get("type", "")).upper())
        if key in seen:
            continue
        seen.add(key)
        hits.append(_public_hit(entity))
    return hits


def residual_report_path(anonymized_file_path: str) -> str:
    """``data/stats/<stem>.residual_pii.json`` next to other stats files."""
    anonymized_path = Path(anonymized_file_path)
    file_stem = anonymized_path.name.replace(
        f".anonymized{anonymized_path.suffix}", ""
    )
    if file_stem == anonymized_path.name:
        file_stem = anonymized_path.stem
    os.makedirs(DEFAULT_STATS_DIR, exist_ok=True)
    return f"{DEFAULT_STATS_DIR}/{file_stem}.residual_pii.json"


def verify_anonymized_text(
    text: str,
    *,
    anonymized_file: Optional[str] = None,
    regex_patterns: Optional[Dict[str, str]] = None,
    use_llm: bool = False,
    model_name: Optional[str] = None,
    max_retries: int = 3,
    base_retry_delay: float = 1.0,
    max_retry_delay: float = 10.0,
) -> Dict[str, Any]:
    """Scan masked text. Never rewrites it.

    Returns a report dict with regex_hits, optional llm_hits, and counts.
    """
    regex_hits = scan_residual_regex(text, regex_patterns)
    llm_hits: List[Dict[str, str]] = []
    if use_llm:
        if not model_name:
            raise ValueError("model_name is required when use_llm is True")
        llm_hits = scan_residual_llm(
            text,
            model_name,
            max_retries=max_retries,
            base_retry_delay=base_retry_delay,
            max_retry_delay=max_retry_delay,
        )

    report: Dict[str, Any] = {
        "anonymized_file": anonymized_file,
        "regex_hits": regex_hits,
        "llm_hits": llm_hits,
        "residual_count": len(regex_hits) + len(llm_hits),
        "rewritten": False,
    }
    return report


def write_residual_report(report: Dict[str, Any], anonymized_file_path: str) -> str:
    """Write the report JSON and return its path."""
    path = residual_report_path(anonymized_file_path)
    report = dict(report)
    report["anonymized_file"] = anonymized_file_path
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=4)
    return path
