import unittest
from unittest.mock import Mock, patch

from pdf_anonymizer_core.call_llm import identify_entities_with_llm
from pdf_anonymizer_core.prompts import simple


class TestAnonymizer(unittest.TestCase):
    @patch("pdf_anonymizer_core.call_llm.get_provider")
    def test_identify_entities_with_gemini(self, mock_get_provider):
        """
        Tests the entity identification function with a mock Gemini API response.
        """
        # Create a mock response object
        mock_provider = Mock()
        mock_provider.call.return_value = """
        {
            "entities": [
                {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
                {"text": "New York", "type": "LOCATION", "base_form": "New York"}
            ]
        }
        """
        mock_get_provider.return_value = mock_provider

        # Input text
        text = "My name is John Doe and I live in New York."

        # Call the function
        entities = identify_entities_with_llm(
            text,
            prompt_template=simple.prompt_template,
            model_name="gemini-2.5-flash",
        )

        # Asserts
        mock_get_provider.assert_called_once_with("google")
        expected_entities = [
            {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
            {"text": "New York", "type": "LOCATION", "base_form": "New York"},
        ]
        self.assertEqual(entities, expected_entities)

    @patch("pdf_anonymizer_core.call_llm.get_provider")
    def test_identify_entities_with_ollama(self, mock_get_provider):
        """
        Tests the entity identification function with a mock Ollama API response.
        """
        # Create a mock response object
        mock_provider = Mock()
        mock_provider.call.return_value = """
        {
            "entities": [
                {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
                {"text": "New York", "type": "LOCATION", "base_form": "New York"}
            ]
        }
        """
        mock_get_provider.return_value = mock_provider

        # Input text
        text = "My name is John Doe and I live in New York."

        # Call the function
        entities = identify_entities_with_llm(
            text,
            prompt_template=simple.prompt_template,
            model_name="gemma:7b",
        )

        # Asserts
        mock_get_provider.assert_called_once_with("ollama")
        expected_entities = [
            {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
            {"text": "New York", "type": "LOCATION", "base_form": "New York"},
        ]
        self.assertEqual(entities, expected_entities)


if __name__ == "__main__":
    unittest.main()