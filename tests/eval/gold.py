"""Gold-corpus loaders, public-source converters, and leftover helpers.

Downloaded files live under ``data/gold-corpus/`` (gitignored). The committed
mini fixture and domain pack are always available.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from pdf_anonymizer_core.spans import make_boundary_pattern

from tests.eval.metrics import evaluate_fixture, mention_kind

EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parents[1]
DEFAULT_DEST = REPO_ROOT / "data" / "gold-corpus"
SOURCES_PATH = EVAL_DIR / "sources.json"
DOMAIN_PACK_PATH = EVAL_DIR / "domain_pack.json"
MINI_TAB_PATH = EVAL_DIR / "fixture.json"
BASELINE_PATH = EVAL_DIR / "baselines" / "gold_corpus_regex_only.json"

STRUCTURED_TYPES = frozenset(
    {
        "EMAIL",
        "PHONE",
        "FAX",
        "SSN",
        "SSN_US",
        "CREDIT_CARD",
        "CREDIT_CARD_LIKE",
        "IBAN",
        "IBAN_LIKE",
        "IPV4_ADDRESS",
        "IPV6_ADDRESS",
        "IP_ADDRESS",
        "DATE_ISO",
    }
)

# Residual-scan CI gate (plan item 19): emails, cards, IBANs, phones, IPs, SSNs.
RED_TEAM_TYPES = frozenset(
    {
        "EMAIL",
        "PHONE",
        "FAX",
        "SSN",
        "SSN_US",
        "CREDIT_CARD",
        "CREDIT_CARD_LIKE",
        "IBAN",
        "IBAN_LIKE",
        "IPV4_ADDRESS",
        "IPV6_ADDRESS",
        "IP_ADDRESS",
    }
)

CI_GOLD_SOURCES = ("mini-tab", "domain-pack")
STRUCTURED_LEFTOVER_CEILING = 0.0
DOWNLOADED_STRUCTURED_LEFTOVER_CEILING = 0.10


def _type_name(mention: Dict[str, Any]) -> str:
    return str(mention.get("type") or "").upper()


def is_structured_type(typ: str) -> bool:
    name = str(typ or "").upper()
    return name in STRUCTURED_TYPES or name.endswith("_LIKE")


def is_red_team_type(typ: str) -> bool:
    name = str(typ or "").upper()
    if name in RED_TEAM_TYPES:
        return True
    if name.endswith("_LIKE") and name[: -len("_LIKE")] in RED_TEAM_TYPES:
        return True
    return False


def structured_mentions(mentions: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [mention for mention in mentions if is_structured_type(_type_name(mention))]


def structured_residual_hits(hits: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [hit for hit in hits if is_red_team_type(str(hit.get("type") or ""))]


# Source label -> (package type, default kind). Kind is overridden when the
# source already marks DIRECT vs QUASI.
_TYPE_MAP: Dict[str, Tuple[str, str]] = {
    # TAB (Pilán et al. 2022)
    "person": ("PERSON", "direct"),
    "code": ("ID", "direct"),
    "loc": ("LOCATION", "quasi"),
    "org": ("ORGANIZATION", "quasi"),
    "dem": ("INDIRECT", "quasi"),
    "datetime": ("DATE", "quasi"),
    "quantity": ("INDIRECT", "quasi"),
    "misc": ("INDIRECT", "quasi"),
    # Presidio synth
    "email_address": ("EMAIL", "direct"),
    "email": ("EMAIL", "direct"),
    "phone_number": ("PHONE", "direct"),
    "phone": ("PHONE", "direct"),
    "us_ssn": ("SSN", "direct"),
    "ssn": ("SSN", "direct"),
    "credit_card": ("CREDIT_CARD", "direct"),
    "credit_card_number": ("CREDIT_CARD", "direct"),
    "iban_code": ("IBAN", "direct"),
    "iban": ("IBAN", "direct"),
    "ip_address": ("IPV4_ADDRESS", "direct"),
    "ipv4": ("IPV4_ADDRESS", "direct"),
    "ipv4_address": ("IPV4_ADDRESS", "direct"),
    "location": ("LOCATION", "quasi"),
    "city": ("LOCATION", "quasi"),
    "country": ("LOCATION", "quasi"),
    "street_address": ("ADDRESS", "quasi"),
    "address": ("ADDRESS", "quasi"),
    "date_time": ("DATE", "quasi"),
    "date": ("DATE", "quasi"),
    "date_of_birth": ("DATE", "quasi"),
    "organization": ("ORGANIZATION", "quasi"),
    "nrp": ("INDIRECT", "quasi"),
    "title": ("JOB_TITLE", "quasi"),
    "age": ("AGE", "quasi"),
    "us_driver_license": ("DRIVERS_LICENSE_US", "direct"),
    "us_bank_number": ("ACCOUNT", "direct"),
    # Gretel / industry labels
    "name": ("PERSON", "direct"),
    "first_name": ("PERSON", "direct"),
    "last_name": ("PERSON", "direct"),
    "user_name": ("ID", "direct"),
    "username": ("ID", "direct"),
    "account_number": ("ACCOUNT", "direct"),
    "unique_identifier": ("ID", "direct"),
    "medical_record_number": ("MEDICAL_RECORD", "direct"),
    "medical_record": ("MEDICAL_RECORD", "direct"),
    "npi": ("MEDICAL_NPI_US", "direct"),
}

_DOMAIN_KEYWORDS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("healthcare", ("health", "medical", "clinical", "pharma", "hospital", "phi")),
    ("legal", ("legal", "law", "court", "contract", "counsel")),
    ("government", ("government", "public", "civic", "immigration", "census", "tax")),
    ("research", ("research", "academic", "education", "survey", "university", "irb")),
    ("finance", ("bank", "finance", "insur", "credit", "fintech", "account")),
    ("identity", ("identity", "kyc", "verification")),
    ("enterprise", ("enterprise", "cyber", "support", "ticket", "hr")),
)


def load_sources_catalog() -> Dict[str, Any]:
    return json.loads(SOURCES_PATH.read_text(encoding="utf-8"))


def map_entity_type(raw: str) -> Tuple[str, str]:
    key = str(raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    return _TYPE_MAP.get(key, (str(raw or "MISC").upper(), "other"))


def infer_domain(raw: Optional[str], fallback: str = "general") -> str:
    if not raw:
        return fallback
    blob = str(raw).lower()
    for domain, keys in _DOMAIN_KEYWORDS:
        if domain in blob or any(key in blob for key in keys):
            return domain
    return fallback


def ensure_offsets(document: Dict[str, Any]) -> Dict[str, Any]:
    text = str(document.get("text") or "")
    for mention in document.get("mentions") or []:
        if isinstance(mention.get("start"), int) and isinstance(
            mention.get("end"), int
        ):
            continue
        value = str(mention.get("text") or "")
        if not value:
            continue
        idx = text.find(value)
        if idx >= 0:
            mention["start"] = idx
            mention["end"] = idx + len(value)
    return document


def mention_still_present(text: str, mention_text: str) -> bool:
    value = (mention_text or "").strip()
    if not value:
        return False
    try:
        return re.search(make_boundary_pattern(value), text) is not None
    except re.error:
        return value in text


def leftover_mentions(
    gold: Sequence[Dict[str, Any]], anonymized_text: str
) -> List[Dict[str, Any]]:
    return [
        mention
        for mention in gold
        if mention_still_present(anonymized_text, str(mention.get("text") or ""))
    ]


def leftover_report(
    gold: Sequence[Dict[str, Any]], anonymized_text: str
) -> Dict[str, Any]:
    left = leftover_mentions(gold, anonymized_text)
    structured_gold = structured_mentions(list(gold))
    structured_left = structured_mentions(left)
    gold_n = len(gold)
    structured_n = len(structured_gold)
    return {
        "leftover": len(left),
        "gold": gold_n,
        "leftover_rate": (len(left) / gold_n) if gold_n else 0.0,
        "structured_leftover": len(structured_left),
        "structured_gold": structured_n,
        "structured_leftover_rate": (
            (len(structured_left) / structured_n) if structured_n else 0.0
        ),
    }


def _mention(
    text: str,
    raw_type: str,
    *,
    start: Optional[int] = None,
    end: Optional[int] = None,
    kind: Optional[str] = None,
    base_form: Optional[str] = None,
) -> Dict[str, Any]:
    mapped_type, default_kind = map_entity_type(raw_type)
    item: Dict[str, Any] = {
        "text": text,
        "type": mapped_type,
        "kind": kind or default_kind,
        "base_form": base_form or text,
    }
    if isinstance(start, int) and isinstance(end, int):
        item["start"] = start
        item["end"] = end
    return item


def convert_tab_document(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Union DIRECT/QUASI mentions across annotators (privacy-conservative)."""
    text = str(raw.get("text") or "")
    seen: Dict[Tuple[int, int, str], Dict[str, Any]] = {}
    annotations = raw.get("annotations") or {}
    for _annotator, payload in annotations.items():
        mentions = (payload or {}).get("entity_mentions") or []
        for mention in mentions:
            identifier = str(mention.get("identifier_type") or "").upper()
            if identifier not in {"DIRECT", "QUASI"}:
                continue
            start = mention.get("start_offset")
            end = mention.get("end_offset")
            if mention.get("span_text"):
                span = str(mention["span_text"])
            elif isinstance(start, int) and isinstance(end, int):
                span = text[start:end]
            else:
                span = ""
            if not span:
                continue
            key = (int(start), int(end), span)
            kind = "direct" if identifier == "DIRECT" else "quasi"
            current = seen.get(key)
            if current is None or (
                kind == "direct" and current.get("kind") != "direct"
            ):
                seen[key] = _mention(
                    span,
                    str(mention.get("entity_type") or "MISC"),
                    start=int(start),
                    end=int(end),
                    kind=kind,
                    base_form=str(mention.get("entity_id") or span),
                )
    return ensure_offsets(
        {
            "name": f"tab-{raw.get('doc_id', 'doc')}",
            "source": "tab",
            "domain": "legal",
            "split": raw.get("dataset_type"),
            "text": text,
            "mentions": list(seen.values()),
        }
    )


def convert_presidio_document(raw: Dict[str, Any], index: int) -> Dict[str, Any]:
    text = str(raw.get("full_text") or raw.get("text") or "")
    mentions: List[Dict[str, Any]] = []
    for span in raw.get("spans") or []:
        value = str(span.get("entity_value") or "")
        if not value:
            continue
        mentions.append(
            _mention(
                value,
                str(span.get("entity_type") or "MISC"),
                start=span.get("start_position"),
                end=span.get("end_position"),
            )
        )
    return ensure_offsets(
        {
            "name": f"presidio-{index:04d}",
            "source": "presidio",
            "domain": "general",
            "text": text,
            "mentions": mentions,
        }
    )


def convert_gretel_document(raw: Dict[str, Any]) -> Dict[str, Any]:
    text = str(raw.get("text") or "")
    entities = raw.get("entities") or []
    if isinstance(entities, str):
        try:
            entities = json.loads(entities)
        except json.JSONDecodeError:
            entities = ast.literal_eval(entities)
    mentions: List[Dict[str, Any]] = []
    for entity in entities:
        value = str(entity.get("entity") or "").strip()
        types = entity.get("types") or []
        raw_type = types[0] if types else "MISC"
        if not value:
            continue
        mentions.append(_mention(value, str(raw_type)))
    return ensure_offsets(
        {
            "name": f"gretel-{raw.get('uid') or raw.get('name') or 'doc'}",
            "source": "gretel",
            "domain": infer_domain(raw.get("domain"), "general"),
            "gretel_domain": raw.get("domain"),
            "document_type": raw.get("document_type"),
            "text": text,
            "mentions": mentions,
        }
    )


def iter_json_array_or_object(path: Path) -> Iterable[Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    return [payload]


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")
            count += 1
    return count


def load_domain_pack() -> List[Dict[str, Any]]:
    payload = json.loads(DOMAIN_PACK_PATH.read_text(encoding="utf-8"))
    docs = []
    for raw in payload.get("documents") or []:
        doc = {
            "name": raw.get("name"),
            "source": "domain-pack",
            "domain": raw.get("domain") or "general",
            "text": raw.get("text") or "",
            "mentions": list(raw.get("mentions") or []),
        }
        docs.append(ensure_offsets(doc))
    return docs


def load_mini_tab() -> List[Dict[str, Any]]:
    fixture = json.loads(MINI_TAB_PATH.read_text(encoding="utf-8"))
    return [
        ensure_offsets(
            {
                "name": fixture.get("name", "mini-tab"),
                "source": "mini-tab",
                "domain": "general",
                "text": fixture.get("text") or "",
                "mentions": list(fixture.get("mentions") or []),
            }
        )
    ]


def load_normalized_source(path: Path) -> List[Dict[str, Any]]:
    if path.suffix == ".jsonl":
        return [ensure_offsets(row) for row in iter_jsonl(path)]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "documents" in payload:
        return [ensure_offsets(row) for row in payload["documents"]]
    if isinstance(payload, list):
        return [ensure_offsets(row) for row in payload]
    return [ensure_offsets(payload)]


def load_gold_corpus(
    dest: Path = DEFAULT_DEST,
    sources: Optional[Sequence[str]] = None,
    max_docs: Optional[int] = None,
    include_committed: bool = True,
) -> List[Dict[str, Any]]:
    wanted = set(sources) if sources else None
    documents: List[Dict[str, Any]] = []

    if include_committed:
        if wanted is None or "mini-tab" in wanted:
            documents.extend(load_mini_tab())
        if wanted is None or "domain-pack" in wanted:
            documents.extend(load_domain_pack())

    normalized = dest / "normalized"
    if normalized.is_dir():
        for path in sorted(normalized.glob("*.jsonl")):
            source_id = path.stem
            if wanted is not None and source_id not in wanted:
                continue
            documents.extend(load_normalized_source(path))

    if max_docs is not None:
        documents = documents[: max(0, max_docs)]
    return documents


def evaluate_documents(
    documents: Sequence[Dict[str, Any]],
    predicted: Sequence[Sequence[Dict[str, Any]]],
) -> Dict[str, Any]:
    gold: List[Dict[str, Any]] = []
    pred: List[Dict[str, Any]] = []
    for document, hits in zip(documents, predicted):
        gold.extend(document.get("mentions") or [])
        pred.extend(hits)
    fixture = {"name": "gold-corpus", "mentions": gold}
    report = evaluate_fixture(fixture, pred)
    report["documents"] = len(documents)
    report["gold_mentions"] = len(gold)
    report["predicted_mentions"] = len(pred)
    return report


def group_key(document: Dict[str, Any], field: str) -> str:
    return str(document.get(field) or "unknown")


def mentions_by_kind(
    mentions: Iterable[Dict[str, Any]], kind: str
) -> List[Dict[str, Any]]:
    return [mention for mention in mentions if mention_kind(mention) == kind]
