"""National-ID patterns for GB."""

CODE = "GB"

PATTERNS = {
    "NINO_GB": "\\b[A-CEGHJ-PR-TW-Z]{1}[A-CEGHJ-NPR-TW-Z]{1}\\d{6}[A-DFM]?\\b",
    "DRIVERS_LICENSE_GB": "\\b[A-Z9]{5}\\d{6}[A-Z9]{2}\\d[A-Z]{2}\\b",
    "VAT_GB": "\\bGB\\d{9}\\b|\\bGB\\d{12}\\b|\\bGBGD\\d{3}\\b|\\bGBHA\\d{3}\\b",
    "COMPANIES_HOUSE_GB": "\\b(?:SC|NI|OC|SO)?\\d{6,8}\\b",
    # Books issued from 2015: two letters and seven digits.
    # SC, NI, OC, and SO are Companies House prefixes, so they are not passports.
    "PASSPORT_GB": (
        r"\b(?:[A-MP-RT-Z][A-Z]|S[A-BD-NP-Z]|N[A-HJ-Z]|O[A-BD-Z])\d{7}\b"
    ),
    # 10 digits, optional spaces or hyphens in the 3-3-4 print form.
    "NHS_GB": r"\b\d{3}[- ]?\d{3}[- ]?\d{4}\b",
}
