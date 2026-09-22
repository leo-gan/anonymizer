"""Optional table-only k-anonymity. Default cell replace stays unchanged."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from pdf_anonymizer_cli.cli import app
from pdf_anonymizer_core.core import anonymize_tabular_file
from pdf_anonymizer_core.table_privacy import (
    apply_table_privacy,
    generalize,
    prosecutor_report,
)
from pdf_anonymizer_core.tables import (
    TableCell,
    TableDocument,
    TableSheet,
    load_table,
)
from pdf_anonymizer_core.utils import save_results

ROSTER = """name,email,zip,gender,diagnosis
Ada,ada@example.com,02139,F,flu
Bea,bea@example.com,02139,F,cold
Cy,cy@example.com,10001,M,flu
"""


def _write(tmp_path: Path) -> Path:
    path = tmp_path / "roster.csv"
    path.write_text(ROSTER, encoding="utf-8")
    return path


def _doc(path: Path) -> TableDocument:
    return load_table(str(path))


def _values(doc: TableDocument) -> dict[tuple[int, int], str]:
    return {(cell.row, cell.column): cell.search_text for cell in doc.sheets[0].cells}


def test_generalize_zip_age_and_date() -> None:
    assert generalize("02139", "zip", 1) == "021**"
    assert generalize("42", "age", 1) == "40-44"
    assert generalize("1981-04-12", "date", 2) == "1981"
    assert generalize("F", "categorical", 1) == "*"


def test_prosecutor_risk_is_one_over_class_size() -> None:
    report = prosecutor_report(
        [("02139", "F"), ("02139", "F"), ("10001", "M")],
        k=2,
        sensitive=["flu", "cold", "flu"],
    )
    assert report["max_prosecutor_risk"] == 1.0
    assert report["records_below_k"] == 1
    assert report["l_diversity"] == 1
    assert "not a privacy certificate" in report["disclaimer"]


def test_k_hides_the_unique_quasi_combination(tmp_path: Path) -> None:
    doc = _doc(_write(tmp_path))
    report = apply_table_privacy(
        doc, k=2, quasi_columns=["zip", "gender"], sensitive_column="diagnosis"
    )
    values = _values(doc)
    assert values[(2, 3)] == values[(3, 3)] == values[(4, 3)]
    assert values[(2, 4)] == values[(3, 4)] == values[(4, 4)]
    assert report["sheets"][0]["k_met"] is True
    assert report["sheets"][0]["max_prosecutor_risk"] <= 0.5
    assert report["sheets"][0]["l_diversity"] == 2
    assert values[(2, 2)] == "ada@example.com"


def test_default_run_does_not_generalize(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = _write(tmp_path)
    review, mapping, texts = anonymize_tabular_file(
        str(path),
        characters_to_anonymize=1000,
        prompt_template="unused",
        model_name="unused",
        use_llm=False,
    )
    assert "F" in review
    assert "ada@example.com" not in review
    save_results(
        review,
        {value: key for key, value in mapping.items()},
        str(path),
        entity_texts=texts,
        orig_to_written=mapping,
    )
    written = (tmp_path / "data/anonymized/roster.anonymized.csv").read_text()
    assert ",F," in written
    assert not (tmp_path / "data/stats/roster.anonymized.table_privacy.json").exists()


def test_cli_k_writes_table_and_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = _write(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "run",
            str(path),
            "--no-llm",
            "--no-ner",
            "--k",
            "2",
            "--quasi-columns",
            "zip,gender",
            "--sensitive-column",
            "diagnosis",
        ],
    )
    assert result.exit_code == 0, result.output
    grid = list(
        csv.reader((tmp_path / "data/anonymized/roster.anonymized.csv").open())
    )
    assert grid[1][2] == grid[2][2] == grid[3][2]
    assert "ada@example.com" not in Path(
        tmp_path / "data/anonymized/roster.anonymized.csv"
    ).read_text()
    report = json.loads(
        (tmp_path / "data/stats/roster.anonymized.table_privacy.json").read_text()
    )
    assert report["sheets"][0]["k_met"] is True
    assert "not a privacy certificate" in report["disclaimer"]


def test_k_refuses_a_pdf(tmp_path: Path) -> None:
    pdf = tmp_path / "note.md"
    pdf.write_text("Ada lives in 02139.", encoding="utf-8")
    result = CliRunner().invoke(app, ["run", str(pdf), "--no-llm", "--no-ner", "--k", "2"])
    assert result.exit_code != 0
    assert pdf.read_text(encoding="utf-8") == "Ada lives in 02139."


def test_in_memory_sheet_shape() -> None:
    """The helper accepts the same cell objects the CSV loader builds."""
    cells = [
        TableCell("Sheet1", 1, 1, "zip", "zip", "text"),
        TableCell("Sheet1", 2, 1, "02139", "02139", "text"),
        TableCell("Sheet1", 3, 1, "02138", "02138", "text"),
    ]
    doc = TableDocument(
        path="memory.csv",
        kind="csv",
        sheets=[TableSheet("Sheet1", False, 3, 1, cells)],
    )
    report = apply_table_privacy(doc, k=2, quasi_columns=["zip"])
    assert report["sheets"][0]["records"] == 2
    assert cells[1].search_text == cells[2].search_text
