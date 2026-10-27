"""Delete local files that hold personal data from a run.

The command removes the language-model cache, mapping files, stats reports,
and ``app.log``. It leaves anonymized and deanonymized documents alone, because
those are the files the user asked to keep.
"""

from __future__ import annotations

import os
from pathlib import Path

_DIRECTORIES = (
    Path("data") / "cache",
    Path("data") / "mappings",
    Path("data") / "stats",
)


def purge_local_artifacts(root: str | os.PathLike[str]) -> list[str]:
    """Unlink cache, mapping, stats, and log files under ``root``.

    Symlinks are skipped so a link cannot point the delete at another tree.
    """
    base = Path(root)
    removed: list[str] = []
    for relative in _DIRECTORIES:
        directory = base / relative
        if not directory.is_dir() or directory.is_symlink():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            path.unlink()
            removed.append(str(path))
    log_path = base / "app.log"
    if log_path.is_file() and not log_path.is_symlink():
        log_path.unlink()
        removed.append(str(log_path))
    return removed
