# China (`CN`)

National-ID patterns loaded when you pass `countries=["CN"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `RESIDENT_ID_CN` — Resident Identity Card number (居民身份证)

The 18-character number on the PRC Resident Identity Card. The last character is a check digit and may be X. The encoding is specified in GB 11643-1999.

| | |
|---|---|
| **Package type** | `RESIDENT_ID_CN` |
| **Shape this package looks for** | 17 digits + digit or X |
| **Checksum** | ISO 7064 MOD 11-2 weights from GB 11643 |
| **Example (synthetic)** | `11010519491231002X` |

**Official sources**

- [National Immigration Administration — ID cards](https://www.nia.gov.cn/)
- [GB 11643-1999 (citizen identification number)](https://openstd.samr.gov.cn/)

## `UNIFIED_SOCIAL_CREDIT_CODE_CN` — Unified Social Credit Code (统一社会信用代码)

An 18-character code that identifies a legal person or other organisation in China.

| | |
|---|---|
| **Package type** | `UNIFIED_SOCIAL_CREDIT_CODE_CN` |
| **Shape this package looks for** | 18 letters or digits |
| **Checksum** | none in this package |
| **Example (synthetic)** | `91110000MA01234567` |

**Official sources**

- [SAMR — unified social credit code](https://www.samr.gov.cn/)

## `PASSPORT_CN` — Chinese passport number

Common ordinary-passport prefixes E, G, or S plus 8 digits.

| | |
|---|---|
| **Package type** | `PASSPORT_CN` |
| **Shape this package looks for** | E/G/S + 8 digits |
| **Checksum** | none |
| **Example (synthetic)** | `E12345678` |

**Official sources**

- [National Immigration Administration — passports](https://www.nia.gov.cn/)
- [ICAO Doc 9303](https://www.icao.int/publications/pages/publication.aspx?docnum=9303)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
