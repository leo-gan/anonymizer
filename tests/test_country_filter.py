"""Country filter for first-stage regex patterns."""

import pytest

from pdf_anonymizer_core.conf import (
    COUNTRY_PATTERN_SUFFIXES,
    DEFAULT_REGEX_PATTERNS,
    ConfigProfile,
    filter_regex_patterns,
    get_config_for_profile,
    pattern_country,
)


class TestPatternCountry:
    def test_universal_keys_have_no_country(self) -> None:
        for key in (
            "EMAIL",
            "PHONE",
            "URL",
            "CREDIT_CARD",
            "IBAN",
            "IPV4_ADDRESS",
            "IPV6_ADDRESS",
            "MAC_ADDRESS",
            "CRYPTO_BTC",
            "CRYPTO_ETH",
            "DATE_ISO",
            "VIN",
            "BIC_SWIFT",
            "CURRENCY_AMOUNT",
            "IP_ADDRESS",
        ):
            assert pattern_country(key) is None, key

    def test_suffixed_and_alias_keys(self) -> None:
        assert pattern_country("SSN_US") == "US"
        assert pattern_country("NINO_GB") == "GB"
        assert pattern_country("PESEL_PL") == "PL"
        assert pattern_country("AADHAAR_IN") == "IN"
        assert pattern_country("SSN") == "US"


class TestFilterRegexPatterns:
    def test_none_or_empty_returns_all(self) -> None:
        assert filter_regex_patterns(None) == DEFAULT_REGEX_PATTERNS
        assert filter_regex_patterns([]) == DEFAULT_REGEX_PATTERNS

    def test_keeps_universals_and_selected_countries(self) -> None:
        filtered = filter_regex_patterns(["US", "GB"])
        assert "EMAIL" in filtered
        assert "IBAN" in filtered
        assert "CREDIT_CARD" in filtered
        assert "SSN_US" in filtered
        assert "SSN" in filtered
        assert "NINO_GB" in filtered
        assert "VAT_GB" in filtered
        assert "PESEL_PL" not in filtered
        assert "AADHAAR_IN" not in filtered
        assert "INSEE_FR" not in filtered

    def test_gb_only_drops_us_alias(self) -> None:
        filtered = filter_regex_patterns(["gb"])
        assert "NINO_GB" in filtered
        assert "EMAIL" in filtered
        assert "SSN" not in filtered
        assert "SSN_US" not in filtered

    def test_unknown_code_raises(self) -> None:
        with pytest.raises(ValueError, match="XX"):
            filter_regex_patterns(["US", "XX"])

    def test_custom_pattern_dict_is_filtered(self) -> None:
        custom = {
            "EMAIL": "e",
            "SSN_US": "u",
            "NINO_GB": "g",
        }
        filtered = filter_regex_patterns(["US"], patterns=custom)
        assert filtered == {"EMAIL": "e", "SSN_US": "u"}

    def test_profile_helper_applies_filter(self) -> None:
        cfg = get_config_for_profile(ConfigProfile.BEST_SPEED, countries=["FR"])
        assert "INSEE_FR" in cfg.regex_patterns
        assert "EMAIL" in cfg.regex_patterns
        assert "NINO_GB" not in cfg.regex_patterns

    def test_suffix_set_covers_builtin_country_keys(self) -> None:
        seen = {
            pattern_country(key)
            for key in DEFAULT_REGEX_PATTERNS
            if pattern_country(key)
        }
        assert seen <= COUNTRY_PATTERN_SUFFIXES
        assert len(seen) >= 20
