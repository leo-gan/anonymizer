"""Optional k-anonymity for CSV and Excel tables.

Direct identifiers stay on the normal cell operators. Quasi-identifier
columns are generalized or suppressed until each combination appears at
least k times, or until every quasi column is suppressed. The report is
an aid for a table release. It is not a certificate, and this module
does not read or write PDFs.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from pdf_anonymizer_core.tables import (
    TableCell,
    TableDocument,
    TableSheet,
    header_labels,
)

SUPPRESSED = "*"
_DISCLAIMER = (
    "This is an aid for a table release, not a privacy certificate. "
    "Prosecutor risk assumes the person is in this table and the attacker "
    "knows these quasi-identifiers. Cell values are generalized or "
    "suppressed. They are not Laplace-noised."
)

# Header token → generalization family. Direct identifiers (name, email)
# are intentionally absent so the default detector still owns them.
_HINTS: Tuple[Tuple[str, str], ...] = (
    ("zipcode", "zip"),
    ("zip", "zip"),
    ("postal", "zip"),
    ("postcode", "zip"),
    ("gender", "categorical"),
    ("sex", "categorical"),
    ("race", "categorical"),
    ("ethnicity", "categorical"),
    ("city", "categorical"),
    ("state", "categorical"),
    ("age", "age"),
    ("dob", "date"),
    ("birthdate", "date"),
    ("birthday", "date"),
    ("birth", "date"),
    ("date", "date"),
)
_MAX_LEVEL = {"zip": 3, "age": 4, "date": 4, "categorical": 1, "text": 1}


def _tokens(name: str) -> List[str]:
    return [part for part in re.split(r"[^a-z0-9]+", name.lower()) if part]


def column_kind(name: str) -> str:
    """Generalization family for a header. Unknown headers suppress in one step."""
    tokens = set(_tokens(name))
    for hint, kind in _HINTS:
        if hint in tokens:
            return kind
    return "text"


def generalize(value: str, kind: str, level: int) -> str:
    """Coarsen one quasi-identifier value. Level 0 keeps it."""
    text = "" if value is None else str(value).strip()
    if level <= 0 or text == "":
        return text
    if kind == "zip":
        digits = re.sub(r"\D", "", text)
        if level == 1 and len(digits) >= 3:
            return digits[:3] + "**"
        if level == 2 and len(digits) >= 1:
            return digits[:1] + "****"
        return SUPPRESSED
    if kind == "age":
        try:
            age = int(float(text))
        except ValueError:
            return SUPPRESSED
        width = {1: 5, 2: 10, 3: 20}.get(level)
        if width is None:
            return SUPPRESSED
        start = (age // width) * width
        return f"{start}-{start + width - 1}"
    if kind == "date":
        year, month = _year_month(text)
        if year is None:
            return SUPPRESSED
        if level == 1 and month is not None:
            return f"{year:04d}-{month:02d}"
        if level == 1 or level == 2:
            return f"{year:04d}"
        if level == 3:
            decade = (year // 10) * 10
            return f"{decade}s"
        return SUPPRESSED
    return SUPPRESSED


def _year_month(text: str) -> Tuple[Optional[int], Optional[int]]:
    match = re.search(r"(\d{4})(?:[-/](\d{1,2}))?", text)
    if not match:
        return None, None
    year = int(match.group(1))
    month = int(match.group(2)) if match.group(2) else None
    if month is not None and not 1 <= month <= 12:
        month = None
    return year, month


def _project(
    rows: Sequence[Sequence[str]],
    columns: Sequence[int],
    kinds: Mapping[int, str],
    levels: Mapping[int, int],
) -> List[Tuple[str, ...]]:
    projected: List[Tuple[str, ...]] = []
    for row in rows:
        projected.append(
            tuple(
                generalize(row[column] if column < len(row) else "", kinds[column], levels[column])
                for column in columns
            )
        )
    return projected


def choose_levels(
    rows: Sequence[Sequence[str]],
    columns: Sequence[int],
    kinds: Mapping[int, str],
    k: int,
) -> Dict[int, int]:
    """Raise each quasi column until every combination has size at least k."""
    if k < 2:
        raise ValueError("k must be at least 2.")
    levels = {column: 0 for column in columns}
    if not rows or not columns:
        return levels
    for _ in range(sum(_MAX_LEVEL[kinds[column]] for column in columns) + 1):
        projected = _project(rows, columns, kinds, levels)
        counts = Counter(projected)
        if min(counts.values()) >= k:
            return levels
        candidates = [
            column
            for column in columns
            if levels[column] < _MAX_LEVEL[kinds[column]]
        ]
        if not candidates:
            return levels
        best_column = candidates[0]
        best_score: Optional[Tuple[int, int]] = None
        for column in candidates:
            trial = dict(levels)
            trial[column] += 1
            trial_values = _project(rows, columns, kinds, trial)
            trial_counts = Counter(trial_values)
            covered = sum(1 for key in trial_values if trial_counts[key] >= k)
            score = (covered, -trial[column])
            if best_score is None or score > best_score:
                best_score = score
                best_column = column
        levels[best_column] += 1
    return levels


def prosecutor_report(
    quasi_rows: Sequence[Tuple[str, ...]],
    *,
    k: int,
    sensitive: Optional[Sequence[str]] = None,
    columns: Optional[Sequence[Mapping[str, str]]] = None,
) -> dict:
    """Prosecutor risk for one table. Risk of a row is 1 / class size."""
    counts: Counter[Tuple[str, ...]] = Counter(quasi_rows)
    risks = [1 / counts[row] for row in quasi_rows] if quasi_rows else []
    sizes = list(counts.values()) if counts else []
    k_achieved = min(sizes) if sizes else 0
    report: dict = {
        "model": "prosecutor",
        "k": k,
        "k_achieved": k_achieved,
        "k_met": bool(sizes) and k_achieved >= k,
        "records": len(quasi_rows),
        "classes": len(counts),
        "min_class_size": k_achieved,
        "average_prosecutor_risk": (sum(risks) / len(risks)) if risks else None,
        "max_prosecutor_risk": max(risks) if risks else None,
        "records_below_k": sum(1 for row in quasi_rows if counts[row] < k),
        "columns": list(columns or []),
        "disclaimer": _DISCLAIMER,
    }
    if sensitive is not None:
        report.update(_diversity(quasi_rows, sensitive, counts))
    return report


def _diversity(
    quasi_rows: Sequence[Tuple[str, ...]],
    sensitive: Sequence[str],
    counts: Counter,
) -> dict:
    by_class: Dict[Tuple[str, ...], List[str]] = {}
    for key, value in zip(quasi_rows, sensitive):
        by_class.setdefault(key, []).append(value)
    global_counts = Counter(sensitive)
    total = len(sensitive) or 1
    ell_values = []
    distances = []
    for values in by_class.values():
        ell_values.append(len(set(values)))
        local = Counter(values)
        keys = set(global_counts) | set(local)
        distance = 0.5 * sum(
            abs((local[key] / len(values)) - (global_counts[key] / total))
            for key in keys
        )
        distances.append(distance)
    return {
        "l_diversity": min(ell_values) if ell_values else None,
        "t_closeness": max(distances) if distances else None,
    }


def apply_table_privacy(
    doc: TableDocument,
    *,
    k: int,
    quasi_columns: Optional[Iterable[str]] = None,
    sensitive_column: Optional[str] = None,
) -> dict:
    """Generalize quasi columns on each sheet. Returns one report per sheet."""
    requested = [name.strip() for name in (quasi_columns or []) if name and name.strip()]
    sheets = []
    for sheet in doc.sheets:
        sheets.append(
            _apply_sheet(
                sheet.cells,
                sheet.max_row,
                sheet.max_column,
                k=k,
                requested=requested,
                sensitive_column=sensitive_column,
                sheet_name=sheet.name,
            )
        )
    if not any(item["columns"] for item in sheets):
        raise ValueError(
            "No quasi-identifier columns. Pass quasi column headers such as "
            "zip,gender,dob. This engine does not rewrite PDFs."
        )
    return {
        "k": k,
        "sheets": sheets,
        "disclaimer": _DISCLAIMER,
    }


def _apply_sheet(
    cells: List[TableCell],
    max_row: int,
    max_column: int,
    *,
    k: int,
    requested: Sequence[str],
    sensitive_column: Optional[str],
    sheet_name: str,
) -> dict:
    sheet = TableSheet(
        name=sheet_name,
        hidden=False,
        max_row=max_row,
        max_column=max_column,
        cells=cells,
    )
    labels = header_labels(sheet)
    by_name = {label.lower(): column for column, label in labels.items()}
    if requested:
        missing = [name for name in requested if name.lower() not in by_name]
        if missing:
            raise ValueError(
                "Unknown quasi column(s): "
                + ", ".join(missing)
                + ". Headers are "
                + ", ".join(labels[column] for column in sorted(labels))
                + "."
            )
        columns = [by_name[name.lower()] for name in requested]
    else:
        columns = [
            column
            for column, label in labels.items()
            if any(hint in set(_tokens(label)) for hint, _kind in _HINTS)
        ]
    kinds = {column: column_kind(labels[column]) for column in columns}
    lookup = {(cell.row, cell.column): cell for cell in cells}
    data_rows: List[int] = []
    matrix: List[List[str]] = []
    for row in range(2, max_row + 1):
        values = [
            _cell_text(lookup.get((row, column)))
            for column in range(1, max_column + 1)
        ]
        if columns and any(values[column - 1] for column in columns):
            data_rows.append(row)
            matrix.append(values)
    zero_columns = [column - 1 for column in columns]
    zero_kinds = {column - 1: kinds[column] for column in columns}
    levels_zero = choose_levels(matrix, zero_columns, zero_kinds, k)
    levels = {column + 1: level for column, level in levels_zero.items()}
    for row_number, values in zip(data_rows, matrix):
        for column in columns:
            cell = lookup.get((row_number, column))
            if cell is None or cell.kind == "formula":
                continue
            new = generalize(values[column - 1], kinds[column], levels[column])
            if new != cell.search_text:
                cell.search_text = new
                cell.kind = "text"
    projected = _project(matrix, zero_columns, zero_kinds, levels_zero)
    sensitive_values = None
    if sensitive_column:
        sensitive_index = by_name.get(sensitive_column.lower())
        if sensitive_index is None:
            raise ValueError(
                f"Unknown sensitive column {sensitive_column!r}."
            )
        sensitive_values = [
            values[sensitive_index - 1] if sensitive_index - 1 < len(values) else ""
            for values in matrix
        ]
    column_report = [
        {
            "header": labels[column],
            "kind": kinds[column],
            "level": levels.get(column, 0),
        }
        for column in columns
    ]
    report = prosecutor_report(
        projected,
        k=k,
        sensitive=sensitive_values,
        columns=column_report,
    )
    report["sheet"] = sheet_name
    return report


def write_table_privacy_report(report: dict, anonymized_file_path: str) -> str:
    """Write ``data/stats/<stem>.table_privacy.json``."""
    import json
    import os
    from pathlib import Path

    from pdf_anonymizer_core.conf import DEFAULT_STATS_DIR

    os.makedirs(DEFAULT_STATS_DIR, exist_ok=True)
    stem = Path(anonymized_file_path).stem
    path = f"{DEFAULT_STATS_DIR}/{stem}.table_privacy.json"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def _cell_text(cell: Optional[TableCell]) -> str:
    if cell is None or cell.kind in {"empty", "bool", "formula"}:
        return ""
    return cell.search_text or ""
