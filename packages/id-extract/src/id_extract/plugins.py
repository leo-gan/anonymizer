"""Country plugins and pattern filtering.

National-ID patterns are selected at call time with ``countries=``, not at
install time. ``pip install id-extract`` always ships every bundled country.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, Iterable, List, Optional, Tuple

from id_extract import countries as countries_pkg

# ISO-2 suffixes used on country-specific keys (SSN_US, NINO_GB, PESEL_PL, ...).
COUNTRY_PATTERN_SUFFIXES: frozenset[str] = frozenset(
    {
        "US",
        "CA",
        "GB",
        "FR",
        "ES",
        "IT",
        "IN",
        "CN",
        "DE",
        "JP",
        "KR",
        "AU",
        "NZ",
        "BR",
        "MX",
        "AR",
        "ZA",
        "SG",
        "HK",
        "TW",
        "NL",
        "BE",
        "CH",
        "AT",
        "SE",
        "NO",
        "DK",
        "FI",
        "PL",
        "IE",
        "PT",
        "GR",
        "IL",
        "TR",
        "RU",
        "TH",
        "MY",
        "ID",
    }
)

# Caller aliases. Internal country code stays ISO-2.
COUNTRY_ALIASES: Dict[str, str] = {
    "UK": "GB",
}

# Keys with no suffix that still belong to one country.
_PATTERN_COUNTRY_ALIASES: Dict[str, str] = {
    "SSN": "US",
}


def normalize_country(code: str) -> str:
    """Upper-case an ISO-2 code and apply aliases (``UK`` -> ``GB``)."""
    upper = str(code).strip().upper()
    return COUNTRY_ALIASES.get(upper, upper)


def pattern_country(key: str) -> Optional[str]:
    """Return the ISO-2 country for a pattern key, or None if it is universal."""
    upper = key.upper()
    if upper in _PATTERN_COUNTRY_ALIASES:
        return _PATTERN_COUNTRY_ALIASES[upper]
    suffix = upper.rsplit("_", 1)[-1]
    if suffix in COUNTRY_PATTERN_SUFFIXES:
        return suffix
    return None


_PLUGIN_CACHE: Optional[Tuple[Dict[str, str], Dict[str, Dict[str, str]]]] = None


def _load_builtin_plugins() -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
    global _PLUGIN_CACHE
    if _PLUGIN_CACHE is not None:
        return _PLUGIN_CACHE
    universal: Dict[str, str] = {}
    by_country: Dict[str, Dict[str, str]] = {}
    for info in pkgutil.iter_modules(countries_pkg.__path__):
        mod = importlib.import_module(f"id_extract.countries.{info.name}")
        loaded = getattr(mod, "PATTERNS", None)
        if not isinstance(loaded, dict):
            continue
        code = getattr(mod, "CODE", None)
        if code is None or str(code).upper() == "UNIVERSAL":
            universal.update(loaded)
            continue
        by_country[str(code).upper()] = dict(loaded)
    _PLUGIN_CACHE = (universal, by_country)
    return _PLUGIN_CACHE


def available_countries() -> List[str]:
    """ISO-2 codes that have a bundled national-ID plugin."""
    _universal, by_country = _load_builtin_plugins()
    return sorted(by_country)


def resolve_countries(
    countries: Optional[Iterable[str] | str] = "all",
) -> Optional[frozenset[str]]:
    """Normalize a countries argument.

    ``None``, ``\"all\"``, or an empty list means every bundled national-ID
    plugin (plus universals). Otherwise return the requested ISO-2 set.
    """
    if countries is None:
        return None
    if isinstance(countries, str):
        if countries.strip().lower() == "all":
            return None
        wanted = {normalize_country(countries)}
    else:
        wanted = {normalize_country(code) for code in countries if str(code).strip()}
        if not wanted or any(code == "ALL" for code in wanted):
            return None

    unknown = sorted(code for code in wanted if code not in COUNTRY_PATTERN_SUFFIXES)
    if unknown:
        raise ValueError(
            "Unknown country code(s): "
            + ", ".join(unknown)
            + ". Use ISO-2 codes such as US, GB, FR (UK is accepted as GB)."
        )
    return frozenset(wanted)


def patterns(
    countries: Optional[Iterable[str] | str] = "all",
    source: Optional[Dict[str, str]] = None,
    *,
    opt_in: Optional[Iterable[str] | str | bool] = None,
) -> Dict[str, str]:
    """Return universal patterns plus national-ID patterns for ``countries``.

    The default ``countries=\"all\"`` is the full bundled map. Universal keys
    (EMAIL, IBAN, CREDIT_CARD, VIN, ...) always stay. ``opt_in`` adds state,
    provincial, and industry patterns. It defaults to none.
    """
    from id_extract.opt_in import opt_in_patterns

    wanted = resolve_countries(countries)
    if source is None:
        universal, by_country = _load_builtin_plugins()
        merged = dict(universal)
        if wanted is None:
            for extra in by_country.values():
                merged.update(extra)
        else:
            for code in wanted:
                merged.update(by_country.get(code, {}))
    elif wanted is None:
        merged = dict(source)
    else:
        merged = {}
        for key, pattern in source.items():
            country = pattern_country(key)
            if country is None or country in wanted:
                merged[key] = pattern
    merged.update(opt_in_patterns(opt_in, wanted))
    return merged


def filter_regex_patterns(
    countries: Optional[Iterable[str]] = None,
    patterns: Optional[Dict[str, str]] = None,
    *,
    opt_in: Optional[Iterable[str] | str | bool] = None,
) -> Dict[str, str]:
    """Compatibility wrapper used by ``pdf_anonymizer_core.conf``.

    ``None`` or an empty list returns the full national map, matching the
    historical ``filter_regex_patterns`` contract. Opt-in patterns stay out
    unless ``opt_in`` is set.
    """
    if not countries:
        wanted: Optional[Iterable[str] | str] = "all"
    else:
        wanted = countries
    return globals()["patterns"](countries=wanted, source=patterns, opt_in=opt_in)
