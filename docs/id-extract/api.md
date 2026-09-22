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

extract(text, patterns=None, *, countries="all", opt_in=None) -> list[Entity]
```

| Argument | Meaning |
|---|---|
| `text` | The string to scan. Offsets are indexes in this string. |
| `patterns` | Optional RE2 map. When given, `countries` is ignored. |
| `countries` | `"all"` (default), one ISO-2 code, or a list. `UK` is treated as `GB`. |
| `opt_in` | `None` (default) loads no state, provincial, or industry pattern. `"all"` or `True` loads every selective one for the selected countries. A list of keys loads those keys, including broad digit-only patterns. |

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
patterns(countries=["US"], opt_in="all")
patterns(opt_in=["LICENSE_IL_US"])    # one broad key, not in "all"
```

`available_opt_in()` lists every opt-in key. The [opt-in catalog](opt-in-us-ca-mx.md) says which keys `"all"` includes.

Universal keys (email, cards, IBAN, …) are always included when you load a country subset.

## Checksums

After a match, a registered extra-digit check may run. For most types a failure does not drop the hit. The type is renamed with the `_LIKE` suffix. Four types drop a failed check instead, because the shape alone is a common digit run.

Types with a check today: `CREDIT_CARD`, `IBAN`, `VIN`, `MEDICAL_NPI_US`, `SIN_CA`, `DNI_ES`, `NIE_ES`, `RESIDENT_ID_CN`, `AADHAAR_IN`, `CPF_BR`, `CODICE_FISCALE_IT`, `PESEL_PL`, `RTN_US`, `CUSIP_NNA`, `PHN_BC_CA`, `CLABE_MX`.

`RTN_US`, `CUSIP_NNA`, `PHN_BC_CA`, and `CLABE_MX` drop a failed check. The other checked types keep the hit and add `_LIKE`.

## Filter used by the anonymizer

`pdf-anonymizer-core` still imports `filter_regex_patterns` from this package. `None` or an empty list means the full map, which matches the historical CLI default.

## Version

`id-extract` versions independently of `pdf-anonymizer-*`. This documentation describes the package as published from this monorepo.
