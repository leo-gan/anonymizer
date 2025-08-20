import unittest
from unittest.mock import patch, MagicMock
import json
import time

from pdf_anonymizer.main import anonymize_text_with_gemini

class TestAnonymizeTextWithGemini(unittest.TestCase):

    @patch('pdf_anonymizer.main.genai.GenerativeModel')
    def test_anonymize_text_with_gemini_success_on_first_try(self, mock_generative_model):
        # Mock the response from the generative model
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "anonymized_text": "This is an anonymized text.",
            "mapping": {"person": "PERSON_1"}
        })
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_generative_model.return_value = mock_model_instance

        text = "This is a test text."
        existing_mapping = {}
        anonymized_text, mapping = anonymize_text_with_gemini(text, existing_mapping)

        self.assertEqual(anonymized_text, "This is an anonymized text.")
        self.assertEqual(mapping, {"person": "PERSON_1"})
        mock_model_instance.generate_content.assert_called_once()

    @patch('pdf_anonymizer.main.genai.GenerativeModel')
    def test_anonymize_text_with_gemini_retry_on_json_decode_error(self, mock_generative_model):
        # Mock the response to fail twice with JSONDecodeError, then succeed
        mock_response_fail = MagicMock()
        mock_response_fail.text = "this is not a valid json"
        mock_response_success = MagicMock()
        mock_response_success.text = json.dumps({
            "anonymized_text": "This is an anonymized text.",
            "mapping": {"person": "PERSON_1"}
        })

        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]
        mock_generative_model.return_value = mock_model_instance

        text = "This is a test text."
        existing_mapping = {}
        anonymized_text, mapping = anonymize_text_with_gemini(text, existing_mapping)

        self.assertEqual(anonymized_text, "This is an anonymized text.")
        self.assertEqual(mapping, {"person": "PERSON_1"})
        self.assertEqual(mock_model_instance.generate_content.call_count, 3)

    @patch('pdf_anonymizer.main.genai.GenerativeModel')
    def test_anonymize_text_with_gemini_retry_on_exception(self, mock_generative_model):
        # Mock the response to fail twice with a generic Exception, then succeed
        mock_response_success = MagicMock()
        mock_response_success.text = json.dumps({
            "anonymized_text": "This is an anonymized text.",
            "mapping": {"person": "PERSON_1"}
        })

        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = [Exception("API error"), Exception("API error"), mock_response_success]
        mock_generative_model.return_value = mock_model_instance

        text = "This is a test text."
        existing_mapping = {}
        anonymized_text, mapping = anonymize_text_with_gemini(text, existing_mapping)

        self.assertEqual(anonymized_text, "This is an anonymized text.")
        self.assertEqual(mapping, {"person": "PERSON_1"})
        self.assertEqual(mock_model_instance.generate_content.call_count, 3)

    @patch('pdf_anonymizer.main.genai.GenerativeModel')
    def test_anonymize_text_with_gemini_max_retries_reached(self, mock_generative_model):
        # Mock the response to fail on all attempts
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = [Exception("API error")] * 3
        mock_generative_model.return_value = mock_model_instance

        text = "This is a test text."
        existing_mapping = {}
        anonymized_text, mapping = anonymize_text_with_gemini(text, existing_mapping)

        self.assertEqual(anonymized_text, text)
        self.assertEqual(mapping, existing_mapping)
        self.assertEqual(mock_model_instance.generate_content.call_count, 3)

if __name__ == '__main__':
    unittest.main()
