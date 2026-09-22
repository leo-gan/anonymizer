"""National-ID patterns for DE."""

CODE = "DE"

PATTERNS = {
    # First digit is 1–9. A failed ISO 7064 check is dropped.
    "STEUER_ID_DE": r"\b[1-9]\d{10}\b",
    "VAT_DE": "\\bDE\\d{9}\\b",
    # nPA: ICAO charset (no A, B, D, E, I, O, Q, S, U) plus a check digit.
    # Legacy cards are T plus eight digits and have no check digit.
    "PERSONALAUSWEIS_DE": (
        r"\b(?:[CFGHJKLMNPRTVWXYZ][CFGHJKLMNPRTVWXYZ0-9]{7}\d|T\d{8})\b"
    ),
    "HANDELSREGISTER_DE": r"\bHR[AB]\s*\d{1,6}\b",
    "DRIVERS_LICENSE_DE": "\\b[A-Z0-9]{11,12}\\b",
}
