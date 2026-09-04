"""Word .docx load/save, per-paragraph apply, and review flatten."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Literal, Optional

from pdf_anonymizer_core import conf
from pdf_anonymizer_core.spans import replace_entities

DOCX_SUFFIXES = frozenset({".docx"})
REJECT_WORD_SUFFIXES = frozenset({".doc", ".docm", ".dot", ".dotm", ".dotx"})

DOCX_EXTRA_MESSAGE = (
    'Word support requires the extra: pip install "pdf-anonymizer-core[docx]"'
)

_REJECT_MESSAGES = {
    ".doc": "Legacy .doc is not supported. Re-save as .docx.",
    ".dot": "Legacy Word templates are not supported. Re-save as .docx.",
    ".docm": (
        "Macro-enabled Word documents are not supported "
        "(macros can re-derive PII). Re-save as .docx."
    ),
    ".dotm": (
        "Macro-enabled Word templates are not supported "
        "(macros can re-derive PII). Re-save as .docx."
    ),
    ".dotx": (
        "Word templates (.dotx) are not supported in this version. Save a .docx copy."
    ),
}

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W_P = f"{{{_W_NS}}}p"
W_T = f"{{{_W_NS}}}t"
W_DEL = f"{{{_W_NS}}}del"
W_TAB = f"{{{_W_NS}}}tab"
W_BR = f"{{{_W_NS}}}br"
W_CR = f"{{{_W_NS}}}cr"
W_INSTR = f"{{{_W_NS}}}instrText"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

_STORY_TYPE_MARKERS = (
    "document.main+xml",
    "header+xml",
    "footer+xml",
    "footnotes+xml",
    "endnotes+xml",
    "comments+xml",
    "glossary.document+xml",
)
_MACRO_TYPE_MARKERS = (
    "application/vnd.ms-word.document.macroEnabled",
    "application/vnd.ms-word.template.macroEnabled",
)

BlockKind = Literal["paragraph", "hyperlink", "field"]


@dataclass
class WordBlock:
    part_name: str
    index: int
    search_text: str
    kind: BlockKind = "paragraph"
    _p: Any = field(default=None, repr=False, compare=False)
    _rel: Any = field(default=None, repr=False, compare=False)
    _instr: Any = field(default=None, repr=False, compare=False)


@dataclass
class WordDocument:
    path: str
    kind: Literal["docx"] = "docx"
    blocks: list[WordBlock] = field(default_factory=list)
    _document: Any = field(default=None, repr=False, compare=False)


def is_word_path(path: str) -> bool:
    return Path(path).suffix.lower() in DOCX_SUFFIXES


def is_rejected_word(path: str) -> bool:
    return Path(path).suffix.lower() in REJECT_WORD_SUFFIXES


def rejected_word_error(path: str) -> ValueError:
    suffix = Path(path).suffix.lower()
    message = _REJECT_MESSAGES.get(suffix, f"Word format {suffix} is not supported.")
    return ValueError(message)


def _require_docx() -> None:
    try:
        import docx  # noqa: F401
    except ImportError as exc:
        raise ValueError(DOCX_EXTRA_MESSAGE) from exc


def _part_name(part: Any) -> str:
    name = getattr(part, "partname", None)
    if name is None:
        return "unknown"
    return str(name)


def _is_story_part(part: Any) -> bool:
    content_type = getattr(part, "content_type", "") or ""
    return any(marker in content_type for marker in _STORY_TYPE_MARKERS)


def _is_macro_part(part: Any) -> bool:
    content_type = getattr(part, "content_type", "") or ""
    return any(marker in content_type for marker in _MACRO_TYPE_MARKERS)


def _iter_package_parts(document: Any) -> Iterator[Any]:
    seen: set[int] = set()

    def walk(part: Any) -> Iterator[Any]:
        marker = id(part)
        if marker in seen:
            return
        seen.add(marker)
        yield part
        rels = getattr(part, "rels", None)
        if rels is None:
            return
        for rel in rels.values():
            if getattr(rel, "is_external", False):
                continue
            target = getattr(rel, "target_part", None)
            if target is None:
                continue
            yield from walk(target)

    package = getattr(getattr(document, "part", None), "package", None)
    if package is not None and hasattr(package, "iter_parts"):
        for part in package.iter_parts():
            marker = id(part)
            if marker in seen:
                continue
            seen.add(marker)
            yield part
        return
    yield from walk(document.part)


def _iter_story_parts(document: Any) -> list[Any]:
    parts = [part for part in _iter_package_parts(document) if _is_story_part(part)]
    parts.sort(
        key=lambda part: (
            0 if _part_name(part).endswith("document.xml") else 1,
            _part_name(part),
        )
    )
    return parts


def _walk_visible_pieces(p_elem: Any) -> list[tuple[str, Any, str]]:
    pieces: list[tuple[str, Any, str]] = []

    def walk(el: Any) -> None:
        if el.tag == W_DEL:
            return
        if el.tag == W_T:
            pieces.append(("t", el, el.text or ""))
            return
        if el.tag == W_TAB:
            pieces.append(("tab", el, "\t"))
            return
        if el.tag in {W_BR, W_CR}:
            pieces.append(("br", el, "\n"))
            return
        for child in el:
            walk(child)

    walk(p_elem)
    return pieces


def paragraph_visible_text(p_elem: Any) -> str:
    return "".join(text for _kind, _node, text in _walk_visible_pieces(p_elem))


def _set_paragraph_visible_text(p_elem: Any, new_text: str) -> None:
    nodes = [node for kind, node, _text in _walk_visible_pieces(p_elem) if kind == "t"]
    if not nodes:
        return
    nodes[0].text = new_text
    if new_text[:1].isspace() or new_text[-1:].isspace():
        nodes[0].set(XML_SPACE, "preserve")
    for node in nodes[1:]:
        node.text = ""


def write_block_text(block: WordBlock, new_text: str) -> None:
    """Write replacement text back onto the live XML / relationship."""
    if block.kind == "paragraph" and block._p is not None:
        _set_paragraph_visible_text(block._p, new_text)
    elif block.kind == "hyperlink" and block._rel is not None:
        block._rel._target = new_text
    elif block.kind == "field" and block._instr is not None:
        block._instr.text = new_text
    block.search_text = new_text


def _hyperlink_reltype() -> str:
    try:
        from docx.opc.constants import RELATIONSHIP_TYPE as RT

        return RT.HYPERLINK
    except Exception:
        return (
            "http://schemas.openxmlformats.org/officeDocument/2006/"
            "relationships/hyperlink"
        )


def _iter_hyperlink_rels(document: Any) -> Iterator[Any]:
    reltype = _hyperlink_reltype()
    seen: set[int] = set()
    for part in _iter_package_parts(document):
        rels = getattr(part, "rels", None)
        if rels is None:
            continue
        for rel in rels.values():
            if not getattr(rel, "is_external", False):
                continue
            this_type = getattr(rel, "reltype", "") or ""
            if this_type != reltype and not this_type.endswith("/hyperlink"):
                continue
            marker = id(rel)
            if marker in seen:
                continue
            seen.add(marker)
            target = getattr(rel, "target_ref", None)
            if isinstance(target, str) and target:
                yield rel


def load_docx(path: str) -> WordDocument:
    """Load a ``.docx`` file as a ``WordDocument``.

    Raises ``ValueError`` for rejected Word suffixes, a missing ``[docx]``
    extra, a file over the size / block cap, or an unreadable package.
    """
    suffix = Path(path).suffix.lower()
    if suffix in REJECT_WORD_SUFFIXES:
        raise rejected_word_error(path)
    if suffix != ".docx":
        raise ValueError(f"Not a supported Word file: {path}")

    _require_docx()
    from docx import Document

    file_size = os.path.getsize(path)
    if file_size > conf.MAX_DOCX_BYTES:
        raise ValueError(
            f"Word file exceeds the size limit of {conf.MAX_DOCX_BYTES} bytes."
        )

    try:
        document = Document(path)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Cannot open Word document {path}") from exc

    for part in _iter_package_parts(document):
        if _is_macro_part(part):
            raise ValueError(
                "Macro-enabled Word documents are not supported "
                "(macros can re-derive PII). Re-save as .docx."
            )

    blocks: list[WordBlock] = []
    nonempty = 0
    for part in _iter_story_parts(document):
        element = getattr(part, "element", None)
        if element is None:
            continue
        part_name = _part_name(part)
        index = 0
        for p_elem in element.iter(W_P):
            text = paragraph_visible_text(p_elem)
            if not text:
                continue
            nonempty += 1
            if nonempty > conf.MAX_DOCX_BLOCKS:
                raise ValueError(
                    f"Word file exceeds the limit of {conf.MAX_DOCX_BLOCKS} "
                    "non-empty paragraphs."
                )
            index += 1
            blocks.append(
                WordBlock(
                    part_name=part_name,
                    index=index,
                    search_text=text,
                    kind="paragraph",
                    _p=p_elem,
                )
            )
        field_index = 0
        for instr in element.iter(W_INSTR):
            raw = instr.text or ""
            if not raw:
                continue
            nonempty += 1
            if nonempty > conf.MAX_DOCX_BLOCKS:
                raise ValueError(
                    f"Word file exceeds the limit of {conf.MAX_DOCX_BLOCKS} "
                    "non-empty paragraphs."
                )
            field_index += 1
            blocks.append(
                WordBlock(
                    part_name=f"{part_name}#fields",
                    index=field_index,
                    search_text=raw,
                    kind="field",
                    _instr=instr,
                )
            )

    link_index = 0
    for rel in _iter_hyperlink_rels(document):
        target = rel.target_ref
        nonempty += 1
        if nonempty > conf.MAX_DOCX_BLOCKS:
            raise ValueError(
                f"Word file exceeds the limit of {conf.MAX_DOCX_BLOCKS} "
                "non-empty paragraphs."
            )
        link_index += 1
        blocks.append(
            WordBlock(
                part_name="hyperlinks",
                index=link_index,
                search_text=target,
                kind="hyperlink",
                _rel=rel,
            )
        )

    return WordDocument(path=path, blocks=blocks, _document=document)


def save_docx(doc: WordDocument, path: str) -> None:
    """Write the live ``python-docx`` package to ``path``."""
    if doc._document is None:
        raise ValueError("Word document has no in-memory package to save.")
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        doc._document.save(path)
    except Exception as exc:
        raise ValueError(f"Cannot write Word document {path}") from exc


def apply_mapping_to_docx(
    doc: WordDocument,
    orig_to_written: Dict[str, str],
    entity_texts: Iterable[str],
) -> WordDocument:
    """Replace detected entity texts in each block. Does not use mapping keys."""
    texts = [text for text in entity_texts if text]
    if not texts:
        return doc
    for block in doc.blocks:
        if not block.search_text:
            continue
        new = replace_entities(block.search_text, texts, orig_to_written)
        if new != block.search_text:
            write_block_text(block, new)
    return doc


def flatten_docx_for_review(doc: WordDocument, *, anonymized: bool = True) -> str:
    """Part-wise flatten for verify / risk / consolidate.

    Blank line after the part header and after every block, including the last,
    so risk windows do not glue a header onto the next paragraph.
    """
    del anonymized  # blocks already hold the current (maybe replaced) text
    parts: list[str] = []
    current: Optional[str] = None
    for block in doc.blocks:
        if block.part_name != current:
            current = block.part_name
            parts.append(f"# Part: {current}")
            parts.append("")
        parts.append(block.search_text)
        parts.append("")
    if not parts:
        return ""
    return "\n".join(parts) + "\n"


def write_anonymized_docx(
    source_path: str,
    dest_path: str,
    orig_to_written: Dict[str, str],
    entity_texts: Iterable[str],
) -> None:
    doc = load_docx(source_path)
    apply_mapping_to_docx(doc, orig_to_written, entity_texts)
    save_docx(doc, dest_path)


def iter_blocks(doc: WordDocument) -> Iterable[WordBlock]:
    return iter(doc.blocks)
