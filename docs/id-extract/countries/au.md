# Australia (`AU`)

National-ID patterns loaded when you pass `countries=["AU"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `ABN_AU` — Australian Business Number (ABN)

An 11-digit number that identifies a business or organisation to the Australian Government and the public. It is issued through the Australian Business Register.

| | |
|---|---|
| **Package type** | `ABN_AU` |
| **Shape this package looks for** | 11 digits, optional spaces as 2 3 3 3 |
| **Checksum** | none in this package (the ABR uses a weighting check the regex does not run) |
| **Example (synthetic)** | `51 824 753 556` |

**Official sources**

- [What an ABN is (ABR)](https://www.abr.gov.au/business-super-funds-charities/applying-abn)
- [A New Tax System (Australian Business Number) Act 1999](https://www.legislation.gov.au/C2004A00467/latest)
- [ATO — registering for an ABN](https://www.ato.gov.au/businesses-and-organisations/starting-registering-or-closing-a-business/starting-your-own-business/registration-obligations-for-businesses/registering-for-an-australian-business-number)

## `TFN_AU` — Tax File Number (TFN)

A personal reference number in the Australian tax and superannuation systems. The ATO says it is usually 9 digits and stays with the person for life.

| | |
|---|---|
| **Package type** | `TFN_AU` |
| **Shape this package looks for** | 9 digits, optional spaces as 3 3 3 |
| **Checksum** | none |
| **Example (synthetic)** | `123 456 789` |

**Official sources**

- [ATO — What is a tax file number?](https://www.ato.gov.au/individuals-and-families/tax-file-number/what-is-a-tax-file-number)
- [Income Tax Assessment Act 1936 s 202B (TFN application)](https://www.legislation.gov.au/C1936A00027/latest)

## `DRIVERS_LICENSE_AU` — Driver licence (state and territory)

A licence to drive is issued by each state or territory, not by the Commonwealth. Formats differ. This pattern is a broad 8–10 character token and will over-match.

| | |
|---|---|
| **Package type** | `DRIVERS_LICENSE_AU` |
| **Shape this package looks for** | 8–10 letters or digits |
| **Checksum** | none |
| **Example (synthetic)** | `12345678` |

**Official sources**

- [National Transport Commission — driver licensing](https://www.ntc.gov.au/transport-reform/ntc-projects/australian-driver-licensing)
- [Example issuer: NSW Service — driver licences](https://www.nsw.gov.au/driving-boating-and-transport/driver-and-rider-licences)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
