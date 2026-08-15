"""Linkage-risk scoring on masked text. Does not rewrite."""

from pathlib import Path

from pdf_anonymizer_core.risk import (
    assess_entity_list,
    assess_linkage_risk,
    placeholder_type,
    write_risk_report,
)


class TestPlaceholderType:
    def test_strips_index_and_variation(self) -> None:
        assert placeholder_type("PERSON_1") == "PERSON"
        assert placeholder_type("IBAN_LIKE_2") == "IBAN_LIKE"
        assert placeholder_type("ORGANIZATION_3.v_1") == "ORGANIZATION"


class TestAssessLinkageRisk:
    def test_job_org_place_is_high(self) -> None:
        text = (
            "We met JOB_TITLE_1 of ORGANIZATION_1 at the office in LOCATION_1.\n\n"
            "Later we had lunch."
        )
        report = assess_linkage_risk(text)
        assert report["rewritten"] is False
        assert report["overall"] == "high"
        assert report["high_count"] >= 1
        assert any(
            {"JOB_TITLE", "ORGANIZATION", "LOCATION"} <= set(w["types"])
            for w in report["windows"]
        )

    def test_indirect_is_high(self) -> None:
        report = assess_linkage_risk("Please copy INDIRECT_1 on the filing.")
        assert report["overall"] == "high"

    def test_person_and_location_is_medium(self) -> None:
        report = assess_linkage_risk("PERSON_1 lives in LOCATION_1.")
        assert report["overall"] == "medium"

    def test_lone_person_is_low(self) -> None:
        report = assess_linkage_risk("PERSON_1 sat down.")
        assert report["overall"] == "low"

    def test_email_only_is_not_a_clump(self) -> None:
        report = assess_linkage_risk("Write to EMAIL_1 please.")
        assert report["overall"] == "low"
        assert report["window_count"] == 0

    def test_writes_json(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        report = assess_linkage_risk("PERSON_1 of ORGANIZATION_1 in LOCATION_1.")
        path = write_risk_report(report, "data/anonymized/note.anonymized.md")
        assert Path(path).name == "note.risk.json"
        assert Path(path).is_file()
        assert "high" in Path(path).read_text(encoding="utf-8")

    def test_entity_list_helper(self) -> None:
        report = assess_entity_list(
            [
                {"text": "CEO", "type": "JOB_TITLE"},
                {"text": "Tesla", "type": "ORGANIZATION"},
                {"text": "Austin", "type": "LOCATION"},
            ]
        )
        assert report["overall"] == "high"
        assert report["rewritten"] is False
