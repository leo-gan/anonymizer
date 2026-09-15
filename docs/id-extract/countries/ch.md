# Switzerland (`CH`)

National-ID patterns loaded when you pass `countries=["CH"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `AHV_CH` — AHV / AVS number (13 digits, 756…)

The Swiss social-security number. Since 2008 it is a 13-digit number that starts with 756 (the ISO country code).

| | |
|---|---|
| **Package type** | `AHV_CH` |
| **Shape this package looks for** | 756.XXXX.XXXX.XX or 756 + 10 digits |
| **Checksum** | none in this package |
| **Example (synthetic)** | `756.1234.5678.97` |

**Official sources**

- [AHV/AVS — new insurance number](https://www.ahv-iv.ch/en/Social-insurances/Old-age-and-survivors-insurance-OASI/Insurance-number)
- [Federal Act on Old-Age and Survivors’ Insurance (AHVG)](https://www.fedlex.admin.ch/eli/cc/63/837_843_843/en)

## `VAT_CH` — Swiss UID / VAT (CHE…)

The enterprise identification number used as a VAT number, often written CHE followed by 9 digits and MWST, TVA, or IVA.

| | |
|---|---|
| **Package type** | `VAT_CH` |
| **Shape this package looks for** | CHE + 9 digits + optional MWST/TVA/IVA |
| **Checksum** | none |
| **Example (synthetic)** | `CHE123456789MWST` |

**Official sources**

- [UID-Register](https://www.uid.admin.ch/)
- [Federal Act on the Business Identification Number](https://www.fedlex.admin.ch/eli/cc/2010/614/en)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
