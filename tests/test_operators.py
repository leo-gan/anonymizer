"""Per-type operators: replace, mask, hash, generalize, shift."""

import pytest

from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.operators import (
    apply_operator,
    fake_value,
    generalize_value,
    hash_value,
    mask_value,
    operator_for_type,
    parse_operator_specs,
    shift_date_value,
)


class TestParseSpecs:
    def test_parses_and_rejects_bad(self) -> None:
        assert parse_operator_specs(["CREDIT_CARD=mask", "DATE=generalize"]) == {
            "CREDIT_CARD": "mask",
            "DATE": "generalize",
        }
        assert parse_operator_specs(["PERSON=fake"]) == {"PERSON": "fake"}
        with pytest.raises(ValueError, match="Unknown operator"):
            parse_operator_specs(["PERSON=redact"])
        with pytest.raises(ValueError, match="Invalid"):
            parse_operator_specs(["PERSON"])


class TestOperatorForType:
    def test_like_and_date_follow_parent(self) -> None:
        ops = {"CREDIT_CARD": "mask", "DATE": "generalize"}
        assert operator_for_type("CREDIT_CARD_LIKE", ops) == "mask"
        assert operator_for_type("DATE_ISO", ops) == "generalize"
        assert operator_for_type("PERSON", ops) == "replace"


class TestMaskHashGeneralizeShift:
    def test_mask_card_keeps_last_four(self) -> None:
        assert mask_value("4111 1111 1111 1111", "CREDIT_CARD").endswith("1111")
        assert "4111" not in mask_value("4111 1111 1111 1111", "CREDIT_CARD")[:4]

    def test_mask_email(self) -> None:
        out = mask_value("ada@example.com", "EMAIL")
        assert out.startswith("a")
        assert "@" in out
        assert "ada@" not in out

    def test_hash_is_stable(self) -> None:
        assert hash_value("Ada") == hash_value("Ada")
        assert hash_value("Ada") != hash_value("Bob")
        assert hash_value("Ada").startswith("H_")

    def test_generalize_date_zip_age(self) -> None:
        assert generalize_value("2019-06-20", "DATE_ISO") == "2019"
        assert generalize_value("02139", "ZIP") == "021**"
        assert generalize_value("47", "AGE") == "40-49"
        assert generalize_value("91", "AGE") == "90+"
        assert "021**" in generalize_value("123 Main St, Boston MA 02139", "ADDRESS")

    def test_shift_is_stable_per_base_form(self) -> None:
        a = shift_date_value("2019-06-20", "Ada Lovelace")
        b = shift_date_value("2019-06-20", "Ada Lovelace")
        c = shift_date_value("2019-06-20", "Someone Else")
        assert a == b
        assert a != "2019-06-20"
        assert c != a
        assert len(a) >= 10

    def test_replace_returns_placeholder(self) -> None:
        assert apply_operator("Ada", "PERSON", "PERSON_1", "replace") == "PERSON_1"

    def test_fake_is_stable_per_base_form_and_secret(self) -> None:
        a = fake_value("Ada Lovelace", "PERSON", "Ada Lovelace", "s")
        b = fake_value("Ada", "PERSON", "Ada Lovelace", "s")
        c = fake_value("Ada Lovelace", "PERSON", "Ada Lovelace", "other")
        d = fake_value("Bob", "PERSON", "Bob", "s")
        assert a == b
        assert a != c
        assert a != d
        assert a != "Ada Lovelace"
        assert " " in a

    def test_fake_email_and_phone_shape(self) -> None:
        email = fake_value("ada@old.com", "EMAIL", "ada@old.com", "s")
        phone = fake_value("555-1234", "PHONE", "555-1234", "s")
        assert "@" in email
        assert phone.startswith("555-010")


class TestAnonymizeWithOperators:
    def test_mask_card_in_document(self, mocker) -> None:
        mocker.patch("os.path.getsize", return_value=0)
        text = "Card 4111 1111 1111 1111"
        mocker.patch(
            "pdf_anonymizer_core.core.load_and_extract_text_from_file",
            return_value=(text, [text]),
        )
        mocker.patch("pdf_anonymizer_core.core.identify_entities_with_llm", return_value=[])
        mocker.patch(
            "pdf_anonymizer_core.core.extract_entities_via_regex",
            return_value=[
                {
                    "text": "4111 1111 1111 1111",
                    "type": "CREDIT_CARD",
                    "base_form": "4111 1111 1111 1111",
                }
            ],
        )
        anonymized, mapping = anonymize_file(
            "dummy.pdf",
            1000,
            "dummy",
            "dummy",
            operators={"CREDIT_CARD": "mask"},
        )
        assert "4111 1111 1111 1111" not in anonymized
        assert anonymized.endswith("1111") or "1111" in anonymized
        assert "CREDIT_CARD_1" not in anonymized
        assert mapping["4111 1111 1111 1111"] != "CREDIT_CARD_1"

    def test_default_is_still_replace(self, mocker) -> None:
        mocker.patch("os.path.getsize", return_value=0)
        text = "Hello Ada Lovelace"
        mocker.patch(
            "pdf_anonymizer_core.core.load_and_extract_text_from_file",
            return_value=(text, [text]),
        )
        mocker.patch(
            "pdf_anonymizer_core.core.identify_entities_with_llm",
            return_value=[
                {"text": "Ada Lovelace", "type": "PERSON", "base_form": "Ada Lovelace"}
            ],
        )
        mocker.patch(
            "pdf_anonymizer_core.core.extract_entities_via_regex",
            return_value=[],
        )
        anonymized, mapping = anonymize_file("dummy.pdf", 1000, "dummy", "dummy")
        assert anonymized == "Hello PERSON_1"
        assert mapping["Ada Lovelace"] == "PERSON_1"
