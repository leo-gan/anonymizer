"""Extract structured identifiers with RE2 and checksums.

This package finds placements. It does not replace text, build a mapping,
or open files. Documentation lives in the anonymizer monorepo
(https://leo-gan.github.io/anonymizer/).
"""

from id_extract.extract import extract
from id_extract.opt_in import available_opt_in
from id_extract.plugins import (
    available_countries,
    filter_regex_patterns,
    pattern_country,
    patterns,
)
from id_extract.types import Entity

__all__ = [
    "Entity",
    "available_countries",
    "available_opt_in",
    "extract",
    "filter_regex_patterns",
    "pattern_country",
    "patterns",
]
