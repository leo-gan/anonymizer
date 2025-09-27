prompt_template = """
    You are an expert in identifying Personally Identifiable Information (PII).
    Your task is to read the text below and identify all PII entities.

    Instructions:
    1.  Read the text carefully.
    2.  Identify all PII based on the guidelines below.
    3.  Return a single JSON object with one key: "entities".
    4.  The value of "entities" should be a list of JSON objects, where each object represents a PII entity and has two keys: "text" (the PII) and "type" (the entity type).

    ENTITY TYPES:
    *   **PERSON:** Full names, first names, last names, middle names.
    *   **ADDRESS:** Street names, house numbers, city names, state/province names, postal codes, country names.
    *   **DATE:** Only birthdates. Do not identify other dates.
    *   **PHONE:** Any numerical sequences resembling phone numbers.
    *   **EMAIL:** Standard email address formats.
    *   **ORGANIZATION:** Names of organizations, businesses, companies.
    *   **JOB_TITLE:** Specific roles or positions within organizations.
    *   **ID:** Any alphanumeric strings that appear to be account numbers or identifiers.
    *   **LOCATION:** Locations that are not full addresses, like cities or landmarks.

    Example:
    Text: "John Doe from Acme Inc. visited our office in Springfield yesterday."
    Response:
    {{
        "entities": [
            {{"text": "John Doe", "type": "PERSON"}},
            {{"text": "Acme Inc.", "type": "ORGANIZATION"}},
            {{"text": "Springfield", "type": "LOCATION"}}
        ]
    }}

    Text to process:
    ---
    {text}
    ---

    Respond with ONLY the JSON object.
    """
