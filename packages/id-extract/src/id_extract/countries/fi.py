"""National-ID patterns for FI."""

CODE = "FI"

PATTERNS = {
    # Century mark and the 31-character check alphabet from DVV.
    "HETU_FI": (
        r"\b\d{6}[-+ABCDEFYXWVU]\d{3}[0-9ABCDEFHJKLMNPRSTUVWXY]\b"
    ),
}
