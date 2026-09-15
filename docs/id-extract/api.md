# Install and API

## Install

```bash
pip install id-extract
# or
uv add id-extract
```

The only runtime dependency is `google-re2`. Python 3.10 or newer.

There are no per-country extras. One install ships every bundled country. Select countries when you call `extract`.

## `extract`

```python
from id_extract import extract

extract(text: str, patterns: dict[str, str] | None = None, *, countries="all") -> list[Entity]
```

| Argument | Meaning |
|---|---|
| `text` | The string to scan. Offsets are indexes in this string. |
| `patterns` | Optional RE2 map. When given, `countries` is ignored. |
| `countries` | `"all"` (default), one ISO-2 code, or a list. `UK` is treated as `GB`. |

Each entity is:

| Field | Meaning |
|---|---|
| `text` | The matched substring |
| `type` | Upper-case key (`ABN_AU`, `IBAN`, `IBAN_LIKE`, …) |
| `base_form` | Same as `text` today |
| `start`, `end` | Character offsets in `text` |
| `score` | `0.95` if a checksum passed, `0.85` if there is no check, `0.55` if the check failed |
| `source` | Always `"regex"` |

Unknown country codes raise `ValueError`.

## `patterns` and `available_countries`

```python
from id_extract import available_countries, patterns

available_countries()                 # ['AR', 'AT', 'AU', ...]
patterns(countries=["AU"])            # dict of RE2 strings
patterns(countries="all")             # full map, including universal keys
```

Universal keys (email, cards, IBAN, …) are always included when you load a country subset.

## Checksums

After a match, a registered extra-digit check may run. Failure does **not** drop the hit. The type is renamed with the `_LIKE` suffix.

Types with a check today: `CREDIT_CARD`, `IBAN`, `VIN`, `MEDICAL_NPI_US`, `SIN_CA`, `DNI_ES`, `NIE_ES`, `RESIDENT_ID_CN`, `AADHAAR_IN`, `CPF_BR`, `CODICE_FISCALE_IT`, `PESEL_PL`.

## Filter used by the anonymizer

`pdf-anonymizer-core` still imports `filter_regex_patterns` from this package. `None` or an empty list means the full map, which matches the historical CLI default.

## Version

`id-extract` versions independently of `pdf-anonymizer-*`. This documentation describes the package as published from this monorepo.
