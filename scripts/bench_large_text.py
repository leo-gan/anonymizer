#!/usr/bin/env python3
"""Time a regex-only run on a synthetic text file and print peak memory.

The file is generated in a temporary directory. It is one email plus filler,
so the measurement is the cost of reading and scanning the bytes. A 100 MB
run on one workstation was still going after 25 minutes at about 1.9 GiB
resident memory. CSV, Excel, and Word are not this path. They are refused
above 50 MiB.

    uv run python scripts/bench_large_text.py --bytes 100000000
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "packages" / "pdf-anonymizer-core" / "src"))

from pdf_anonymizer_core.core import anonymize_file  # noqa: E402

_MARKER = b"Contact ada@example.com.\n"


def measure(size_bytes: int, directory: Path) -> dict[str, int | float]:
    """Run regex-only anonymization and return elapsed seconds and peak RSS.

    ``max_rss_kib`` is the process peak from :func:`resource.getrusage`.
    On Linux that value is kibibytes for the whole process, not this call alone.
    """
    if size_bytes < 1:
        raise ValueError("size_bytes must be at least 1")
    directory.mkdir(parents=True, exist_ok=True)
    source = directory / "synthetic.txt"
    if size_bytes <= len(_MARKER):
        payload = b"a" * size_bytes
    else:
        payload = _MARKER + (b"a" * (size_bytes - len(_MARKER)))
    source.write_bytes(payload)
    previous = Path.cwd()
    os.chdir(directory)
    started = time.perf_counter()
    try:
        anonymize_file(
            file_path=str(source),
            characters_to_anonymize=200_000,
            prompt_template="",
            model_name="none",
            use_llm=False,
            use_ner=False,
        )
    finally:
        os.chdir(previous)
        elapsed = time.perf_counter() - started
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "bytes": size_bytes,
        "seconds": round(elapsed, 3),
        "max_rss_kib": int(peak),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bytes", type=int, default=100_000_000)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="anonymizer-bench-") as temporary:
        result = measure(args.bytes, Path(temporary))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
