"""Federal identifiers are on by default. State and industry IDs are opt-in."""

import pytest

from id_extract import available_opt_in, extract, patterns
from id_extract.checksums import passes_checksum


def _types(text: str, **kwargs) -> set[str]:
    return {item["type"] for item in extract(text, **kwargs)}


def test_default_map_has_new_federal_ids_and_not_opt_in() -> None:
    loaded = patterns()
    assert "ITIN_US" in loaded
    assert "PROGRAM_ACCOUNT_CA" in loaded
    assert "CLABE_MX" in loaded
    assert "NSS_MX" in loaded
    assert "DL_FL_US" not in loaded
    assert "NAM_QC_CA" not in loaded
    assert "RTN_US" not in loaded


def test_itin_and_atin_replace_the_ssn_label() -> None:
    assert _types("ITIN 900-70-0000") >= {"ITIN_US"}
    assert "SSN_US" not in _types("ITIN 900-70-0000")
    assert "SSN" not in _types("ITIN 900-70-0000")
    assert _types("ATIN 900-93-0000") >= {"ATIN_US"}
    assert "ITIN_US" not in _types("ATIN 900-93-0000")
    assert _types("SSN 123-45-6789") >= {"SSN_US"}
    assert "ITIN_US" not in _types("SSN 123-45-6789")


def test_other_us_federal_shapes() -> None:
    text = (
        "PTIN P00000000 MBI 1EG4-TE5-MK73 A-Number A000000001 "
        "receipt ABC0000000001 case XYZ0123456789 DEA AB1234563"
    )
    found = _types(text, countries=["US"])
    assert {
        "PTIN_US",
        "MBI_US",
        "A_NUMBER_US",
        "USCIS_RECEIPT_US",
        "DEA_US",
    } <= found
    assert "MEDICAL_LICENSE_US" not in found
    assert "DOS_CASE_US" in _types("case XYZ012345678", countries=["US"])


def test_unissued_ssn_groups_do_not_match() -> None:
    assert "SSN_US" not in _types("000-12-1234")
    assert "SSN_US" not in _types("666-12-1234")
    assert "SSN_US" not in _types("123-00-1234")
    assert "SSN_US" not in _types("123-45-0000")
    assert "SSN_US" in _types("667-12-1234")


def test_sin_rejects_a_leading_zero_or_eight() -> None:
    assert "SIN_CA" not in _types("046-454-286", countries=["CA"])
    assert "SIN_CA" not in _types("812-345-678", countries=["CA"])


def test_new_official_shapes_keep_only_a_passing_check() -> None:
    assert "ACN_AU" in _types("ACN 530 000 009", countries=["AU"])
    assert "ACN_AU" not in _types("ACN 530 000 000", countries=["AU"])
    assert "MEDICARE_AU" in _types("Medicare 2428 77813 1", countries=["AU"])
    assert "MEDICARE_AU" not in _types("Medicare 2428778141", countries=["AU"])
    assert "NHS_GB" in _types("NHS 943 476 5919", countries=["GB"])
    assert "NHS_GB" not in _types("NHS 9434765918", countries=["GB"])
    assert "UEN_SG" in _types("UEN 201912345R", countries=["SG"])
    assert "UEN_SG" not in _types("UEN 201912345A", countries=["SG"])
    assert "PASSPORT_GB" in _types("passport AB1234567", countries=["GB"])
    assert "PASSPORT_GB" not in _types("company SC1234567", countries=["GB"])
    assert "COMPANIES_HOUSE_GB" in _types("company SC1234567", countries=["GB"])
    germany = _types("card C00000004 legacy T22000129 HRB 12345", countries=["DE"])
    assert {"PERSONALAUSWEIS_DE", "HANDELSREGISTER_DE"} <= germany
    assert "PERSONALAUSWEIS_DE" not in _types("card C00000005", countries=["DE"])
    assert "PERSONALAUSWEIS_DE_LIKE" in _types("card C00000005", countries=["DE"])
    assert passes_checksum("DEA_US", "AB1234563")
    assert not passes_checksum("DEA_US", "AB1234567")


def test_remaining_presidio_checks() -> None:
    assert "NRIC_SG" in _types("FIN F1234567A and M1234567B", countries=["SG"])
    assert "HETU_FI" in _types("hetu 131052-308T", countries=["FI"])
    assert "HETU_FI_LIKE" in _types("hetu 131052-308A", countries=["FI"])
    assert "HETU_FI" not in _types("hetu 131052-308A", countries=["FI"])
    assert "NATIONAL_ID_TH" in _types("Thai 1101700200001", countries=["TH"])
    assert "NATIONAL_ID_TH" not in _types("Thai 1101700200000", countries=["TH"])
    assert "NATIONAL_ID_TR" in _types("TCKN 10000000146", countries=["TR"])
    assert "NATIONAL_ID_TR" not in _types("TCKN 10000000147", countries=["TR"])
    assert "STEUER_ID_DE" in _types("IdNr 26954371827", countries=["DE"])
    assert "STEUER_ID_DE" not in _types("IdNr 26954371820", countries=["DE"])
    assert "STEUER_ID_DE" not in _types("IdNr 01234567890", countries=["DE"])


def test_canada_and_mexico_federal_shapes() -> None:
    canada = _types(
        "BN 123456789RT0001 DIN 00000000 NPN 00000000 DIN-HM 00000000 UCI 00-0000-0000",
        countries=["CA"],
    )
    assert {
        "PROGRAM_ACCOUNT_CA",
        "DIN_CA",
        "NPN_CA",
        "DIN_HM_CA",
        "UCI_CA",
    } <= canada
    mexico = _types("NSS 00000000000 pedimento 26  01  0001  6000001", countries=["MX"])
    assert {"NSS_MX", "PEDIMENTO_MX"} <= mexico


def test_clabe_keeps_a_passing_control_digit_only() -> None:
    assert passes_checksum("CLABE_MX", "000000000000000000")
    assert "CLABE_MX" in _types("CLABE 000000000000000000", countries=["MX"])
    assert "CREDIT_CARD" not in _types("000000000000000000", countries=["MX"])
    assert "CLABE_MX" not in _types("CLABE 000000000000000001", countries=["MX"])


def test_opt_in_all_is_selective_and_country_scoped() -> None:
    us = patterns(countries=["US"], opt_in="all")
    assert "DL_FL_US" in us
    assert "RTN_US" in us
    assert "CUSIP_NNA" in us
    assert "NAM_QC_CA" not in us
    assert "LICENSE_IL_US" not in us
    assert "UEI_US" not in us
    ca = patterns(countries=["CA"], opt_in="all")
    assert "NAM_QC_CA" in ca
    assert "CUSIP_NNA" in ca
    assert "DL_FL_US" not in ca


def test_named_broad_key_and_unknown_key() -> None:
    assert "LICENSE_IL_US" in patterns(countries=["US"], opt_in=["LICENSE_IL_US"])
    assert "I94_US" in _types("I-94 00000000001", opt_in="I94_US")
    with pytest.raises(ValueError, match="NOT_A_KEY"):
        patterns(opt_in=["NOT_A_KEY"])
    assert "DL_FL_US" in available_opt_in()


def test_state_and_provincial_shapes() -> None:
    us = _types(
        "FL Z123-456-78-901-0 and Z123456789010 payroll 000-0000-0 "
        "N12345 hull ABC12A34A485 FFL 9-99-999-99-6B-99999",
        countries=["US"],
        opt_in="all",
    )
    assert {
        "DL_FL_US",
        "EDD_PAYROLL_US",
        "N_NUMBER_US",
        "HIN_US",
        "FFL_US",
    } <= us
    assert "N_NUMBER_US" not in _types("bad N01Z", opt_in="all")
    ontario = _types("licence A12345678901231", countries=["CA"], opt_in="all")
    assert "DL_ON_CA" in ontario
    assert "DRIVERS_LICENSE_CA" not in ontario
    assert "DL_ON_CA" not in _types(
        "licence A12345678901232", countries=["CA"], opt_in="all"
    )
    assert "NAM_QC_CA" in _types("NAM ABCD12345678", opt_in="all")
    assert "TVQ_QC_CA" in _types("TVQ 1234567890TQ0001", opt_in="all")
    assert "HEALTH_ON_CA" in _types("HN 1234567890AB", opt_in="all")


def test_checked_opt_in_drops_a_bad_digit() -> None:
    assert passes_checksum("RTN_US", "010000003")
    assert "RTN_US" in _types("routing 010000003", opt_in="all")
    assert "RTN_US" not in _types("routing 010000000", opt_in="all")
    assert passes_checksum("PHN_BC_CA", "9012372173")
    phn = _types("PHN 9012372173", opt_in=["PHN_BC_CA"])
    assert "PHN_BC_CA" in phn
    assert "MEDICAL_NPI_US" not in phn
    assert "MEDICAL_NPI_US_LIKE" not in phn
    body = "AAA000AA"
    good = next(
        body + digit
        for digit in "0123456789"
        if passes_checksum("CUSIP_NNA", body + digit)
    )
    assert "CUSIP_NNA" in _types(f"CUSIP {good}", opt_in="all")
    bad = body + ("0" if good[-1] != "0" else "1")
    assert "CUSIP_NNA" not in _types(f"CUSIP {bad}", opt_in="all")
