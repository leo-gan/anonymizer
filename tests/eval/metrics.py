"""Mention-level and entity-level scores, split by direct vs quasi identifiers.

TAB (Pilán et al., 2022) reports these separately because quasi-identifiers
are common and can hide a poor score on names and emails.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Set, Tuple

DIRECT_TYPES = frozenset(
    {
        "PERSON",
        "EMAIL",
        "PHONE",
        "FAX",
        "SSN",
        "SSN_US",
        "CREDIT_CARD",
        "CREDIT_CARD_LIKE",
        "IBAN",
        "IBAN_LIKE",
        "ID",
        "ACCOUNT",
        "MEDICAL_RECORD",
        "HEALTH_PLAN_ID",
    }
)
QUASI_TYPES = frozenset(
    {
        "LOCATION",
        "ADDRESS",
        "DATE",
        "DATE_ISO",
        "ORGANIZATION",
        "JOB_TITLE",
        "AGE",
        "INDIRECT",
    }
)


def mention_key(mention: Dict[str, Any]) -> Tuple[Any, ...]:
    """Prefer exact offsets; fall back to lowercase text."""
    start, end = mention.get("start"), mention.get("end")
    text = str(mention.get("text", "")).strip().lower()
    if isinstance(start, int) and isinstance(end, int):
        return ("span", start, end, text)
    return ("text", text)


def entity_key(mention: Dict[str, Any]) -> Tuple[str, str]:
    kind = mention_kind(mention)
    base = str(mention.get("base_form") or mention.get("text") or "").strip().lower()
    return (kind, base)


def mention_kind(mention: Dict[str, Any]) -> str:
    if mention.get("kind") in {"direct", "quasi"}:
        return str(mention["kind"])
    typ = str(mention.get("type", "")).upper()
    if typ in DIRECT_TYPES or typ.startswith("SSN"):
        return "direct"
    if typ in QUASI_TYPES:
        return "quasi"
    return "other"


def _prf(true_pos: int, pred_n: int, gold_n: int) -> Dict[str, float]:
    precision = true_pos / pred_n if pred_n else 0.0
    recall = true_pos / gold_n if gold_n else 0.0
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": true_pos,
        "predicted": pred_n,
        "gold": gold_n,
    }


def mention_scores(
    gold: Iterable[Dict[str, Any]], predicted: Iterable[Dict[str, Any]]
) -> Dict[str, float]:
    gold_keys = [mention_key(item) for item in gold]
    pred_keys = [mention_key(item) for item in predicted]
    gold_set: Set[Tuple[Any, ...]] = set(gold_keys)
    matched = 0
    used: Set[Tuple[Any, ...]] = set()
    for key in pred_keys:
        if key in gold_set and key not in used:
            matched += 1
            used.add(key)
    return _prf(matched, len(pred_keys), len(gold_keys))


def entity_recall(
    gold: Iterable[Dict[str, Any]], predicted: Iterable[Dict[str, Any]]
) -> Dict[str, float]:
    gold_entities = {entity_key(item) for item in gold}
    pred_entities = {entity_key(item) for item in predicted}
    hit = len(gold_entities & pred_entities)
    return _prf(hit, len(pred_entities), len(gold_entities))


def scores_by_kind(
    gold: List[Dict[str, Any]], predicted: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    report: Dict[str, Dict[str, Any]] = {"all": {}}
    report["all"]["mention"] = mention_scores(gold, predicted)
    report["all"]["entity"] = entity_recall(gold, predicted)
    for kind in ("direct", "quasi"):
        gold_k = [item for item in gold if mention_kind(item) == kind]
        pred_k = [item for item in predicted if mention_kind(item) == kind]
        report[kind] = {
            "mention": mention_scores(gold_k, pred_k),
            "entity": entity_recall(gold_k, pred_k),
        }
    return report


def evaluate_fixture(
    fixture: Dict[str, Any], predicted: List[Dict[str, Any]]
) -> Dict[str, Any]:
    gold = list(fixture.get("mentions") or [])
    return {
        "name": fixture.get("name", "fixture"),
        "scores": scores_by_kind(gold, predicted),
    }
