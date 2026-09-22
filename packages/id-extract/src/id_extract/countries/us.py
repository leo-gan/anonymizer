"""National-ID patterns for US."""

CODE = "US"

# MBI letters exclude S, L, O, I, B, and Z (CMS format sheet).
_MBI_LETTER = "AC-HJ-KMNP-RT-Y"

PATTERNS = {
    "SSN_US": "\\b\\d{3}-\\d{2}-\\d{4}\\b",
    "EIN_US": "\\b\\d{2}-\\d{7}\\b",
    "DRIVERS_LICENSE_US": "\\b[A-Z]{1,2}\\d{6,8}\\b|\\b\\d{8,9}\\b|\\b[A-Z]\\d{7,8}\\b",
    "MEDICAL_NPI_US": "\\b[0-9]{10}\\b",
    "MEDICAL_LICENSE_US": "\\b[A-Z]{1,2}\\d{6,9}\\b",
    "SSN": "\\b\\d{3}-\\d{2}-\\d{4}\\b",
    # IRS IRM: 9NN-NN-NNNN, 4th–5th digits in the ITIN ranges.
    "ITIN_US": ("\\b9\\d{2}-(?:5\\d|6[0-5]|7\\d|8[0-8]|9[0-2]|9[4-9])-\\d{4}\\b"),
    "ATIN_US": "\\b9\\d{2}-93-\\d{4}\\b",
    "PTIN_US": "\\bP\\d{8}\\b",
    "MBI_US": (
        "\\b[1-9][" + _MBI_LETTER + "][" + _MBI_LETTER + "0-9][0-9]-?"
        "[" + _MBI_LETTER + "][" + _MBI_LETTER + "0-9][0-9]-?"
        "[" + _MBI_LETTER + "][" + _MBI_LETTER + "][0-9][0-9]\\b"
    ),
    "A_NUMBER_US": "\\bA-?\\d{7,9}\\b",
    "USCIS_RECEIPT_US": "\\b[A-Z]{3}\\d{10}\\b",
    "DOS_CASE_US": "\\b(?:[A-Z]{3}\\d{9,10}|\\d{4}[A-Z]{2}\\d{5})\\b",
    "DEA_US": "\\b[A-Z]{2}\\d{7}(?:-[A-Z0-9]{1,7})?\\b",
}
