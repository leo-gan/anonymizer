# United Kingdom (`GB`)

National-ID patterns loaded when you pass `countries=["GB"]` (or `"all"`). Universal patterns always stay.

`UK is accepted as GB`.


!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `NINO_GB` — National Insurance number

HMRC uses this number to record National Insurance contributions and tax against one person. GOV.UK describes it as 2 letters, 6 numbers, and a final letter.

| | |
|---|---|
| **Package type** | `NINO_GB` |
| **Shape this package looks for** | Two prefix letters (not all pairs), 6 digits, optional suffix A/B/C/D/F/M |
| **Checksum** | none |
| **Example (synthetic)** | `AB123456C` |

**Official sources**

- [GOV.UK — Find your National Insurance number](https://www.gov.uk/find-national-insurance-number)
- [GOV.UK — National Insurance](https://www.gov.uk/national-insurance)

## `VAT_GB` — VAT registration number

The UK VAT number as used after Brexit. Common printed forms are GB plus 9 or 12 digits, or the government-department prefixes GD and HA.

| | |
|---|---|
| **Package type** | `VAT_GB` |
| **Shape this package looks for** | GB + 9 or 12 digits, or GBGD/GBHA + 3 digits |
| **Checksum** | none |
| **Example (synthetic)** | `GB123456789` |

**Official sources**

- [GOV.UK — VAT registration numbers](https://www.gov.uk/vat-registration-numbers)
- [HMRC — Check a UK VAT number](https://www.gov.uk/check-uk-vat-number)

## `COMPANIES_HOUSE_GB` — Companies House company number

The registrar’s number for a company. England and Wales companies are usually 8 digits. Scotland and Northern Ireland use prefixes such as SC and NI.

| | |
|---|---|
| **Package type** | `COMPANIES_HOUSE_GB` |
| **Shape this package looks for** | Optional SC/NI/OC/SO + 6–8 digits |
| **Checksum** | none |
| **Example (synthetic)** | `SC123456` |

**Official sources**

- [Companies House — get information about a company](https://www.gov.uk/get-information-about-a-company)
- [Companies Act 2006](https://www.legislation.gov.uk/ukpga/2006/46/contents)

## `DRIVERS_LICENSE_GB` — Photocard driving licence number

The 16-character driver number printed on a Great Britain photocard licence.

| | |
|---|---|
| **Package type** | `DRIVERS_LICENSE_GB` |
| **Shape this package looks for** | 16 characters in the DVLA layout |
| **Checksum** | none |
| **Example (synthetic)** | `MORGA753116SM9IJ` |

**Official sources**

- [GOV.UK — driving licence categories](https://www.gov.uk/driving-licence-categories)
- [DVLA](https://www.gov.uk/government/organisations/driver-and-vehicle-licensing-agency)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
