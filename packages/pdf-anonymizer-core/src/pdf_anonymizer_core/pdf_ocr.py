"""OCR and word-box layout for scanned PDFs.

Digital text extraction stays in ``load_and_extract``. This module runs only
when ``--ocr`` is on and the PDF has no usable text layer. Word boxes are
written so a later native-PDF redact pass (item 15) can find the same spans.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

OCR_OFF_EMPTY_MESSAGE = (
    "This PDF has pages but no extractable text (likely a scan). "
    "Re-run with --ocr after installing Tesseract, or supply a text-layer PDF. "
    "Refusing to write a success file with empty content."
)

OCR_EMPTY_MESSAGE = (
    "OCR ran and still found no text. "
    "Refusing to write a success file with empty content."
)

TESSERACT_MISSING_MESSAGE = (
    "OCR requires the Tesseract binary on PATH. "
    "Install Tesseract (a system package, not a pip extra) and retry with --ocr."
)

LAYOUT_SCHEMA = 1

_last_source: str = ""
_last_words: list["PdfWord"] = []


@dataclass(frozen=True)
class PdfWord:
    page: int
    text: str
    x0: float
    y0: float
    x1: float
    y1: float


def tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def store_pdf_layout(source: str, words: Iterable[PdfWord]) -> None:
    global _last_source, _last_words
    _last_source = source
    _last_words = list(words)


def take_pdf_layout() -> tuple[str, list[PdfWord]]:
    """Return and clear the layout stashed by the last OCR extract."""
    global _last_source, _last_words
    source, words = _last_source, _last_words
    _last_source = ""
    _last_words = []
    return source, words


def layout_to_json(source: str, words: Iterable[PdfWord]) -> dict[str, Any]:
    return {
        "schema": LAYOUT_SCHEMA,
        "engine": "pymupdf-tesseract",
        "source": source,
        "words": [asdict(word) for word in words],
    }


def write_layout_sidecar(dest_path: str, source: str, words: Iterable[PdfWord]) -> str:
    """Write ``<anonymized-stem>.layout.json`` next to the anonymized file."""
    dest = Path(dest_path)
    # letter.anonymized.md → letter.anonymized.layout.json
    layout_path = dest.with_suffix(".layout.json")
    layout_path.parent.mkdir(parents=True, exist_ok=True)
    layout_path.write_text(
        json.dumps(layout_to_json(source, words), indent=2),
        encoding="utf-8",
    )
    return str(layout_path)


def load_layout_sidecar(path: str) -> list[PdfWord]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    words = []
    for item in payload.get("words") or []:
        words.append(
            PdfWord(
                page=int(item["page"]),
                text=str(item["text"]),
                x0=float(item["x0"]),
                y0=float(item["y0"]),
                x1=float(item["x1"]),
                y1=float(item["y1"]),
            )
        )
    return words


def ocr_pdf(
    path: str,
    *,
    language: str = "eng",
    dpi: int = 200,
) -> tuple[str, list[PdfWord]]:
    """OCR every page. Returns ``(plain_text, words_with_boxes)``."""
    if not tesseract_available():
        raise ValueError(TESSERACT_MISSING_MESSAGE)

    try:
        import pymupdf
    except ImportError as exc:
        raise ValueError("OCR requires pymupdf.") from exc

    words: list[PdfWord] = []
    page_texts: list[str] = []
    try:
        document = pymupdf.open(path)
    except Exception as exc:
        raise ValueError(f"Cannot open PDF for OCR: {exc}") from exc

    try:
        for index, page in enumerate(document):
            try:
                textpage = page.get_textpage_ocr(language=language, dpi=dpi, full=True)
            except Exception as exc:
                raise ValueError(f"OCR failed on page {index + 1}: {exc}") from exc
            raw_words = page.get_text("words", textpage=textpage) or []
            tokens: list[str] = []
            for item in raw_words:
                if len(item) < 5:
                    continue
                x0, y0, x1, y1, token = item[:5]
                text = str(token)
                if not text.strip():
                    continue
                words.append(
                    PdfWord(
                        page=index,
                        text=text,
                        x0=float(x0),
                        y0=float(y0),
                        x1=float(x1),
                        y1=float(y1),
                    )
                )
                tokens.append(text)
            if tokens:
                page_texts.append(" ".join(tokens))
    finally:
        document.close()

    return "\n\n".join(page_texts), words


def pdf_page_count(file_path: str) -> Optional[int]:
    """Page count, or ``None`` when the file is missing (mocked PDF tests)."""
    try:
        import pymupdf
    except ImportError:
        raise ValueError("PDF extract is empty and pymupdf is not installed.")

    try:
        document = pymupdf.open(file_path)
    except FileNotFoundError:
        return None
    except Exception as exc:
        raise ValueError(
            f"PDF extract is empty and the file is not readable: {exc}"
        ) from exc
    try:
        return int(document.page_count)
    finally:
        document.close()
