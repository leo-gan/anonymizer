import unittest
from unittest.mock import Mock, patch

from pdf_anonymizer.call_llm import identify_entities_with_llm
from pdf_anonymizer.prompts import simple


class TestAnonymizer(unittest.TestCase):
    @patch("pdf_anonymizer.call_llm.genai.Client")
    def test_identify_entities_with_gemini(self, mock_client):
        """
        Tests the entity identification function with a mock Gemini API response.
        """
        # Create a mock response object
        mock_response = Mock()
        mock_response.text = """
        {
            "entities": [
                {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
                {"text": "New York", "type": "LOCATION", "base_form": "New York"}
            ]
        }
        """

        # Configure the mock model to return the mock response
        mock_client_instance = mock_client.return_value
        mock_model_instance = mock_client_instance.models
        mock_model_instance.generate_content.return_value = mock_response

        # Input text
        text = "My name is John Doe and I live in New York."

        # Call the function
        entities = identify_entities_with_llm(
            text,
            prompt_template=simple.prompt_template,
            model_name="gemini-1.5-flash",
        )

        # Asserts
        expected_entities = [
            {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
            {"text": "New York", "type": "LOCATION", "base_form": "New York"}
        ]
        self.assertEqual(entities, expected_entities)

    @patch("pdf_anonymizer.call_llm.ollama.chat")
    def test_identify_entities_with_ollama(self, mock_ollama_chat):
        """
        Tests the entity identification function with a mock Ollama API response.
        """
        # Create a mock response object
        mock_response = {
            "message": {
                "content": """
                {
                    "entities": [
                        {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
                        {"text": "New York", "type": "LOCATION", "base_form": "New York"}
                    ]
                }
                """
            }
        }

        # Configure the mock model to return the mock response
        mock_ollama_chat.return_value = mock_response

        # Input text
        text = "My name is John Doe and I live in New York."

        # Call the function
        entities = identify_entities_with_llm(
            text,
            prompt_template=simple.prompt_template,
            model_name="gemma",
        )

        # Asserts
        expected_entities = [
            {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
            {"text": "New York", "type": "LOCATION", "base_form": "New York"}
        ]
        self.assertEqual(entities, expected_entities)


if __name__ == "__main__":
    unittest.main()