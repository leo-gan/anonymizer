prompt_template = """
You are an expert at anonymizing text while maintaining the original meaning and context. Your task is to process the following text and perform two key actions:

1. **Anonymize the text:** Identify and replace personally identifiable information (PII) and sensitive entities with anonymized tags.
2. **Generate a JSON mapping:** Create a one-to-one mapping between the original entities and their corresponding anonymized tags.
3. "Output": Return a single JSON object with two keys:
        - "anonymized_text": The text with all PII replaced by placeholders.
        - "mapping": The complete and updated JSON mapping.

>>>>>>>>>>>>>>>>>>>>>>
ANONYMIZATION GUIDELINES:

*   **Entity Types:** Focus on identifying and anonymizing common PII and sensitive data, including but not limited to:

    *   **Names:** Full names, first names, last names, middle names.
    *   **Addresses:** Street names, house numbers, city names, state/province names, postal codes, country names.
    *   **Dates:** Do not anonymize dates! Only birthdates should be anonymized.
    *   **Phone Numbers:** Any numerical sequences resembling phone numbers.
    *   **Email Addresses:** Standard email address formats.
    *   **Company Names:** Names of organizations, businesses.
    *   **Job Titles:** Specific roles or positions within organizations.
    *   **Account Numbers/IDs:** Any alphanumeric strings that appear to be identifiers.
    *   **Other Sensitive Information:** Any other data that could reasonably identify an individual or organization.

*   **Anonymized Tagging Convention:**

    *   Use a consistent naming convention for anonymized tags.
    *   Prefix tags with the entity type (e.g., `PERSON`, `ADDRESS`, `DATE`, `EMAIL`, `COMPANY`, `PHONE`, `JOB_TITLE`, `ACCOUNT_ID`).
    *   Follow the prefix with an underscore (`_`) and a sequential numerical identifier (e.g., `PERSON_1`, `ADDRESS_1`, `DATE_5`).
    *   **Handling Variations of Entities:** If you encounter a variation of an already anonymized entity, it should create a new, related anonymized tag to indicate this variation. The convention for variations will be: `[Original_Anonymized_Tag].v_[variation_number]`.

        *   **Example:** If "Mary Smith" is mapped as `PERSON_1`, then "Mary's" should be mapped as `PERSON_1.v_2`.
        *   **Example:** If "John Doe" is mapped as `PERSON_2`, then "Mr. John Doe" should be mapped as `PERSON_2.v_2`.
        *   **Example:** If "123 Oak Street" is mapped as `ADDRESS_3`, then "Oak Street" (if referring as the same street in context) could be mapped to `ADDRESS_3.v_2`.
        *   **Example:** If "Springfield" is mapped as `LOCATION_4`, then "Springfield's" could be mapped as `LOCATION_4.v_2`.

*   **One-to-One Mapping:** Each distinct original entity found in the text must have a unique entry in the JSON mapping. If an entity appears multiple times, it should be mapped to the same anonymized tag each time.

*   **Contextual Awareness:** Use contextual clues to determine if a piece of information is indeed sensitive or an entity to be anonymized. For example, "Apple" as a fruit should not be anonymized, but "Apple Inc." should.

>>>>>>>>>>>>>>>>>>>>>>
EXAMPLES:

**Input Text Example:**

"John Joe, who lives at 2864, Holm st, Springfild, met Mary Smith yesterday."


**Anonymized Text Example:**

"PERSON_1, who lives at ADDRESS_1, PERSON_3, met PERSON_2 yesterday."

**JSON Output Example:** 
{{
	"anonymized_text": "PERSON_1, who lives at ADDRESS_1, met PERSON_2 yesterday.",
	"mapping": {{

	  "PERSON_1": "John Joe",
	  "ADDRESS_1": "2864, Holm st, Springfild",
	  "LOCATION_2": "Springfild",
	  "PERSON_2": "Mary Smith" 
	}}
}}

>>>>>>>>>>>>>>>>>>>>>>
EXISTING MAPPING:

{existing_mapping}

>>>>>>>>>>>>>>>>>>>>>>
TEXT TO ANONYMIZE:

{text}
  
"""
