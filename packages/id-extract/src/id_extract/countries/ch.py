"""National-ID patterns for CH."""

CODE = "CH"

PATTERNS = {
    "AHV_CH": "\\b756\\.\\d{4}\\.\\d{4}\\.\\d{2}\\b|\\b756\\d{10}\\b",
    "VAT_CH": "\\bCHE\\d{9}(?:MWST|TVA|IVA)?\\b",
}
