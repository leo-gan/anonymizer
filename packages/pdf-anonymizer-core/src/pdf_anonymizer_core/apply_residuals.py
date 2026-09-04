"""Apply leftover hits from a residual report (item 23).

The leftover scan is still report-only by default. This module rewrites
an already-masked file when the caller accepts some of those hits.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from pdf_anonymizer_core.conf import DEFAULT_MAPPINGS_DIR
from pdf_anonymizer_core.core import build_mapping
from pdf_anonymizer_core.gazetteers import load_phrase_list
from pdf_anonymizer_core.mapping_crypto import encrypt_mapping
from pdf_anonymizer_core.secure_io import write_private_json
from pdf_anonymizer_core.spans import replace_entities
from pdf_anonymizer_core.tables import (
    is_tabular_path,
    write_anonymized_table,
)
from pdf_anonymizer_core.utils import (
    load_seed_mapping,
    mapping_to_placeholder_original,
)
from pdf_anonymizer_core.word import is_word_path, write_anonymized_docx

NATIVE_PDF_APPLY_MESSAGE = (
    "Applying leftovers to a native PDF is not supported. "
    "Apply them to the Markdown output instead."
)


def hits_from_report(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Regex hits first, then LLM hits. Duplicate texts keep the first."""
    hits: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for hit in list(report.get("regex_hits") or []) + list(
        report.get("llm_hits") or []
    ):
        text = (hit.get("text") or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        item = dict(hit)
        item["text"] = text
        item["type"] = str(hit.get("type") or "CUSTOM").upper()
        item["base_form"] = hit.get("base_form") or text
        hits.append(item)
    return hits


def load_decision_list(path: str) -> List[str]:
    """JSON list / ``{"accept": [...]}`` object, or one phrase per line."""
    raw = Path(path).read_text(encoding="utf-8")
    stripped = raw.strip()
    if stripped.startswith("[") or stripped.startswith("{"):
        data = json.loads(stripped)
        if isinstance(data, list):
            return [str(item) for item in data if str(item).strip()]
        if isinstance(data, dict):
            for key in ("accept", "skip", "texts", "phrases"):
                value = data.get(key)
                if isinstance(value, list):
                    return [str(item) for item in value if str(item).strip()]
        raise ValueError(
            f"{path} is JSON but has no list of phrases "
            "(use an array, or an object with accept/skip/texts)."
        )
    return load_phrase_list(path)


def select_residual_hits(
    hits: Sequence[Dict[str, Any]],
    *,
    accept: Optional[Iterable[str]] = None,
    skip: Optional[Iterable[str]] = None,
    accept_all: bool = False,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split hits into accepted and skipped.

    ``skip`` always wins. ``accept_all`` takes every remaining hit.
    A provided ``accept`` list takes only those texts. With neither
    ``accept`` nor ``accept_all``, every hit is skipped.
    """
    skip_set = {phrase for phrase in (skip or []) if phrase}
    accept_set = {phrase for phrase in accept if phrase} if accept is not None else None
    accepted: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for hit in hits:
        text = hit["text"]
        if text in skip_set:
            skipped.append(hit)
            continue
        if accept_all or (accept_set is not None and text in accept_set):
            accepted.append(hit)
        else:
            skipped.append(hit)
    return accepted, skipped


def _anonymized_stem(anonymized_file: str) -> str:
    path = Path(anonymized_file)
    stem = path.name.replace(f".anonymized{path.suffix}", "")
    if stem == path.name:
        stem = path.stem
    return stem


def guess_mapping_path(anonymized_file: str) -> Optional[str]:
    """Conventional ``data/mappings/<stem>.mapping.json`` (or ``.enc``)."""
    stem = _anonymized_stem(anonymized_file)
    enc = Path(DEFAULT_MAPPINGS_DIR) / f"{stem}.mapping.json.enc"
    plain = Path(DEFAULT_MAPPINGS_DIR) / f"{stem}.mapping.json"
    if enc.is_file():
        return str(enc)
    if plain.is_file():
        return str(plain)
    return None


def default_mapping_out(anonymized_file: str) -> str:
    stem = _anonymized_stem(anonymized_file)
    return str(Path(DEFAULT_MAPPINGS_DIR) / f"{stem}.mapping.json")


def apply_residual_hits(
    anonymized_path: str,
    hits: Sequence[Dict[str, Any]],
    *,
    seed_mapping: Optional[Dict[str, str]] = None,
    mapping_out: Optional[str] = None,
    mapping_passphrase: Optional[str] = None,
    write_mapping: bool = True,
) -> Dict[str, Any]:
    """Hide accepted leftovers on an already-masked file.

    ``seed_mapping`` is original → written. New leftovers get the next
    typed stand-in. The anonymized file is rewritten in place.
    """
    path = Path(anonymized_path)
    if path.suffix.lower() == ".pdf":
        raise ValueError(NATIVE_PDF_APPLY_MESSAGE)
    if not path.is_file():
        raise ValueError(f"Anonymized file not found: {anonymized_path}")

    entities: List[dict] = []
    for hit in hits:
        text = (hit.get("text") or "").strip()
        if not text:
            continue
        entities.append(
            {
                "text": text,
                "type": str(hit.get("type") or "CUSTOM").upper(),
                "base_form": hit.get("base_form") or text,
                "score": 1.0,
                "source": hit.get("source") or "residual",
            }
        )

    orig_to_written = build_mapping(
        entities,
        seed_mapping=seed_mapping,
        operators=None,
        fake_secret=None,
    )
    texts = [entity["text"] for entity in entities]
    if texts:
        if is_tabular_path(anonymized_path):
            write_anonymized_table(
                anonymized_path, anonymized_path, orig_to_written, texts
            )
        elif is_word_path(anonymized_path):
            write_anonymized_docx(
                anonymized_path, anonymized_path, orig_to_written, texts
            )
        else:
            current = path.read_text(encoding="utf-8")
            path.write_text(
                replace_entities(current, texts, orig_to_written),
                encoding="utf-8",
            )

    if write_mapping:
        dest = mapping_out or default_mapping_out(anonymized_path)
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        placeholder_to_original = mapping_to_placeholder_original(orig_to_written)
        if mapping_passphrase:
            write_private_json(
                dest,
                encrypt_mapping(placeholder_to_original, mapping_passphrase),
            )
        else:
            write_private_json(dest, placeholder_to_original)

    return {
        "anonymized_file": anonymized_path,
        "applied": texts,
        "mapping": orig_to_written,
        "rewritten": bool(texts),
    }


def load_residual_report(path: str) -> Dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a residual report object.")
    return data


def seed_mapping_from_path(
    mapping_path: Optional[str],
    mapping_passphrase: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    if not mapping_path:
        return None
    if not Path(mapping_path).is_file():
        raise ValueError(f"Mapping file not found: {mapping_path}")
    return load_seed_mapping(mapping_path, mapping_passphrase)
