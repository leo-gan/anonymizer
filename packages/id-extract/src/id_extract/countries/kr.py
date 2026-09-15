"""National-ID patterns for KR."""

CODE = "KR"

PATTERNS = {
    "RESIDENT_REGISTRATION_KR": "\\b\\d{6}-\\d{7}\\b",
    "BUSINESS_REG_KR": "\\b\\d{3}-\\d{2}-\\d{5}\\b",
}
