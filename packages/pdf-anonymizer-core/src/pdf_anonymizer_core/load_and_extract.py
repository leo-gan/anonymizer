"""Text extraction and semantic chunking for PDF, Markdown, and plain text.

Uses pymupdf4llm for high-quality PDF → Markdown conversion (preserves
structure useful for LLMs) and langchain text splitters:
- MarkdownTextSplitter for .pdf and .md (respects headers/code blocks)
- RecursiveCharacterTextSplitter for .txt / fallback

Chunk size and overlap are the primary controls for memory usage and
LLM context consumption.
"""

import logging
from pathlib import Path
from typing import List, Tuple

import pymupdf4llm
from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)


def load_and_extract_text_from_pdf(
    file_path: str, characters_to_anonymize: int = 100000, chunk_overlap: int = 0
) -> Tuple[str, List[str]]:
    """
    Loads a PDF file and extracts text from each page, returning the full text and chunked text.

    Args:
        file_path (str): The path to the PDF file.
        characters_to_anonymize: Number of characters to anonymize in one go (chunk size).
        chunk_overlap: Overlap size between chunks.

    Returns:
        Tuple[str, List[str]]: The full text as a string, and a list of chunk strings.
    """
    try:
        md_text = pymupdf4llm.to_markdown(file_path, show_progress=False)
        splitter = MarkdownTextSplitter(
            chunk_size=characters_to_anonymize, chunk_overlap=chunk_overlap
        )
        docs = splitter.create_documents([md_text])
        return md_text, [doc.page_content for doc in docs]
    except FileNotFoundError as e:
        logging.error(f"Error: The file at {file_path} was not found.")
        raise e
    except Exception as e:
        logging.error(f"An error occurred while reading the PDF: {e}")
        raise e


def load_and_extract_text_from_file(
    file_path: str, characters_to_anonymize: int = 100000, chunk_overlap: int = 0
) -> Tuple[str, List[str]]:
    """
    Loads a file and extracts text, returning the full text and chunked text.

    Args:
        file_path (str): The path to the file.
        characters_to_anonymize: Number of characters to process in each chunk.
        chunk_overlap: Overlap size between chunks.

    Returns:
        Tuple[str, List[str]]: The full text as a string, and a list of chunk strings.
    """
    path = Path(file_path)
    file_extension = path.suffix.lower()

    try:
        if file_extension == ".pdf":
            return load_and_extract_text_from_pdf(
                file_path, characters_to_anonymize, chunk_overlap
            )
        elif file_extension == ".md":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            splitter = MarkdownTextSplitter(
                chunk_size=characters_to_anonymize, chunk_overlap=chunk_overlap
            )
            docs = splitter.create_documents([text])
            return text, [doc.page_content for doc in docs]
        elif file_extension == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=characters_to_anonymize, chunk_overlap=chunk_overlap
            )
            docs = splitter.create_documents([text])
            return text, [doc.page_content for doc in docs]
        else:
            logging.warning(
                f"Unsupported file type: {file_extension}. Treating as plain text."
            )
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=characters_to_anonymize, chunk_overlap=chunk_overlap
            )
            docs = splitter.create_documents([text])
            return text, [doc.page_content for doc in docs]
    except FileNotFoundError as e:
        logging.error(f"Error: The file at {file_path} was not found.")
        raise e
    except Exception as e:
        logging.error(f"An error occurred while reading the file: {e}")
        raise e
