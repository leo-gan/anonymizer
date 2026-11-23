"""Public id-extract API: default is all countries, UK aliases GB."""

from id_extract import available_countries, extract, patterns


def test_default_extract_uses_all_countries() -> None:
    text = "Card 4111111111111111 and SSN 123-45-6789 and NINO AB123456C"
    ents = extract(text)
    types = {item["type"] for item in ents}
    assert "CREDIT_CARD" in types
    assert "SSN_US" in types or "SSN" in types
    assert "NINO_GB" in types


def test_country_filter_drops_other_national_ids() -> None:
    text = "SSN 123-45-6789 and NINO AB123456C"
    types = {item["type"] for item in extract(text, countries=["GB"])}
    assert "NINO_GB" in types
    assert "SSN_US" not in types
    assert "SSN" not in types


def test_uk_alias_matches_gb() -> None:
    assert patterns(countries=["UK"]) == patterns(countries=["GB"])
    assert "NINO_GB" in patterns(countries=["uk"])
    assert "SSN_US" not in patterns(countries=["UK"])


def test_available_countries_lists_bundled_iso2() -> None:
    codes = available_countries()
    assert "US" in codes
    assert "GB" in codes
    assert "CA" in codes
    assert "FR" in codes


def test_offsets_are_in_the_given_string() -> None:
    text = "Write ada@example.com please"
    ents = extract(text, countries=["US"])
    email = next(item for item in ents if item["type"] == "EMAIL")
    assert text[email["start"] : email["end"]] == email["text"]
    assert email["source"] == "regex"


def test_drivers_licenses_do_not_match_uppercase_headings() -> None:
    headings = (
        "FACTS PROCEDURE SUMMARY APPENDIX ABSTRACT METHODS RESULTS "
        "INTERVIEWER PARTICIPANT CONFIDENTIAL INTRODUCTION"
    )
    hits = [
        item
        for item in extract(headings)
        if item["type"].startswith("DRIVERS_LICENSE") or item["type"] == "BIC_SWIFT"
    ]
    assert hits == []


def test_tightened_drivers_license_examples_still_match() -> None:
    samples = [
        ("DRIVERS_LICENSE_CA", "A1234-12345-12345", ["CA"]),
        ("DRIVERS_LICENSE_AU", "12345678", ["AU"]),
        ("DRIVERS_LICENSE_ES", "12345678Z", ["ES"]),
        ("DRIVERS_LICENSE_IT", "U1A2345678", ["IT"]),
        ("DRIVERS_LICENSE_DE", "B072RRE2I55", ["DE"]),
        ("DRIVERS_LICENSE_FR", "12AB34567890", ["FR"]),
    ]
    for expected_type, sample, countries in samples:
        types = {item["type"] for item in extract(sample, countries=countries)}
        assert expected_type in types, f"{expected_type} missed on {sample}"
