"""LLM calling logic with structured parsing and resilient retries.

Contains:
- Pydantic models used to validate LLM JSON responses (EntityModel, IdentificationResult).
- classify_error(): decides which exceptions are worth retrying.
- identify_entities_with_llm(): the main retrying wrapper that talks to providers.
"""

import logging
import random
import time
from typing import List, Optional

from pydantic import BaseModel, Field

from pdf_anonymizer_core.conf import get_provider_and_model_name
from pdf_anonymizer_core.llm_provider import current_llm_stats, get_provider


class LLMIdentificationError(RuntimeError):
    """The language model did not return entities for one chunk.

    The message names the model and the error category. It does not include
    the chunk, so a log of this exception is not a second copy of the document.
    """


def extract_json_object(raw: str) -> str:
    """Return the JSON object inside a model reply.

    Models often wrap the object in a fence, a thinking block, or a sentence.
    The parser keeps the outermost braces and leaves a bare JSON string unchanged.
    """
    text = (raw or "").strip()
    if "</think>" in text:
        text = text.split("</think>", 1)[1].strip()
    text = text.replace("```json", "").replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


# Pydantic models for structured output parsing
class EntityModel(BaseModel):
    text: str = Field(description="The exact PII text found in the document.")
    type: str = Field(description="The type of the entity (e.g. PERSON, ORGANIZATION).")
    base_form: Optional[str] = Field(
        default=None, description="The canonical or base form of the entity."
    )


class IdentificationResult(BaseModel):
    entities: List[EntityModel]


def classify_error(exception: Exception) -> tuple[bool, str]:
    """
    Classify an exception to determine if it is retryable and get a descriptive label.

    Args:
        exception: The exception object.

    Returns:
        A tuple of (is_retryable, error_category).
    """
    exc_name = type(exception).__name__
    exc_msg = str(exception).lower()

    # RateLimit errors (429)
    if "ratelimit" in exc_name.lower() or "429" in exc_msg or "rate limit" in exc_msg:
        return True, "RATE_LIMIT_ERROR"

    # Server / Temporary errors (5xx)
    if (
        "500" in exc_msg
        or "502" in exc_msg
        or "503" in exc_msg
        or "504" in exc_msg
        or "server error" in exc_msg
    ):
        return True, "SERVER_ERROR"

    # Connection / Timeout errors
    if (
        "connection" in exc_msg
        or "timeout" in exc_msg
        or "api-connection" in exc_msg
        or "apiconnection" in exc_name.lower()
    ):
        return True, "CONNECTION_ERROR"

    # Authentication / Permissions (401, 403)
    if (
        "authentication" in exc_name.lower()
        or "401" in exc_msg
        or "403" in exc_msg
        or "apikey" in exc_msg
        or "api key" in exc_msg
        or "unauthorized" in exc_msg
    ):
        return False, "AUTHENTICATION_ERROR"

    # JSON decoding / Pydantic validation errors (retryable, LLM might fix it next attempt)
    if "jsondecodeerror" in exc_name.lower() or "validationerror" in exc_name.lower():
        return True, "PARSING_ERROR"

    # Standard fallback
    return True, "GENERIC_ERROR"


def identify_entities_with_llm(
    text: str,
    prompt_template: str,
    model_name: str,
    max_retries: int = 3,
    base_retry_delay: float = 1.0,
    max_retry_delay: float = 10.0,
) -> List[dict]:
    """Call an LLM (via the configured provider) to extract PII entities from one chunk.

    The call is wrapped with retry logic:
    - Transient errors (rate limits, 5xx, connection, parsing) are retried.
    - Auth errors are not retried.
    - Uses exponential backoff + jitter.

    The response is cleaned of markdown fences and validated with Pydantic
    before returning a list of plain dicts.

    Args:
        text: The chunk of text to analyze.
        prompt_template: Prompt containing a {text} placeholder.
        model_name: Model string (passed through get_provider_and_model_name).
        max_retries: Maximum number of attempts.
        base_retry_delay: Starting backoff delay (seconds).
        max_retry_delay: Upper bound on backoff delay (seconds).

    Returns:
        List of entity dicts (each with "text", "type", "base_form",
        "score" 0.70, and "source" "llm").

    Raises:
        LLMIdentificationError: Auth failed, or retries are exhausted.
            The caller must not write a file that looks fully anonymized.
    """
    prompt = prompt_template.format(text=text)

    for attempt in range(max_retries):
        try:
            logging.info(
                f"Calling '{model_name}': text: {len(text):,}, attempt {attempt + 1}"
            )
            provider_name, actual_model_name = get_provider_and_model_name(model_name)
            provider = get_provider(provider_name)
            stats = current_llm_stats()
            if stats is not None:
                stats.calls += 1
            raw_text = provider.call(prompt, actual_model_name)

            cleaned_response = extract_json_object(raw_text)

            # Validate and parse response using Pydantic
            result = IdentificationResult.model_validate_json(cleaned_response)

            dumped: List[dict] = []
            for entity in result.entities:
                item = entity.model_dump()
                item.setdefault("score", 0.70)
                item.setdefault("source", "llm")
                if not item.get("base_form"):
                    item["base_form"] = item["text"]
                dumped.append(item)
            return dumped

        except Exception as e:
            is_retryable, category = classify_error(e)
            if category == "PARSING_ERROR":
                stats = current_llm_stats()
                if stats is not None:
                    stats.parse_failures += 1
            logging.error(
                "Attempt %s failed with error category %s (%s).",
                attempt + 1,
                category,
                type(e).__name__,
            )

            if not is_retryable or attempt + 1 == max_retries:
                if (
                    category in {"CONNECTION_ERROR", "RATE_LIMIT_ERROR"}
                    or "connect" in str(e).lower()
                ):
                    failed = current_llm_stats()
                    if failed is not None:
                        failed.transport_failures += 1
                raise LLMIdentificationError(
                    f"Language model {model_name} stopped ({category}) "
                    f"after {attempt + 1} attempt(s). No anonymized file was written."
                ) from None

            # Exponential backoff with jitter
            backoff = min(base_retry_delay * (2**attempt), max_retry_delay)
            jitter = random.uniform(0, 0.1 * backoff)
            sleep_time = backoff + jitter

            logging.info(f"Retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

    raise LLMIdentificationError(
        f"Language model {model_name} stopped (GENERIC_ERROR) after 0 attempts. "
        "No anonymized file was written."
    )
