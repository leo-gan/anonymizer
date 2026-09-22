"""State, provincial, and industry identifiers.

These patterns stay out of the default country map. Pass ``opt_in`` to
``extract`` or ``patterns``. ``"all"`` loads the selective rows. A bare
digit run is available only when its key is named.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, NamedTuple, Optional, Union


class OptInId(NamedTuple):
    key: str
    pattern: str
    countries: frozenset[str]
    selective: bool


def _id(
    key: str,
    pattern: str,
    countries: str,
    *,
    selective: bool,
) -> OptInId:
    return OptInId(key, pattern, frozenset(countries.split()), selective)


# Last two Ontario licence digits are 01-31.
_ON_DAY = "(?:0[1-9]|[12]\\d|3[01])"

OPT_IN_IDS: tuple[OptInId, ...] = (
    _id(
        "RTN_US",
        "\\b(?:0\\d|1[0-2]|2[1-9]|3[0-2]|6[1-9]|7[0-2]|80)\\d{7}\\b",
        "US",
        selective=True,
    ),
    _id(
        "CUSIP_NNA",
        "\\b[0-9A-Z]{8}[0-9]\\b",
        "US CA",
        selective=True,
    ),
    _id(
        "FFL_US",
        "\\b\\d-\\d{2}-\\d{3}-\\d{2}-[A-Z0-9]{2}-\\d{5}\\b",
        "US",
        selective=True,
    ),
    _id(
        "N_NUMBER_US",
        "\\b(?:N[1-9]\\d{0,4}|N[1-9]\\d{0,3}[A-HJ-NP-Z]|N[1-9]\\d{0,2}[A-HJ-NP-Z]{2})\\b",
        "US",
        selective=True,
    ),
    _id(
        "HIN_US",
        "\\b[A-Z0-9]{3}[A-HJ-NPR-Z0-9]{5}[A-L][0-9]{3}\\b",
        "US",
        selective=True,
    ),
    _id(
        "DL_FL_US",
        "\\b[A-Z](?:\\d{12}|\\d{3}-\\d{3}-\\d{2}-\\d{3}-\\d)\\b",
        "US",
        selective=True,
    ),
    _id(
        "EDD_PAYROLL_US",
        "\\b\\d{3}-\\d{4}-\\d\\b",
        "US",
        selective=True,
    ),
    _id("LICENSE_IL_US", "\\b\\d{9}\\b", "US", selective=False),
    _id("UEI_US", "\\b[A-Z0-9]{12}\\b", "US", selective=False),
    _id("TAXONOMY_US", "\\b[A-Z0-9]{10}\\b", "US", selective=False),
    _id("I94_US", "\\b\\d{11}\\b", "US", selective=False),
    _id("NAM_QC_CA", "\\b[A-Z]{4}\\d{8}\\b", "CA", selective=True),
    _id(
        "TVQ_QC_CA",
        "\\b\\d{10}\\s?(?:TQ|NR)\\s?\\d{4}\\b",
        "CA",
        selective=True,
    ),
    _id(
        "DL_ON_CA",
        "\\b[A-Z]\\d{4}-?\\d{5}-?\\d{3}" + _ON_DAY + "\\b",
        "CA",
        selective=True,
    ),
    _id(
        "HEALTH_ON_CA",
        "\\b[1-9]\\d{9}[A-Z]{2}\\b",
        "CA",
        selective=True,
    ),
    _id("PHN_BC_CA", "\\b9\\d{9}\\b", "CA", selective=True),
    _id("NEQ_QC_CA", "\\b(?:11|22|33|88)\\d{8}\\b", "CA", selective=True),
    _id("HEALTH_NT_CA", "\\b[A-Z]\\d{7}\\b", "CA", selective=True),
    _id("HEALTH_CF_CA", "\\b[A-Z]\\d{8}\\b", "CA", selective=True),
    _id("HEALTH_AB_CA", "\\b\\d{9}\\b", "CA", selective=False),
    _id("HEALTH_MB_CA", "\\b\\d{9}\\b", "CA", selective=False),
    _id("HEALTH_NB_CA", "\\b\\d{9}\\b", "CA", selective=False),
    _id("HEALTH_NU_CA", "\\b\\d{9}\\b", "CA", selective=False),
    _id("HEALTH_SK_CA", "\\b\\d{9}\\b", "CA", selective=False),
    _id("HEALTH_YT_CA", "\\b\\d{9}\\b", "CA", selective=False),
    _id("HEALTH_NL_CA", "\\b\\d{12}\\b", "CA", selective=False),
    _id("HEALTH_NS_CA", "\\b\\d{10}\\b", "CA", selective=False),
    _id("HEALTH_PE_CA", "\\b\\d{8,9}\\b", "CA", selective=False),
    _id(
        "FOLIO_FISCAL_MX",
        "\\b[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}\\b",
        "MX",
        selective=True,
    ),
    _id("OCR_INE_MX", "\\b\\d{12,13}\\b", "MX", selective=False),
    _id("REGISTRO_PATRONAL_MX", "\\b[A-Z0-9]{11}\\b", "MX", selective=False),
)

_BY_KEY: Dict[str, OptInId] = {item.key: item for item in OPT_IN_IDS}

OptInArg = Optional[Union[bool, str, Iterable[str]]]


def available_opt_in() -> List[str]:
    """Every opt-in key, selective and broad."""
    return sorted(_BY_KEY)


def opt_in_patterns(
    opt_in: OptInArg,
    countries: Optional[frozenset[str]],
) -> Dict[str, str]:
    """Resolve ``opt_in`` to a pattern map.

    ``countries`` is the caller's ISO-2 filter. ``None`` means every country.
    Named keys are returned even when their country is outside that filter.
    ``"all"`` returns only selective keys for the selected countries.
    """
    if opt_in is None or opt_in is False:
        return {}
    named = _named_keys(opt_in)
    if named == []:
        return {}
    if named is None:
        chosen = [
            item
            for item in OPT_IN_IDS
            if item.selective and _country_ok(item, countries)
        ]
    else:
        unknown = [key for key in named if key not in _BY_KEY]
        if unknown:
            raise ValueError(
                "Unknown opt-in key(s): "
                + ", ".join(unknown)
                + ". Use available_opt_in() or 'all'."
            )
        chosen = [_BY_KEY[key] for key in named]
    return {item.key: item.pattern for item in chosen}


def _country_ok(item: OptInId, countries: Optional[frozenset[str]]) -> bool:
    if countries is None:
        return True
    return not item.countries.isdisjoint(countries)


def _named_keys(opt_in: Union[bool, str, Iterable[str]]) -> Optional[List[str]]:
    """Return named keys, or None when the caller asked for the selective set."""
    if opt_in is True:
        return None
    if isinstance(opt_in, str):
        parts = [part.strip().upper() for part in opt_in.split(",") if part.strip()]
        if not parts or "ALL" in parts:
            return None
        return parts
    parts = [str(key).strip().upper() for key in opt_in if str(key).strip()]
    if not parts:
        return []
    if "ALL" in parts:
        return None
    return parts
