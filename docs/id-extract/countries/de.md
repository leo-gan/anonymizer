# Germany (`DE`)

National-ID patterns loaded when you pass `countries=["DE"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `STEUER_ID_DE` — Steuerliche Identifikationsnummer

The 11-digit personal tax ID assigned by the Federal Central Tax Office (BZSt). It stays with the person for life.

| | |
|---|---|
| **Package type** | `STEUER_ID_DE` |
| **Shape this package looks for** | 11 digits |
| **Checksum** | none in this package |
| **Example (synthetic)** | `12345678901` |

**Official sources**

- [BZSt — Identifikationsnummer](https://www.bzst.de/DE/Privatpersonen/SteuerlicheIdentifikationsnummer/steuerlicheidentifikationsnummer_node.html)
- [§ 139a AO](https://www.gesetze-im-internet.de/ao_1977/__139a.html)

## `VAT_DE` — Umsatzsteuer-Identifikationsnummer

Germany’s VAT ID: DE plus 9 digits.

| | |
|---|---|
| **Package type** | `VAT_DE` |
| **Shape this package looks for** | DE + 9 digits |
| **Checksum** | none |
| **Example (synthetic)** | `DE123456789` |

**Official sources**

- [BZSt — USt-IdNr.](https://www.bzst.de/DE/Unternehmen/Identifikationsnummern/Umsatzsteuer-Identifikationsnummer/umsatzsteuer-identifikationsnummer_node.html)

## `PERSONALAUSWEIS_DE` — Personalausweis / passport number (structural)

A coarse 9–10 character token for German ID-card or passport numbers.

| | |
|---|---|
| **Package type** | `PERSONALAUSWEIS_DE` |
| **Shape this package looks for** | 9–10 letters or digits |
| **Checksum** | none |
| **Example (synthetic)** | `T22000129` |

**Official sources**

- [BMI — Personalausweis](https://www.personalausweisportal.de/)

## `DRIVERS_LICENSE_DE` — Führerscheinnummer

A coarse 11–12 character token for a German driving-licence number.

| | |
|---|---|
| **Package type** | `DRIVERS_LICENSE_DE` |
| **Shape this package looks for** | 11–12 letters or digits |
| **Checksum** | none |
| **Example (synthetic)** | `B072RRE2I55` |

**Official sources**

- [KBA — Fahrerlaubnis](https://www.kba.de/DE/Themen/ZentraleRegister/FAER/faer_node.html)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
