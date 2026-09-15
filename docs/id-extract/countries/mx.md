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

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
