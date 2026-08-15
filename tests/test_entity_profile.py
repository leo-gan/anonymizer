"""HIPAA Safe Harbor entity profile — coverage aid, not a certificate."""

from pdf_anonymizer_core.conf import (
    EntityProfile,
    HIPAA_SAFE_HARBOR_OPERATORS,
    operators_for_entity_profile,
    types_for_entity_profile,
)
from pdf_anonymizer_core.operators import operator_for_type
from pdf_anonymizer_core.prompts import hipaa
from pdf_anonymizer_core.validators import type_matches_filter


class TestHipaaProfile:
    def test_covers_core_safe_harbor_classes(self) -> None:
        types = types_for_entity_profile(EntityProfile.HIPAA_SAFE_HARBOR)
        assert types is not None
        needed = {
            "PERSON",
            "ADDRESS",
            "DATE",
            "PHONE",
            "EMAIL",
            "SSN",
            "MEDICAL_RECORD",
            "HEALTH_PLAN_ID",
            "ACCOUNT",
            "VIN",
            "URL",
            "IPV4_ADDRESS",
            "BIOMETRIC",
            "PHOTO",
        }
        assert needed <= set(types)

    def test_generalizes_dates_address_age(self) -> None:
        ops = operators_for_entity_profile(EntityProfile.HIPAA_SAFE_HARBOR)
        assert ops["DATE"] == "generalize"
        assert ops["DATE_ISO"] == "generalize"
        assert ops["ADDRESS"] == "generalize"
        assert ops["AGE"] == "generalize"
        assert operator_for_type("DATE_ISO", {**HIPAA_SAFE_HARBOR_OPERATORS}) == "generalize"

    def test_type_filter_includes_country_licenses(self) -> None:
        types = types_for_entity_profile(EntityProfile.HIPAA_SAFE_HARBOR)
        assert types is not None
        assert type_matches_filter("DRIVERS_LICENSE_US", types)
        assert type_matches_filter("US_PASSPORT", types)
        assert type_matches_filter("SSN_US", types)
        assert type_matches_filter("DATE_ISO", types)

    def test_prompt_asks_for_more_than_birthdates(self) -> None:
        text = hipaa.prompt_template
        assert "birth" in text.lower()
        assert "admission" in text.lower()
        assert "MEDICAL_RECORD" in text
        assert "BIOMETRIC" in text
        assert "not a legal certification" in text.lower() or "not a legal" in text.lower()
        assert "AGE" in text

    def test_none_profile_is_a_no_op(self) -> None:
        assert types_for_entity_profile(None) is None
        assert operators_for_entity_profile(None) == {}
