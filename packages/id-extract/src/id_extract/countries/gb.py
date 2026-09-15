"""National-ID patterns for GB."""

CODE = "GB"

PATTERNS = {
    "NINO_GB": "\\b[A-CEGHJ-PR-TW-Z]{1}[A-CEGHJ-NPR-TW-Z]{1}\\d{6}[A-DFM]?\\b",
    "DRIVERS_LICENSE_GB": "\\b[A-Z9]{5}\\d{6}[A-Z9]{2}\\d[A-Z]{2}\\b",
    "VAT_GB": "\\bGB\\d{9}\\b|\\bGB\\d{12}\\b|\\bGBGD\\d{3}\\b|\\bGBHA\\d{3}\\b",
    "COMPANIES_HOUSE_GB": "\\b(?:SC|NI|OC|SO)?\\d{6,8}\\b",
}
