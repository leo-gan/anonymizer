"""National-ID patterns for FR."""

CODE = "FR"

PATTERNS = {
    "INSEE_FR": "\\b[12]\\d{12,14}\\b",
    "VAT_FR": "\\bFR[A-HJ-NP-Z0-9]{2}\\d{9}\\b",
    "DRIVERS_LICENSE_FR": "\\b[A-Z0-9]{12}\\b",
    "PASSPORT_FR": "\\b\\d{2}[A-Z]{2}\\d{5}\\b",
}
