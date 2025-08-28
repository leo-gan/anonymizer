import json
import logging
import time

import ollama
from google import genai


OLLAMA_MODELS = ["gemma", "phi4-mini"]


def anonymize_text_with_llm(text, existing_mapping, prompt_template, model_name: str):
    """
    Anonymizes a text chunk using a specified language model and updates the mapping.
    It retries on failure up to a maximum of 3 times.

    Args:
        model_name: The name of the model to use.
        prompt_template: The prompt template for the anonymization task.
        text (str): The text to anonymize.
        existing_mapping (dict): The existing mapping of original to anonymized entities.

    Returns:
        tuple: A tuple containing the anonymized text and the updated mapping.
    """
    prompt = prompt_template.format(
        existing_mapping=json.dumps(existing_mapping),
        text=text
    )

    response = None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logging.info(f"Calling '{model_name}': text: {len(text):,}, mapping: {len(existing_mapping):,}, attempt {attempt + 1}")
            if model_name in OLLAMA_MODELS:
                response = ollama.chat(model=model_name, messages=[
                    {
                        'role': 'user',
                        'content': prompt,
                    },
                ])
                raw_text = response['message']['content']
            else:
                client = genai.Client()
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                raw_text = response.text

            cleaned_response = raw_text.strip().replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned_response)
            return result.get("anonymized_text", ""), result.get("mapping", existing_mapping)
        except json.JSONDecodeError as e:
            response_text = ""
            if model_name in OLLAMA_MODELS:
                if response and 'message' in response and 'content' in response['message']:
                    response_text = response['message']['content']
            else:
                if response:
                    response_text = response.text
            logging.error(f"Attempt {attempt + 1} failed with JSON decode error: {e}, {response_text[:200] = } ...")
            if attempt + 1 == max_retries:
                logging.error("Max retries reached. Returning original text.")
                return text, existing_mapping
            time.sleep(1)  # Wait for 1 second before retrying
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed with an error: {e}")
            if attempt + 1 == max_retries:
                logging.error("Max retries reached. Returning original text.")
                return text, existing_mapping
            time.sleep(1)

    # This part should not be reached if the loop is exited correctly.
    return text, existing_mapping
