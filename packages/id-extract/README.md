# id-extract

Find structured identifiers in text. This package returns character offsets. It does not replace values or open files.

```bash
pip install id-extract
```

```python
from id_extract import extract

for hit in extract("ABN 51 824 753 556 and ada@example.com"):
    print(hit["type"], hit["text"], hit["start"], hit["end"])
```

The default is every bundled country. Narrow the set with `countries=["AU", "GB"]`. `UK` is accepted as `GB`.

Full guide, including one page per country with official sources:

- [id-extract overview](https://leo-gan.github.io/anonymizer/id-extract/)
- [Install and API](https://leo-gan.github.io/anonymizer/id-extract/api/)
- [Country catalog](https://leo-gan.github.io/anonymizer/id-extract/countries/)
- Example: [Australia (ABN, TFN)](https://leo-gan.github.io/anonymizer/id-extract/countries/au/)

A hit means the text looked like that identifier. It is not a legal determination.
