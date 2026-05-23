import os
import unittest
from unittest.mock import Mock, patch
from pdf_anonymizer_core.core import anonymize_file


class TestLargePdfAnonymizer(unittest.TestCase):
    @patch("os.path.getsize")
    @patch("pymupdf4llm.to_markdown")
    @patch("pdf_anonymizer_core.call_llm.get_provider")
    def test_large_pdf_anonymization_instant_and_mocked(
        self, mock_get_provider, mock_to_markdown, mock_getsize
    ):
        """
        Tests that a simulated 10 GB PDF runs instantly and consumes 0 tokens
        by fully mocking the PDF conversion and the LLM API calls.
        It also tests the hybrid NER (Regex first, then LLM).
        """
        # Mock file size to be 10 GB
        mock_getsize.return_value = 10 * 1024 * 1024 * 1024  # 10 GB

        # Mock the extracted markdown content from PDF
        # It contains structured PII (email, phone, ip) for Regex stage
        # and a name (John Doe) for LLM stage
        mock_markdown = (
            "# Large Report\n\n"
            "Author: John Doe\n"
            "Email: john.doe@example.com\n"
            "Phone: +1-555-0199\n"
            "Server IP: 192.168.1.100\n"
            "Please contact John Doe if you have questions."
        )
        mock_to_markdown.return_value = mock_markdown

        # Mock LLM provider to return the name (John Doe)
        mock_provider = Mock()
        mock_provider.call.return_value = """
        {
            "entities": [
                {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"}
            ]
        }
        """
        mock_get_provider.return_value = mock_provider

        # Run anonymization with standard detailed prompt and gemini-2.5-pro model
        # Chunk overlap: 1000 characters
        anonymized_text, mapping = anonymize_file(
            file_path="very_large_10gb_file.pdf",
            characters_to_anonymize=50000,
            prompt_template="Identify PII: {text}",
            model_name="gemini-2.5-pro",
            chunk_overlap=1000,
        )

        # Assertions
        # 1. Verify file size mock was queried
        mock_getsize.assert_called_once_with("very_large_10gb_file.pdf")
        
        # 2. Verify pymupdf4llm mock was queried
        mock_to_markdown.assert_called_once_with("very_large_10gb_file.pdf", show_progress=False)

        # 3. Verify LLM provider mock was called
        mock_get_provider.assert_called_once_with("google")

        # 4. Verify hybrid NER placeholders are correct
        # LLM entity placeholder
        self.assertIn("PERSON_1", anonymized_text)
        # Regex entity placeholders (EMAIL, PHONE, IP_ADDRESS)
        self.assertIn("EMAIL_1", anonymized_text)
        self.assertIn("PHONE_1", anonymized_text)
        self.assertIn("IP_ADDRESS_1", anonymized_text)

        # 5. Verify the replacement works without duplicating or losing text structure
        self.assertNotIn("John Doe", anonymized_text)
        self.assertNotIn("john.doe@example.com", anonymized_text)
        self.assertNotIn("+1-555-0199", anonymized_text)
        self.assertNotIn("192.168.1.100", anonymized_text)

        # 6. Verify correct mapping is returned
        expected_mapping = {
            "John Doe": "PERSON_1",
            "john.doe@example.com": "EMAIL_1",
            "+1-555-0199": "PHONE_1",
            "192.168.1.100": "IP_ADDRESS_1",
        }
        self.assertEqual(mapping, expected_mapping)


if __name__ == "__main__":
    unittest.main()
