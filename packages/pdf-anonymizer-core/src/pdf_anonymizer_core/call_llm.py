import json
import logging
import time
from typing import List, TypedDict

from pdf_anonymizer_core.conf import get_provider_and_model_name
from pdf_anonymizer_core.llm_provider import get_provider


# Type definitions for better code clarity
class Entity(TypedDict):
    text: str
    type: str
    base_form: str


class IdentificationResult(TypedDict):
    entities: List[Entity]


def identify_entities_with_llm(
    text: str,
    prompt_template: str,
    model_name: str,
) -> List[Entity]:
    """
    Identifies PII entities in a text chunk using a specified language model.
    It retries on failure up to a maximum of 3 times.

    Args:
        text: The text to analyze.
        prompt_template: The prompt template for the identification task.
        model_name: The name of the model to use.

    Returns:
        A list of identified entities.
    """
    prompt = prompt_template.format(text=text)
    max_retries = 3

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
            result: IdentificationResult = json.loads(cleaned_response)

            return result.get("entities", [])

        except json.JSONDecodeError as e:
            logging.error(
                f"Attempt {attempt + 1} failed with JSON decode error: {e}, "
                f"response: {raw_text[:200] if 'raw_text' in locals() else 'N/A'}..."
            )
            if attempt + 1 == max_retries:
                logging.error("Max retries reached. Returning empty list.")
                return []

        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed with an error: {e}")
            if attempt + 1 == max_retries:
                logging.error("Max retries reached. Returning empty list.")
                return []

        time.sleep(1)  # Wait before retrying

    return []
