"""National-ID patterns for TH."""

CODE = "TH"

PATTERNS = {
    # The first digit is never 0. A failed check is dropped.
    "NATIONAL_ID_TH": r"\b[1-9]\d{12}\b",
}
