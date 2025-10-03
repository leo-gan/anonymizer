import json
import unittest
from unittest.mock import MagicMock, patch

from pdf_anonymizer_core.call_llm import identify_entities_with_llm
from pdf_anonymizer_core.prompts import simple


class TestIdentifyEntitiesWithLlm(unittest.TestCase):
    def setUp(self):
        self.prompt_template = simple.prompt_template
        self.model_name = "gemini-2.5-pro"

    @patch("pdf_anonymizer_core.call_llm.get_provider")
    def test_identify_entities_with_llm_success_on_first_try(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.call.return_value = json.dumps(
            {"entities": [{"text": "person", "type": "PERSON", "base_form": "person"}]}
        )
        mock_get_provider.return_value = mock_provider

        text = "This is a test text."
        entities = identify_entities_with_llm(
            text, self.prompt_template, self.model_name
        )

        self.assertEqual(
            entities, [{"text": "person", "type": "PERSON", "base_form": "person"}]
        )
        mock_provider.call.assert_called_once()
        mock_get_provider.assert_called_once_with("google")

    @patch("pdf_anonymizer_core.call_llm.get_provider")
    def test_identify_entities_with_llm_retry_on_json_decode_error(
        self, mock_get_provider
    ):
        mock_provider = MagicMock()
        mock_provider.call.side_effect = [
            "this is not a valid json",
            "this is not a valid json",
            json.dumps(
                {
                    "entities": [
                        {"text": "person", "type": "PERSON", "base_form": "person"}
                    ]
                }
            ),
        ]
        mock_get_provider.return_value = mock_provider

        text = "This is a test text."
        entities = identify_entities_with_llm(
            text, self.prompt_template, self.model_name
        )

        self.assertEqual(
            entities, [{"text": "person", "type": "PERSON", "base_form": "person"}]
        )
        self.assertEqual(mock_provider.call.call_count, 3)

    @patch("pdf_anonymizer_core.call_llm.get_provider")
    def test_identify_entities_with_llm_retry_on_exception(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.call.side_effect = [
            Exception("API error"),
            Exception("API error"),
            json.dumps(
                {
                    "entities": [
                        {"text": "person", "type": "PERSON", "base_form": "person"}
                    ]
                }
            ),
        ]
        mock_get_provider.return_value = mock_provider

        text = "This is a test text."
        entities = identify_entities_with_llm(
            text, self.prompt_template, self.model_name
        )

        self.assertEqual(
            entities, [{"text": "person", "type": "PERSON", "base_form": "person"}]
        )
        self.assertEqual(mock_provider.call.call_count, 3)

    @patch("pdf_anonymizer_core.call_llm.get_provider")
    def test_identify_entities_with_llm_max_retries_reached(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.call.side_effect = [Exception("API error")] * 3
        mock_get_provider.return_value = mock_provider

        text = "This is a test text."
        entities = identify_entities_with_llm(
            text, self.prompt_template, self.model_name
        )

        self.assertEqual(entities, [])
        self.assertEqual(mock_provider.call.call_count, 3)


if __name__ == "__main__":
    unittest.main()
