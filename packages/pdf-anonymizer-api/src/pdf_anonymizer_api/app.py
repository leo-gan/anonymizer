"""Thin HTTP service: anonymize, deanonymize, verify, report.

Install ``pdf-anonymizer-api``. Auth is out of scope. Bind to localhost
or a compose network. This package calls ``pdf-anonymizer-core`` only.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from pdf_anonymizer_core.conf import filter_regex_patterns
from pdf_anonymizer_core.core import (
    build_mapping,
    collect_entities_from_chunks,
    finalize_entities,
)
from pdf_anonymizer_core.prompts import detailed, hipaa, simple
from pdf_anonymizer_core.risk import assess_linkage_risk
from pdf_anonymizer_core.spans import replace_entities
from pdf_anonymizer_core.operators import restore_encrypt_tokens
from pdf_anonymizer_core.utils import (
    mapping_to_placeholder_original,
    restore_placeholders_in_text,
)
from pdf_anonymizer_core.verify import verify_anonymized_text

API_INSTALL_MESSAGE = "HTTP service requires: pip install pdf-anonymizer-api"
MAX_TEXT_CHARS = 5_000_000
_PROMPTS = {
    "simple": simple.prompt_template,
    "detailed": detailed.prompt_template,
    "hipaa": hipaa.prompt_template,
}


class AnonymizeBody(BaseModel):
    text: str
    use_llm: bool = False
    use_ner: bool = False
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    keep_list: Optional[List[str]] = None
    deny_list: Optional[List[str]] = None
    operators: Optional[Dict[str, str]] = None
    seed_mapping: Optional[Dict[str, str]] = None
    fake_secret: Optional[str] = None
    encrypt_secret: Optional[str] = None
    model_name: Optional[str] = None
    prompt_name: str = "simple"
    anonymized_entities: Optional[List[str]] = None
    countries: Optional[List[str]] = None


class DeanonymizeBody(BaseModel):
    text: str
    mapping: Dict[str, str]
    encrypt_secret: Optional[str] = None


class TextBody(BaseModel):
    text: str
    countries: Optional[List[str]] = None
    use_llm: bool = False
    model_name: Optional[str] = None


def _public_entity(entity: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "text": entity.get("text", ""),
        "type": str(entity.get("type", "")).upper(),
        "base_form": entity.get("base_form") or entity.get("text", ""),
        "score": float(entity.get("score", 1.0)),
        "source": entity.get("source") or "regex",
    }


def anonymize_text_request(
    text: str,
    *,
    use_llm: bool = False,
    use_ner: bool = False,
    min_confidence: float = 0.0,
    keep_list: Optional[List[str]] = None,
    deny_list: Optional[List[str]] = None,
    operators: Optional[Dict[str, str]] = None,
    seed_mapping: Optional[Dict[str, str]] = None,
    fake_secret: Optional[str] = None,
    encrypt_secret: Optional[str] = None,
    model_name: Optional[str] = None,
    prompt_name: str = "simple",
    anonymized_entities: Optional[List[str]] = None,
    countries: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Run the same engine as the CLI on an in-memory string."""
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text is {len(text):,} characters; the HTTP limit is {MAX_TEXT_CHARS:,}."
        )
    template = _PROMPTS.get(prompt_name)
    if template is None:
        raise ValueError(
            f"Unknown prompt_name {prompt_name!r}. Use simple, detailed, or hipaa."
        )
    if not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be between 0 and 1.")

    collected = collect_entities_from_chunks(
        [text],
        prompt_template=template,
        model_name=model_name or "gemini-2.5-flash",
        regex_patterns=filter_regex_patterns(countries),
        max_retries=3,
        base_retry_delay=1.0,
        max_retry_delay=10.0,
        use_llm=use_llm,
        use_ner=use_ner,
    )
    entities = finalize_entities(
        collected,
        text,
        anonymized_entities=anonymized_entities,
        keep_list=keep_list,
        deny_list=deny_list,
        min_confidence=min_confidence,
        seed_mapping=seed_mapping,
    )
    mapping = build_mapping(
        entities,
        seed_mapping=seed_mapping,
        operators=operators,
        fake_secret=fake_secret,
        encrypt_secret=encrypt_secret,
    )
    anonymized = text
    if entities:
        anonymized = replace_entities(
            text, (entity["text"] for entity in entities), mapping
        )
    return {
        "anonymized_text": anonymized,
        "mapping": mapping,
        "entities": [_public_entity(entity) for entity in entities],
    }


def deanonymize_text_request(
    text: str,
    mapping: Dict[str, str],
    *,
    encrypt_secret: Optional[str] = None,
) -> Dict[str, Any]:
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text is {len(text):,} characters; the HTTP limit is {MAX_TEXT_CHARS:,}."
        )
    placeholder_to_original = mapping_to_placeholder_original(mapping)
    restored, used = restore_placeholders_in_text(text, placeholder_to_original)
    if encrypt_secret:
        restored = restore_encrypt_tokens(restored, encrypt_secret)
    return {
        "text": restored,
        "restored_count": len(used),
    }


def create_app():
    """Build the FastAPI app."""
    from fastapi import FastAPI, HTTPException

    application = FastAPI(
        title="PDF Anonymizer",
        description=(
            "Local HTTP wrapper around pdf-anonymizer-core. "
            "No authentication. Bind to localhost or a compose network."
        ),
        version="0.26.0",
    )

    @application.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok", "version": "0.26.0"}

    @application.post("/anonymize")
    def anonymize(body: AnonymizeBody) -> Dict[str, Any]:
        try:
            return anonymize_text_request(
                body.text,
                use_llm=body.use_llm,
                use_ner=body.use_ner,
                min_confidence=body.min_confidence,
                keep_list=body.keep_list,
                deny_list=body.deny_list,
                operators=body.operators,
                seed_mapping=body.seed_mapping,
                fake_secret=body.fake_secret,
                encrypt_secret=body.encrypt_secret,
                model_name=body.model_name,
                prompt_name=body.prompt_name,
                anonymized_entities=body.anonymized_entities,
                countries=body.countries,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @application.post("/deanonymize")
    def deanonymize(body: DeanonymizeBody) -> Dict[str, Any]:
        try:
            return deanonymize_text_request(
                body.text,
                body.mapping,
                encrypt_secret=body.encrypt_secret,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @application.post("/verify")
    def verify(body: TextBody) -> Dict[str, Any]:
        try:
            return verify_anonymized_text(
                body.text,
                regex_patterns=filter_regex_patterns(body.countries),
                use_llm=body.use_llm,
                model_name=body.model_name,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @application.post("/report")
    def report(body: TextBody) -> Dict[str, Any]:
        return assess_linkage_risk(body.text)

    return application
