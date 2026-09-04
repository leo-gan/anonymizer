#!/usr/bin/env python3
"""Print the public eval table (regex-only vs NER vs detailed LLM).

NER is item 20 and is not shipped. Live LLM is opt-in so PR CI stays
offline. Default reads the committed regex-only baseline.

Usage:
    uv run python scripts/eval_public_table.py
    uv run python scripts/eval_public_table.py --ci-fixtures
    uv run python scripts/eval_public_table.py --llm --model-name ollama/phi4-mini
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

from tests.eval.gold import BASELINE_PATH, CI_GOLD_SOURCES  # noqa: E402

TABLE_PATH = ROOT / "tests" / "eval" / "baselines" / "public_eval_table.md"


def _mention_block(report: Dict[str, Any]) -> Dict[str, Any]:
    return ((report.get("overall") or {}).get("scores") or {}).get("all") or {}


def _row_from_report(
    profile: str, report: Dict[str, Any], note: str = ""
) -> Dict[str, Any]:
    mention = (_mention_block(report).get("mention")) or {}
    leftover = (report.get("overall") or {}).get("leftover") or {}
    return {
        "profile": profile,
        "documents": report.get("documents"),
        "precision": mention.get("precision"),
        "recall": mention.get("recall"),
        "f1": mention.get("f1"),
        "leftover_rate": leftover.get("leftover_rate"),
        "structured_leftover_rate": leftover.get("structured_leftover_rate"),
        "note": note,
    }


def _placeholder(profile: str, note: str) -> Dict[str, Any]:
    return {
        "profile": profile,
        "documents": None,
        "precision": None,
        "recall": None,
        "f1": None,
        "leftover_rate": None,
        "structured_leftover_rate": None,
        "note": note,
    }


def render_table(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Public eval table",
        "",
        "Regex-only is measured. NER waits on item 20. `detailed` LLM is nightly / opt-in.",
        "This is not a legal privacy proof.",
        "",
        "| Profile | Docs | Mention P | Mention R | Mention F1 | Leftover | Structured leftover | Note |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:

        def fmt(value: Optional[float]) -> str:
            if value is None:
                return "—"
            return f"{value:.3f}"

        docs = "—" if row["documents"] is None else str(row["documents"])
        lines.append(
            f"| {row['profile']} | {docs} | {fmt(row['precision'])} | "
            f"{fmt(row['recall'])} | {fmt(row['f1'])} | {fmt(row['leftover_rate'])} | "
            f"{fmt(row['structured_leftover_rate'])} | {row['note']} |"
        )
    lines.append("")
    return "\n".join(lines)


def rows_from_baseline(path: Path = BASELINE_PATH) -> List[Dict[str, Any]]:
    report = json.loads(path.read_text(encoding="utf-8"))
    return [
        _row_from_report("regex-only", report, "committed baseline"),
        _placeholder("ner", "not shipped (item 20)"),
        _placeholder("detailed-llm", "opt-in / nightly; no API key in PR CI"),
    ]


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
        "--llm",
        action="store_true",
        help="Also run the live detailed LLM profile (needs a model)",
    )
    parser.add_argument("--model-name", default=None)
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
            _placeholder("ner", "not shipped (item 20)"),
            _placeholder("detailed-llm", "opt-in / nightly; no API key in PR CI"),
        ]
    else:
        rows = rows_from_baseline()

    if args.llm:
        if not args.model_name:
            raise SystemExit("--llm requires --model-name")
        rows = [row for row in rows if row["profile"] != "detailed-llm"]
        rows.append(
            _placeholder(
                "detailed-llm",
                f"requested ({args.model_name}); wire when a nightly job exists",
            )
        )

    text = render_table(rows)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
