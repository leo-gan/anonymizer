"""Fast first-stage Named Entity Recognition using regular expressions (RE2 engine).

The hybrid pipeline (core.anonymize_file) ALWAYS runs this regex NER pass before
the (more expensive) LLM stage. Matches are later merged/deduped with LLM results
via a priority system in core.py (EMAIL, CREDIT_CARD, IBAN, crypto, SSN_* etc.
receive elevated priority).

ENGINE
------
This module uses the RE2 engine (package "google-re2") instead of Python's stdlib
`re`. Benefits:
  * Linear-time matching (O(length) worst-case). Immune to catastrophic backtracking
    (ReDoS) even with complex patterns or adversarial input.
  * Predictable performance on large PDFs / logs / code dumps.
  * Same fundamental API surface: compile / finditer / match.group(0) / error.

RE2 LIMITATIONS (patterns here are written to be compliant)
----------------------------------------------------------
  * No look-ahead / look-behind assertions ((?=...), (?!...), (?<=...)).
  * Limited support for some advanced Python re features (no recursive patterns,
    limited backreferences). All DEFAULT patterns and documented examples stay
    within the safe subset.
  * \b word boundaries are supported and used for many PII tokens.

COUNTRY PARTITIONING & EXTENSIVE PII COVERAGE
---------------------------------------------
Patterns are defined in pdf_anonymizer_core.conf.DEFAULT_REGEX_PATTERNS and are
partitioned by country using ISO-2 suffixes (SSN_US, NINO_GB, INSEE_FR, AADHAAR_IN,
RESIDENT_ID_CN, DNI_ES, CODICE_FISCALE_IT, ...).

Mandatory countries covered: USA, Canada, UK, Spain, Italy, France, India, China.
30+ total countries supported via dedicated national/tax/driver/VAT/business ID
patterns + universal patterns (IBAN covers most EU+ countries, credit cards, crypto,
VIN, MAC, etc. are global).

Supported categories (non-exhaustive):
  EMAIL, PHONE, URL, IPV4/IPV6, MAC, CREDIT_CARD, CURRENCY_AMOUNT,
  CRYPTO_BTC / CRYPTO_ETH, IBAN, BIC_SWIFT, VIN, DATE_ISO,
  SSN / SSN_US / SIN_CA / NINO_GB / INSEE_FR / AADHAAR_IN / RESIDENT_ID_CN,
  EIN_US, VAT_*, PASSPORT_*, DRIVERS_LICENSE_*, MEDICAL_* , business regs,
  CURP_MX, CPF_BR, TFN_AU, NRIC_SG, HKID_HK, PESEL_PL, etc.

CUSTOMISATION
-------------
You can supply a completely custom `regex_patterns: Dict[str, str]` (type -> pattern)
when calling anonymize_file(). Keys become the emitted entity TYPE (upper-cased)
and are used for placeholder generation (EMAIL_1, IBAN_7, DRIVERS_LICENSE_CA_2, ...).
Only the keys you provide are used; there is no automatic merging with defaults
unless you build your dict from DEFAULT_REGEX_PATTERNS.

The function is intentionally tiny. It only does structural scanning. Semantic
disambiguation, name coreference, and hard-to-regex PII remain the responsibility
of the LLM stage that always follows.
"""

import logging
from typing import Dict, List, TypedDict

import re2 as re


class EntityDict(TypedDict):
    text: str
    type: str
    base_form: str


def extract_entities_via_regex(text: str, patterns: Dict[str, str]) -> List[EntityDict]:
    """
    Scans the text for PII using pre-configured regular expressions (RE2 engine).

    Args:
        text: Input text to analyze.
        patterns: Dictionary mapping entity type strings (e.g. "IBAN", "SSN_US",
            "CRYPTO_ETH") to RE2-compatible regex pattern strings.

    Returns:
        A list of EntityDict representing identified PII. "type" is always
        upper-cased. "base_form" currently equals the matched text (core
        consolidation may later promote variations to a longer base form).
    """
    entities: List[EntityDict] = []

    for entity_type, pattern_str in patterns.items():
        try:
            compiled_pattern = re.compile(pattern_str)
            for match in compiled_pattern.finditer(text):
                matched_text = match.group(0)
                # Filter out empty or whitespace-only matches
                if not matched_text.strip():
                    continue

                entities.append(
                    {
                        "text": matched_text,
                        "type": entity_type.upper(),
                        "base_form": matched_text,
                    }
                )
        except re.error as e:
            logging.error(f"Invalid regex pattern configured for {entity_type}: {e}")

    return entities
