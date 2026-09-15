# Spain (`ES`)

National-ID patterns loaded when you pass `countries=["ES"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `DNI_ES` — Documento Nacional de Identidad (DNI / NIF)

The Spanish national identity document. The Ministry of the Interior issues it. The number plus a check letter is the NIF for natural persons.

| | |
|---|---|
| **Package type** | `DNI_ES` |
| **Shape this package looks for** | 8 digits + check letter (not I, Ñ, O, U) |
| **Checksum** | remainder modulo 23 → letter table in RD 255/2025 art. 12 |
| **Example (synthetic)** | `12345678Z` |

**Official sources**

- [Ministerio del Interior — DNI](https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/)
- [Cálculo del dígito de control del NIF/NIE](https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/calculo-del-digito-de-control-del-nif-nie/)
- [Normativa básica reguladora del DNI (Interior; includes RD 255/2025 and LO 4/2015)](https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/normativa-basica-reguladora/)

## `NIE_ES` — Número de Identidad de Extranjero (NIE)

The identity number for foreign residents in Spain. It starts with X, Y, or Z, then 7 digits and the same check letter as the DNI.

| | |
|---|---|
| **Package type** | `NIE_ES` |
| **Shape this package looks for** | X/Y/Z + 7 digits + letter |
| **Checksum** | same letter table as DNI after mapping X=0, Y=1, Z=2 |
| **Example (synthetic)** | `X1234567L` |

**Official sources**

- [Ministerio del Interior — NIF/NIE check digit](https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/calculo-del-digito-de-control-del-nif-nie/)
- [Ministerio del Interior — extranjería (NIE)](https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/extranjeria/)

## `CIF_ES` — Código de Identificación Fiscal (companies)

The Spanish tax identifier for legal persons. Agencia Tributaria assigns it.

| | |
|---|---|
| **Package type** | `CIF_ES` |
| **Shape this package looks for** | Letter + 7 digits + letter or digit |
| **Checksum** | none in this package |
| **Example (synthetic)** | `A12345674` |

**Official sources**

- [Agencia Tributaria — NIF](https://sede.agenciatributaria.gob.es/Sede/en_gb/todas-gestiones/censos-nif-domicilio-fiscal.html)

## `VAT_ES` — Spanish VAT number

Intra-Community form ES + the national tax identifier.

| | |
|---|---|
| **Package type** | `VAT_ES` |
| **Shape this package looks for** | ES + 9 alphanumeric |
| **Checksum** | none |
| **Example (synthetic)** | `ESA12345674` |

**Official sources**

- [VIES — validate a VAT number](https://ec.europa.eu/taxation_customs/vies/)

## `DRIVERS_LICENSE_ES` — Permiso de conducción

A coarse 9–10 character token for Spanish driving-licence numbers.

| | |
|---|---|
| **Package type** | `DRIVERS_LICENSE_ES` |
| **Shape this package looks for** | 9–10 letters or digits |
| **Checksum** | none |
| **Example (synthetic)** | `12345678Z` |

**Official sources**

- [DGT — permiso de conducción](https://www.dgt.es/nuestros-servicios/permisos-de-conducir/)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
