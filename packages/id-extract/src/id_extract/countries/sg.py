"""National-ID patterns for SG."""

CODE = "SG"

PATTERNS = {
    # S/T citizens and PRs; F/G/M foreign identification numbers.
    "NRIC_SG": r"\b[STFGM]\d{7}[A-Z]\b",
    # Business (8 digits + letter), local company (9 digits + letter),
    # or other entity (T/S/R, year, entity type, serial, letter).
    "UEN_SG": r"\b\d{8}[A-Z]\b|\b\d{9}[A-Z]\b|\b[TSR]\d{2}[A-Z]{2}\d{4}[A-Z]\b",
}
