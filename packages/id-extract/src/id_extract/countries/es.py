"""National-ID patterns for ES."""

CODE = "ES"

PATTERNS = {
    "DNI_ES": "\\b\\d{8}[A-HJ-NP-TV-Z]\\b",
    "NIE_ES": "\\b[XYZ]\\d{7}[A-HJ-NP-TV-Z]\\b",
    "CIF_ES": "\\b[A-HJ-NP-S]\\d{7}[A-J0-9]\\b",
    "VAT_ES": "\\bES[A-Z0-9]\\d{7}[A-Z0-9]\\b",
    "DRIVERS_LICENSE_ES": "\\b[A-Z0-9]{9,10}\\b",
}
