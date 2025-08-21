import logging
import sys

from PyPDF2 import PdfReader


def load_and_extract_text(pdf_path):
    """
    Loads a PDF file and extracts text from each page.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        list: A list of strings, where each string is the text of a page.
    """
    try:
        reader = PdfReader(pdf_path)
        text_pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_pages.append(text)
        return text_pages
    except FileNotFoundError:
        logging.error(f"Error: The file at {pdf_path} was not found.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred while reading the PDF: {e}")
        sys.exit(1)
