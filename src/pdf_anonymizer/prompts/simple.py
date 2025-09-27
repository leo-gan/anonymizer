prompt_template = """
    You are an expert in identifying Personally Identifiable Information (PII).
    Your task is to read the text below and identify all PII entities.

    Instructions:
    1.  Read the text carefully.
    2.  Identify all PII, such as names, locations, organizations, phone numbers, email addresses, etc.
    3.  Return a single JSON object with one key: "entities".
    4.  The value of "entities" should be a list of JSON objects, where each object represents a PII entity and has two keys: "text" (the PII) and "type" (the entity type, e.g., PERSON, ORGANIZATION).

    Example:
    Text: "John Doe from Acme Inc. visited our office."
    Response:
    {{
        "entities": [
            {{"text": "John Doe", "type": "PERSON"}},
            {{"text": "Acme Inc.", "type": "ORGANIZATION"}}
        ]
    }}

    Text to process:
    ---
    {text}
    ---

    Respond with ONLY the JSON object.
    """
