import json
import logging
import time

from google import generativeai as genai


def print_token_count(response):
    # Update token counts
    usage_metadata = response.usage_metadata
    logging.info(f"    Prompt tokens: {usage_metadata.prompt_token_count}")
    logging.info(f"    Candidate tokens: {usage_metadata.candidates_token_count}")
    logging.info(f"    Total tokens: {usage_metadata.total_token_count}")

def anonymize_text_with_gemini(text, existing_mapping, prompt_template):
    """
    Anonymizes a text chunk using Google Gemini and updates the mapping.
    It retries on failure up to a maximum of 3 times.

    Args:
        prompt_template:
        text (str): The text to anonymize.
        existing_mapping (dict): The existing mapping of original to anonymized entities.

    Returns:
        tuple: A tuple containing the anonymized text and the updated mapping.
    """
    model_name = 'gemini-2.5-flash'
    model = genai.GenerativeModel(model_name)
    prompt = prompt_template.format(
        existing_mapping=json.dumps(existing_mapping),
        text=text
    )

    response = None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logging.info(f"Calling '{model_name}': text: {len(text):,}, mapping: {len(existing_mapping):,}, attempt {attempt + 1}")
            response = model.generate_content(prompt)
            print_token_count(response)
            # It's better to clean the response from markdown code block markers
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned_response)
            return result.get("anonymized_text", ""), result.get("mapping", existing_mapping)
        except json.JSONDecodeError as e:
            logging.error(f"Attempt {attempt + 1} failed with JSON decode error: {e} {response.text}")
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
