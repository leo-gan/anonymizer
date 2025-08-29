import json
import logging
import time
from typing import Dict, Tuple, TypedDict, Union

import ollama
from google import genai

from pdf_anonymizer.conf import ModelName, ModelProvider
from pdf_anonymizer.exceptions import AnonymizationError

# Type definitions for better code clarity
class OllamaResponse(TypedDict):
    message: Dict[str, str]


class ModelResponse(TypedDict):
    text: str


class AnonymizationResult(TypedDict):
    anonymized_text: str
    mapping: Dict[str, str]


def anonymize_text_with_llm(
    text: str,
    existing_mapping: Dict[str, str],
    prompt_template: str,
    model_name: ModelName,
) -> Tuple[str, Dict[str, str]]:
    """
    Anonymizes a text chunk using a specified language model and updates the mapping.
    It retries on failure up to a maximum of 3 times.

    Args:
        text: The text to anonymize.
        existing_mapping: The existing mapping of original to anonymized entities.
        prompt_template: The prompt template for the anonymization task.
        model_name: The name of the model to use.

    Returns:
        A tuple containing the anonymized text and the updated mapping.
    """
    prompt = prompt_template.format(
        existing_mapping=json.dumps(existing_mapping), text=text
    )

    response: Union[OllamaResponse, ModelResponse, None] = None
    max_retries = 3

    for attempt in range(max_retries):
        try:
            logging.info(
                f"Calling '{model_name.value}': text: {len(text):,}, "
                f"mapping: {len(existing_mapping):,}, attempt {attempt + 1}"
            )

            if model_name.provider == ModelProvider.OLLAMA:
                response = ollama.chat(
                    model=model_name.value,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw_text: str = response["message"]["content"]
            else:
                client = genai.Client()
                response = client.models.generate_content(
                    model=model_name.value, contents=prompt
                )
                raw_text = response.text

            cleaned_response = (
                raw_text.strip().replace("```json", "").replace("```", "").strip()
            )
            result: AnonymizationResult = json.loads(cleaned_response)

            return (
                result.get("anonymized_text", ""),
                result.get("mapping", existing_mapping),
            )

        except json.JSONDecodeError as e:
            response_text = _get_response_text(response, model_name)
            logging.error(
                f"Attempt {attempt + 1} failed with JSON decode error: {e}, "
                f"response: {response_text[:200]}..."
            )
            if attempt + 1 == max_retries:
                raise AnonymizationError("Max retries reached due to JSON decode error.")

        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed with an error: {e}")
            if attempt + 1 == max_retries:
                raise AnonymizationError(f"Max retries reached due to an error: {e}")

        time.sleep(1)  # Wait before retrying

    raise AnonymizationError("Anonymization failed after all retries.")


def _get_response_text(
    response: Union[OllamaResponse, ModelResponse, None], model_name: ModelName
) -> str:
    """Extract text content from different response types."""
    if not response:
        return ""

    if model_name.provider == ModelProvider.OLLAMA:
        if (
            isinstance(response, dict)
            and "message" in response
            and "content" in response["message"]
        ):
            return response["message"]["content"]
    elif hasattr(response, "text"):
        return response.text

    return ""
