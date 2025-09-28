import json
import unittest
from unittest.mock import MagicMock, patch

from pdf_anonymizer.call_llm import identify_entities_with_llm
from pdf_anonymizer.prompts import simple


class TestIdentifyEntitiesWithLlm(unittest.TestCase):
    def setUp(self):
        self.prompt_template = simple.prompt_template

    @patch("pdf_anonymizer.call_llm.genai.Client")
    def test_identify_entities_with_llm_success_on_first_try(self, mock_client):
        # Mock the response from the generative model
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "entities": [
                    {"text": "person", "type": "PERSON", "base_form": "person"}
                ]
            }
        )
        mock_client_instance = mock_client.return_value
        mock_model_instance = mock_client_instance.models
        mock_model_instance.generate_content.return_value = mock_response

        text = "This is a test text."
        entities = identify_entities_with_llm(
            text, self.prompt_template, "gemini-2.5-pro"
        )

        self.assertEqual(entities, [{"text": "person", "type": "PERSON", "base_form": "person"}])
        mock_model_instance.generate_content.assert_called_once()

    @patch("pdf_anonymizer.call_llm.genai.Client")
    def test_identify_entities_with_llm_retry_on_json_decode_error(self, mock_client):
        # Mock the response to fail twice with JSONDecodeError, then succeed
        mock_response_fail = MagicMock()
        mock_response_fail.text = "this is not a valid json"

        mock_response_success = MagicMock()
        mock_response_success.text = json.dumps(
            {
                "entities": [
                    {"text": "person", "type": "PERSON", "base_form": "person"}
                ]
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
        entities = identify_entities_with_llm(
            text, self.prompt_template, "gemini-2.5-pro"
        )

        self.assertEqual(entities, [{"text": "person", "type": "PERSON", "base_form": "person"}])
        self.assertEqual(mock_model_instance.generate_content.call_count, 3)

    @patch("pdf_anonymizer.call_llm.genai.Client")
    def test_identify_entities_with_llm_retry_on_exception(self, mock_client):
        # Mock the response to fail twice with a generic Exception, then succeed
        mock_response_success = MagicMock()
        mock_response_success.text = json.dumps(
            {
                "entities": [
                    {"text": "person", "type": "PERSON", "base_form": "person"}
                ]
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
        entities = identify_entities_with_llm(
            text, self.prompt_template, "gemini-2.5-pro"
        )

        self.assertEqual(entities, [{"text": "person", "type": "PERSON", "base_form": "person"}])
        self.assertEqual(mock_model_instance.generate_content.call_count, 3)

    @patch("pdf_anonymizer.call_llm.genai.Client")
    def test_identify_entities_with_llm_max_retries_reached(self, mock_client):
        # Mock the response to fail on all attempts
        mock_client_instance = mock_client.return_value
        mock_model_instance = mock_client_instance.models
        mock_model_instance.generate_content.side_effect = [Exception("API error")] * 3

        text = "This is a test text."
        entities = identify_entities_with_llm(
            text, self.prompt_template, "gemini-2.5-pro"
        )

        self.assertEqual(entities, [])
        self.assertEqual(mock_model_instance.generate_content.call_count, 3)


if __name__ == "__main__":
    unittest.main()