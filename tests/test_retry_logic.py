import json
import unittest
from unittest.mock import MagicMock, patch

from pdf_anonymizer.call_llm import anonymize_text_with_llm
from pdf_anonymizer.conf import ModelName
from pdf_anonymizer.exceptions import AnonymizationError
from pdf_anonymizer.prompts import simple


class TestAnonymizeTextWithLlm(unittest.TestCase):
    def setUp(self):
        self.prompt_template = simple.prompt_template

    @patch("pdf_anonymizer.call_llm.genai.Client")
    def test_anonymize_text_with_llm_success_on_first_try(self, mock_client):
        # Mock the response from the generative model
        mock_response = MagicMock()
        # Add the usage_metadata attribute to the mock_response
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20
        mock_response.usage_metadata.total_token_count = 30
        mock_response.text = json.dumps(
            {
                "anonymized_text": "This is an anonymized text.",
                "mapping": {"person": "PERSON_1"},
            }
        )
        mock_client_instance = mock_client.return_value
        mock_model_instance = mock_client_instance.models
        mock_model_instance.generate_content.return_value = mock_response

        text = "This is a test text."
        existing_mapping = {}
        anonymized_text, mapping = anonymize_text_with_llm(
            text, existing_mapping, self.prompt_template, ModelName.gemini_2_5_pro
        )

        self.assertEqual(anonymized_text, "This is an anonymized text.")
        self.assertEqual(mapping, {"person": "PERSON_1"})
        mock_model_instance.generate_content.assert_called_once()

    @patch("pdf_anonymizer.call_llm.genai.Client")
    def test_anonymize_text_with_llm_retry_on_json_decode_error(self, mock_client):
        # Mock the response to fail twice with JSONDecodeError, then succeed
        mock_response_fail = MagicMock()
        mock_response_fail.text = "this is not a valid json"
        # Add the usage_metadata attribute to the mock_response
        mock_response_fail.usage_metadata = MagicMock()
        mock_response_fail.usage_metadata.prompt_token_count = 10
        mock_response_fail.usage_metadata.candidates_token_count = 20
        mock_response_fail.usage_metadata.total_token_count = 30
        mock_response_success = MagicMock()
        # Add the usage_metadata attribute to the mock_response
        mock_response_success.usage_metadata = MagicMock()
        mock_response_success.usage_metadata.prompt_token_count = 10
        mock_response_success.usage_metadata.candidates_token_count = 20
        mock_response_success.usage_metadata.total_token_count = 30
        mock_response_success.text = json.dumps(
            {
                "anonymized_text": "This is an anonymized text.",
                "mapping": {"person": "PERSON_1"},
            }
        )

        mock_client_instance = mock_client.return_value
        mock_model_instance = mock_client_instance.models
        mock_model_instance.generate_content.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success,
        ]

        text = "This is a test text."
        existing_mapping = {}
        anonymized_text, mapping = anonymize_text_with_llm(
            text, existing_mapping, self.prompt_template, ModelName.gemini_2_5_pro
        )

        self.assertEqual(anonymized_text, "This is an anonymized text.")
        self.assertEqual(mapping, {"person": "PERSON_1"})
        self.assertEqual(mock_model_instance.generate_content.call_count, 3)

    @patch("pdf_anonymizer.call_llm.genai.Client")
    def test_anonymize_text_with_llm_retry_on_exception(self, mock_client):
        # Mock the response to fail twice with a generic Exception, then succeed
        mock_response_success = MagicMock()
        # Add the usage_metadata attribute to the mock_response
        mock_response_success.usage_metadata = MagicMock()
        mock_response_success.usage_metadata.prompt_token_count = 10
        mock_response_success.usage_metadata.candidates_token_count = 20
        mock_response_success.usage_metadata.total_token_count = 30
        mock_response_success.text = json.dumps(
            {
                "anonymized_text": "This is an anonymized text.",
                "mapping": {"person": "PERSON_1"},
            }
        )

        mock_client_instance = mock_client.return_value
        mock_model_instance = mock_client_instance.models
        mock_model_instance.generate_content.side_effect = [
            Exception("API error"),
            Exception("API error"),
            mock_response_success,
        ]

        text = "This is a test text."
        existing_mapping = {}
        anonymized_text, mapping = anonymize_text_with_llm(
            text, existing_mapping, self.prompt_template, ModelName.gemini_2_5_pro
        )

        self.assertEqual(anonymized_text, "This is an anonymized text.")
        self.assertEqual(mapping, {"person": "PERSON_1"})
        self.assertEqual(mock_model_instance.generate_content.call_count, 3)

    @patch("pdf_anonymizer.call_llm.genai.Client")
    def test_anonymize_text_with_llm_max_retries_reached(self, mock_client):
        # Mock the response to fail on all attempts
        mock_client_instance = mock_client.return_value
        mock_model_instance = mock_client_instance.models
        mock_model_instance.generate_content.side_effect = [Exception("API error")] * 3

        text = "This is a test text."
        existing_mapping = {}
        with self.assertRaises(AnonymizationError):
            anonymize_text_with_llm(
                text, existing_mapping, self.prompt_template, ModelName.gemini_2_5_pro
            )

        self.assertEqual(mock_model_instance.generate_content.call_count, 3)


if __name__ == "__main__":
    unittest.main()
