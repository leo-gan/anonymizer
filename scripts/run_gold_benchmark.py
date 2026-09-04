#!/usr/bin/env python3
"""Score this package on the installed gold-corpus.

Default profile is regex-only so the baseline is deterministic and needs no
API key. Live LLM scoring is opt-in.

Usage:
    uv run python scripts/run_gold_benchmark.py
    uv run python scripts/run_gold_benchmark.py --write-baseline
    uv run python scripts/run_gold_benchmark.py --sources tab,presidio --max-docs 50
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "packages" / "pdf-anonymizer-core" / "src"))

from pdf_anonymizer_core.conf import DEFAULT_REGEX_PATTERNS  # noqa: E402
from pdf_anonymizer_core.core import anonymize_text_content  # noqa: E402
from pdf_anonymizer_core.regex_ner import extract_entities_via_regex  # noqa: E402
from pdf_anonymizer_core.verify import scan_residual_regex  # noqa: E402

from tests.eval.gold import (  # noqa: E402
    BASELINE_PATH,
    DEFAULT_DEST,
    evaluate_documents,
    leftover_report,
    load_gold_corpus,
)


def _package_version() -> str:
    try:
        from importlib.metadata import version

        return version("pdf-anonymizer-core")
    except Exception:
        return "0.17.0"


def _predict_regex(text: str) -> List[Dict[str, Any]]:
    ents = extract_entities_via_regex(text, DEFAULT_REGEX_PATTERNS)
    return [
        {
            "text": ent["text"],
            "type": ent["type"],
            "start": ent.get("start"),
            "end": ent.get("end"),
            "base_form": ent.get("base_form") or ent["text"],
        }
        for ent in ents
    ]


def _apply_regex(text: str) -> str:
    anonymized, _mapping = anonymize_text_content(
        text,
        [text],
        prompt_template="",
        model_name="",
        use_llm=False,
    )
    return anonymized


def _merge_leftover(parts: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    leftover = sum(part["leftover"] for part in parts)
    gold = sum(part["gold"] for part in parts)
    structured_left = sum(part["structured_leftover"] for part in parts)
    structured_gold = sum(part["structured_gold"] for part in parts)
    residual = sum(part.get("residual_regex", 0) for part in parts)
    return {
        "leftover": leftover,
        "gold": gold,
        "leftover_rate": (leftover / gold) if gold else 0.0,
        "structured_leftover": structured_left,
        "structured_gold": structured_gold,
        "structured_leftover_rate": (
            (structured_left / structured_gold) if structured_gold else 0.0
        ),
        "residual_regex": residual,
    }


def _score_group(docs: Sequence[Dict[str, Any]], preds: Sequence[List[Dict[str, Any]]]):
    if not docs:
        return None
    report = evaluate_documents(docs, preds)
    leftovers = [
        leftover_report(doc.get("mentions") or [], doc["_anonymized"]) for doc in docs
    ]
    for leftover, doc in zip(leftovers, docs):
        leftover["residual_regex"] = len(scan_residual_regex(doc["_anonymized"]))
    report["leftover"] = _merge_leftover(leftovers)
    return report


def run_benchmark(
    dest: Path,
    sources: Optional[Sequence[str]],
    max_docs: Optional[int],
) -> Dict[str, Any]:
    documents = load_gold_corpus(dest=dest, sources=sources, max_docs=max_docs)
    if not documents:
        raise SystemExit(
            "No gold documents found. Run: uv run python scripts/download_gold_corpus.py"
        )

    predictions: List[List[Dict[str, Any]]] = []
    for document in documents:
        text = document.get("text") or ""
        predictions.append(_predict_regex(text))
        document["_anonymized"] = _apply_regex(text)

    overall = _score_group(documents, predictions)

    by_source: Dict[str, Any] = {}
    by_domain: Dict[str, Any] = {}
    source_docs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    source_preds: Dict[str, List[List[Dict[str, Any]]]] = defaultdict(list)
    domain_docs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    domain_preds: Dict[str, List[List[Dict[str, Any]]]] = defaultdict(list)
    for document, pred in zip(documents, predictions):
        source_docs[str(document.get("source") or "unknown")].append(document)
        source_preds[str(document.get("source") or "unknown")].append(pred)
        domain_docs[str(document.get("domain") or "unknown")].append(document)
        domain_preds[str(document.get("domain") or "unknown")].append(pred)
    for key in sorted(source_docs):
        by_source[key] = _score_group(source_docs[key], source_preds[key])
    for key in sorted(domain_docs):
        by_domain[key] = _score_group(domain_docs[key], domain_preds[key])

    manifest_path = dest / "manifest.json"
    manifest = None
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for document in documents:
        document.pop("_anonymized", None)

    return {
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "profile": "regex-only",
        "package_version": _package_version(),
        "documents": len(documents),
        "sources": sorted({str(doc.get("source")) for doc in documents}),
        "domains": sorted({str(doc.get("domain")) for doc in documents}),
        "max_docs": max_docs,
        "corpus_manifest": manifest,
        "overall": overall,
        "by_source": by_source,
        "by_domain": by_domain,
    }


def _print_table(report: Dict[str, Any]) -> None:
    def row(label: str, block: Optional[Dict[str, Any]]) -> None:
        if not block:
            return
        mention = block["scores"]["all"]["mention"]
        leftover = block.get("leftover") or {}
        print(
            f"{label:<22} "
            f"docs={block.get('documents', 0):<5} "
            f"P={mention['precision']:.3f} "
            f"R={mention['recall']:.3f} "
            f"F1={mention['f1']:.3f} "
            f"left={leftover.get('leftover_rate', 0):.3f} "
            f"struct_left={leftover.get('structured_leftover_rate', 0):.3f}"
        )

    print("gold-corpus regex-only")
    row("overall", report.get("overall"))
    print("-- by source --")
    for key, block in (report.get("by_source") or {}).items():
        row(key, block)
    print("-- by domain --")
    for key, block in (report.get("by_domain") or {}).items():
        row(key, block)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default=str(DEFAULT_DEST))
    parser.add_argument(
        "--sources",
        default=None,
        help="Comma-separated source ids (tab,presidio,gretel,domain-pack,mini-tab)",
    )
    parser.add_argument("--max-docs", type=int, default=None)
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help=f"Write {BASELINE_PATH.relative_to(ROOT)}",
    )
    parser.add_argument("--output", default=None, help="Optional extra JSON path")
    args = parser.parse_args()

    sources = (
        [part.strip() for part in args.sources.split(",") if part.strip()]
        if args.sources
        else None
    )
    report = run_benchmark(Path(args.dest), sources, args.max_docs)
    _print_table(report)

    payload = json.dumps(report, indent=2) + "\n"
    if args.write_baseline:
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_PATH.write_text(payload, encoding="utf-8")
        print(f"wrote {BASELINE_PATH}")
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
