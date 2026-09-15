"""National-ID patterns for BR."""

CODE = "BR"

PATTERNS = {
    "CPF_BR": "\\b\\d{3}\\.?\\d{3}\\.?\\d{3}-?\\d{2}\\b",
    "CNPJ_BR": "\\b\\d{2}\\.?\\d{3}\\.?\\d{3}/?\\d{4}-?\\d{2}\\b",
    "RG_BR": "\\b\\d{2}\\.?\\d{3}\\.?\\d{3}-?[0-9X]\\b",
}
