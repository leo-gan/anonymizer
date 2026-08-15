"""Linkage-risk report for already-masked text.

A name can be gone and the page can still point to one person: job + company
+ city in the same paragraph. This module only *scores* those clumps. It does
not change the file.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from pdf_anonymizer_core.conf import DEFAULT_STATS_DIR

_PLACEHOLDER = re.compile(r"\b([A-Z][A-Z0-9_]*_[0-9]+(?:\.v_[0-9]+)?)\b")

QUASI_TYPES = frozenset(
    {
        "PERSON",
        "JOB_TITLE",
        "ORGANIZATION",
        "LOCATION",
        "ADDRESS",
        "DATE",
        "DATE_ISO",
        "AGE",
        "INDIRECT",
    }
)

_IDENTITY_CORE = frozenset(
    {"PERSON", "JOB_TITLE", "ORGANIZATION", "LOCATION", "ADDRESS", "INDIRECT"}
)

HIGH_REASONS = {
    "indirect": "A nameless phrase that still points to one person sits in this passage.",
    "job_org_place": "A job, a company, and a place sit together (the 'CEO of Tesla in Austin' pattern).",
    "person_org_place": "A person, a company, and a place sit together.",
    "person_job_org": "A person, a job, and a company sit together.",
    "three_clues": "Three or more identity clues sit in the same passage.",
}

LEVEL_ORDER = {"low": 1, "medium": 2, "high": 3}


def placeholder_type(token: str) -> str:
    """PERSON_1.v_2 → PERSON; IBAN_LIKE_1 → IBAN_LIKE."""
    base = token.split(".v_")[0]
    if "_" not in base:
        return base
    name, _, maybe_num = base.rpartition("_")
    if maybe_num.isdigit():
        return name
    return base


def _windows(text: str) -> List[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not parts:
        return [text] if text.strip() else []
    # Split very long paragraphs so one wall of text is not one giant window.
    windows: List[str] = []
    for part in parts:
        if len(part) <= 800:
            windows.append(part)
            continue
        for i in range(0, len(part), 600):
            chunk = part[i : i + 800].strip()
            if chunk:
                windows.append(chunk)
    return windows


def _score_types(types: Sequence[str]) -> Tuple[str, str]:
    present = set(types)
    quasi = present & QUASI_TYPES
    core = present & _IDENTITY_CORE

    if "INDIRECT" in quasi:
        return "high", HIGH_REASONS["indirect"]
    if {"JOB_TITLE", "ORGANIZATION", "LOCATION"} <= quasi:
        return "high", HIGH_REASONS["job_org_place"]
    if {"PERSON", "ORGANIZATION", "LOCATION"} <= quasi:
        return "high", HIGH_REASONS["person_org_place"]
    if {"PERSON", "JOB_TITLE", "ORGANIZATION"} <= quasi:
        return "high", HIGH_REASONS["person_job_org"]
    if len(core) >= 3:
        return "high", HIGH_REASONS["three_clues"]
    if len(core) >= 2 or (
        "PERSON" in quasi and ({"DATE", "DATE_ISO", "AGE"} & quasi)
    ):
        return "medium", "Two identity clues sit in the same passage."
    if quasi:
        return "low", "Only one kind of identity clue is in this passage."
    return "low", "No identity-clue combination in this passage."


def assess_linkage_risk(text: str) -> Dict[str, Any]:
    """Score identity-clue clumps in masked text. Does not rewrite it."""
    findings: List[Dict[str, Any]] = []
    overall = "low"
    for excerpt in _windows(text):
        tokens = _PLACEHOLDER.findall(excerpt)
        if not tokens:
            continue
        types = sorted({placeholder_type(tok) for tok in tokens})
        quasi_here = [t for t in types if t in QUASI_TYPES]
        if not quasi_here:
            continue
        level, reason = _score_types(types)
        if LEVEL_ORDER[level] > LEVEL_ORDER[overall]:
            overall = level
        findings.append(
            {
                "level": level,
                "types": quasi_here,
                "placeholders": sorted(set(tokens)),
                "excerpt": excerpt if len(excerpt) <= 280 else excerpt[:277] + "...",
                "reason": reason,
            }
        )

    # Singleton combos (a set of placeholders that appear in only one window)
    # stay at least medium — that is the "rare combination" signal.
    combo_counts: Dict[Tuple[str, ...], int] = {}
    for finding in findings:
        key = tuple(sorted(finding["placeholders"]))
        combo_counts[key] = combo_counts.get(key, 0) + 1
    for finding in findings:
        key = tuple(sorted(finding["placeholders"]))
        if combo_counts.get(key, 0) == 1 and len(finding["types"]) >= 2:
            if LEVEL_ORDER[finding["level"]] < LEVEL_ORDER["medium"]:
                finding["level"] = "medium"
                finding["reason"] = (
                    "This mix of clues appears only once, so it is easier to pin on one person."
                )
            if LEVEL_ORDER[finding["level"]] > LEVEL_ORDER[overall]:
                overall = finding["level"]

    return {
        "overall": overall,
        "window_count": len(findings),
        "high_count": sum(1 for f in findings if f["level"] == "high"),
        "medium_count": sum(1 for f in findings if f["level"] == "medium"),
        "low_count": sum(1 for f in findings if f["level"] == "low"),
        "windows": findings,
        "rewritten": False,
    }


def assess_entity_list(entities: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Score a flat entity list as one window (no positions). Does not rewrite."""
    types = sorted(
        {
            str(ent.get("type", "")).upper()
            for ent in entities
            if ent.get("type")
        }
    )
    if not types:
        return {
            "overall": "low",
            "window_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "windows": [],
            "rewritten": False,
        }
    level, reason = _score_types(types)
    texts = [str(ent.get("text", "")) for ent in entities if ent.get("text")]
    finding = {
        "level": level,
        "types": [t for t in types if t in QUASI_TYPES],
        "placeholders": [],
        "excerpt": "; ".join(texts)[:280],
        "reason": reason,
    }
    return {
        "overall": level,
        "window_count": 1,
        "high_count": int(level == "high"),
        "medium_count": int(level == "medium"),
        "low_count": int(level == "low"),
        "windows": [finding],
        "rewritten": False,
    }


def risk_report_path(anonymized_file_path: str) -> str:
    anonymized_path = Path(anonymized_file_path)
    file_stem = anonymized_path.name.replace(
        f".anonymized{anonymized_path.suffix}", ""
    )
    if file_stem == anonymized_path.name:
        file_stem = anonymized_path.stem
    os.makedirs(DEFAULT_STATS_DIR, exist_ok=True)
    return f"{DEFAULT_STATS_DIR}/{file_stem}.risk.json"


def write_risk_report(report: Dict[str, Any], anonymized_file_path: str) -> str:
    path = risk_report_path(anonymized_file_path)
    payload = dict(report)
    payload["anonymized_file"] = anonymized_file_path
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4)
    return path
