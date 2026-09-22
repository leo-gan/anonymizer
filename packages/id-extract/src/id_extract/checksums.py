"""Cheap, unambiguous checksums for structured regex hits.

The regex stage is structural on purpose (RE2 cannot do Luhn, IBAN mod-97, etc.).
After a match, this module checks the extra digit when one exists.

- Check passes: keep the real type (``IBAN``).
- Check fails: keep the text, but relabel as ``IBAN_LIKE`` so a mistyped
  number is still hidden.
- A type in ``STRICT_CHECKSUMS`` drops a failed check instead. Those shapes
  are common digit runs.
- No registered check: accept the type unchanged.

Only attach a check when it is cheap and unambiguous. Do not invent rules for
identifiers that have none (most SSNs, many passports, most VAT numbers).
"""

from __future__ import annotations

from datetime import date
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


def validate_rtn_us(text: str) -> bool:
    """ABA routing number: weights 3, 7, 1 and a zero mod-10 total."""
    digits = _digits_only(text)
    if len(digits) != 9:
        return False
    prefix = int(digits[:2])
    if not (prefix <= 12 or 21 <= prefix <= 32 or 61 <= prefix <= 72 or prefix == 80):
        return False
    weights = (3, 7, 1, 3, 7, 1, 3, 7, 1)
    total = sum((ord(digits[i]) - 48) * weights[i] for i in range(9))
    return total % 10 == 0


def validate_cusip(text: str) -> bool:
    """CUSIP Modulus 10 double-add-double check digit (CGS / ANSI X9.6)."""
    compact = _alnum_upper(text)
    if len(compact) != 9 or not compact[8].isdigit():
        return False
    total = 0
    for i, ch in enumerate(compact[:8]):
        if ch.isdigit():
            value = ord(ch) - 48
        elif "A" <= ch <= "Z":
            value = ord(ch) - ord("A") + 10
        else:
            return False
        if i % 2 == 1:
            value *= 2
        total += value // 10 + value % 10
    check = (10 - (total % 10)) % 10
    return compact[8] == str(check)


def validate_phn_bc(text: str) -> bool:
    """BC Personal Health Number: leading 9 and the Teleplan MOD-11 digit."""
    digits = _digits_only(text)
    if len(digits) != 10 or digits[0] != "9":
        return False
    weights = (2, 4, 8, 5, 10, 9, 7, 3)
    total = sum((ord(digits[i + 1]) - 48) * weights[i] for i in range(8))
    remainder = total % 11
    expected = 0 if remainder == 0 else 11 - remainder
    if expected == 10:
        return False
    return digits[9] == str(expected)


def validate_dea_us(text: str) -> bool:
    """DEA check digit on the seven digits after the two-letter prefix.

    Add the 1st, 3rd, and 5th of those digits to twice the 2nd, 4th, and 6th.
    The units digit of that sum is the 7th digit. A hyphenated hospital suffix
    is ignored.
    """
    body = text.upper().split("-", 1)[0].strip()
    if len(body) != 9 or not body[:2].isalpha() or not body[2:].isdigit():
        return False
    digits = body[2:]
    total = (
        int(digits[0])
        + int(digits[2])
        + int(digits[4])
        + 2 * (int(digits[1]) + int(digits[3]) + int(digits[5]))
    )
    return int(digits[6]) == total % 10


def validate_personalausweis_de(text: str) -> bool:
    """ICAO Doc 9303 check on a neuer Personalausweis number.

    A legacy ``T`` plus eight digits has no check digit and is accepted.
    """
    value = _alnum_upper(text)
    if len(value) != 9:
        return False
    if value[0] == "T" and value[1:].isdigit():
        return True
    weights = (7, 3, 1)
    total = 0
    for index, char in enumerate(value[:-1]):
        if char.isdigit():
            number = int(char)
        elif "A" <= char <= "Z":
            number = ord(char) - ord("A") + 10
        else:
            return False
        total += number * weights[index % 3]
    return value[-1].isdigit() and total % 10 == int(value[-1])


def validate_acn_au(text: str) -> bool:
    """ASIC modified modulus 10 on the nine digits of an ACN."""
    digits = _digits_only(text)
    if len(digits) != 9:
        return False
    weights = (8, 7, 6, 5, 4, 3, 2, 1)
    total = sum(int(digits[index]) * weights[index] for index in range(8))
    check = (10 - (total % 10)) % 10
    return digits[8] == str(check)


def validate_medicare_au(text: str) -> bool:
    """Medicare modulus 10 on the first eight digits. The 9th digit is the check.

    The 10th digit is the person reference on the card and is not part of the check.
    """
    digits = _digits_only(text)
    if len(digits) != 10 or digits[0] not in "23456":
        return False
    weights = (1, 3, 7, 9, 1, 3, 7, 9)
    total = sum(int(digits[index]) * weights[index] for index in range(8))
    return int(digits[8]) == total % 10


def validate_nhs_gb(text: str) -> bool:
    """NHS number modulus 11. Weights 10..2 on the first nine digits.

    Check digit = 11 - (sum mod 11). A result of 11 is stored as 0.
    A result of 10 is not issued.
    """
    digits = _digits_only(text)
    if len(digits) != 10:
        return False
    weights = (10, 9, 8, 7, 6, 5, 4, 3, 2)
    total = sum(int(digits[index]) * weights[index] for index in range(9))
    check = 11 - (total % 11)
    if check == 10:
        return False
    if check == 11:
        check = 0
    return int(digits[9]) == check


_UEN_A_WEIGHT = (10, 4, 9, 3, 8, 2, 7, 1)
_UEN_A_ALPHABET = "XMKECAWLJDB"
_UEN_B_WEIGHT = (10, 8, 6, 4, 9, 7, 5, 3, 1)
_UEN_B_ALPHABET = "ZKCMDNERGWH"
_UEN_C_WEIGHT = (4, 3, 5, 3, 10, 2, 2, 5, 7)
_UEN_C_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWX0123456789"
_UEN_C_ENTITY = frozenset(
    {
        "LP",
        "LL",
        "FC",
        "PF",
        "RF",
        "MQ",
        "MM",
        "NB",
        "CC",
        "CS",
        "MB",
        "FM",
        "GS",
        "DP",
        "CP",
        "NR",
        "CM",
        "CD",
        "MD",
        "HS",
        "VH",
        "CH",
        "MH",
        "CL",
        "XL",
        "CX",
        "HC",
        "RP",
        "TU",
        "TC",
        "FB",
        "FN",
        "PA",
        "PB",
        "SS",
        "MC",
        "SM",
        "GA",
        "GB",
    }
)


def validate_uen_sg(text: str) -> bool:
    """Singapore UEN check for the business, local-company, and other-entity forms."""
    value = _alnum_upper(text)
    if len(value) == 9 and value[:8].isdigit():
        check = _UEN_A_ALPHABET[
            sum(int(char) * weight for char, weight in zip(value[:8], _UEN_A_WEIGHT)) % 11
        ]
        return value[8] == check
    if len(value) == 10 and value[:9].isdigit():
        if int(value[:4]) > date.today().year:
            return False
        check = _UEN_B_ALPHABET[
            sum(int(char) * weight for char, weight in zip(value[:9], _UEN_B_WEIGHT)) % 11
        ]
        return value[9] == check
    if (
        len(value) == 10
        and value[0] in "TSR"
        and value[1:3].isdigit()
        and value[3:5].isalpha()
        and value[5:9].isdigit()
    ):
        if value[3:5] not in _UEN_C_ENTITY:
            return False
        total = sum(
            _UEN_C_ALPHABET.index(char) * weight
            for char, weight in zip(value[:9], _UEN_C_WEIGHT)
        )
        return value[9] == _UEN_C_ALPHABET[(total - 5) % 11]
    return False


_HETU_CENTURY = {
    "+": 1800,
    "-": 1900,
    "Y": 1900,
    "X": 1900,
    "W": 1900,
    "V": 1900,
    "U": 1900,
    "A": 2000,
    "B": 2000,
    "C": 2000,
    "D": 2000,
    "E": 2000,
    "F": 2000,
}
_HETU_CHECK = "0123456789ABCDEFHJKLMNPRSTUVWXY"


def validate_hetu_fi(text: str) -> bool:
    """DVV control character. The century mark selects the year, then the date must exist."""
    value = text.strip().upper()
    if len(value) != 11:
        return False
    century = _HETU_CENTURY.get(value[6])
    if century is None or value[-1] not in _HETU_CHECK:
        return False
    try:
        date(century + int(value[4:6]), int(value[2:4]), int(value[0:2]))
    except ValueError:
        return False
    number = int(value[0:6] + value[7:10])
    return _HETU_CHECK[number % 31] == value[-1]


def validate_national_id_th(text: str) -> bool:
    """Thai national-ID check: weights 13..2 on the first 12 digits, then (11 - sum mod 11) mod 10."""
    digits = _digits_only(text)
    if len(digits) != 13 or digits[0] == "0":
        return False
    total = sum(int(digits[index]) * (13 - index) for index in range(12))
    check = (11 - (total % 11)) % 10
    return int(digits[12]) == check


def validate_national_id_tr(text: str) -> bool:
    """NVI check. Digit 10 is from the odd and even places. Digit 11 is the sum of the first ten."""
    digits = _digits_only(text)
    if len(digits) != 11 or digits[0] == "0":
        return False
    nums = [int(char) for char in digits]
    odd = sum(nums[index] for index in range(0, 9, 2))
    even = sum(nums[index] for index in range(1, 8, 2))
    if nums[9] != (odd * 7 - even) % 10:
        return False
    return nums[10] == sum(nums[:10]) % 10


def validate_steuer_id_de(text: str) -> bool:
    """ISO 7064 mod 11,10 on a German tax id. The first digit is never 0."""
    digits = _digits_only(text)
    if len(digits) != 11 or digits[0] == "0":
        return False
    nums = [int(char) for char in digits]
    product = 10
    for index in range(10):
        total = (nums[index] + product) % 10
        if total == 0:
            total = 10
        product = (total * 2) % 11
    check = 11 - product
    if check == 10:
        check = 0
    return check == nums[10]


def validate_clabe_mx(text: str) -> bool:
    """CLABE control digit: cyclic weights 3, 7, 1 on the first 17 digits."""
    digits = _digits_only(text)
    if len(digits) != 18:
        return False
    weights = (3, 7, 1)
    total = 0
    for i, ch in enumerate(digits[:17]):
        total += ((ord(ch) - 48) * weights[i % 3]) % 10
    check = (10 - (total % 10)) % 10
    return digits[17] == str(check)


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
    "RTN_US": validate_rtn_us,
    "CUSIP_NNA": validate_cusip,
    "PHN_BC_CA": validate_phn_bc,
    "CLABE_MX": validate_clabe_mx,
    "DEA_US": validate_dea_us,
    "PERSONALAUSWEIS_DE": validate_personalausweis_de,
    "ACN_AU": validate_acn_au,
    "MEDICARE_AU": validate_medicare_au,
    "NHS_GB": validate_nhs_gb,
    "UEN_SG": validate_uen_sg,
    "HETU_FI": validate_hetu_fi,
    "NATIONAL_ID_TH": validate_national_id_th,
    "NATIONAL_ID_TR": validate_national_id_tr,
    "STEUER_ID_DE": validate_steuer_id_de,
}

# These shapes are common digit runs. A failed check is dropped instead of
# kept as TYPE_LIKE, which is what the other validators do.
STRICT_CHECKSUMS = frozenset(
    {
        "RTN_US",
        "CUSIP_NNA",
        "PHN_BC_CA",
        "CLABE_MX",
        "ACN_AU",
        "MEDICARE_AU",
        "NHS_GB",
        "UEN_SG",
        "NATIONAL_ID_TH",
        "NATIONAL_ID_TR",
        "STEUER_ID_DE",
    }
)


def has_checksum(entity_type: str) -> bool:
    """Return True if this type has a registered extra-digit check."""
    return entity_type.upper() in CHECKSUM_VALIDATORS


def strict_checksum(entity_type: str) -> bool:
    """Return True when a failed check should drop the hit."""
    return entity_type.upper() in STRICT_CHECKSUMS


def passes_checksum(entity_type: str, text: str) -> bool:
    """Return True if ``text`` has no check, or if its check succeeds."""
    validator = CHECKSUM_VALIDATORS.get(entity_type.upper())
    if validator is None:
        return True
    return validator(text)
