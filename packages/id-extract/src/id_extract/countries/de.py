"""National-ID patterns for DE."""

CODE = "DE"

PATTERNS = {
    "STEUER_ID_DE": "\\b\\d{11}\\b",
    "VAT_DE": "\\bDE\\d{9}\\b",
    "PERSONALAUSWEIS_DE": "\\b[A-Z0-9]{9,10}\\b",
    "DRIVERS_LICENSE_DE": "\\b[A-Z0-9]{11,12}\\b",
}
