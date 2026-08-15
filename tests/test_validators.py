"""Checksum helpers used after the regex stage."""

from pdf_anonymizer_core.validators import (
    like_type,
    luhn_ok,
    parent_type,
    passes_checksum,
    type_matches_filter,
    validate_aadhaar_in,
    validate_codice_fiscale_it,
    validate_cpf_br,
    validate_credit_card,
    validate_dni_es,
    validate_iban,
    validate_nie_es,
    validate_npi,
    validate_pesel_pl,
    validate_resident_id_cn,
    validate_sin_ca,
    validate_vin,
    verhoeff_ok,
)


class TestLuhnAndVerhoeff:
    def test_luhn_known_cards(self) -> None:
        assert luhn_ok("4111111111111111")
        assert luhn_ok("378282246310005")
        assert not luhn_ok("4111111111111112")
        assert not luhn_ok("")

    def test_verhoeff_aadhaar_check_digit(self) -> None:
        assert verhoeff_ok("234123412346")
        assert not verhoeff_ok("234123412347")


class TestTypedValidators:
    def test_credit_card_strips_separators(self) -> None:
        assert validate_credit_card("4111 1111 1111 1111")
        assert validate_credit_card("4242-4242-4242-4242")
        assert not validate_credit_card("1234-5678-9012-3456")

    def test_npi_uses_80840_prefix(self) -> None:
        assert validate_npi("1234567893")
        assert not validate_npi("1234567890")

    def test_sin_ca_is_luhn(self) -> None:
        assert validate_sin_ca("046-454-286")
        assert validate_sin_ca("123-456-782")
        assert not validate_sin_ca("123-456-789")

    def test_iban_mod97_and_country_length(self) -> None:
        assert validate_iban("GB82WEST12345698765432")
        assert validate_iban("DE89 3704 0044 0532 0130 00")
        assert not validate_iban("GB00WEST12345698765432")
        # Wrong length for GB (22).
        assert not validate_iban("GB82WEST1234569876543")
        # Unknown country code.
        assert not validate_iban("ZZ82WEST12345698765432")

    def test_vin_check_digit(self) -> None:
        assert validate_vin("1HGCM82633A004352")
        assert validate_vin("1FTFW1EF0EFA00001")
        assert not validate_vin("1HGCM82633A123456")

    def test_spanish_dni_and_nie(self) -> None:
        assert validate_dni_es("12345678Z")
        assert not validate_dni_es("12345678A")
        assert validate_nie_es("Y1234567X")
        assert not validate_nie_es("Y1234567A")

    def test_chinese_resident_id(self) -> None:
        assert validate_resident_id_cn("110105199001011232")
        assert not validate_resident_id_cn("110105199001011234")

    def test_aadhaar_rejects_leading_zero_or_one(self) -> None:
        assert validate_aadhaar_in("2345 6789 0124")
        assert not validate_aadhaar_in("1234 5678 9012")

    def test_cpf_and_pesel_and_codice(self) -> None:
        assert validate_cpf_br("123.456.789-09")
        assert not validate_cpf_br("111.111.111-11")
        assert validate_pesel_pl("44051401359")
        assert not validate_pesel_pl("44051401350")
        assert validate_codice_fiscale_it("RSSMRA85M01H501Q")
        assert not validate_codice_fiscale_it("RSSMRA85M01H501Z")


class TestPassesChecksumDispatch:
    def test_unknown_type_is_accepted(self) -> None:
        assert passes_checksum("EMAIL", "not-a-real-check")
        assert passes_checksum("PHONE", "999")

    def test_known_type_is_checked(self) -> None:
        assert passes_checksum("CREDIT_CARD", "4111111111111111")
        assert not passes_checksum("CREDIT_CARD", "4111111111111112")
        assert passes_checksum("iban", "DE89370400440532013000")

    def test_like_type_helpers(self) -> None:
        assert like_type("IBAN") == "IBAN_LIKE"
        assert parent_type("IBAN_LIKE") == "IBAN"
        assert parent_type("IBAN") == "IBAN"

    def test_filter_includes_like_sibling(self) -> None:
        assert type_matches_filter("IBAN_LIKE", ["IBAN"])
        assert type_matches_filter("IBAN", ["IBAN"])
        assert type_matches_filter("IBAN_LIKE", ["IBAN_LIKE"])
        assert not type_matches_filter("CREDIT_CARD", ["IBAN"])
        assert not type_matches_filter("PERSON", ["IBAN"])

    def test_filter_matches_type_prefix(self) -> None:
        assert type_matches_filter("DRIVERS_LICENSE_US", ["DRIVERS_LICENSE"])
        assert type_matches_filter("DATE_ISO", ["DATE"])
        assert not type_matches_filter("PERSON", ["PER"])
