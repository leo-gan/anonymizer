"""Cross-border patterns. Always loaded."""

CODE = "UNIVERSAL"

# Official ISO 3166-1 alpha-2 country codes (+ XK) required in positions 5-6 of ISO 9362 BIC/SWIFT.
_ISO_3166_ALPHA2 = "|".join(
    "AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ "
    "BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ "
    "CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ "
    "DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR "
    "GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY "
    "HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP "
    "KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY "
    "MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ "
    "NA NC NE NF NG NI NL NO NP NR NU NZ OM "
    "PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW "
    "SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ "
    "TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ "
    "VA VC VE VG VI VN VU WF WS XK YE YT ZA ZM ZW".split()
)

PATTERNS = {
    "EMAIL": "\\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}\\b",
    "PHONE": "\\+?\\b(?:\\d{1,4}[- \\s]?)?\\(?\\d{2,4}\\)?[- \\s]?\\d{3,4}(?:[- \\s]?\\d{3,9})?\\b",
    "URL": "\\bhttps?://[a-zA-Z0-9.-]+(?:/[^\\s<>\\\"']*)?\\b",
    "IP_ADDRESS": "\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b",
    "IPV4_ADDRESS": "\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b",
    "IPV6_ADDRESS": "\\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\\b|\\b(?:[0-9a-fA-F]{1,4}:){1,7}:\\b|\\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\\b",
    "MAC_ADDRESS": "\\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\\b",
    "CREDIT_CARD": "\\b\\d{4}[-\\s]?\\d{4}[-\\s]?\\d{4}[-\\s]?\\d{1,7}\\b|\\b\\d{4}[-\\s]?\\d{6}[-\\s]?\\d{5}\\b",
    "CURRENCY_AMOUNT": "\\b(?:USD|EUR|GBP|JPY|CNY|INR|CAD|AUD|CHF|SEK|NOK|DKK|ZAR)\\s+\\d{1,3}(?:[,\\s]\\d{3})*(?:\\.\\d{2})?\\b|\\b(?:USD|EUR|GBP|JPY|CNY|INR|CAD|AUD|CHF|SEK|NOK|DKK|ZAR)?\\s?[\\$€£¥₹₩₽]\\s?\\d{1,3}(?:[,\\s]\\d{3})*(?:\\.\\d{2})?\\b|\\b\\d{1,3}(?:[,\\s]\\d{3})*(?:\\.\\d{2})?\\s?(?:USD|EUR|GBP|JPY|CNY|INR|CAD)\\b",
    "CRYPTO_BTC": "\\b(?:[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-zA-HJ-NP-Z0-9]{39,59})\\b",
    "CRYPTO_ETH": "\\b0x[a-fA-F0-9]{40}\\b",
    "IBAN": "\\b[A-Z]{2}\\d{2}[A-Z0-9]{11,30}\\b",
    "BIC_SWIFT": (
        f"\\b[A-Z]{{4}}(?:{_ISO_3166_ALPHA2})[A-Z2-9][A-NP-Z0-9](?:[A-Z0-9]{{3}})?\\b"
    ),
    "VIN": "\\b[A-HJ-NPR-Z0-9]{17}\\b",
    "DATE_ISO": "\\b\\d{4}-\\d{2}-\\d{2}(?:[T ]\\d{2}:\\d{2}:\\d{2}(?:\\.\\d{1,6})?(?:Z|[+-]\\d{2}:\\d{2})?)?\\b",
    "US_PASSPORT": "\\b[A-Z][0-9]{8}\\b|\\b[0-9]{9}\\b",
    "CA_PASSPORT": "\\b[A-Z]{2}\\d{6}\\b",
    "GB_PASSPORT": "\\b[0-9]{9}\\b",
}
