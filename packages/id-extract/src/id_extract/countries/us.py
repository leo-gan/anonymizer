"""National-ID patterns for US."""

CODE = "US"

PATTERNS = {
    "SSN_US": "\\b\\d{3}-\\d{2}-\\d{4}\\b",
    "EIN_US": "\\b\\d{2}-\\d{7}\\b",
    "DRIVERS_LICENSE_US": "\\b[A-Z]{1,2}\\d{6,8}\\b|\\b\\d{8,9}\\b|\\b[A-Z]\\d{7,8}\\b",
    "MEDICAL_NPI_US": "\\b[0-9]{10}\\b",
    "MEDICAL_LICENSE_US": "\\b[A-Z]{1,2}\\d{6,9}\\b",
    "SSN": "\\b\\d{3}-\\d{2}-\\d{4}\\b",
}
