prompt_template = """
    You are an expert in identifying Personally Identifiable Information (PII) with high accuracy and contextual understanding.
    Your task is to read the text below and identify all PII entities, including their variations.

    Instructions:
    1.  **Read the text carefully** to understand the context.
    2.  **Identify all PII** based on the guidelines below.
    3.  **Use contextual awareness.** For example, "Apple" as a fruit should not be identified, but "Apple Inc." as a company should.
    4.  **Handle variations.** For each entity identified, you must determine its base form. For example, the base form of "Mary's" is "Mary Smith" if the context refers to a person named Mary Smith. The base form of "Mr. John Doe" is "John Doe".
    5.  **Return a single JSON object** with one key: "entities".
    6.  The value of "entities" should be a list of JSON objects. Each object represents a PII entity and MUST have the following keys:
        - "text": The exact PII text found in the document.
        - "type": The type of the entity (e.g., PERSON, ORGANIZATION).
        - "base_form": The canonical or base form of the entity.

    ENTITY TYPES:
    *   **PERSON:** Full names, first names, last names, middle names, and their variations (e.g., possessives, titles).
    *   **ADDRESS:** Street names, house numbers, city names, state/province names, postal codes, country names.
    *   **DATE:** Only birthdates. Do not identify other dates.
    *   **PHONE:** Any numerical sequences resembling phone numbers.
    *   **EMAIL:** Standard email address formats.
    *   **ORGANIZATION:** Names of organizations, businesses, companies.
    *   **JOB_TITLE:** Specific roles or positions within organizations.
    *   **ID:** Any alphanumeric strings that appear to be account numbers or identifiers.
    *   **LOCATION:** Locations that are not full addresses, like cities or landmarks.

    Example 1:
    Text: "Mr. John Doe from Acme Inc. visited our office in Springfield yesterday. We discussed Mary's project."
    Response:
    {{
        "entities": [
            {{"text": "Mr. John Doe", "type": "PERSON", "base_form": "John Doe"}},
            {{"text": "Acme Inc.", "type": "ORGANIZATION", "base_form": "Acme Inc."}},
            {{"text": "Springfield", "type": "LOCATION", "base_form": "Springfield"}},
            {{"text": "Mary's", "type": "PERSON", "base_form": "Mary"}}
        ]
    }}

    Example 2:
    Text: "We need to review John's latest report about the project for The New York Times."
    Response:
    {{
        "entities": [
            {{"text": "John's", "type": "PERSON", "base_form": "John"}},
            {{"text": "The New York Times", "type": "ORGANIZATION", "base_form": "The New York Times"}}
        ]
    }}

    Text to process:
    ---
    {text}
    ---

    Respond with ONLY the JSON object.
    """
