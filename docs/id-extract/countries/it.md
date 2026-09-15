# Italy (`IT`)

National-ID patterns loaded when you pass `countries=["IT"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `CODICE_FISCALE_IT` — Codice fiscale

The Italian tax code for a natural person. The Agenzia delle Entrate assigns it. Sixteen characters encode name, birth date, place, and a check letter.

| | |
|---|---|
| **Package type** | `CODICE_FISCALE_IT` |
| **Shape this package looks for** | 6 letters + 2 digits + letter + 2 digits + letter + 3 digits + letter |
| **Checksum** | odd/even character table, last letter |
| **Example (synthetic)** | `RSSMRA85T10A562S` |

**Official sources**

- [Agenzia delle Entrate — codice fiscale](https://www.agenziaentrate.gov.it/portale/web/guest/schede/istanze/richiesta-ts_cf/informazioni-codice-fiscale)
- [DPR 605/1973 (anagrafe tributaria)](https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.del.presidente.della.repubblica:1973-09-29;605)

## `VAT_IT` — Partita IVA

Italy’s VAT number in intra-Community form: IT plus 11 digits.

| | |
|---|---|
| **Package type** | `VAT_IT` |
| **Shape this package looks for** | IT + 11 digits |
| **Checksum** | none in this package |
| **Example (synthetic)** | `IT12345678901` |

**Official sources**

- [Agenzia delle Entrate — partita IVA](https://www.agenziaentrate.gov.it/portale/web/guest/schede/istanze/apertura-partita-iva/infogen-apertura-piva)

## `DRIVERS_LICENSE_IT` — Patente di guida

A coarse 10-character token for an Italian driving-licence number.

| | |
|---|---|
| **Package type** | `DRIVERS_LICENSE_IT` |
| **Shape this package looks for** | 10 letters or digits |
| **Checksum** | none |
| **Example (synthetic)** | `U1A2345678` |

**Official sources**

- [MIT — patente di guida](https://www.ilportaledellautomobilista.it/)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
