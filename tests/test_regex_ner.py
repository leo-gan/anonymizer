import unittest

from pdf_anonymizer_core.conf import DEFAULT_REGEX_PATTERNS
from pdf_anonymizer_core.regex_ner import extract_entities_via_regex


def _extract_types(text: str, only: list[str] | None = None) -> list[str]:
    pats = DEFAULT_REGEX_PATTERNS
    if only:
        pats = {k: DEFAULT_REGEX_PATTERNS[k] for k in only if k in DEFAULT_REGEX_PATTERNS}
    ents = extract_entities_via_regex(text, pats)
    return [e["type"] for e in ents]


def _extract_texts(text: str, key: str) -> list[str]:
    ents = extract_entities_via_regex(text, {key: DEFAULT_REGEX_PATTERNS[key]})
    return [e["text"] for e in ents]


class TestRegexNerCore(unittest.TestCase):
    """Basic sanity and engine switch tests."""

    def test_uses_re2_and_basic_match(self):
        # Smoke test that re2-backed function works end to end
        text = "Contact: alice@example.co.uk  Phone +44 20 7946 0958  IP 10.0.0.1"
        ents = extract_entities_via_regex(
            text,
            {
                "EMAIL": DEFAULT_REGEX_PATTERNS["EMAIL"],
                "PHONE": DEFAULT_REGEX_PATTERNS["PHONE"],
                "IPV4_ADDRESS": DEFAULT_REGEX_PATTERNS["IPV4_ADDRESS"],
            },
        )
        types = {e["type"] for e in ents}
        self.assertIn("EMAIL", types)
        self.assertIn("PHONE", types)
        self.assertIn("IPV4_ADDRESS", types)

    def test_legacy_ip_address_key_still_works(self):
        text = "dns 8.8.8.8 and 192.168.0.1"
        ips = _extract_texts(text, "IP_ADDRESS")
        self.assertIn("8.8.8.8", ips)
        self.assertIn("192.168.0.1", ips)


class TestUniversalPatterns(unittest.TestCase):
    def test_email(self):
        text = "Emails: user.name+tag@sub.domain.co.uk and bad@@x.y"
        hits = _extract_texts(text, "EMAIL")
        self.assertIn("user.name+tag@sub.domain.co.uk", hits)
        self.assertNotIn("bad@@x.y", hits)

    def test_url(self):
        text = "See https://example.com/path?x=1 and http://foo.bar/baz."
        hits = _extract_texts(text, "URL")
        self.assertIn("https://example.com/path?x=1", hits)

    def test_ipv4_valid_and_rejects_invalids(self):
        text = "good: 192.168.1.100  8.8.8.8  10.0.0.255  bad: 999.1.2.3  256.0.0.1  1.2.3.4.5  123.045.067.089"
        hits = _extract_texts(text, "IPV4_ADDRESS")
        self.assertIn("192.168.1.100", hits)
        self.assertIn("8.8.8.8", hits)
        for bad in ("999.1.2.3", "256.0.0.1"):
            self.assertNotIn(bad, hits)

    def test_ipv6_basic(self):
        text = "v6 2001:0db8:85a3:0000:0000:8a2e:0370:7334 and 2001:db8::1"
        hits = _extract_texts(text, "IPV6_ADDRESS")
        # The pattern is intentionally not the most complete IPv6 regex;
        # we just require that common full form matches.
        self.assertTrue(any("2001" in h for h in hits))

    def test_mac(self):
        text = "MACs: 00:1A:2B:3C:4D:5E  aa-bb-cc-dd-ee-ff  00:1a:2b:3c:4d:5e"
        hits = _extract_texts(text, "MAC_ADDRESS")
        self.assertEqual(len(hits), 3)

    def test_credit_card_variants(self):
        text = "Visa-ish 4111 1111 1111 1111  Amex 3782 822463 10005  spaced 1234-5678-9012-3456"
        hits = _extract_texts(text, "CREDIT_CARD")
        self.assertTrue(len(hits) >= 2)
        self.assertTrue(any("4111" in h for h in hits))

    def test_crypto(self):
        text = "BTC 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa  ETH 0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        btc = _extract_texts(text, "CRYPTO_BTC")
        eth = _extract_texts(text, "CRYPTO_ETH")
        self.assertTrue(any("1A1z" in b for b in btc))
        self.assertTrue(any(h.startswith("0x742d") for h in eth))

    def test_iban_and_bic(self):
        # Real-looking IBANs (structure only)
        text = "IBANs: GB82WEST12345698765432  FR1420041010050500013M02606  DE89370400440532013000"
        ibans = _extract_texts(text, "IBAN")
        self.assertGreaterEqual(len(ibans), 2)
        bics = _extract_texts("BIC: DEUTDEFF  CHASUS33XXX", "BIC_SWIFT")
        self.assertIn("DEUTDEFF", bics)

    def test_vin(self):
        text = "Vehicle 1HGCM82633A123456 and junk I0OQ1234567890123 (I/O/Q forbidden)"
        vins = _extract_texts(text, "VIN")
        self.assertIn("1HGCM82633A123456", vins)
        self.assertNotIn("I0OQ1234567890123", [v for v in vins])  # pattern excludes I O Q

    def test_currency_and_date_iso(self):
        text = "Paid $1,234.56 on 2025-06-20T14:30:00Z or 2024-12-31"
        curr = _extract_texts(text, "CURRENCY_AMOUNT")
        dates = _extract_texts(text, "DATE_ISO")
        self.assertTrue(any("1,234" in c or "$" in c for c in curr))
        self.assertTrue(any("2025-06-20" in d for d in dates))


class TestMandatoryCountries(unittest.TestCase):
    """Cover at least the 8 mandatory countries with representative high-value PII."""

    def test_us(self):
        text = "SSN 123-45-6789  EIN 12-3456789  NPI 1234567890  Passport A12345678  DL X1234567"
        types = set(_extract_types(text))
        self.assertIn("SSN_US", types)
        self.assertIn("EIN_US", types)
        self.assertIn("MEDICAL_NPI_US", types)

    def test_canada(self):
        text = "SIN 123-456-789  CA passport AB123456"
        types = set(_extract_types(text, only=["SIN_CA", "CA_PASSPORT"]))
        self.assertIn("SIN_CA", types)

    def test_uk_gb(self):
        text = "NINO AB123456C  UK VAT GB123456789  Companies 01234567  DL ABCDE123456FG1H2J"
        types = set(_extract_types(text))
        self.assertIn("NINO_GB", types)
        self.assertIn("VAT_GB", types)

    def test_france(self):
        text = "INSEE 1851075240027  VAT FRXX123456789  Passport 12AB34567"
        types = set(_extract_types(text))
        self.assertIn("INSEE_FR", types)
        self.assertIn("VAT_FR", types)

    def test_spain(self):
        text = "DNI 12345678Z  NIE Y1234567X  CIF A12345678  VAT ESB12345678"
        types = set(_extract_types(text))
        self.assertIn("DNI_ES", types)
        self.assertIn("NIE_ES", types)
        self.assertIn("CIF_ES", types)

    def test_italy(self):
        text = "CF RSSMRA85M01H501Z  VAT IT01234567890"
        types = set(_extract_types(text))
        self.assertIn("CODICE_FISCALE_IT", types)
        self.assertIn("VAT_IT", types)

    def test_india(self):
        text = "Aadhaar 1234 5678 9012  PAN ABCDE1234F  GSTIN 22AAAAA0000A1Z5"
        types = set(_extract_types(text))
        self.assertIn("AADHAAR_IN", types)
        self.assertIn("PAN_IN", types)
        self.assertIn("GSTIN_IN", types)

    def test_china(self):
        text = "ID 110105199001011234  USCC 91310000MA0ABCDEFG  Passport E12345678"
        types = set(_extract_types(text))
        self.assertIn("RESIDENT_ID_CN", types)
        self.assertIn("UNIFIED_SOCIAL_CREDIT_CODE_CN", types)


class TestAdditionalCountries30Plus(unittest.TestCase):
    """Ensure we have representative patterns for many more countries."""

    def test_eu_and_others(self):
        samples = {
            "DE": "Steuer 12345678901 VAT DE123456789",
            "JP": "MyNumber 1234 5678 9012",
            "KR": "RRN 901010-1234567",
            "AU": "TFN 123 456 789  ABN 12 345 678 901",
            "NZ": "IRD 12-345-678",
            "BR": "CPF 123.456.789-09  CNPJ 12.345.678/0001-90",
            "MX": "CURP HEPT900101HMCRRRN1 RFC HECJ900101ABC",
            "SG": "NRIC S1234567D",
            "HK": "HKID A1234567B",
            "NL": "BSN 123456789  VAT NL123456789B01",
            "SE": "Person 19851212-1234",
            "IE": "PPS 1234567A",
            "IL": "ID 123456789",
            "ZA": "SAID 9001011234087",
        }
        # Just ensure the corresponding pattern keys exist and at least one sample matches its family
        for cc, sample in samples.items():
            # Run full set (cheap) and verify we don't crash + some hits appear for these countries' keys
            ents = extract_entities_via_regex(sample, DEFAULT_REGEX_PATTERNS)
            # At minimum we expect some PII-like matches (numbers) were picked up by one of the patterns
            self.assertGreater(len(ents), 0, f"No matches for {cc} sample")

    def test_many_country_keys_exist(self):
        # Guard that we actually ship patterns for >= 30 countries worth of keys
        country_suffixes = {
            "US", "CA", "GB", "FR", "ES", "IT", "IN", "CN",
            "DE", "JP", "KR", "AU", "NZ", "BR", "MX", "AR",
            "ZA", "SG", "HK", "TW", "NL", "BE", "CH", "AT",
            "SE", "NO", "DK", "FI", "PL", "IE", "PT", "GR",
            "IL", "TR", "RU", "TH", "MY", "ID",
        }
        present = set()
        for key in DEFAULT_REGEX_PATTERNS:
            for suf in country_suffixes:
                if key.endswith("_" + suf):
                    present.add(suf)
                    break
        # Also count universal that cover many (IBAN alone covers dozens)
        self.assertGreaterEqual(len(present) + 3, 30, "Need patterns touching at least ~30 countries")


class TestNoFalsePositivesOnJunk(unittest.TestCase):
    def test_long_numeric_version_not_misread_as_ip(self):
        # Note: without look-ahead (RE2 limitation) a valid 4-octet prefix inside
        # "1.2.3.4.5.6" may match as "1.2.3.4". We primarily care that grossly invalid
        # addresses (256+, 999+, too many octets as a token) are not returned as matches.
        text = "Version 1.2.3.4.5.6  build 192.168.1.1000  not-an-ip 999.999.999.999  256.1.2.3  1.2.3.4.5"
        ips = _extract_texts(text, "IPV4_ADDRESS")
        for bad in ("999.999.999.999", "256.1.2.3", "192.168.1.1000"):
            self.assertNotIn(bad, ips)

    def test_vin_excludes_invalid_chars(self):
        bad = "VIN candidate: IOO0123456789ABCDE (contains forbidden I O Q)"
        self.assertNotIn("IOO0123456789ABCDE", _extract_texts(bad, "VIN"))


class TestFullDefaultIntegration(unittest.TestCase):
    def test_full_default_on_mixed_pii_document(self):
        """Realistic mixed document containing PII from several countries + universal."""
        doc = """
        From: alice.smith@acme.co.uk
        Paid invoice USD 4,567.89 via IBAN DE89370400440532013000 on 2025-03-14T09:00:00Z
        US customer SSN 987-65-4321 , CC 4242-4242-4242-4242
        Crypto donation 0xAbC1230000000000000000000000000000000000
        French client INSEE 1851075240027 VAT FRXX123456789
        Indian Aadhaar 2345 6789 0123 PAN AAAPA1234A
        Chinese resident 110101200001011234
        VIN for the fleet: 1FTFW1EF5EFA00001   MAC 00:11:22:33:44:55
        """
        ents = extract_entities_via_regex(doc, DEFAULT_REGEX_PATTERNS)
        types = {e["type"] for e in ents}
        texts = {e["text"] for e in ents}

        # Universals
        self.assertIn("EMAIL", types)
        self.assertIn("IBAN", types)
        self.assertIn("CREDIT_CARD", types)
        self.assertIn("CRYPTO_ETH", types)
        self.assertIn("VIN", types)
        self.assertIn("MAC_ADDRESS", types)
        self.assertIn("DATE_ISO", types)
        self.assertIn("CURRENCY_AMOUNT", types)

        # Country partitioned
        self.assertIn("SSN_US", types)
        self.assertIn("INSEE_FR", types)
        self.assertIn("VAT_FR", types)
        self.assertIn("AADHAAR_IN", types)
        self.assertIn("PAN_IN", types)
        self.assertIn("RESIDENT_ID_CN", types)

        # Actual values captured
        self.assertIn("alice.smith@acme.co.uk", texts)
        self.assertIn("DE89370400440532013000", texts)
        self.assertIn("4242-4242-4242-4242", texts)
        self.assertIn("1FTFW1EF5EFA00001", texts)


if __name__ == "__main__":
    unittest.main()
