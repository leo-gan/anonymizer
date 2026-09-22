# Mexico (`MX`)

National-ID patterns loaded when you pass `countries=["MX"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `CURP_MX` — CURP

Clave Única de Registro de Población. An 18-character code that identifies a person in Mexican federal records.

| | |
|---|---|
| **Package type** | `CURP_MX` |
| **Shape this package looks for** | 4 letters + 6 digits + H/M + 5 letters + alphanumeric + digit |
| **Checksum** | none in this package |
| **Example (synthetic)** | `GARC850101HDFRRN09` |

**Official sources**

- [Gobierno de México — CURP](https://www.gob.mx/curp)
- [RENAPO](https://www.gob.mx/segob/renapo)

## `RFC_MX` — RFC (Registro Federal de Contribuyentes)

The federal tax identifier issued by the SAT. Natural persons use 13 characters; legal persons use 12.

| | |
|---|---|
| **Package type** | `RFC_MX` |
| **Shape this package looks for** | 3–4 letters + 6 digits + 3 alphanumeric |
| **Checksum** | none |
| **Example (synthetic)** | `XAXX010101000` |

**Official sources**

- [SAT — RFC](https://www.sat.gob.mx/tramites/operacion/28753/obten-tu-rfc-con-la-clave-unica-de-registro-de-poblacion-curp)

## `CLABE_MX` — CLABE

The 18-digit interbank account key: 3 bank digits, 3 plaza digits, 11 account digits, and a control digit. A failed control digit is dropped.

| | |
|---|---|
| **Package type** | `CLABE_MX` |
| **Shape this package looks for** | 18 digits |
| **Checksum** | weights 3, 7, 1 on the first 17 digits |
| **Example (synthetic)** | `000000000000000000` |

**Official sources**

- [ABM — how a CLABE is built](https://www.abm.org.mx/preguntas-frecuentes/)

## `NSS_MX` — IMSS social-security number (NSS)

The 11-digit number IMSS assigns to a person. It is permanent. Any standalone 11-digit run matches, so this pattern is broad.

| | |
|---|---|
| **Package type** | `NSS_MX` |
| **Shape this package looks for** | 11 digits |
| **Checksum** | none |
| **Example (synthetic)** | `00000000000` |

**Official sources**

- [IMSS procedure 9210-003-200](https://www.imss.gob.mx/sites/all/statics/pdf/procedimientos/9210-003-200.pdf)

## `PEDIMENTO_MX` — Customs pedimento number

The 15-digit customs declaration number from SAT Anexo 22. The printed form separates the year, customs office, and patent with two spaces and leaves the last seven digits together.

| | |
|---|---|
| **Package type** | `PEDIMENTO_MX` |
| **Shape this package looks for** | 2 digits, two spaces, 2 digits, two spaces, 4 digits, two spaces, 7 digits |
| **Checksum** | none |
| **Example (synthetic)** | `26  01  0001  6000001` |

**Official sources**

- [SAT Anexo 22 (2026 compilation)](https://www.sat.gob.mx/minisitio/NormatividadRMFyRGCE/documentos2026/rgce/compiladas/CompiladoAnexo22_1raRMRGCE2026.pdf)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
