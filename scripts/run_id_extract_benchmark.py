#!/usr/bin/env python3
"""Score id-extract on the installed gold-corpus (detection only).

This baseline does not run replacement, mapping, or file I/O. Use it to
improve the extractor without going through pdf-anonymizer-core.

Usage:
    uv run python scripts/run_id_extract_benchmark.py
    uv run python scripts/run_id_extract_benchmark.py --write-baseline
    uv run python scripts/run_id_extract_benchmark.py --sources mini-tab,domain-pack
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
    sys.path.insert(0, str(ROOT / "packages" / "id-extract" / "src"))

from id_extract import extract  # noqa: E402

from tests.eval.gold import (  # noqa: E402
    DEFAULT_DEST,
    ID_EXTRACT_BASELINE_PATH,
    evaluate_documents,
    load_gold_corpus,
    structured_mentions,
)
from tests.eval.metrics import mention_scores  # noqa: E402


def _package_version() -> str:
    try:
        from importlib.metadata import version

        return version("id-extract")
    except Exception:
        return "0.1.0"


def _predict(text: str) -> List[Dict[str, Any]]:
    return [
        {
            "text": item["text"],
            "type": item["type"],
            "start": item["start"],
            "end": item["end"],
            "base_form": item.get("base_form") or item["text"],
        }
        for item in extract(text)
    ]


def _structured_block(
    docs: Sequence[Dict[str, Any]], preds: Sequence[List[Dict[str, Any]]]
) -> Dict[str, Any]:
    gold = [
        mention
        for doc in docs
        for mention in structured_mentions(doc.get("mentions") or [])
    ]
    pred = [hit for pred in preds for hit in pred]
    return {"mention": mention_scores(gold, pred)}


def _score_group(docs: Sequence[Dict[str, Any]], preds: Sequence[List[Dict[str, Any]]]):
    if not docs:
        return None
    report = evaluate_documents(docs, preds)
    report["structured"] = _structured_block(docs, preds)
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
        predictions.append(_predict(document.get("text") or ""))

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

    return {
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "package": "id-extract",
        "profile": "extract",
        "countries": "all",
        "package_version": _package_version(),
        "documents": len(documents),
        "sources": sorted({str(doc.get("source")) for doc in documents}),
        "domains": sorted({str(doc.get("domain")) for doc in documents}),
        "max_docs": max_docs,
        "overall": overall,
        "by_source": by_source,
        "by_domain": by_domain,
    }


def _print_table(report: Dict[str, Any]) -> None:
    def row(label: str, block: Optional[Dict[str, Any]]) -> None:
        if not block:
            return
        mention = block["scores"]["all"]["mention"]
        structured = (block.get("structured") or {}).get("mention") or {}
        print(
            f"{label:<22} "
            f"docs={block.get('documents', 0):<5} "
            f"P={mention['precision']:.3f} "
            f"R={mention['recall']:.3f} "
            f"F1={mention['f1']:.3f} "
            f"struct_R={structured.get('recall', 0):.3f}"
        )

    print("gold-corpus id-extract")
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
        default="mini-tab,domain-pack",
        help="Comma-separated source ids (default: committed CI set)",
    )
    parser.add_argument("--max-docs", type=int, default=None)
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help=f"Write {ID_EXTRACT_BASELINE_PATH.relative_to(ROOT)}",
    )
    parser.add_argument("--output", default=None, help="Optional extra JSON path")
    args = parser.parse_args()

    sources = [part.strip() for part in args.sources.split(",") if part.strip()]
    report = run_benchmark(Path(args.dest), sources, args.max_docs)
    _print_table(report)

    payload = json.dumps(report, indent=2) + "\n"
    if args.write_baseline:
        ID_EXTRACT_BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        ID_EXTRACT_BASELINE_PATH.write_text(payload, encoding="utf-8")
        print(f"wrote {ID_EXTRACT_BASELINE_PATH}")
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
