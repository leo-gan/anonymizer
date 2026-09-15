# Canada (`CA`)

National-ID patterns loaded when you pass `countries=["CA"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `SIN_CA` — Social Insurance Number (SIN)

A unique 9-digit number issued by Service Canada. It identifies a person for income tax under Income Tax Act s. 237 and for certain federal programs. Temporary SINs begin with 9.

| | |
|---|---|
| **Package type** | `SIN_CA` |
| **Shape this package looks for** | NNN-NNN-NNN |
| **Checksum** | Luhn |
| **Example (synthetic)** | `046-454-286` |

**Official sources**

- [Service Canada — Social Insurance Number](https://www.canada.ca/en/employment-social-development/services/sin.html)
- [CRA — SIN on a tax return](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-address-information/social-insurance-number.html)
- [Income Tax Act (Canada)](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/)

## `DRIVERS_LICENSE_CA` — Driver licence (province or territory)

Licences are issued by each province or territory. Formats vary. The second alternative in the pattern is very broad.

| | |
|---|---|
| **Package type** | `DRIVERS_LICENSE_CA` |
| **Shape this package looks for** | Letter + grouped digits, or 5–15 alphanumeric |
| **Checksum** | none |
| **Example (synthetic)** | `A1234-12345-12345` |

**Official sources**

- [Example issuer: Ontario — driver's licence](https://www.ontario.ca/page/drivers-licence)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
