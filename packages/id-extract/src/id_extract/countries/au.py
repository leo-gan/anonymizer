"""National-ID patterns for AU."""

CODE = "AU"

PATTERNS = {
    "TFN_AU": "\\b\\d{3}\\s?\\d{3}\\s?\\d{3}\\b",
    "ABN_AU": "\\b\\d{2}\\s?\\d{3}\\s?\\d{3}\\s?\\d{3}\\b",
    "DRIVERS_LICENSE_AU": "\\b[A-Z0-9]{8,10}\\b",
}
