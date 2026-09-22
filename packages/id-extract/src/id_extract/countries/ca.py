"""National-ID patterns for CA."""

CODE = "CA"

PATTERNS = {
    "SIN_CA": "\\b\\d{3}-\\d{3}-\\d{3}\\b",
    "DRIVERS_LICENSE_CA": "\\b[A-Z]\\d{4,5}-\\d{5,6}-\\d{5}\\b|\\b[A-Z0-9]{5,15}\\b",
    # CRA program account: 9-digit BN + program letters + 4-digit reference.
    "PROGRAM_ACCOUNT_CA": "\\b\\d{9}\\s?(?:RT|RP|RC|RM|RZ|RR|RG)\\s?\\d{4}\\b",
    "DIN_CA": "\\bDIN\\s?\\d{8}\\b",
    "NPN_CA": "\\bNPN\\s?\\d{8}\\b",
    "DIN_HM_CA": "\\bDIN-HM\\s?\\d{8}\\b",
    # IRCC prints the 10-digit UCI as NN-NNNN-NNNN.
    "UCI_CA": "\\b\\d{2}-\\d{4}-\\d{4}\\b",
}
