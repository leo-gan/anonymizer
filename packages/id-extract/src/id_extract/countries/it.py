"""National-ID patterns for IT."""

CODE = "IT"

PATTERNS = {
    "CODICE_FISCALE_IT": "\\b[A-Z]{6}\\d{2}[A-Z]\\d{2}[A-Z]\\d{3}[A-Z]\\b",
    "VAT_IT": "\\bIT\\d{11}\\b",
    "DRIVERS_LICENSE_IT": "\\b[A-Z0-9]{10}\\b",
}
