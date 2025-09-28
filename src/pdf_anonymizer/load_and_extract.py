import logging
from pathlib import Path

import pymupdf4llm
from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)


def load_and_extract_text_from_pdf(
    file_path: str, characters_to_anonymize: int = 100000
) -> list[str]:
    """
    Loads a PDF file and extracts text from each page.

    Args:
        characters_to_anonymize: Number of characters to anonymize in one go.
        file_path (str): The path to the PDF file.

    Returns:
        list: A list of strings, where each string is the text of a page.
    """
    try:
        md_text = pymupdf4llm.to_markdown(file_path, show_progress=False)
        splitter = MarkdownTextSplitter(
            chunk_size=characters_to_anonymize, chunk_overlap=0
        )
        docs = splitter.create_documents([md_text])
        return [doc.page_content for doc in docs]
    except FileNotFoundError as e:
        logging.error(f"Error: The file at {file_path} was not found.")
        raise e
    except Exception as e:
        logging.error(f"An error occurred while reading the PDF: {e}")
        raise e


def load_and_extract_text_from_file(
    file_path: str, characters_to_anonymize: int = 100000
) -> list[str]:
    """
    Loads a file and extracts text, splitting it into chunks.

    Args:
        file_path (str): The path to the file.
        characters_to_anonymize: Number of characters to process in each chunk.

    Returns:
        list: A list of strings, where each string is a chunk of text.
    """
    path = Path(file_path)
    file_extension = path.suffix.lower()

    try:
        if file_extension == ".pdf":
            return load_and_extract_text_from_pdf(file_path, characters_to_anonymize)
        elif file_extension == ".md":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            splitter = MarkdownTextSplitter(
                chunk_size=characters_to_anonymize, chunk_overlap=0
            )
            docs = splitter.create_documents([text])
            return [doc.page_content for doc in docs]
        elif file_extension == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=characters_to_anonymize, chunk_overlap=0
            )
            docs = splitter.create_documents([text])
            return [doc.page_content for doc in docs]
        else:
            logging.warning(
                f"Unsupported file type: {file_extension}. Treating as plain text."
            )
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=characters_to_anonymize, chunk_overlap=0
            )
            docs = splitter.create_documents([text])
            return [doc.page_content for doc in docs]
    except FileNotFoundError as e:
        logging.error(f"Error: The file at {file_path} was not found.")
        raise e
    except Exception as e:
        logging.error(f"An error occurred while reading the file: {e}")
        raise e
