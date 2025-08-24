import logging
import pymupdf  # PyMuPDF

def load_pdf(pdf_path: str):
    """
    Loads a PDF file using PyMuPDF.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        A PyMuPDF document object, or None if an error occurs.
    """
    try:
        doc = pymupdf.open(pdf_path)
        return doc
    except Exception as e:
        logging.error(f"An error occurred while opening the PDF at {pdf_path}: {e}")
        return None
