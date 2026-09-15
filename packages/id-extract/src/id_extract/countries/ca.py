"""National-ID patterns for CA."""

CODE = "CA"

PATTERNS = {
    "SIN_CA": "\\b\\d{3}-\\d{3}-\\d{3}\\b",
    "DRIVERS_LICENSE_CA": "\\b[A-Z]\\d{4,5}-\\d{5,6}-\\d{5}\\b|\\b[A-Z0-9]{5,15}\\b",
}
