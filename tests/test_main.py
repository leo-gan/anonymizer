import os
import unittest
from unittest.mock import Mock, patch

from pdf_anonymizer.call_llm import anonymize_text_with_llm
from pdf_anonymizer.load_and_extract_pdf import load_and_extract_text
from pdf_anonymizer.prompts import simple


class TestAnonymizer(unittest.TestCase):
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    sample_pdf_path = os.path.join(data_path, "sample.pdf")

    def test_save_results(self):
        """
        Tests the save_results function.
        """
        # Sample data
        import shutil

        from pdf_anonymizer.utils import save_results

        full_anonymized_text = "This is a test."
        final_mapping = {"key": "value"}
        pdf_path = self.sample_pdf_path

        # expected file paths
        expected_anonymized_file = "data/anonymized/sample.anonymized.md"
        expected_mapping_file = "data/mappings/sample.mapping.json"

        # clean up before test
        if os.path.exists("data"):
            shutil.rmtree("data")

        # Call the function
        anonymized_output_file, mapping_file = save_results(
            full_anonymized_text, final_mapping, pdf_path
        )

        # Asserts
        self.assertEqual(anonymized_output_file, expected_anonymized_file)
        self.assertEqual(mapping_file, expected_mapping_file)
        self.assertTrue(os.path.exists(anonymized_output_file))
        self.assertTrue(os.path.exists(mapping_file))

        with open(anonymized_output_file, "r") as f:
            self.assertEqual(f.read(), full_anonymized_text)

        with open(mapping_file, "r") as f:
            import json

            self.assertEqual(json.load(f), final_mapping)

        # clean up after test
        shutil.rmtree("data")

    @patch("pdf_anonymizer.call_llm.genai.Client")
    def test_anonymize_text_with_gemini(self, mock_client):
        """
        Tests the anonymization function with a mock Gemini API response.
        """
        # Create a mock response object
        mock_response = Mock()
        mock_response.text = """
        {
            "anonymized_text": "My name is PERSON_1 and I live in LOCATION_1.",
            "mapping": {
                "John Doe": "PERSON_1",
                "New York": "LOCATION_1"
            }
        }
        """

        # Configure the mock model to return the mock response
        mock_client_instance = mock_client.return_value
        mock_model_instance = mock_client_instance.models
        mock_model_instance.generate_content.return_value = mock_response

        # Input text and existing mapping
        text = "My name is John Doe and I live in New York."
        existing_mapping = {}

        # Call the function
        anonymized_text, new_mapping = anonymize_text_with_llm(
            text,
            existing_mapping,
            prompt_template=simple.prompt_template,
            model_name="gemini-1.5-flash",
        )

        # Asserts
        self.assertEqual(
            anonymized_text, "My name is PERSON_1 and I live in LOCATION_1."
        )
        self.assertEqual(
            new_mapping, {"John Doe": "PERSON_1", "New York": "LOCATION_1"}
        )

    @patch("pdf_anonymizer.call_llm.ollama.chat")
    def test_anonymize_text_with_ollama(self, mock_ollama_chat):
        """
        Tests the anonymization function with a mock Ollama API response.
        """
        # Create a mock response object
        mock_response = {
            "message": {
                "content": """
                {
                    "anonymized_text": "My name is PERSON_1 and I live in LOCATION_1.",
                    "mapping": {
                        "John Doe": "PERSON_1",
                        "New York": "LOCATION_1"
                    }
                }
                """
            }
        }

        # Configure the mock model to return the mock response
        mock_ollama_chat.return_value = mock_response

        # Input text and existing mapping
        text = "My name is John Doe and I live in New York."
        existing_mapping = {}

        # Call the function
        anonymized_text, new_mapping = anonymize_text_with_llm(
            text,
            existing_mapping,
            prompt_template=simple.prompt_template,
            model_name="gemma",
        )

        # Asserts
        self.assertEqual(
            anonymized_text, "My name is PERSON_1 and I live in LOCATION_1."
        )
        self.assertEqual(
            new_mapping, {"John Doe": "PERSON_1", "New York": "LOCATION_1"}
        )

    def test_load_and_extract_text(self):
        """
        Tests the PDF text extraction function.
        This test relies on the 'sample.pdf' file being present in the root directory.
        """
        # Path to the sample PDF file (assuming it's in the root of the project)
        pdf_path = self.sample_pdf_path

        # Check if the sample file exists before running the test
        if not os.path.exists(pdf_path):
            self.skipTest(f"Sample PDF file not found at {pdf_path}")

        text_pages = load_and_extract_text(pdf_path)

        # The sample PDF has one page
        self.assertEqual(len(text_pages), 1)
        # Check if the extracted text contains the expected "who lives at"
        self.assertIn("who lives at", text_pages[0])


if __name__ == "__main__":
    unittest.main()
