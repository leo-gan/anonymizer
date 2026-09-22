# Türkiye (`TR`)

National-ID patterns loaded when you pass `countries=["TR"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `NATIONAL_ID_TR` — T.C. Kimlik No

The 11-digit Republic of Türkiye identity number. The first digit is never 0. The tenth and eleventh digits are check digits. A failed check is dropped, because eleven digits are a common shape.

| | |
|---|---|
| **Package type** | `NATIONAL_ID_TR` |
| **Shape this package looks for** | 11 digits, first digit 1–9 |
| **Checksum** | NVI check on digits 10 and 11. A failure is dropped. |
| **Example (synthetic)** | `10000000146` |

**Official sources**

- [NVI — identity card](https://www.nvi.gov.tr/)
- [Population Services Law No. 5490](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=5490&MevzuatTur=1&MevzuatTertip=5)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
