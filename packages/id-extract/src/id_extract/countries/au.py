"""National-ID patterns for AU."""

CODE = "AU"

PATTERNS = {
    "TFN_AU": "\\b\\d{3}\\s?\\d{3}\\s?\\d{3}\\b",
    "ABN_AU": "\\b\\d{2}\\s?\\d{3}\\s?\\d{3}\\s?\\d{3}\\b",
    "DRIVERS_LICENSE_AU": "\\b[A-Z0-9]{8,10}\\b",
    # Nine digits, printed as NNN NNN NNN. A failed ASIC check is dropped.
    "ACN_AU": r"\b\d{3} \d{3} \d{3}\b|\b\d{9}\b",
    # First digit 2–6, then nine digits. Printed as NNNN NNNNN N.
    "MEDICARE_AU": r"\b[2-6]\d{3} \d{5} \d\b|\b[2-6]\d{9}\b",
}
