import json
import logging
import time
from typing import Dict, List, TypedDict, Union

import ollama
from google import genai

from pdf_anonymizer.conf import ModelName, ModelProvider

# Type definitions for better code clarity
class OllamaResponse(TypedDict):
    message: Dict[str, str]


class ModelResponse(TypedDict):
    text: str


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

    response: Union[OllamaResponse, ModelResponse, None] = None
    max_retries = 3

    for attempt in range(max_retries):
        try:
            logging.info(
                f"Calling '{model_name}': text: {len(text):,}, attempt {attempt + 1}"
            )
            model_enum = ModelName(model_name)

            if model_enum.provider == ModelProvider.OLLAMA:
                response = ollama.chat(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw_text: str = response["message"]["content"]
            else:
                client = genai.Client()
                response = client.models.generate_content(
                    model=model_name, contents=prompt
                )
                raw_text = response.text

            cleaned_response = (
                raw_text.strip().replace("```json", "").replace("```", "").strip()
            )
            result: IdentificationResult = json.loads(cleaned_response)

            return result.get("entities", [])

        except json.JSONDecodeError as e:
            response_text = _get_response_text(response, model_name)
            logging.error(
                f"Attempt {attempt + 1} failed with JSON decode error: {e}, "
                f"response: {response_text[:200]}..."
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


def _get_response_text(
    response: Union[OllamaResponse, ModelResponse, None], model_name: str
) -> str:
    """Extract text content from different response types."""
    if not response:
        return ""

    model_enum = ModelName(model_name)
    if model_enum.provider == ModelProvider.OLLAMA:
        if (
            isinstance(response, dict)
            and "message" in response
            and "content" in response["message"]
        ):
            return response["message"]["content"]
    elif hasattr(response, "text"):
        return response.text

    return ""