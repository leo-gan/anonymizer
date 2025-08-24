import unittest
from unittest.mock import Mock, patch
import os
import pymupdf  # PyMuPDF
from pathlib import Path

from pdf_anonymizer.core import anonymize_pdf
from pdf_anonymizer.load_and_extract_pdf import load_pdf
from pdf_anonymizer.call_llm import anonymize_text_with_llm
from pdf_anonymizer.prompts import simple


class TestAnonymizer(unittest.TestCase):
    data_path = Path(__file__).parent / 'data'
    sample_pdf_path = data_path / 'sample.pdf'

    # --- Tests for individual components ---

    def test_load_pdf(self):
        """
        Tests that the `load_pdf` function correctly opens a PDF file.
        """
        doc = load_pdf(str(self.sample_pdf_path))
        self.assertIsNotNone(doc)
        self.assertIsInstance(doc, pymupdf.Document)
        self.assertEqual(len(doc), 1)
        doc.close()

    @patch('pdf_anonymizer.call_llm.genai.Client')
    def test_anonymize_text_with_gemini(self, mock_client):
        """
        Tests the LLM call function with a mock Gemini API response.
        This test remains valid as it tests a specific unit of logic.
        """
        mock_response = Mock()
        mock_response.text = '''
        {
            "anonymized_text": "My name is PERSON_1.",
            "mapping": { "John Doe": "PERSON_1" }
        }
        '''
        mock_client.return_value.models.generate_content.return_value = mock_response

        anonymized_text, new_mapping = anonymize_text_with_llm(
            "My name is John Doe.", {}, simple.prompt_template, 'gemini-1.5-flash'
        )
        self.assertEqual(anonymized_text, "My name is PERSON_1.")
        self.assertEqual(new_mapping, {"John Doe": "PERSON_1"})

    # --- End-to-end test for the new workflow ---

    @patch('pdf_anonymizer.core.anonymize_text_with_llm')
    def test_anonymize_pdf_end_to_end(self, mock_anonymize_text_with_llm):
        """
        Tests the full PDF-to-PDF anonymization workflow using a mock LLM.
        """
        # Configure the mock to simulate finding PII in our sample PDF
        original_text = "John Joe, who lives at 2864, Holm st, Springfild, met Mary Smith yesterday. \n"
        anonymized_text_mock = "PERSON_1, who lives at 2864, Holm st, Springfild, met PERSON_2 yesterday. \n"
        mapping_mock = {
            "John Joe": "PERSON_1",
            "Mary Smith": "PERSON_2"
        }

        # The mock will be called with the text of the page, and should return the anonymized version
        mock_anonymize_text_with_llm.return_value = (anonymized_text_mock, mapping_mock)

        # Run the main function
        anonymized_pdf_path, final_mapping = anonymize_pdf(
            self.sample_pdf_path, simple.prompt_template, "mock-model"
        )

        # 1. Assert that the output files were created
        self.assertIsNotNone(anonymized_pdf_path)
        self.assertTrue(os.path.exists(anonymized_pdf_path))

        # 2. Assert the final mapping is correct
        self.assertEqual(final_mapping, mapping_mock)

        # 3. Assert the content of the new PDF is correct
        # Open the generated PDF and extract its text
        output_doc = pymupdf.open(anonymized_pdf_path)
        output_text = output_doc[0].get_text()
        output_doc.close()

        # Check that the PII has been replaced
        self.assertNotIn("John Joe", output_text)
        self.assertNotIn("Mary Smith", output_text)
        self.assertIn("PERSON_1", output_text)
        self.assertIn("PERSON_2", output_text)

        # Clean up the created file
        os.remove(anonymized_pdf_path)


if __name__ == '__main__':
    unittest.main()
