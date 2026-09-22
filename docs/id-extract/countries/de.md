# Germany (`DE`)

National-ID patterns loaded when you pass `countries=["DE"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `STEUER_ID_DE` — Steuerliche Identifikationsnummer

The 11-digit personal tax ID assigned by the Federal Central Tax Office (BZSt). It stays with the person for life. The first digit is never 0. The eleventh digit is the ISO 7064 mod 11,10 check. A failed check is dropped, because eleven digits are a common shape.

| | |
|---|---|
| **Package type** | `STEUER_ID_DE` |
| **Shape this package looks for** | 11 digits, first digit 1–9 |
| **Checksum** | ISO 7064 mod 11,10. A failure is dropped. |
| **Example (synthetic)** | `26954371827` |

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

## `PERSONALAUSWEIS_DE` — Personalausweis number

The document number on a German identity card. Cards issued since November 2010 use nine characters from the ICAO set (the letters A, B, D, E, I, O, Q, S, and U are omitted) and an ICAO check digit. Older cards are the letter T plus eight digits and have no check digit.

| | |
|---|---|
| **Package type** | `PERSONALAUSWEIS_DE` |
| **Shape this package looks for** | ICAO 8 characters + check digit, or T + 8 digits |
| **Checksum** | ICAO Doc 9303 weights 7, 3, 1 on the neuer Personalausweis. The legacy T form is accepted without a check. A failed nPA check is kept as PERSONALAUSWEIS_DE_LIKE. |
| **Example (synthetic)** | `C00000004` |

**Official sources**

- [BMI — Personalausweis](https://www.personalausweisportal.de/)
- [Personalausweisgesetz](https://www.gesetze-im-internet.de/pauswg/)

## `HANDELSREGISTER_DE` — Handelsregisternummer

The commercial-register number. HRA is used for sole traders and partnerships. HRB is used for corporations. The prefix is followed by one to six digits.

| | |
|---|---|
| **Package type** | `HANDELSREGISTER_DE` |
| **Shape this package looks for** | HRA or HRB, optional space, 1–6 digits |
| **Checksum** | none |
| **Example (synthetic)** | `HRB 12345` |

**Official sources**

- [§ 14 HGB](https://www.gesetze-im-internet.de/hgb/__14.html)

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
