import logging
import random
import time
from typing import List, Optional
from pydantic import BaseModel, Field

from pdf_anonymizer_core.conf import get_provider_and_model_name
from pdf_anonymizer_core.llm_provider import get_provider

# Pydantic models for structured output parsing
class EntityModel(BaseModel):
    text: str = Field(description="The exact PII text found in the document.")
    type: str = Field(description="The type of the entity (e.g. PERSON, ORGANIZATION).")
    base_form: Optional[str] = Field(default=None, description="The canonical or base form of the entity.")

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
    if "500" in exc_msg or "502" in exc_msg or "503" in exc_msg or "504" in exc_msg or "server error" in exc_msg:
        return True, "SERVER_ERROR"
        
    # Connection / Timeout errors
    if "connection" in exc_msg or "timeout" in exc_msg or "api-connection" in exc_msg or "apiconnection" in exc_name.lower():
        return True, "CONNECTION_ERROR"
        
    # Authentication / Permissions (401, 403)
    if "authentication" in exc_name.lower() or "401" in exc_msg or "403" in exc_msg or "apikey" in exc_msg or "api key" in exc_msg or "unauthorized" in exc_msg:
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
    """
    Identifies PII entities in a text chunk using a specified language model.
    It retries on failure up to max_retries with exponential backoff.

    Args:
        text: The text to analyze.
        prompt_template: The prompt template for the identification task.
        model_name: The name of the model to use.
        max_retries: Max number of attempts.
        base_retry_delay: Base delay for backoff.
        max_retry_delay: Max delay for backoff.

    Returns:
        A list of identified entities as dicts.
    """
    prompt = prompt_template.format(text=text)

    for attempt in range(max_retries):
        try:
            logging.info(
                f"Calling '{model_name}': text: {len(text):,}, attempt {attempt + 1}"
            )
            provider_name, actual_model_name = get_provider_and_model_name(model_name)
            provider = get_provider(provider_name)
            raw_text = provider.call(prompt, actual_model_name)

            cleaned_response = (
                raw_text.strip().replace("```json", "").replace("```", "").strip()
            )
            
            # Validate and parse response using Pydantic
            result = IdentificationResult.model_validate_json(cleaned_response)
            
            return [entity.model_dump() for entity in result.entities]

        except Exception as e:
            is_retryable, category = classify_error(e)
            logging.error(
                f"Attempt {attempt + 1} failed with error category '{category}': {e}"
            )
            
            if not is_retryable or attempt + 1 == max_retries:
                if attempt + 1 == max_retries:
                    logging.error("Max retries reached. Returning empty list.")
                else:
                    logging.error(f"Fatal error category '{category}'. Stopping retries.")
                return []
                
            # Exponential backoff with jitter
            backoff = min(base_retry_delay * (2 ** attempt), max_retry_delay)
            jitter = random.uniform(0, 0.1 * backoff)
            sleep_time = backoff + jitter
            
            logging.info(f"Retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

    return []
