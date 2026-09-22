"""National-ID patterns for TR."""

CODE = "TR"

PATTERNS = {
    # The first digit is never 0. A failed NVI check is dropped.
    "NATIONAL_ID_TR": r"\b[1-9]\d{10}\b",
}
