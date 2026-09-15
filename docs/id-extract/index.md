# id-extract

`id-extract` finds structured identifiers in text. It returns character offsets. It does not replace text, write a mapping, or open files.

Install it on its own:

```bash
pip install id-extract
```

Then:

```python
from id_extract import extract

hits = extract("Card 4111111111111111 and TFN 123 456 789")
for hit in hits:
    print(hit["type"], hit["text"], hit["start"], hit["end"])
```

The default is every bundled country plus the universal patterns (email, cards, IBAN, and the rest). Narrow the set at call time:

```python
extract(text, countries=["AU", "GB"])
extract(text, countries="all")          # same as the default
extract(text, countries=["UK"])         # UK is accepted as GB
```

CLI users of the anonymizer pass the same filter as `--countries AU,GB`.

## What this package is

The detector is a RE2 regular-expression pass plus a few cheap checksums (Luhn for cards, ISO 13616 mod-97 for IBAN, and a short list of national checks). A match that fails its checksum is kept and labeled `TYPE_LIKE` (for example `IBAN_LIKE`) so a mistyped number is still found.

It is not a legal determination. A hit means the text looked like that identifier. It does not mean the number was issued, is still valid, or that a cited statute applies to the document.

## Independent of the anonymizer

You do not need `pdf-anonymizer-core` to use this package. The anonymizer depends on `id-extract` for its first stage. Replacement, mapping, and file I/O stay in the anonymizer.

| Need | Use |
|---|---|
| Find IDs in a string | `id_extract.extract` |
| List bundled countries | `id_extract.available_countries()` |
| Get the RE2 map | `id_extract.patterns(countries=["AU"])` |
| Hide the values in a file | `pdf-anonymizer-cli` |

## Pages in this guide

- [Install and API](api.md)
- [Universal identifiers](universal.md) (email, cards, IBAN, VIN, …)
- [Country catalog](countries/index.md) — one page per ISO-2 plugin

Each country page names the identifier, the type key the package emits, the shape it looks for, a synthetic example, whether a checksum runs, and links to the issuing agency or the statute that defines it.

## Honesty

The country pages cite official sources so you can see what the identifier *is*. The regex is a structural approximation. Driver-licence patterns in particular are broad and will match other tokens. Do not treat a hit as evidence for a regulator.
