"""Optional local span NER (GLiNER-class) for names and organizations.

Regex still runs first. This stage is the cheap semantic detector when the
``[ner]`` extra is installed. Identity clues stay on the language-model path
(item 20). The default extra-less install does not import ``gliner`` or
download a checkpoint.
"""

from __future__ import annotations

import logging
from typing import Iterable, List, Optional

from pdf_anonymizer_core.regex_ner import EntityDict

NER_EXTRA_MESSAGE = (
    'Local span NER requires the extra: pip install "pdf-anonymizer-core[ner]"'
)

# Zero-shot labels GLiNER understands. Mapped to this project's TYPE names.
DEFAULT_NER_LABELS: tuple[str, ...] = (
    "person",
    "organization",
    "location",
    "address",
    "date",
)
_LABEL_TO_TYPE = {
    "person": "PERSON",
    "organization": "ORGANIZATION",
    "location": "LOCATION",
    "address": "ADDRESS",
    "date": "DATE",
}

DEFAULT_NER_MODEL = "urchade/gliner_small-v2.1"
_MAX_WINDOW = 1200

_model = None


def ner_available() -> bool:
    try:
        import gliner  # noqa: F401
    except ImportError:
        return False
    return True


def resolve_semantic_stages(
    *,
    use_llm: bool,
    use_ner: Optional[bool],
    replace_llm_when_ner: bool,
) -> tuple[bool, bool]:
    """Return ``(run_ner, run_llm)``.

    ``use_ner`` is True / False / None (auto). Auto turns NER on only when
    the extra is installed and the language model would have run. Speed and
    cost profiles set ``replace_llm_when_ner`` so NER replaces the LLM.
    """
    if use_ner is True:
        if not ner_available():
            raise ValueError(NER_EXTRA_MESSAGE)
        run_ner = True
    elif use_ner is False:
        run_ner = False
    else:
        run_ner = bool(use_llm) and ner_available()

    run_llm = bool(use_llm)
    if run_ner and replace_llm_when_ner:
        run_llm = False
    return run_ner, run_llm


def _windows(text: str, size: int = _MAX_WINDOW) -> list[tuple[int, str]]:
    if len(text) <= size:
        return [(0, text)]
    parts: list[tuple[int, str]] = []
    start = 0
    while start < len(text):
        parts.append((start, text[start : start + size]))
        start += size
    return parts


def _load_model(model_name: str):
    global _model
    if _model is not None:
        return _model
    try:
        from gliner import GLiNER
    except ImportError as exc:
        raise ValueError(NER_EXTRA_MESSAGE) from exc
    logging.info("Loading local span NER model %s (CPU).", model_name)
    _model = GLiNER.from_pretrained(model_name)
    return _model


def extract_entities_via_ner(
    text: str,
    *,
    model_name: str = DEFAULT_NER_MODEL,
    labels: Optional[Iterable[str]] = None,
) -> List[EntityDict]:
    """Return PERSON / ORGANIZATION / LOCATION / ADDRESS / DATE spans.

    Does not emit identity clues (``INDIRECT``). That stays on the LLM path.
    """
    if not (text or "").strip():
        return []
    if not ner_available():
        raise ValueError(NER_EXTRA_MESSAGE)

    label_list = list(labels) if labels is not None else list(DEFAULT_NER_LABELS)
    model = _load_model(model_name)
    entities: List[EntityDict] = []
    seen: set[tuple[str, str]] = set()
    for _offset, window in _windows(text):
        try:
            hits = model.predict_entities(window, label_list)
        except Exception as exc:
            logging.warning("Local span NER failed on a window: %s", exc)
            continue
        for hit in hits or []:
            raw = (hit.get("text") or "").strip()
            label = str(hit.get("label") or "").strip().lower()
            if not raw or label not in _LABEL_TO_TYPE:
                continue
            ent_type = _LABEL_TO_TYPE[label]
            key = (raw, ent_type)
            if key in seen:
                continue
            seen.add(key)
            entities.append({"text": raw, "type": ent_type, "base_form": raw})
    return entities
