"""Cheap, unambiguous checksums for structured regex hits.

The regex stage is structural on purpose (RE2 cannot do Luhn, IBAN mod-97, etc.).
After a match, this module checks the extra digit when one exists.

- Check passes: keep the real type (``IBAN``).
- Check fails: keep the text, but relabel as ``IBAN_LIKE`` so a mistyped
  number is still hidden. Never drop the hit.
- No registered check: accept the type unchanged.

Only attach a check when it is cheap and unambiguous. Do not invent rules for
identifiers that have none (most SSNs, many passports, most VAT numbers).
"""

from __future__ import annotations

from typing import Callable, Dict

# Official IBAN character lengths by country code (ISO 13616).
# Unknown countries are rejected so random "ABxx..." tokens do not survive.
_IBAN_LENGTHS: Dict[str, int] = {
    "AD": 24,
    "AE": 23,
    "AL": 28,
    "AT": 20,
    "AZ": 28,
    "BA": 20,
    "BE": 16,
    "BG": 22,
    "BH": 22,
    "BR": 29,
    "BY": 28,
    "CH": 21,
    "CR": 22,
    "CY": 28,
    "CZ": 24,
    "DE": 22,
    "DK": 18,
    "DO": 28,
    "EE": 20,
    "EG": 29,
    "ES": 24,
    "FI": 18,
    "FO": 18,
    "FR": 27,
    "GB": 22,
    "GE": 22,
    "GI": 23,
    "GL": 18,
    "GR": 27,
    "GT": 28,
    "HR": 21,
    "HU": 28,
    "IE": 22,
    "IL": 23,
    "IQ": 23,
    "IS": 26,
    "IT": 27,
    "JO": 30,
    "KW": 30,
    "KZ": 20,
    "LB": 28,
    "LC": 32,
    "LI": 21,
    "LT": 20,
    "LU": 20,
    "LV": 21,
    "LY": 25,
    "MC": 27,
    "MD": 24,
    "ME": 22,
    "MK": 19,
    "MR": 27,
    "MT": 31,
    "MU": 30,
    "NL": 18,
    "NO": 15,
    "PK": 24,
    "PL": 28,
    "PS": 29,
    "PT": 25,
    "QA": 29,
    "RO": 24,
    "RS": 22,
    "SA": 24,
    "SE": 24,
    "SI": 19,
    "SK": 24,
    "SM": 27,
    "TN": 24,
    "TR": 26,
    "UA": 29,
    "VA": 22,
    "VG": 24,
    "XK": 20,
}

# ISO 3779 VIN transliteration (I, O, Q are not used).
_VIN_TRANSLIT = {
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
    "E": 5,
    "F": 6,
    "G": 7,
    "H": 8,
    "J": 1,
    "K": 2,
    "L": 3,
    "M": 4,
    "N": 5,
    "P": 7,
    "R": 9,
    "S": 2,
    "T": 3,
    "U": 4,
    "V": 5,
    "W": 6,
    "X": 7,
    "Y": 8,
    "Z": 9,
}
_VIN_WEIGHTS = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)

# Spanish DNI / NIE remainder -> letter.
_DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
_NIE_PREFIX = {"X": "0", "Y": "1", "Z": "2"}

# Chinese Resident Identity Card (GB 11643-1999).
_CN_WEIGHTS = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
_CN_CHECK = "10X98765432"

# Verhoeff tables (Aadhaar).
_VERHOEFF_D = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)
_VERHOEFF_P = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
)

# Italian codice fiscale: odd positions (1-based) and even positions.
_CF_ODD = {
    "0": 1,
    "1": 0,
    "2": 5,
    "3": 7,
    "4": 9,
    "5": 13,
    "6": 15,
    "7": 17,
    "8": 19,
    "9": 21,
    "A": 1,
    "B": 0,
    "C": 5,
    "D": 7,
    "E": 9,
    "F": 13,
    "G": 15,
    "H": 17,
    "I": 19,
    "J": 21,
    "K": 2,
    "L": 4,
    "M": 18,
    "N": 20,
    "O": 11,
    "P": 3,
    "Q": 6,
    "R": 8,
    "S": 12,
    "T": 14,
    "U": 16,
    "V": 10,
    "W": 22,
    "X": 25,
    "Y": 24,
    "Z": 23,
}
_CF_EVEN = {
    **{str(i): i for i in range(10)},
    **{chr(ord("A") + i): i for i in range(26)},
}


def _digits_only(text: str) -> str:
    return "".join(ch for ch in text if ch.isdigit())


def _alnum_upper(text: str) -> str:
    return "".join(ch for ch in text.upper() if ch.isalnum())


def luhn_ok(digits: str) -> bool:
    """Return True if ``digits`` (0-9 only) passes the Luhn check."""
    if not digits or not digits.isdigit():
        return False
    total = 0
    # Double every second digit from the right.
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        n = ord(ch) - 48
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def verhoeff_ok(digits: str) -> bool:
    """Return True if ``digits`` (0-9 only) passes the Verhoeff check."""
    if not digits or not digits.isdigit():
        return False
    checksum = 0
    for i, ch in enumerate(reversed(digits)):
        checksum = _VERHOEFF_D[checksum][_VERHOEFF_P[i % 8][ord(ch) - 48]]
    return checksum == 0


def validate_credit_card(text: str) -> bool:
    digits = _digits_only(text)
    if not 13 <= len(digits) <= 19:
        return False
    return luhn_ok(digits)


def validate_npi(text: str) -> bool:
    # CMS: Luhn over the prefix 80840 + the 10-digit NPI.
    digits = _digits_only(text)
    if len(digits) != 10:
        return False
    return luhn_ok("80840" + digits)


def validate_sin_ca(text: str) -> bool:
    digits = _digits_only(text)
    if len(digits) != 9:
        return False
    return luhn_ok(digits)


def validate_iban(text: str) -> bool:
    compact = _alnum_upper(text)
    if len(compact) < 5 or not compact[:2].isalpha() or not compact[2:4].isdigit():
        return False
    expected = _IBAN_LENGTHS.get(compact[:2])
    if expected is None or len(compact) != expected:
        return False
    rearranged = compact[4:] + compact[:4]
    numeric = []
    for ch in rearranged:
        if ch.isdigit():
            numeric.append(ch)
        else:
            numeric.append(str(ord(ch) - 55))  # A=10 ... Z=35
    return int("".join(numeric)) % 97 == 1


def validate_vin(text: str) -> bool:
    vin = _alnum_upper(text)
    if len(vin) != 17:
        return False
    total = 0
    for i, ch in enumerate(vin):
        if ch.isdigit():
            value = ord(ch) - 48
        else:
            value = _VIN_TRANSLIT.get(ch)
            if value is None:
                return False
        total += value * _VIN_WEIGHTS[i]
    remainder = total % 11
    expected = "X" if remainder == 10 else str(remainder)
    return vin[8] == expected


def validate_dni_es(text: str) -> bool:
    compact = _alnum_upper(text)
    if len(compact) != 9 or not compact[:8].isdigit() or not compact[8].isalpha():
        return False
    return compact[8] == _DNI_LETTERS[int(compact[:8]) % 23]


def validate_nie_es(text: str) -> bool:
    compact = _alnum_upper(text)
    if len(compact) != 9 or compact[0] not in _NIE_PREFIX:
        return False
    return validate_dni_es(_NIE_PREFIX[compact[0]] + compact[1:])


def validate_resident_id_cn(text: str) -> bool:
    compact = _alnum_upper(text)
    if len(compact) != 18 or not compact[:17].isdigit():
        return False
    total = sum((ord(compact[i]) - 48) * _CN_WEIGHTS[i] for i in range(17))
    return compact[17] == _CN_CHECK[total % 11]


def validate_aadhaar_in(text: str) -> bool:
    digits = _digits_only(text)
    if len(digits) != 12 or digits[0] in "01":
        return False
    return verhoeff_ok(digits)


def validate_cpf_br(text: str) -> bool:
    digits = _digits_only(text)
    if len(digits) != 11 or len(set(digits)) == 1:
        return False

    def _cpf_digit(body: str, start_weight: int) -> str:
        total = sum((ord(ch) - 48) * (start_weight - i) for i, ch in enumerate(body))
        remainder = total % 11
        return "0" if remainder < 2 else str(11 - remainder)

    if digits[9] != _cpf_digit(digits[:9], 10):
        return False
    return digits[10] == _cpf_digit(digits[:10], 11)


def validate_codice_fiscale_it(text: str) -> bool:
    compact = _alnum_upper(text)
    if len(compact) != 16:
        return False
    total = 0
    for i, ch in enumerate(compact[:15]):
        table = _CF_ODD if i % 2 == 0 else _CF_EVEN
        value = table.get(ch)
        if value is None:
            return False
        total += value
    return compact[15] == chr(ord("A") + (total % 26))


def validate_pesel_pl(text: str) -> bool:
    digits = _digits_only(text)
    if len(digits) != 11:
        return False
    weights = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)
    total = sum((ord(digits[i]) - 48) * weights[i] for i in range(10))
    check = (10 - (total % 10)) % 10
    return digits[10] == str(check)


ValidatorFn = Callable[[str], bool]

# Keys must match entity TYPEs emitted by the regex stage (upper-case).
CHECKSUM_VALIDATORS: Dict[str, ValidatorFn] = {
    "CREDIT_CARD": validate_credit_card,
    "MEDICAL_NPI_US": validate_npi,
    "SIN_CA": validate_sin_ca,
    "IBAN": validate_iban,
    "VIN": validate_vin,
    "DNI_ES": validate_dni_es,
    "NIE_ES": validate_nie_es,
    "RESIDENT_ID_CN": validate_resident_id_cn,
    "AADHAAR_IN": validate_aadhaar_in,
    "CPF_BR": validate_cpf_br,
    "CODICE_FISCALE_IT": validate_codice_fiscale_it,
    "PESEL_PL": validate_pesel_pl,
}


LIKE_SUFFIX = "_LIKE"


def has_checksum(entity_type: str) -> bool:
    """Return True if this type has a registered extra-digit check."""
    return entity_type.upper() in CHECKSUM_VALIDATORS


def like_type(entity_type: str) -> str:
    """``IBAN`` -> ``IBAN_LIKE``."""
    return f"{entity_type.upper()}{LIKE_SUFFIX}"


def parent_type(entity_type: str) -> str:
    """``IBAN_LIKE`` -> ``IBAN``; ``IBAN`` -> ``IBAN``."""
    upper = entity_type.upper()
    if upper.endswith(LIKE_SUFFIX) and len(upper) > len(LIKE_SUFFIX):
        return upper[: -len(LIKE_SUFFIX)]
    return upper


def type_matches_filter(entity_type: str, allowed: list[str] | set[str]) -> bool:
    """True if the type is listed, is a ``_LIKE`` sibling, or matches a prefix.

    A listed ``DRIVERS_LICENSE`` matches ``DRIVERS_LICENSE_US``.
    A listed ``DATE`` matches ``DATE_ISO``.
    """
    allowed_upper = {item.upper() for item in allowed}
    upper = entity_type.upper()
    parent = parent_type(upper)
    if upper in allowed_upper or parent in allowed_upper:
        return True
    for item in allowed_upper:
        if upper.startswith(item + "_") or parent.startswith(item + "_"):
            return True
        if upper.endswith("_" + item) or parent.endswith("_" + item):
            return True
    return False


def passes_checksum(entity_type: str, text: str) -> bool:
    """Return True if ``text`` has no check, or if its check succeeds."""
    validator = CHECKSUM_VALIDATORS.get(entity_type.upper())
    if validator is None:
        return True
    return validator(text)
