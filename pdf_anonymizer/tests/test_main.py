import unittest
from unittest.mock import Mock, patch
import os
import sys

# Add the parent directory to the path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf_anonymizer.load_and_extract_pdf import load_and_extract_text
from pdf_anonymizer.call_gemini import anonymize_text_with_gemini
from pdf_anonymizer.prompts import simple


class TestAnonymizer(unittest.TestCase):
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'pdf_anonymizer', 'tests', 'data')
    sample_pdf_path = os.path.join(data_path, 'sample.pdf')
    output_txt_path = os.path.join(data_path, 'sample.anonymized_output.txt')
    mapping_path = os.path.join(data_path, 'sample.mapping.json')

    @patch('main.genai.GenerativeModel')
    def test_anonymize_text_with_gemini(self, MockGenerativeModel):
        """
        Tests the anonymization function with a mock Gemini API response.
        """
        # Create a mock response object
        mock_response = Mock()
        mock_response.text = '''
        {
            "anonymized_text": "My name is PERSON_1 and I live in LOCATION_1.",
            "mapping": {
                "John Doe": "PERSON_1",
                "New York": "LOCATION_1"
            }
        }
        '''

        # Configure the mock model to return the mock response
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.generate_content.return_value = mock_response

        # Input text and existing mapping
        text = "My name is John Doe and I live in New York."
        existing_mapping = {}

        # Call the function
        anonymized_text, new_mapping = anonymize_text_with_gemini(text, existing_mapping, prompt_template=simple.prompt_template)

        # Asserts
        self.assertEqual(anonymized_text, "My name is PERSON_1 and I live in LOCATION_1.")
        self.assertEqual(new_mapping, {"John Doe": "PERSON_1", "New York": "LOCATION_1"})

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

        # check if the output file exists
        self.assertTrue(os.path.exists(self.output_txt_path))
        self.assertTrue(os.path.exists(self.mapping_path))

if __name__ == '__main__':
    unittest.main()
