"""HIPAA Safe Harbor *aid* prompt.

Asks for the identifier classes that apply to text (names, small-area geography,
dates about a person, phones, emails, IDs, URLs, IPs, and so on).

This is a helper for coverage. It is not a legal determination that the output
meets the HIPAA Safe Harbor standard.
"""

prompt_template = """
    You are helping hide health-related personal details in a document.
    This is a coverage aid, not a legal certification.

    Read the text and list every span that falls in the classes below.
    Use exact text from the document.

    Instructions:
    1. Read the whole passage.
    2. Mark names of people, and names of their relatives, employers, or household members.
    3. Mark places smaller than a state: street, city, county, precinct, ZIP / postal code.
       Leave a lone state name (e.g. "Texas") unless it is part of a full address.
    4. Mark every date that relates to a person (birth, admission, discharge, death,
       appointment, specimen). Do NOT skip non-birth dates. Use type DATE.
    5. Mark ages. If someone is older than 89, still list the age text (type AGE).
    6. Mark phone numbers and fax numbers (PHONE or FAX).
    7. Mark email addresses (EMAIL).
    8. Mark Social Security numbers and similar national IDs (SSN).
    9. Mark medical record numbers (MEDICAL_RECORD), health-plan IDs (HEALTH_PLAN_ID),
       account numbers (ACCOUNT), license numbers (DRIVERS_LICENSE or MEDICAL_LICENSE),
       and other IDs (ID).
    10. Mark vehicle IDs including VIN and plate-like tokens (VIN).
    11. Mark device IDs (DEVICE_ID, MAC_ADDRESS).
    12. Mark URLs (URL) and IP addresses (IPV4_ADDRESS or IPV6_ADDRESS).
    13. If the text names a biometric (fingerprint, voiceprint, retina) or a face photo
        caption, list that phrase as BIOMETRIC or PHOTO. You cannot hide pixels.
    14. Mark identity clues that point to one person without a name as INDIRECT
        (or PERSON with base_form if you know who it is).
    15. Return one JSON object with key "entities". Each item needs "text", "type",
        and "base_form".

    Example:
    Text: "Ada Lovelace, DOB 1815-12-10, MRN 998877, seen in Austin on 2020-03-04. Age 91."
    Response:
    {{
        "entities": [
            {{"text": "Ada Lovelace", "type": "PERSON", "base_form": "Ada Lovelace"}},
            {{"text": "1815-12-10", "type": "DATE", "base_form": "1815-12-10"}},
            {{"text": "MRN 998877", "type": "MEDICAL_RECORD", "base_form": "998877"}},
            {{"text": "Austin", "type": "LOCATION", "base_form": "Austin"}},
            {{"text": "2020-03-04", "type": "DATE", "base_form": "2020-03-04"}},
            {{"text": "91", "type": "AGE", "base_form": "91"}}
        ]
    }}

    Text to process:
    ---
    {text}
    ---

    Respond with ONLY the JSON object.
    """
