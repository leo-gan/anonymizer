#!/usr/bin/env python3
"""Score a system output against a TAB-style gold fixture.

Usage:
    uv run python scripts/eval_tab.py
    uv run python scripts/eval_tab.py --fixture tests/eval/fixture.json --predictions pred.json

If --predictions is omitted, the built-in regex stage is run on the fixture text.
Prints JSON with mention-level and entity-level scores for all / direct / quasi.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "packages" / "pdf-anonymizer-core" / "src"))

from tests.eval.metrics import evaluate_fixture  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        default=str(ROOT / "tests" / "eval" / "fixture.json"),
        help="Gold JSON with text + mentions",
    )
    parser.add_argument(
        "--predictions",
        default=None,
        help="JSON list of predicted mentions, or omit to run regex NER",
    )
    args = parser.parse_args()

    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    if args.predictions:
        predicted = json.loads(Path(args.predictions).read_text(encoding="utf-8"))
    else:
        from pdf_anonymizer_core.conf import DEFAULT_REGEX_PATTERNS
        from pdf_anonymizer_core.regex_ner import extract_entities_via_regex

        ents = extract_entities_via_regex(fixture["text"], DEFAULT_REGEX_PATTERNS)
        predicted = [
            {
                "text": ent["text"],
                "type": ent["type"],
                "start": ent.get("start"),
                "end": ent.get("end"),
            }
            for ent in ents
        ]

    report = evaluate_fixture(fixture, predicted)
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
