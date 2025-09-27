import logging
import fitz  # PyMuPDF
from langchain_text_splitters import CharacterTextSplitter


def load_and_extract_text(pdf_path, characters_to_anonymize=100000) -> list[str]:
    """
    Loads a PDF file and extracts text from each page.

    Args:
        characters_to_anonymize: Number of characters to anonymize in one go.
        pdf_path (str): The path to the PDF file.

    Returns:
        list: A list of strings, where each string is a chunk of text.
    """
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()

        splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=characters_to_anonymize,
            chunk_overlap=0,
            length_function=len,
        )
        chunks = splitter.split_text(full_text)
        return chunks
    except FileNotFoundError as e:
        logging.error(f"Error: The file at {pdf_path} was not found.")
        raise e
    except Exception as e:
        logging.error(f"An error occurred while reading the PDF: {e}")
        raise e
