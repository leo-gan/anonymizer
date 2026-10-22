#!/usr/bin/env python3
"""Print the public eval table (regex-only, NER, local detailed, closed detailed).

Live model rows are opt-in so PR CI stays offline. Default reads whatever
baseline files are already committed.

Usage:
    uv run python scripts/eval_public_table.py
    uv run python scripts/eval_public_table.py --ci-fixtures
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "packages" / "pdf-anonymizer-core" / "src"))

from tests.eval.gold import (  # noqa: E402
    CI_GOLD_SOURCES,
    PROFILE_BASELINES,
)

TABLE_PATH = ROOT / "tests" / "eval" / "baselines" / "public_eval_table.md"


def _scores(report: Dict[str, Any]) -> Dict[str, Any]:
    return ((report.get("overall") or {}).get("scores") or {})


def _mention_block(report: Dict[str, Any]) -> Dict[str, Any]:
    return _scores(report).get("all") or {}


def _kind_f1(report: Dict[str, Any], kind: str) -> Optional[float]:
    block = (_scores(report).get(kind) or {}).get("mention") or {}
    value = block.get("f1")
    return None if value is None else float(value)


def _row_from_report(
    profile: str, report: Dict[str, Any], note: str = ""
) -> Dict[str, Any]:
    mention = (_mention_block(report).get("mention")) or {}
    entity = (_mention_block(report).get("entity")) or {}
    leftover = (report.get("overall") or {}).get("leftover") or {}
    model = report.get("model") or ""
    return {
        "profile": profile,
        "model": model,
        "documents": report.get("documents"),
        "precision": mention.get("precision"),
        "recall": mention.get("recall"),
        "f1": mention.get("f1"),
        "entity_f1": entity.get("f1"),
        "direct_f1": _kind_f1(report, "direct"),
        "quasi_f1": _kind_f1(report, "quasi"),
        "leftover_rate": leftover.get("leftover_rate"),
        "structured_leftover_rate": leftover.get("structured_leftover_rate"),
        "note": note,
    }


def _placeholder(profile: str, note: str) -> Dict[str, Any]:
    return {
        "profile": profile,
        "model": "",
        "documents": None,
        "precision": None,
        "recall": None,
        "f1": None,
        "entity_f1": None,
        "direct_f1": None,
        "quasi_f1": None,
        "leftover_rate": None,
        "structured_leftover_rate": None,
        "note": note,
    }


def render_table(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Public eval table",
        "",
        "Regex-only is the offline gate. NER, local detailed, and closed detailed",
        "appear when their baseline files exist. This is not a legal privacy proof.",
        "",
        "| Profile | Model | Docs | Mention P | Mention R | Mention F1 | Entity F1 | Direct F1 | Quasi F1 | Leftover | Structured leftover | Note |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:

        def fmt(value: Optional[float]) -> str:
            if value is None:
                return "—"
            return f"{value:.3f}"

        docs = "—" if row["documents"] is None else str(row["documents"])
        model = row.get("model") or "—"
        lines.append(
            f"| {row['profile']} | {model} | {docs} | {fmt(row['precision'])} | "
            f"{fmt(row['recall'])} | {fmt(row['f1'])} | {fmt(row['entity_f1'])} | "
            f"{fmt(row['direct_f1'])} | {fmt(row['quasi_f1'])} | "
            f"{fmt(row['leftover_rate'])} | {fmt(row['structured_leftover_rate'])} | "
            f"{row['note']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _note_for(profile: str, report: Dict[str, Any]) -> str:
    if profile == "regex-only":
        return "committed baseline"
    if profile == "ner":
        return "span NER only"
    if profile == "local-detailed":
        return "RE2 + detailed prompt, think off, num_ctx 8192"
    return "RE2 + detailed prompt, paid API"


def rows_from_baseline() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    missing = {
        "ner": "not measured on this machine",
        "local-detailed": "not measured on this machine",
        "closed-detailed": "not run; closed model not approved yet",
    }
    for profile, path in PROFILE_BASELINES.items():
        if path.is_file():
            report = json.loads(path.read_text(encoding="utf-8"))
            rows.append(_row_from_report(profile, report, _note_for(profile, report)))
        else:
            rows.append(_placeholder(profile, missing.get(profile, "not measured")))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-baseline",
        action="store_true",
        default=True,
        help="Read tests/eval/baselines/gold_corpus_regex_only.json (default)",
    )
    parser.add_argument(
        "--ci-fixtures",
        action="store_true",
        help="Recompute regex-only on the committed mini-tab + domain pack",
    )
    parser.add_argument(
        "--output",
        default=str(TABLE_PATH),
        help="Markdown path",
    )
    args = parser.parse_args()

    if args.ci_fixtures:
        import importlib.util

        from tests.eval.gold import DEFAULT_DEST

        spec = importlib.util.spec_from_file_location(
            "run_gold_benchmark", ROOT / "scripts" / "run_gold_benchmark.py"
        )
        if spec is None or spec.loader is None:
            raise SystemExit("Cannot load scripts/run_gold_benchmark.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.run_benchmark(DEFAULT_DEST, list(CI_GOLD_SOURCES), None)
        rows = [
            _row_from_report("regex-only", report, "CI fixtures"),
            _placeholder("ner", "not measured on this machine"),
            _placeholder("local-detailed", "not measured on this machine"),
            _placeholder("closed-detailed", "not run; closed model not approved yet"),
        ]
    else:
        rows = rows_from_baseline()

    text = render_table(rows)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
