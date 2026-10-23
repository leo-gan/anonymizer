#!/usr/bin/env python3
"""Score this package on the installed gold-corpus.

Default profile is regex-only so the baseline is deterministic and needs no
API key. NER and language-model profiles are opt-in.

Usage:
    uv run python scripts/run_gold_benchmark.py
    uv run python scripts/run_gold_benchmark.py --write-baseline
    uv run python scripts/run_gold_benchmark.py --profile local-detailed --write-baseline
    uv run python scripts/run_gold_benchmark.py --sources tab,presidio --max-docs 50
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "packages" / "pdf-anonymizer-core" / "src"))

from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402

from pdf_anonymizer_core.conf import (  # noqa: E402
    DEFAULT_REGEX_PATTERNS,
    PROFILE_CONFIGS,
    ConfigProfile,
)
from pdf_anonymizer_core.core import (  # noqa: E402
    anonymize_text_content,
    build_mapping,
    collect_entities_from_chunks,
    finalize_entities,
    replace_entities,
)
from pdf_anonymizer_core.llm_provider import (  # noqa: E402
    LlmRunStats,
    bind_llm_stats,
    configure_cache,
    reset_llm_stats,
)
from pdf_anonymizer_core.prompts import detailed  # noqa: E402
from pdf_anonymizer_core.regex_ner import extract_entities_via_regex  # noqa: E402
from pdf_anonymizer_core.span_ner import (  # noqa: E402
    DEFAULT_NER_MODEL,
    extract_entities_via_ner,
    ner_available,
)
from pdf_anonymizer_core.verify import scan_residual_regex  # noqa: E402

from tests.eval.gold import (  # noqa: E402
    DEFAULT_DEST,
    PROFILE_BASELINES,
    align_predictions,
    evaluate_documents,
    leftover_report,
    load_gold_corpus,
)

LOCAL_MODEL = "ollama/gemma4:12b-it-qat"
CLOSED_MODEL = "google/gemini-3.8-flash"
LOCAL_NUM_CTX = "8192"
PROFILES = ("regex-only", "ner", "local-detailed", "closed-detailed")


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


def _chunks(text: str) -> List[str]:
    quality = PROFILE_CONFIGS[ConfigProfile.BEST_QUALITY]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(quality["chunk_size"]),
        chunk_overlap=int(quality["chunk_overlap"]),
    )
    parts = splitter.split_text(text) if text else []
    return parts or [text]


def _anonymized_from_predictions(text: str, predictions: Sequence[Dict[str, Any]]) -> str:
    if not predictions:
        return text
    mapping = build_mapping(
        list(predictions),
        seed_mapping=None,
        operators=None,
        fake_secret=None,
    )
    return replace_entities(
        text, (entity["text"] for entity in predictions), mapping
    )


def _predict_ner(text: str) -> List[Dict[str, Any]]:
    if not ner_available():
        raise SystemExit(
            'Local span NER requires: uv sync --extra ner  '
            '(pip install "pdf-anonymizer-core[ner]")'
        )
    entities = extract_entities_via_ner(text, model_name=DEFAULT_NER_MODEL)
    return align_predictions(text, entities)


def _predict_detailed(text: str, model_name: str) -> List[Dict[str, Any]]:
    collected = collect_entities_from_chunks(
        _chunks(text),
        prompt_template=detailed.prompt_template,
        model_name=model_name,
        regex_patterns=DEFAULT_REGEX_PATTERNS,
        max_retries=2,
        base_retry_delay=1.0,
        max_retry_delay=8.0,
        use_llm=True,
        use_ner=False,
    )
    finalized = finalize_entities(
        collected,
        text,
        anonymized_entities=None,
        keep_list=None,
        deny_list=None,
        apply_deny=False,
    )
    return align_predictions(text, finalized)


def _configure_local_runtime() -> Dict[str, Any]:
    os.environ["ANONYMIZER_OLLAMA_NUM_CTX"] = LOCAL_NUM_CTX
    os.environ["ANONYMIZER_OLLAMA_THINK"] = "false"
    os.environ["ANONYMIZER_OLLAMA_TEMPERATURE"] = "0"
    configure_cache(False)
    return {
        "num_ctx": int(LOCAL_NUM_CTX),
        "think": False,
        "temperature": 0,
        "chunk_size": PROFILE_CONFIGS[ConfigProfile.BEST_QUALITY]["chunk_size"],
        "chunk_overlap": PROFILE_CONFIGS[ConfigProfile.BEST_QUALITY]["chunk_overlap"],
        "max_retries": 2,
        "stages": ["regex", "llm"],
    }


def _doc_key(document: Dict[str, Any]) -> str:
    return f"{document.get('source')}::{document.get('name')}"


def _load_checkpoint(path: Optional[Path]) -> Dict[str, List[Dict[str, Any]]]:
    found: Dict[str, List[Dict[str, Any]]] = {}
    if path is None or not path.is_file():
        return found
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            found[str(row["key"])] = list(row.get("predictions") or [])
    return found


def _append_checkpoint(
    path: Optional[Path], key: str, predictions: Sequence[Dict[str, Any]]
) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps({"key": key, "predictions": list(predictions)}, ensure_ascii=False)
        )
        handle.write("\n")
        handle.flush()


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
    profile: str = "regex-only",
    model_name: Optional[str] = None,
    checkpoint: Optional[Path] = None,
) -> Dict[str, Any]:
    if profile not in PROFILES:
        raise SystemExit(f"Unknown profile {profile!r}. Use one of: {', '.join(PROFILES)}")
    documents = load_gold_corpus(dest=dest, sources=sources, max_docs=max_docs)
    if not documents:
        raise SystemExit(
            "No gold documents found. Run: uv run python scripts/download_gold_corpus.py"
        )

    runtime: Dict[str, Any] = {}
    stats: Optional[LlmRunStats] = None
    stats_token = None
    resolved_model = model_name
    if profile == "local-detailed":
        resolved_model = model_name or LOCAL_MODEL
        runtime = _configure_local_runtime()
        stats = LlmRunStats()
        stats_token = bind_llm_stats(stats)
    elif profile == "closed-detailed":
        resolved_model = model_name or CLOSED_MODEL
        configure_cache(False)
        stats = LlmRunStats()
        stats_token = bind_llm_stats(stats)
        runtime = {
            "chunk_size": PROFILE_CONFIGS[ConfigProfile.BEST_QUALITY]["chunk_size"],
            "chunk_overlap": PROFILE_CONFIGS[ConfigProfile.BEST_QUALITY]["chunk_overlap"],
            "max_retries": 2,
            "stages": ["regex", "llm"],
        }
    elif profile == "ner":
        resolved_model = DEFAULT_NER_MODEL
        runtime = {"stages": ["ner"]}

    saved = _load_checkpoint(checkpoint)
    if saved:
        print(f"resuming {len(saved)} checkpointed documents", flush=True)
    predictions: List[List[Dict[str, Any]]] = []
    started = time.monotonic()
    try:
        for index, document in enumerate(documents, start=1):
            text = document.get("text") or ""
            key = _doc_key(document)
            if key in saved:
                predicted = saved[key]
            elif profile == "regex-only":
                predicted = _predict_regex(text)
            elif profile == "ner":
                predicted = _predict_ner(text)
            else:
                if not resolved_model:
                    raise SystemExit(f"--profile {profile} requires --model-name")
                before_failures = stats.transport_failures if stats is not None else 0
                predicted = _predict_detailed(text, resolved_model)
                if stats is not None and stats.transport_failures > before_failures:
                    raise SystemExit(
                        f"Language model unreachable at {key}. "
                        "This document was not checkpointed."
                    )
                _append_checkpoint(checkpoint, key, predicted)
            predictions.append(predicted)
            if profile == "regex-only":
                document["_anonymized"] = _apply_regex(text)
            else:
                document["_anonymized"] = _anonymized_from_predictions(text, predicted)
            if profile != "regex-only" and (index == 1 or index % 25 == 0 or index == len(documents)):
                elapsed = time.monotonic() - started
                print(
                    f"{profile} {index}/{len(documents)} "
                    f"elapsed={elapsed:.0f}s key={key}",
                    flush=True,
                )
    finally:
        if stats_token is not None:
            reset_llm_stats(stats_token)

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

    report: Dict[str, Any] = {
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "profile": profile,
        "model": resolved_model,
        "package_version": _package_version(),
        "documents": len(documents),
        "sources": sorted({str(doc.get("source")) for doc in documents}),
        "domains": sorted({str(doc.get("domain")) for doc in documents}),
        "max_docs": max_docs,
        "corpus_manifest": manifest,
        "runtime": runtime,
        "overall": overall,
        "by_source": by_source,
        "by_domain": by_domain,
    }
    if stats is not None:
        report["llm_stats"] = {
            "calls": stats.calls,
            "parse_failures": stats.parse_failures,
            "transport_failures": stats.transport_failures,
            "prompt_tokens": stats.prompt_tokens,
            "output_tokens": stats.output_tokens,
        }
    return report


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

    print(f"gold-corpus {report.get('profile')} model={report.get('model')}")
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
        "--profile",
        default="regex-only",
        choices=list(PROFILES),
        help="regex-only is offline. ner, local-detailed, and closed-detailed are opt-in.",
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help=(
            "Override the profile model. "
            f"local-detailed defaults to {LOCAL_MODEL}. "
            f"closed-detailed defaults to {CLOSED_MODEL}."
        ),
    )
    parser.add_argument(
        "--checkpoint",
        default=None,
        help="JSONL of finished documents so a local run can resume.",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Write tests/eval/baselines/gold_corpus_<profile>.json",
    )
    parser.add_argument("--output", default=None, help="Optional extra JSON path")
    args = parser.parse_args()

    sources = (
        [part.strip() for part in args.sources.split(",") if part.strip()]
        if args.sources
        else None
    )
    logging.basicConfig(level=logging.WARNING)
    checkpoint = Path(args.checkpoint) if args.checkpoint else None
    if args.profile == "local-detailed" and checkpoint is None:
        checkpoint = DEFAULT_DEST / "checkpoints" / "local-detailed.jsonl"
    report = run_benchmark(
        Path(args.dest),
        sources,
        args.max_docs,
        profile=args.profile,
        model_name=args.model_name,
        checkpoint=checkpoint,
    )
    _print_table(report)

    payload = json.dumps(report, indent=2) + "\n"
    if args.write_baseline:
        baseline = PROFILE_BASELINES[args.profile]
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline.write_text(payload, encoding="utf-8")
        print(f"wrote {baseline}")
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
