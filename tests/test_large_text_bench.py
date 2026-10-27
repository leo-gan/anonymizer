"""The large-text harness runs. The 100 MB numbers live in the docs, not in CI."""

import json
import subprocess
import sys
from pathlib import Path


def test_large_text_harness_runs_on_a_small_file() -> None:
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "bench_large_text.py"),
            "--bytes",
            "20000",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    assert result["bytes"] == 20000
    assert result["seconds"] >= 0
    assert result["max_rss_kib"] > 0
