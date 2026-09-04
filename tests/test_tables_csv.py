"""CSV as a first-class input: cell-level masking, flatten, save, deanonymize."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pdf_anonymizer_cli.cli import app
from pdf_anonymizer_core.core import anonymize_file, anonymize_tabular_file
from pdf_anonymizer_core.load_and_extract import load_and_extract_text_from_file
from pdf_anonymizer_core.risk import assess_linkage_risk
from pdf_anonymizer_core.tables import (
    EXCEL_EXTRA_MESSAGE,
    TABLE_SUFFIXES,
    TableCell,
    TableDocument,
    TableSheet,
    apply_mapping_to_table,
    flatten_table_for_review,
    load_csv,
    load_review_text,
    load_table,
    save_table,
)
from pdf_anonymizer_core.utils import deanonymize_file, save_results
from pdf_anonymizer_core.verify import verify_anonymized_text

PEOPLE_CSV = Path(__file__).parent / "data" / "tables" / "people.csv"


def _grid(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [list(row) for row in csv.reader(handle)]


def _anonymize_people(**kwargs):
    defaults = dict(
        characters_to_anonymize=1000,
        prompt_template="unused",
        model_name="unused",
        use_llm=False,
    )
    defaults.update(kwargs)
    return anonymize_tabular_file(str(PEOPLE_CSV), **defaults)


class TestPeopleFixture:
    def test_fixture_has_required_shapes(self) -> None:
        doc = load_table(str(PEOPLE_CSV))
        assert doc.kind == "csv"
        sheet = doc.sheets[0]
        assert sheet.name == "Sheet1"
        assert sheet.max_row == 4
        values = {
            (cell.row, cell.column): cell
            for cell in sheet.cells
        }
        assert values[(2, 7)].search_text == "00123"
        assert values[(2, 7)].kind == "text"
        assert values[(2, 8)].kind == "formula"
        assert values[(2, 8)].search_text == "=A1"
        assert values[(2, 9)].search_text == '="Jane"&" Doe"'
        assert values[(2, 9)].kind == "formula"
        assert values[(4, 4)].search_text == "+1-555-0100"
        assert values[(4, 4)].kind == "text"
        assert values[(2, 6)].search_text == "Austin, TX"
        assert "\n" in values[(4, 5)].search_text
        assert (3, 1) not in values


class TestCsvRegexRoundTrip:
    def test_masks_structured_pii_and_preserves_layout(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        review, mapping, entity_texts = _anonymize_people()
        assert "jane@acme.com" not in review
        assert "john@example.com" not in review
        assert "123-45-6789" not in review
        assert "111-22-3333" not in review
        assert "EMAIL_1" in review
        assert "SSN_US_1" in review
        assert mapping["jane@acme.com"].startswith("EMAIL_")
        assert mapping["123-45-6789"].startswith("SSN")

        save_results(
            review,
            {written: original for original, written in mapping.items()},
            str(PEOPLE_CSV),
            entity_texts=entity_texts,
        )
        out = Path("data/anonymized/people.anonymized.csv")
        assert out.is_file()
        rows = _grid(out)
        assert rows[0][0] == "Name"
        assert rows[0][1] == "Email"
        assert rows[2] == [] or all(cell == "" for cell in rows[2])
        assert rows[1][6] == "00123" or "_" in rows[1][6]
        assert rows[1][5] == "Austin, TX"
        assert "\n" in rows[3][4]
        assert rows[1][1].startswith("EMAIL_")
        assert rows[1][2].startswith("SSN")
        assert not rows[1][1].endswith("@acme.com")

    def test_formula_cells_are_prefixed_e164_is_not(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        review, mapping, entity_texts = _anonymize_people()
        save_results(
            review,
            {written: original for original, written in mapping.items()},
            str(PEOPLE_CSV),
            entity_texts=entity_texts,
        )
        rows = _grid(Path("data/anonymized/people.anonymized.csv"))
        assert rows[1][7].startswith("'")
        assert rows[1][7].startswith("'=")
        assert rows[1][8].startswith("'=")
        assert not rows[3][3].startswith("'")
        assert "+1-555-0100" not in rows[3][3] or rows[3][3].startswith("PHONE")
        assert rows[3][3] != "'+1-555-0100"


class TestCsvDeanonymize:
    def test_restores_source_including_equals(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        review, mapping, entity_texts = _anonymize_people()
        anon_path, mapping_path = save_results(
            review,
            {written: original for original, written in mapping.items()},
            str(PEOPLE_CSV),
            entity_texts=entity_texts,
        )
        deanonymized_path, _stats = deanonymize_file(anon_path, mapping_path)
        restored = _grid(Path(deanonymized_path))
        source = _grid(PEOPLE_CSV)
        assert restored == source
        assert restored[1][7] == "=A1"
        assert restored[1][8] == '="Jane"&" Doe"'
        assert restored[3][3] == "+1-555-0100"


class TestCsvDialect:
    def test_semicolon_and_bom_are_preserved(self, tmp_path) -> None:
        src = tmp_path / "eu.csv"
        body = "Name;Email\nAda Lovelace;ada@example.com\n"
        src.write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))
        doc = load_table(str(src))
        assert doc.had_bom is True
        assert doc.dialect["delimiter"] == ";"
        dest = tmp_path / "eu.out.csv"
        save_table(doc, str(dest))
        raw = dest.read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        assert ";" in text
        assert "Ada Lovelace" in text


class TestNotesAndLlmFilter:
    def test_notes_column_replaces_inside_cell(self, mocker) -> None:
        mocker.patch(
            "pdf_anonymizer_core.core.identify_entities_with_llm",
            return_value=[
                {
                    "text": "John Smith",
                    "type": "PERSON",
                    "base_form": "John Smith",
                },
                {"text": "Austin", "type": "LOCATION", "base_form": "Austin"},
            ],
        )
        review, mapping, _texts = _anonymize_people(use_llm=True)
        assert "John Smith" not in review
        assert "Austin" not in review
        assert mapping["John Smith"].startswith("PERSON_")
        assert mapping["Austin"].startswith("LOCATION_")
        assert "Called" in review
        assert "office." in review

    def test_llm_entities_need_locate_spans_in_a_cell(self, mocker, tmp_path) -> None:
        src = tmp_path / "span.csv"
        src.write_text("Name,Email\nAnne,ada@example.com\n", encoding="utf-8")
        mocker.patch(
            "pdf_anonymizer_core.core.identify_entities_with_llm",
            return_value=[
                {
                    "text": "Jane Doe Email",
                    "type": "PERSON",
                    "base_form": "Jane Doe Email",
                },
                {"text": "Ann", "type": "PERSON", "base_form": "Ann"},
            ],
        )
        _review, mapping, entity_texts = anonymize_tabular_file(
            str(src), 1000, "unused", "unused", use_llm=True
        )
        assert "Jane Doe Email" not in mapping
        assert "Ann" not in mapping
        assert "Jane Doe Email" not in entity_texts
        assert "Ann" not in entity_texts
        assert "ada@example.com" in mapping


class TestPerCellApply:
    def test_mapping_does_not_cross_cells(self) -> None:
        doc = TableDocument(
            path="mem.csv",
            kind="csv",
            sheets=[
                TableSheet(
                    name="Sheet1",
                    hidden=False,
                    max_row=1,
                    max_column=2,
                    cells=[
                        TableCell("Sheet1", 1, 1, "May", "May", "text"),
                        TableCell("Sheet1", 1, 2, "Maybe later", "Maybe later", "text"),
                    ],
                )
            ],
        )
        apply_mapping_to_table(doc, {"May": "DATE_1"}, ["May"])
        cells = {(cell.column): cell.search_text for cell in doc.sheets[0].cells}
        assert cells[1] == "DATE_1"
        assert cells[2] == "Maybe later"

    def test_seed_mapping_is_not_applied_without_ner_hit(self) -> None:
        review, mapping, _texts = _anonymize_people(
            seed_mapping={"Ada Lovelace": "PERSON_9"}
        )
        assert "Ada Lovelace" not in review
        assert "PERSON_9" not in review
        source = PEOPLE_CSV.read_text(encoding="utf-8")
        assert "Ada Lovelace" not in source
        jane_cell = [
            cell.search_text
            for cell in load_table(str(PEOPLE_CSV)).sheets[0].cells
            if cell.search_text == "Jane Doe"
        ]
        assert jane_cell
        assert "PERSON_9" not in mapping.get("Jane Doe", "")


class TestSaveResultsInvert:
    def test_cli_style_invert_masks_and_missing_entity_texts_raises(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "ada.csv"
        src.write_text("Name\nAda\n", encoding="utf-8")
        flatten = "# Sheet: Sheet1\n\nName\n\nPERSON_1\n\n"
        out, _mapping = save_results(
            flatten,
            {"PERSON_1": "Ada"},
            str(src),
            entity_texts=["Ada"],
        )
        rows = _grid(Path(out))
        assert rows[1][0] == "PERSON_1"

        out2, _mapping2 = save_results(
            flatten,
            {"Ada": "PERSON_1"},
            str(src),
            entity_texts=["Ada"],
        )
        rows2 = _grid(Path(out2))
        assert rows2[1][0] == "PERSON_1"

        with pytest.raises(ValueError, match="entity_texts"):
            save_results(flatten, {"PERSON_1": "Ada"}, str(src))
        leftover = Path("data/anonymized/ada.anonymized.csv")
        # The successful writes exist; a later missing-entity_texts call must
        # not replace them with the cleartext source.
        assert leftover.read_text(encoding="utf-8")
        assert "Ada" not in leftover.read_text(encoding="utf-8").splitlines()[-1]

        out3, _mapping3 = save_results(
            flatten,
            {"PERSON_1": "Ada"},
            str(src),
            entity_texts=(t for t in ["Ada"]),
        )
        assert _grid(Path(out3))[1][0] == "PERSON_1"

    def test_colliding_mask_needs_engine_orig_map(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "emails.csv"
        src.write_text("Email\nada@example.com\nalice@evil.com\n", encoding="utf-8")
        review, mapping, entity_texts = anonymize_tabular_file(
            str(src),
            1000,
            "unused",
            "unused",
            use_llm=False,
            operators={"EMAIL": "mask"},
        )
        assert mapping["ada@example.com"] == mapping["alice@evil.com"]
        invert = {written: original for original, written in mapping.items()}
        assert len(invert) == 1
        out, _mapping_path = save_results(
            review,
            invert,
            str(src),
            entity_texts=entity_texts,
            orig_to_written=mapping,
        )
        rows = _grid(Path(out))
        assert rows[1][0] == mapping["ada@example.com"]
        assert rows[2][0] == mapping["alice@evil.com"]
        assert "ada@example.com" not in rows[1] + rows[2]
        assert "alice@evil.com" not in rows[1] + rows[2]

        with pytest.raises(ValueError, match="orig_to_written"):
            save_results(
                review,
                {"ada@example.com": mapping["ada@example.com"]},
                str(src),
                entity_texts=["ada@example.com"],
            )


class TestCsvRowWidths:
    def test_ragged_rows_and_empty_field_rows_round_trip(self, tmp_path) -> None:
        src = tmp_path / "ragged.csv"
        src.write_bytes(b"a,b,c\n1,2\n\n,,,\n")
        dest = tmp_path / "out.csv"
        save_table(load_table(str(src)), str(dest))
        assert _grid(dest) == _grid(src)
        assert load_table(str(src)).sheets[0].row_widths == [3, 2, 0, 4]


class TestVerifyAndRiskFlatten:
    def test_flatten_blank_lines_and_high_risk_row(self) -> None:
        doc = TableDocument(
            path="mem.csv",
            kind="csv",
            sheets=[
                TableSheet(
                    name="Employees",
                    hidden=False,
                    max_row=1,
                    max_column=3,
                    cells=[
                        TableCell("Employees", 1, 1, "PERSON_1", "PERSON_1", "text"),
                        TableCell(
                            "Employees", 1, 2, "ORGANIZATION_1", "ORGANIZATION_1", "text"
                        ),
                        TableCell("Employees", 1, 3, "LOCATION_1", "LOCATION_1", "text"),
                    ],
                ),
                TableSheet(
                    name="Hidden",
                    hidden=True,
                    max_row=1,
                    max_column=1,
                    cells=[
                        TableCell("Hidden", 1, 1, "PERSON_2", "PERSON_2", "text"),
                    ],
                ),
            ],
        )
        flat = flatten_table_for_review(doc, anonymized=True)
        assert flat.startswith("# Sheet: Employees\n\n")
        assert "PERSON_1 | ORGANIZATION_1 | LOCATION_1\n\n# Sheet: Hidden\n\n" in flat
        assert flat.endswith("PERSON_2\n\n")
        report = assess_linkage_risk(flat)
        assert report["overall"] == "high"

    def test_load_review_text_is_flatten_not_raw_csv(self, tmp_path) -> None:
        src = tmp_path / "quoted.csv"
        src.write_text(
            'Name,Notes\nAda,"hello, leftover@example.com"\n',
            encoding="utf-8",
        )
        text = load_review_text(str(src))
        assert "# Sheet: Sheet1" in text
        assert " | " in text
        assert "leftover@example.com" in text
        assert not text.startswith("Name,Notes")
        report = verify_anonymized_text(text)
        assert any(hit["text"] == "leftover@example.com" for hit in report["regex_hits"])

    def test_verify_and_report_cli_use_load_review_text(
        self, tmp_path, monkeypatch, mocker
    ) -> None:
        monkeypatch.chdir(tmp_path)
        path = tmp_path / "note.anonymized.txt"
        path.write_text("ok", encoding="utf-8")
        mocked = mocker.patch(
            "pdf_anonymizer_cli.cli.load_review_text",
            return_value="hello leftover@example.com",
        )
        runner = CliRunner()
        verify_result = runner.invoke(app, ["verify", str(path)])
        assert verify_result.exit_code == 0
        mocked.assert_called()
        mocked.reset_mock()
        report_result = runner.invoke(app, ["report", str(path)])
        assert report_result.exit_code == 0
        mocked.assert_called()

    def test_verify_and_report_rejected_suffix_exits_without_traceback(
        self, tmp_path
    ) -> None:
        path = tmp_path / "book.xls"
        path.write_bytes(b"not-a-workbook")
        runner = CliRunner()
        verify_result = runner.invoke(app, ["verify", str(path)])
        assert verify_result.exit_code == 1
        assert "Traceback" not in (verify_result.output or "")
        report_result = runner.invoke(app, ["report", str(path)])
        assert report_result.exit_code == 1
        assert "Traceback" not in (report_result.output or "")


    def test_nul_bytes_are_a_value_error(self, tmp_path) -> None:
        path = tmp_path / "bad.csv"
        path.write_bytes(b"\x00")
        with pytest.raises(ValueError, match="not readable"):
            load_csv(str(path))


class TestRejectsAndLimits:
    def test_table_suffixes_include_xlsx(self) -> None:
        assert ".csv" in TABLE_SUFFIXES
        assert ".xlsx" in TABLE_SUFFIXES

    def test_reject_legacy_spreadsheet_suffixes(self, tmp_path) -> None:
        for name, match in (
            ("book.xls", "Legacy .xls"),
            ("book.xlsm", "Macro-enabled"),
            ("book.ods", "OpenDocument"),
            ("book.xlsb", "Legacy .xls"),
        ):
            path = tmp_path / name
            path.write_bytes(b"not-a-workbook")
            with pytest.raises(ValueError, match=match):
                anonymize_file(str(path), 1000, "unused", "unused", use_llm=False)
            with pytest.raises(ValueError, match=match):
                load_and_extract_text_from_file(str(path))

    def test_xlsx_requires_excel_extra(self, tmp_path, monkeypatch) -> None:
        path = tmp_path / "roster.xlsx"
        path.write_bytes(b"pk")
        monkeypatch.setitem(sys.modules, "openpyxl", None)
        with pytest.raises(ValueError, match=r'pdf-anonymizer-core\[excel\]'):
            load_table(str(path))
        assert EXCEL_EXTRA_MESSAGE in (
            "Excel support requires the extra: "
            'pip install "pdf-anonymizer-core[excel]"'
        )

    def test_cell_limit_raises(self, monkeypatch) -> None:
        monkeypatch.setattr("pdf_anonymizer_core.conf.MAX_TABLE_CELLS", 2)
        with pytest.raises(ValueError, match="cells"):
            load_table(str(PEOPLE_CSV))

    def test_byte_limit_raises(self, tmp_path, monkeypatch) -> None:
        src = tmp_path / "big.csv"
        src.write_text("a,b\n1,2\n", encoding="utf-8")
        monkeypatch.setattr("pdf_anonymizer_core.conf.MAX_TABLE_BYTES", 4)
        with pytest.raises(ValueError, match="bytes"):
            load_table(str(src))


class TestEmptyMappingStillWrites:
    def test_pii_free_csv_is_written(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "plain.csv"
        src.write_text("col_a,col_b\nhello,world\n", encoding="utf-8")
        review, mapping, entity_texts = anonymize_tabular_file(
            str(src), 1000, "unused", "unused", use_llm=False
        )
        assert mapping == {} or all(
            not value.startswith("EMAIL_") for value in mapping.values()
        )
        out, mapping_path = save_results(
            review, mapping, str(src), entity_texts=entity_texts
        )
        assert Path(out).is_file()
        assert _grid(Path(out)) == _grid(src)
        assert Path(mapping_path).is_file()


class TestCrossFileMap:
    def test_same_person_keeps_placeholder(self, mocker, tmp_path) -> None:
        first = tmp_path / "a.csv"
        first.write_text("Name\nJane Doe\n", encoding="utf-8")
        mocker.patch(
            "pdf_anonymizer_core.core.identify_entities_with_llm",
            return_value=[
                {"text": "Jane Doe", "type": "PERSON", "base_form": "Jane Doe"}
            ],
        )
        mocker.patch(
            "pdf_anonymizer_core.core.extract_entities_via_regex",
            return_value=[],
        )
        _review, mapping, _texts = anonymize_tabular_file(
            str(first), 1000, "unused", "unused", use_llm=True
        )
        assert mapping["Jane Doe"] == "PERSON_1"
        mocker.patch("os.path.getsize", return_value=20)
        mocker.patch(
            "pdf_anonymizer_core.core.load_and_extract_text_from_file",
            return_value=("Hello Jane Doe", ["Hello Jane Doe"]),
        )
        _text, second = anonymize_file(
            "notes.md",
            1000,
            "unused",
            "unused",
            seed_mapping=mapping,
            use_llm=True,
        )
        assert second["Jane Doe"] == "PERSON_1"


class TestAnonymizeFileDispatch:
    def test_csv_dispatch_returns_flatten(self) -> None:
        review, mapping = anonymize_file(
            str(PEOPLE_CSV), 1000, "unused", "unused", use_llm=False
        )
        assert review is not None
        assert "# Sheet: Sheet1" in review
        assert mapping is not None
        assert "jane@acme.com" in mapping
