import logging
import sys

import pymupdf4llm
from langchain_text_splitters import MarkdownTextSplitter



def load_and_extract_text(pdf_path, characters_to_anonymize=100000):
    """
    Loads a PDF file and extracts text from each page.

    Args:
        characters_to_anonymize: Number of characters to anonymize in one go.
        pdf_path (str): The path to the PDF file.

    Returns:
        list: A list of strings, where each string is the text of a page.
    """
    try:
        md_text = pymupdf4llm.to_markdown(pdf_path)
        splitter = MarkdownTextSplitter(chunk_size=characters_to_anonymize, chunk_overlap=0)
        docs = splitter.create_documents([md_text])
        return [doc.page_content for doc in docs]
    except FileNotFoundError as e:
        logging.error(f"Error: The file at {pdf_path} was not found.")
        raise e
    except Exception as e:
        logging.error(f"An error occurred while reading the PDF: {e}")
        raise e
