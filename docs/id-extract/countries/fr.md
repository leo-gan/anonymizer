# France (`FR`)

National-ID patterns loaded when you pass `countries=["FR"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `INSEE_FR` — NIR / numéro de sécurité sociale

The numéro d’inscription au répertoire (NIR) is the French social-security number. It is issued from the INSEE directory. It usually starts with 1 or 2 (sex) followed by date and place digits. This pattern is simplified for recall.

| | |
|---|---|
| **Package type** | `INSEE_FR` |
| **Shape this package looks for** | 1 or 2, then 12–14 more digits |
| **Checksum** | none in this package (the official key is mod 97) |
| **Example (synthetic)** | `255081416802538` |

**Official sources**

- [Ameli — numéro de sécurité sociale](https://www.ameli.fr/assure/droits-demarches/principes/numero-securite-sociale)
- [INSEE — répertoire national d’identification des personnes physiques](https://www.insee.fr/fr/metadonnees/definition/c1602)

## `VAT_FR` — Numéro de TVA intracommunautaire

France’s intra-Community VAT identifier. Service-Public describes it as FR + a 2-character key + the 9-digit SIREN.

| | |
|---|---|
| **Package type** | `VAT_FR` |
| **Shape this package looks for** | FR + 2 letters or digits + 9 digits |
| **Checksum** | none |
| **Example (synthetic)** | `FRXX123456789` |

**Official sources**

- [Service-Public — numéro de TVA intracommunautaire](https://www.service-public.fr/professionnels-entreprises/vosdroits/F23570)
- [Council Directive 2006/112/EC (VAT)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32006L0112)

## `PASSPORT_FR` — French passport number

A structural pattern for common French passport numbers.

| | |
|---|---|
| **Package type** | `PASSPORT_FR` |
| **Shape this package looks for** | 2 digits + 2 letters + 5 digits |
| **Checksum** | none |
| **Example (synthetic)** | `12AB34567` |

**Official sources**

- [Service-Public — passeport](https://www.service-public.fr/particuliers/vosdroits/N360)
- [ICAO Doc 9303](https://www.icao.int/publications/pages/publication.aspx?docnum=9303)

## `DRIVERS_LICENSE_FR` — Permis de conduire

A coarse 12-character token for the French driving licence number.

| | |
|---|---|
| **Package type** | `DRIVERS_LICENSE_FR` |
| **Shape this package looks for** | 12 letters or digits |
| **Checksum** | none |
| **Example (synthetic)** | `12AB34567890` |

**Official sources**

- [Service-Public — permis de conduire](https://www.service-public.fr/particuliers/vosdroits/N530)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
