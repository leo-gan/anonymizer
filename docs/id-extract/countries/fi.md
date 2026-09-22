# Finland (`FI`)

National-ID patterns loaded when you pass `countries=["FI"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `HETU_FI` — Henkilötunnus

The Finnish personal identity code. Six digits of the date of birth, a century mark, a three-digit individual number, and a check character. The century mark is + for the 1800s, - Y X W V U for the 1900s, and A B C D E F for the 2000s. A failed check is kept as HETU_FI_LIKE.

| | |
|---|---|
| **Package type** | `HETU_FI` |
| **Shape this package looks for** | DDMMYY + century mark + 3 digits + check character |
| **Checksum** | The nine-digit number modulo 31 indexes 0123456789ABCDEFHJKLMNPRSTUVWXY. The date must be a real day in the century given by the mark. A failure is kept as HETU_FI_LIKE. |
| **Example (synthetic)** | `131052-308T` |

**Official sources**

- [Digital and Population Data Services Agency — personal identity code](https://dvv.fi/en/personal-identity-code)
- [Laki väestötietojärjestelmästä](https://www.finlex.fi/fi/laki/ajantasa/2009/20090661)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
