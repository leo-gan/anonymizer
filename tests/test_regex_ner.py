import unittest
from pdf_anonymizer_core.regex_ner import extract_entities_via_regex
from pdf_anonymizer_core.conf import DEFAULT_REGEX_PATTERNS


class TestRegexNer(unittest.TestCase):
    def test_ip_address_valid(self):
        """Test that valid IP addresses are matched."""
        text = "My local IP is 192.168.1.100 and dns is 8.8.8.8."
        entities = extract_entities_via_regex(text, {"IP_ADDRESS": DEFAULT_REGEX_PATTERNS["IP_ADDRESS"]})
        
        ips = [e["text"] for e in entities]
        self.assertIn("192.168.1.100", ips)
        self.assertIn("8.8.8.8", ips)
        self.assertEqual(len(entities), 2)

    def test_ip_address_invalid(self):
        """Test that invalid IP addresses are ignored."""
        text = "Invalid IPs: 999.999.999.999, 256.1.2.3, 1.2.3.256, 1234.1.2.3, 1.2.3.4567, 1.2.3"
        entities = extract_entities_via_regex(text, {"IP_ADDRESS": DEFAULT_REGEX_PATTERNS["IP_ADDRESS"]})
        
        ips = [e["text"] for e in entities]
        self.assertNotIn("999.999.999.999", ips)
        self.assertNotIn("256.1.2.3", ips)
        self.assertNotIn("1.2.3.256", ips)
        # 1234.1.2.3 and 1.2.3.4567 should be ignored entirely
        self.assertEqual(len(entities), 0)

    def test_ip_address_partial_matches(self):
        """Test that IP_ADDRESS regex avoids partial matches in longer numeric strings."""
        text = "This is a version number 1.2.3.45678 or a long string 192.168.1.1000."
        entities = extract_entities_via_regex(text, {"IP_ADDRESS": DEFAULT_REGEX_PATTERNS["IP_ADDRESS"]})
        self.assertEqual(len(entities), 0)


if __name__ == "__main__":
    unittest.main()
