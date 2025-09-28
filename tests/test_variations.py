import unittest
from unittest.mock import patch
from pdf_anonymizer.core import anonymize_pdf


class TestVariationHandling(unittest.TestCase):
    @patch("os.path.getsize", return_value=0)
    @patch("pdf_anonymizer.core.load_and_extract_text")
    @patch("pdf_anonymizer.core.identify_entities_with_llm")
    def test_consolidate_variations(
        self, mock_identify_entities, mock_load_text, mock_getsize
    ):
        """
        Test that variations of an entity are correctly consolidated under a single base placeholder.
        """
        # Mock the text extraction to return a single page of text
        mock_load_text.return_value = [
            "Mr. John Doe is a consultant. We have a meeting with John Doe tomorrow. Also, we need to review John's latest report."
        ]

        # Mock the LLM's entity identification to return entities with variations
        mock_identify_entities.return_value = [
            {"text": "Mr. John Doe", "type": "PERSON", "base_form": "John Doe"},
            {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
            {"text": "John's", "type": "PERSON", "base_form": "John"},
        ]

        expected_text = "PERSON_1.v_1 is a consultant. We have a meeting with PERSON_1 tomorrow. Also, we need to review PERSON_1.v_2 latest report."
        expected_mapping = {
            "John Doe": "PERSON_1",
            "Mr. John Doe": "PERSON_1.v_1",
            "John's": "PERSON_1.v_2",
        }

        # The path and other arguments are not used by the mocked functions, but are required by the function signature
        anonymized_text, final_mapping = anonymize_pdf(
            "dummy.pdf", 1000, "dummy_prompt", "dummy_model"
        )

        self.assertEqual(anonymized_text.strip(), expected_text)
        self.assertEqual(final_mapping, expected_mapping)

    @patch("os.path.getsize", return_value=0)
    @patch("pdf_anonymizer.core.load_and_extract_text")
    @patch("pdf_anonymizer.core.identify_entities_with_llm")
    def test_no_variations(self, mock_identify_entities, mock_load_text, mock_getsize):
        """
        Test that the logic works correctly when there are no variations.
        """
        mock_load_text.return_value = ["John Doe met Jane Smith."]
        mock_identify_entities.return_value = [
            {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
            {"text": "Jane Smith", "type": "PERSON", "base_form": "Jane Smith"},
        ]

        expected_text = "PERSON_1 met PERSON_2."
        expected_mapping = {"John Doe": "PERSON_1", "Jane Smith": "PERSON_2"}

        anonymized_text, final_mapping = anonymize_pdf(
            "dummy.pdf", 1000, "dummy_prompt", "dummy_model"
        )

        self.assertEqual(anonymized_text.strip(), expected_text)
        self.assertEqual(final_mapping, expected_mapping)


if __name__ == "__main__":
    unittest.main()
