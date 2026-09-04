"""Native PDF write: redaction annotations, optional irreversible mode, sanitize.

Digital PDFs use PyMuPDF ``add_redact_annot`` + ``apply_redactions``. That
excises the old glyphs from the content stream. It is not an overlay-only
black box. Rasterize-and-rebuild is a scan fallback (item 14), not the
default here.

Markdown export stays the default. Callers opt in with ``--output-pdf``.
``--redact`` is irreversible: black boxes, no stand-in text, mapping cannot
restore the page. Do not treat either mode as a legal de-identification
certificate.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable, Sequence, Tuple

Rect = Tuple[float, float, float, float]

OUTPUT_PDF_NOT_PDF_MESSAGE = (
    "--output-pdf only applies to PDF inputs. This file is not a .pdf."
)


def _require_pymupdf():
    try:
        import pymupdf
    except ImportError as exc:
        raise ValueError("Native PDF write requires pymupdf.") from exc
    return pymupdf


def _rects_overlap(left: Rect, right: Rect) -> bool:
    return not (
        left[2] <= right[0]
        or right[2] <= left[0]
        or left[3] <= right[1]
        or right[3] <= left[1]
    )


def _search_hits(
    page,
    entity_texts: Sequence[str],
    orig_to_written: Dict[str, str],
) -> list[tuple[Rect, str, str]]:
    """Longest original first; drop a later hit that overlaps an accepted rect."""
    ordered = sorted((text for text in entity_texts if text), key=len, reverse=True)
    accepted: list[tuple[Rect, str, str]] = []
    for original in ordered:
        written = orig_to_written.get(original)
        if written is None:
            continue
        try:
            found = page.search_for(original) or []
        except Exception:
            found = []
        for item in found:
            rect = (float(item.x0), float(item.y0), float(item.x1), float(item.y1))
            if any(_rects_overlap(rect, existing[0]) for existing in accepted):
                continue
            accepted.append((rect, original, written))
    return accepted


def sanitize_pdf(document) -> None:
    """Drop identity-bearing extras on every native-PDF write.

    Clears ``/Info``, XMP, embedded files, leftover annotations, optional
    content groups, and outline titles are left alone only when they have
    no leftover PII we can see. Incremental ``/Prev`` history is avoided by
    a full rewrite at save time (``garbage=4``, not incremental).
    """
    document.set_metadata({})
    try:
        document.del_xml_metadata()
    except Exception as exc:
        logging.info("Could not delete XMP metadata: %s", exc)

    try:
        count = document.embfile_count()
        for index in range(count - 1, -1, -1):
            document.embfile_del(index)
    except Exception as exc:
        logging.info("Could not delete embedded files: %s", exc)

    try:
        catalog = document.pdf_catalog()
        kind, _value = document.xref_get_key(catalog, "OCProperties")
        if kind != "null":
            document.xref_set_key(catalog, "OCProperties", "null")
    except Exception as exc:
        logging.info("Could not drop optional-content groups: %s", exc)

    try:
        catalog = document.pdf_catalog()
        kind, _value = document.xref_get_key(catalog, "Thumb")
        if kind != "null":
            document.xref_set_key(catalog, "Thumb", "null")
    except Exception:
        pass

    for page in document:
        annots = list(page.annots() or [])
        for annot in annots:
            try:
                page.delete_annot(annot)
            except Exception:
                continue


def write_anonymized_pdf(
    source_path: str,
    dest_path: str,
    orig_to_written: Dict[str, str],
    entity_texts: Iterable[str],
    *,
    redact: bool = False,
) -> None:
    """Rewrite ``source_path`` as a sanitized ``.pdf``.

    When ``redact`` is false, each hit is replaced with its written stand-in
    (reversible with the mapping). When ``redact`` is true, the hit becomes a
    black box and cannot be restored from the page.
    """
    if Path(source_path).suffix.lower() != ".pdf":
        raise ValueError(OUTPUT_PDF_NOT_PDF_MESSAGE)

    pymupdf = _require_pymupdf()
    texts = [text for text in entity_texts if text]
    try:
        document = pymupdf.open(source_path)
    except Exception as exc:
        raise ValueError(f"Cannot open PDF {source_path}") from exc

    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        for page in document:
            hits = _search_hits(page, texts, orig_to_written)
            for rect, _original, written in hits:
                box = pymupdf.Rect(*rect)
                if redact:
                    page.add_redact_annot(box, fill=(0, 0, 0), cross_out=False)
                else:
                    fontsize = max(4.0, min(11.0, box.height * 0.8 or 8.0))
                    page.add_redact_annot(
                        box,
                        text=written,
                        fontsize=fontsize,
                        fill=(1, 1, 1),
                        text_color=(0, 0, 0),
                        cross_out=False,
                    )
            image_mode = (
                pymupdf.PDF_REDACT_IMAGE_PIXELS
                if redact
                else pymupdf.PDF_REDACT_IMAGE_NONE
            )
            page.apply_redactions(images=image_mode)
        sanitize_pdf(document)
        document.save(
            str(dest),
            garbage=4,
            deflate=True,
            incremental=False,
            encryption=pymupdf.PDF_ENCRYPT_NONE,
        )
    except Exception as exc:
        raise ValueError(f"Cannot write native PDF {dest_path}") from exc
    finally:
        document.close()


def write_deanonymized_pdf(
    anonymized_path: str,
    dest_path: str,
    placeholder_to_original: Dict[str, str],
) -> None:
    """Restore stand-ins in a reversible native PDF. No-op on black boxes."""
    orig_to_written = {
        original: placeholder
        for placeholder, original in placeholder_to_original.items()
        if isinstance(placeholder, str) and isinstance(original, str)
    }
    # search_for needs the text currently on the page (placeholders).
    written_to_original = dict(placeholder_to_original)
    write_anonymized_pdf(
        anonymized_path,
        dest_path,
        written_to_original,
        list(written_to_original.keys()),
        redact=False,
    )
    del orig_to_written
