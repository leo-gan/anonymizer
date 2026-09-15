"""National-ID patterns for IN."""

CODE = "IN"

PATTERNS = {
    "AADHAAR_IN": "\\b\\d{4}\\s?\\d{4}\\s?\\d{4}\\b",
    "PAN_IN": "\\b[A-Z]{5}\\d{4}[A-Z]\\b",
    "GSTIN_IN": "\\b\\d{2}[A-Z]{5}\\d{4}[A-Z]\\d[A-Z0-9]{2}\\b",
    "DRIVERS_LICENSE_IN": "\\b[A-Z]{2}\\d{2}\\s?\\d{11}\\b|\\b[A-Z]{2}-\\d{13}\\b",
}
