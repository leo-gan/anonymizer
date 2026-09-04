#!/usr/bin/env python3
"""Install the gold-corpus used to benchmark this package.

Downloads public anonymization tests into data/gold-corpus/ (gitignored)
and writes a normalized JSONL view the benchmark runner can score.

Usage:
    uv run python scripts/download_gold_corpus.py
    uv run python scripts/download_gold_corpus.py --full
    uv run python scripts/download_gold_corpus.py --dest /tmp/gold-corpus

Sources (see tests/eval/sources.json):
    tab         Text Anonymization Benchmark — ECHR court cases (legal)
    presidio    Microsoft Presidio research synth_dataset_v2 (general PII)
    gretel      Gretel PII Masking EN v1 test split (multi-domain)

i2b2/n2c2, MIMIC, Kaggle PII, and MAPA are documented but not fetched
(they need a login or a data-use agreement).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "packages" / "pdf-anonymizer-core" / "src"))

from tests.eval.gold import (  # noqa: E402
    DEFAULT_DEST,
    convert_gretel_document,
    convert_presidio_document,
    convert_tab_document,
    iter_json_array_or_object,
    write_jsonl,
)

USER_AGENT = "pdf-anonymizer-gold-corpus/0.17 (+https://github.com/leo-gan/anonymizer)"
TAB_BASE = (
    "https://raw.githubusercontent.com/NorskRegnesentral/"
    "text-anonymization-benchmark/master"
)
PRESIDIO_URL = (
    "https://raw.githubusercontent.com/microsoft/presidio-research/"
    "master/data/synth_dataset_v2.json"
)
GRETEL_DATASET = "gretelai/gretel-pii-masking-en-v1"
GRETEL_PARQUET = (
    "https://huggingface.co/datasets/gretelai/gretel-pii-masking-en-v1/"
    "resolve/main/data/test-00000-of-00001.parquet"
)
HF_ROWS = "https://datasets-server.huggingface.co/rows"


def _request(url: str, dest: Optional[Path] = None, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Optional[Exception] = None
    for attempt in range(1, 5):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = response.read()
            if dest is not None:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
            return data
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"Failed to download {url}: {last_error}") from last_error


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_tab(raw_dir: Path, full: bool) -> List[Path]:
    names = ["echr_test.json", "echr_dev.json"]
    if full:
        names.append("echr_train.json")
    paths = []
    for name in names:
        dest = raw_dir / "tab" / name
        if dest.exists() and dest.stat().st_size > 0:
            print(f"keep {dest}")
        else:
            print(f"get  {TAB_BASE}/{name}")
            _request(f"{TAB_BASE}/{name}", dest, timeout=180)
        paths.append(dest)
    return paths


def _download_presidio(raw_dir: Path) -> Path:
    dest = raw_dir / "presidio" / "synth_dataset_v2.json"
    if dest.exists() and dest.stat().st_size > 0:
        print(f"keep {dest}")
        return dest
    print(f"get  {PRESIDIO_URL}")
    _request(PRESIDIO_URL, dest)
    return dest


def _gretel_via_parquet(dest: Path) -> Optional[List[Dict[str, Any]]]:
    try:
        import pyarrow.parquet as pq  # type: ignore
    except ImportError:
        return None
    parquet_path = dest.with_suffix(".parquet")
    if not parquet_path.exists():
        print(f"get  {GRETEL_PARQUET}")
        _request(GRETEL_PARQUET, parquet_path, timeout=180)
    table = pq.read_table(parquet_path)
    return table.to_pylist()


def _gretel_via_rows_api() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    offset = 0
    page = 100
    total = None
    while True:
        query = urllib.parse.urlencode(
            {
                "dataset": GRETEL_DATASET,
                "config": "default",
                "split": "test",
                "offset": offset,
                "length": page,
            }
        )
        print(f"get  {GRETEL_DATASET} test[{offset}:{offset + page}]")
        payload = json.loads(_request(f"{HF_ROWS}?{query}"))
        batch = [item["row"] for item in payload.get("rows") or []]
        if not batch:
            break
        rows.extend(batch)
        total = payload.get("num_rows_total", total)
        offset += len(batch)
        if total is not None and offset >= int(total):
            break
    return rows


def _download_gretel(raw_dir: Path) -> Path:
    dest = raw_dir / "gretel" / "test.jsonl"
    if dest.exists() and dest.stat().st_size > 0:
        print(f"keep {dest}")
        return dest
    records = _gretel_via_parquet(dest)
    if records is None:
        records = _gretel_via_rows_api()
    write_jsonl(dest, records)
    return dest


def _normalize_tab(paths: Iterable[Path], out_path: Path) -> int:
    docs: List[Dict[str, Any]] = []
    for path in paths:
        for raw in iter_json_array_or_object(path):
            docs.append(convert_tab_document(raw))
    return write_jsonl(out_path, docs)


def _normalize_presidio(path: Path, out_path: Path) -> int:
    docs = [
        convert_presidio_document(raw, index)
        for index, raw in enumerate(iter_json_array_or_object(path))
    ]
    return write_jsonl(out_path, docs)


def _normalize_gretel(path: Path, out_path: Path) -> int:
    docs = []
    for raw in (
        json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else []
    ):
        docs.append(convert_gretel_document(raw))
    if path.suffix == ".jsonl":
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    docs.append(convert_gretel_document(json.loads(line)))
    return write_jsonl(out_path, docs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default=str(DEFAULT_DEST), help="Install directory")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Also fetch TAB train (extra ~48 MB)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Reuse raw files that are already present (default behaviour)",
    )
    args = parser.parse_args()
    dest = Path(args.dest)
    raw_dir = dest / "raw"
    norm_dir = dest / "normalized"
    dest.mkdir(parents=True, exist_ok=True)

    tab_paths = _download_tab(raw_dir, full=args.full)
    presidio_path = _download_presidio(raw_dir)
    gretel_path = _download_gretel(raw_dir)

    counts = {
        "tab": _normalize_tab(tab_paths, norm_dir / "tab.jsonl"),
        "presidio": _normalize_presidio(presidio_path, norm_dir / "presidio.jsonl"),
        "gretel": _normalize_gretel(gretel_path, norm_dir / "gretel.jsonl"),
    }

    try:
        dest_label = str(dest.resolve().relative_to(ROOT))
    except ValueError:
        dest_label = str(dest)
    manifest = {
        "dest": dest_label,
        "counts": counts,
        "files": {
            str(path.relative_to(dest)): {
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in sorted(dest.rglob("*"))
            if path.is_file()
        },
        "sources": ["tab", "presidio", "gretel"],
        "full_tab": bool(args.full),
    }
    manifest_path = dest / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"installed": counts, "dest": str(dest)}, indent=2))


if __name__ == "__main__":
    main()
