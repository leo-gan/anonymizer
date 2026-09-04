"""Text extraction and semantic chunking for PDF, Markdown, and plain text.

CSV, Excel, and Word files do not use this loader.

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

from pdf_anonymizer_core.pdf_ocr import (
    OCR_EMPTY_MESSAGE,
    OCR_OFF_EMPTY_MESSAGE,
    ocr_pdf,
    pdf_page_count,
    store_pdf_layout,
)
from pdf_anonymizer_core.tables import (
    EXCEL_EXTRA_MESSAGE,
    is_rejected_spreadsheet,
    is_tabular_path,
    rejected_spreadsheet_error,
)
from pdf_anonymizer_core.word import (
    is_rejected_word,
    is_word_path,
    rejected_word_error,
)


def _reject_empty_pdf_extract(file_path: str, *, ocr_attempted: bool = False) -> None:
    """Refuse a silent empty extract when the PDF is not a readable document.

    Image-only PDFs with pages and no text are a hard error (item 14). A
    zero-page or unreadable file must not look like a successful extract.
    Missing files are left alone so mocked PDF tests keep working.
    """
    pages = pdf_page_count(file_path)
    if pages is None:
        return
    if pages < 1:
        raise ValueError("PDF has no pages; refusing empty extract as success.")
    if ocr_attempted:
        raise ValueError(OCR_EMPTY_MESSAGE)
    raise ValueError(OCR_OFF_EMPTY_MESSAGE)


def load_and_extract_text_from_pdf(
    file_path: str,
    characters_to_anonymize: int = 100000,
    chunk_overlap: int = 0,
    ocr: bool = False,
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
        if (md_text or "").strip():
            splitter = MarkdownTextSplitter(
                chunk_size=characters_to_anonymize, chunk_overlap=chunk_overlap
            )
            docs = splitter.create_documents([md_text])
            return md_text, [doc.page_content for doc in docs]

        if ocr:
            ocr_text, words = ocr_pdf(file_path)
            if (ocr_text or "").strip():
                store_pdf_layout(file_path, words)
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=characters_to_anonymize, chunk_overlap=chunk_overlap
                )
                docs = splitter.create_documents([ocr_text])
                return ocr_text, [doc.page_content for doc in docs]
            _reject_empty_pdf_extract(file_path, ocr_attempted=True)

        _reject_empty_pdf_extract(file_path, ocr_attempted=False)
        splitter = MarkdownTextSplitter(
            chunk_size=characters_to_anonymize, chunk_overlap=chunk_overlap
        )
        docs = splitter.create_documents([md_text or ""])
        return md_text or "", [doc.page_content for doc in docs]
    except FileNotFoundError as e:
        logging.error(f"Error: The file at {file_path} was not found.")
        raise e
    except Exception as e:
        logging.error(f"An error occurred while reading the PDF: {e}")
        raise e


def load_and_extract_text_from_file(
    file_path: str,
    characters_to_anonymize: int = 100000,
    chunk_overlap: int = 0,
    ocr: bool = False,
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

    if is_rejected_word(file_path):
        raise rejected_word_error(file_path)
    if is_word_path(file_path):
        raise ValueError(
            ".docx files must be loaded as Word documents, not as plain text."
        )
    if is_rejected_spreadsheet(file_path):
        raise rejected_spreadsheet_error(file_path)
    if is_tabular_path(file_path):
        if file_extension == ".xlsx":
            raise ValueError(EXCEL_EXTRA_MESSAGE)
        raise ValueError(
            f"{file_extension} files must be loaded as tables, not as plain text."
        )

    try:
        if file_extension == ".pdf":
            return load_and_extract_text_from_pdf(
                file_path, characters_to_anonymize, chunk_overlap, ocr=ocr
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
