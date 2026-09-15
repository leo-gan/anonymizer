"""National-ID patterns for JP."""

CODE = "JP"

PATTERNS = {
    "MY_NUMBER_JP": "\\b\\d{4}\\s?\\d{4}\\s?\\d{4}\\b",
    "RESIDENT_CARD_JP": "\\b[A-Z]{2}\\d{8}\\b",
    "DRIVERS_LICENSE_JP": "\\b\\d{12}\\b",
}
