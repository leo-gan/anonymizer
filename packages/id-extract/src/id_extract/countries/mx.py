"""National-ID patterns for MX."""

CODE = "MX"

PATTERNS = {
    "CURP_MX": "\\b[A-Z]{4}\\d{6}[HM][A-Z]{5}[0-9A-Z]\\d\\b",
    "RFC_MX": "\\b[A-Z]{3,4}\\d{6}[A-Z0-9]{3}\\b",
    # 18 digits. A failed control digit is dropped, not relabeled.
    "CLABE_MX": "\\b\\d{18}\\b",
    "NSS_MX": "\\b\\d{11}\\b",
    # SAT Anexo 22 prints the 15 digits in groups separated by two spaces.
    "PEDIMENTO_MX": "\\b\\d{2}  \\d{2}  \\d{4}  \\d{7}\\b",
}
