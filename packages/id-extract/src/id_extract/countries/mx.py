"""National-ID patterns for MX."""

CODE = "MX"

PATTERNS = {
    "CURP_MX": "\\b[A-Z]{4}\\d{6}[HM][A-Z]{5}[0-9A-Z]\\d\\b",
    "RFC_MX": "\\b[A-Z]{3,4}\\d{6}[A-Z0-9]{3}\\b",
}
