"""National-ID patterns for CN."""

CODE = "CN"

PATTERNS = {
    "RESIDENT_ID_CN": "\\b\\d{17}[\\dXx]\\b",
    "UNIFIED_SOCIAL_CREDIT_CODE_CN": "\\b[A-Z0-9]{18}\\b",
    "PASSPORT_CN": "\\bE\\d{8}\\b|\\bG\\d{8}\\b|\\bS\\d{8}\\b",
}
