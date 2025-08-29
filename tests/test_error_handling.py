import unittest
from unittest.mock import patch

from pdf_anonymizer.call_llm import anonymize_text_with_llm
from pdf_anonymizer.conf import ModelName
from pdf_anonymizer.exceptions import AnonymizationError


class TestErrorHandling(unittest.TestCase):
    def test_anonymize_text_with_llm_raises_exception_after_retries(self):
        """
        Test that anonymize_text_with_llm raises AnonymizationError after max retries.
        """
        with patch("pdf_anonymizer.call_llm.ollama.chat") as mock_chat:
            mock_chat.side_effect = Exception("API error")
            with self.assertRaises(AnonymizationError):
                anonymize_text_with_llm(
                    text="This is a test.",
                    existing_mapping={},
                    prompt_template="test prompt",
                    model_name=ModelName.phi4_mini,
                )
            self.assertEqual(mock_chat.call_count, 3)


if __name__ == "__main__":
    unittest.main()
