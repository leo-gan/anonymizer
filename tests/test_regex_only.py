"""Regex-only / offline mode: skip the LLM, keep the rest of the pipeline."""

from pdf_anonymizer_core.conf import ConfigProfile, get_config_for_profile
from pdf_anonymizer_core.core import anonymize_file


def _stub_file(mocker, text: str) -> None:
    mocker.patch("os.path.getsize", return_value=len(text))
    mocker.patch(
        "pdf_anonymizer_core.core.load_and_extract_text_from_file",
        return_value=(text, [text]),
    )


class TestAnonymizeWithoutLlm:
    def test_skips_llm_and_still_masks_structured_pii(self, mocker) -> None:
        text = "Write to ada@example.com about Ada Lovelace."
        _stub_file(mocker, text)
        llm = mocker.patch(
            "pdf_anonymizer_core.core.identify_entities_with_llm",
            return_value=[
                {
                    "text": "Ada Lovelace",
                    "type": "PERSON",
                    "base_form": "Ada Lovelace",
                }
            ],
        )
        anonymized, mapping = anonymize_file(
            "dummy.txt", 1000, "unused", "unused", use_llm=False
        )
        llm.assert_not_called()
        assert "ada@example.com" not in anonymized
        assert "EMAIL_1" in anonymized
        assert mapping["ada@example.com"] == "EMAIL_1"
        # Names and identity clues are not a regex job.
        assert "Ada Lovelace" in anonymized
        assert "PERSON_1" not in anonymized

    def test_default_still_calls_the_language_model(self, mocker) -> None:
        text = "Hello Ada Lovelace"
        _stub_file(mocker, text)
        llm = mocker.patch(
            "pdf_anonymizer_core.core.identify_entities_with_llm",
            return_value=[
                {
                    "text": "Ada Lovelace",
                    "type": "PERSON",
                    "base_form": "Ada Lovelace",
                }
            ],
        )
        mocker.patch(
            "pdf_anonymizer_core.core.extract_entities_via_regex",
            return_value=[],
        )
        anonymized, mapping = anonymize_file("dummy.txt", 1000, "dummy", "dummy")
        llm.assert_called_once()
        assert anonymized == "Hello PERSON_1"
        assert mapping["Ada Lovelace"] == "PERSON_1"

    def test_checksum_like_labels_still_apply(self, mocker) -> None:
        text = "Pay DE89370400440532013000 or GB00WEST12345698765432."
        _stub_file(mocker, text)
        llm = mocker.patch("pdf_anonymizer_core.core.identify_entities_with_llm")
        anonymized, mapping = anonymize_file(
            "dummy.txt", 1000, "unused", "unused", use_llm=False
        )
        llm.assert_not_called()
        assert "DE89370400440532013000" not in anonymized
        assert "GB00WEST12345698765432" not in anonymized
        assert "IBAN_1" in anonymized
        assert "IBAN_LIKE_1" in anonymized
        assert mapping["DE89370400440532013000"] == "IBAN_1"
        assert mapping["GB00WEST12345698765432"] == "IBAN_LIKE_1"

    def test_operators_still_run(self, mocker) -> None:
        text = "Card 4111 1111 1111 1111"
        _stub_file(mocker, text)
        mocker.patch("pdf_anonymizer_core.core.identify_entities_with_llm")
        anonymized, mapping = anonymize_file(
            "dummy.txt",
            1000,
            "unused",
            "unused",
            operators={"CREDIT_CARD": "mask"},
            use_llm=False,
        )
        assert "4111 1111 1111 1111" not in anonymized
        assert "CREDIT_CARD_1" not in anonymized
        assert mapping["4111 1111 1111 1111"] != "CREDIT_CARD_1"

    def test_country_filter_still_applies(self, mocker) -> None:
        from pdf_anonymizer_core.conf import filter_regex_patterns

        text = "US 123-45-6789 and GB AA123456C"
        _stub_file(mocker, text)
        mocker.patch("pdf_anonymizer_core.core.identify_entities_with_llm")
        anonymized, mapping = anonymize_file(
            "dummy.txt",
            1000,
            "unused",
            "unused",
            regex_patterns=filter_regex_patterns(["US"]),
            use_llm=False,
        )
        assert "123-45-6789" not in anonymized
        assert "AA123456C" in anonymized
        assert any("SSN" in written for written in mapping.values())


class TestRegexOnlyProfile:
    def test_regex_only_profile_disables_llm(self) -> None:
        cfg = get_config_for_profile(ConfigProfile.REGEX_ONLY)
        assert cfg.use_llm is False
        assert cfg.enable_cache is False
        assert cfg.model_name == "none"
        assert "EMAIL" in cfg.regex_patterns

    def test_default_profiles_still_use_llm(self) -> None:
        for profile in (
            ConfigProfile.BEST_SPEED,
            ConfigProfile.BEST_QUALITY,
            ConfigProfile.BEST_COST,
        ):
            cfg = get_config_for_profile(profile)
            assert cfg.use_llm is True
            assert cfg.enable_cache is True
