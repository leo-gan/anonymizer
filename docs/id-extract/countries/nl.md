# Netherlands (`NL`)

National-ID patterns loaded when you pass `countries=["NL"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `BSN_NL` — Burgerservicenummer (BSN)

The citizen service number. The Dutch government uses it in dealings with a person. It is 9 digits.

| | |
|---|---|
| **Package type** | `BSN_NL` |
| **Shape this package looks for** | 9 digits |
| **Checksum** | none in this package (11-proef is official) |
| **Example (synthetic)** | `123456782` |

**Official sources**

- [Rijksoverheid — BSN](https://www.rijksoverheid.nl/onderwerpen/privacy-en-persoonsgegevens/burgerservicenummer-bsn)
- [Wet algemene bepalingen burgerservicenummer](https://wetten.overheid.nl/BWBR0022428)

## `VAT_NL` — Dutch VAT number

NL + 9 digits + B + 2-digit establishment.

| | |
|---|---|
| **Package type** | `VAT_NL` |
| **Shape this package looks for** | NL#########B## |
| **Checksum** | none |
| **Example (synthetic)** | `NL123456789B01` |

**Official sources**

- [Belastingdienst — btw-identificatienummer](https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/zakelijk/btw/administratie_bijhouden/btw-nummers/)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
