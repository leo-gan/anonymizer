prompt_template = """
    You are an expert in text anonymization. Your task is to identify and replace Personally Identifiable Information (PII) in the given text.
    PII includes names, locations, organizations, phone numbers, email addresses, etc.

    Instructions:
    1.  Read the text and the provided JSON mapping of existing anonymized entities.
    2.  Identify all PII in the text.
    3.  If a PII entity is already in the mapping, replace it with its existing anonymized value.
    4.  If a new PII entity is found, create a new anonymized placeholder for it (e.g., PERSON_1, LOCATION_1). The number should be incremented for each new entity of the same type.
    5.  Update the mapping with any new entities you find.
    6.  Return a single JSON object with two keys:
        - "anonymized_text": The text with all PII replaced by placeholders.
        - "mapping": The complete and updated JSON mapping.

    Existing mapping:
    {existing_mapping}

    Text to anonymize:
    ---
    {text}
    ---

    Respond with ONLY the JSON object.
    """
