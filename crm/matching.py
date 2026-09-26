"""Patient cross-reference matching between LiveClin and WebDiet systems."""

import unicodedata
from dataclasses import dataclass


@dataclass
class SourceRecord:
    """A record from one of the source systems (LiveClin or WebDiet)."""
    name: str
    phone: str | None
    birthdate: str | None
    email: str | None
    raw: dict


@dataclass
class MatchResult:
    """Result of a successful match between two patient records."""
    liveclin: SourceRecord
    webdiet: SourceRecord
    matched_field: str


def normalize_name(name: str) -> str:
    """
    Normalize a patient name for comparison.

    - Strip whitespace
    - Collapse internal whitespace to single spaces
    - Convert to lowercase
    - Remove accents using NFKD normalization
    """
    if not name:
        return ""

    # Strip and collapse whitespace
    name = " ".join(name.split())

    # Convert to lowercase
    name = name.lower()

    # Remove accents: NFKD normalize, then remove combining marks
    name_nfkd = unicodedata.normalize("NFKD", name)
    name_no_accents = "".join(
        c for c in name_nfkd if not unicodedata.combining(c)
    )

    return name_no_accents


def normalize_phone(phone: str | None) -> str | None:
    """
    Normalize a phone number for comparison.

    - Return None if phone is falsy
    - Keep only digit characters
    - Return None if result is empty
    """
    if not phone:
        return None

    digits = "".join(c for c in phone if c.isdigit())
    return digits if digits else None


def _group_by_normalized(records, field, normalize):
    """
    Group records by their normalized field value.

    Only includes records with non-empty normalized values.
    Returns a dict mapping normalized value -> list of records.
    """
    groups: dict[str, list[SourceRecord]] = {}
    for r in records:
        value = normalize(getattr(r, field))
        if value:  # None or "" never counts as a matching value
            groups.setdefault(value, []).append(r)
    return groups


def _match_by_field(lc_list, wd_list, field):
    """
    Match records from two lists by a specific normalized field.

    Only matches records when exactly one record on each side
    shares the normalized, non-empty value for that field.

    Returns:
        (matched_list, remaining_lc, remaining_wd)
    """
    normalizers = {
        "name": normalize_name,
        "phone": normalize_phone,
        "birthdate": lambda v: v.strip() if v else None,
        "email": lambda v: v.strip().lower() if v else None,
    }

    normalize = normalizers[field]

    # Group each side by normalized value, dropping None/empty values
    lc_by_value = _group_by_normalized(lc_list, field, normalize)
    wd_by_value = _group_by_normalized(wd_list, field, normalize)

    matched, matched_lc_ids, matched_wd_ids = [], set(), set()
    for value, lc_group in lc_by_value.items():
        wd_group = wd_by_value.get(value)
        # Confident match only when exactly one record on each side
        # shares this normalized, non-empty value
        if wd_group and len(lc_group) == 1 and len(wd_group) == 1:
            matched.append(MatchResult(lc_group[0], wd_group[0], field))
            matched_lc_ids.add(id(lc_group[0]))
            matched_wd_ids.add(id(wd_group[0]))

    remaining_lc = [r for r in lc_list if id(r) not in matched_lc_ids]
    remaining_wd = [r for r in wd_list if id(r) not in matched_wd_ids]
    return matched, remaining_lc, remaining_wd


def match_patients(liveclin, webdiet):
    """
    Match patients between LiveClin and WebDiet systems using cascading strategy.

    Cascades through fields in order: name -> phone -> birthdate -> email.
    For each field, matches are only made when exactly one record on each side
    shares the normalized value.

    Args:
        liveclin: list of SourceRecord from LiveClin
        webdiet: list of SourceRecord from WebDiet

    Returns:
        (matches, unmatched_liveclin, unmatched_webdiet)
        where matches is a list of MatchResult objects
    """
    FIELDS_IN_ORDER = ["name", "phone", "birthdate", "email"]

    remaining_lc, remaining_wd = list(liveclin), list(webdiet)
    matches = []

    for field in FIELDS_IN_ORDER:
        found, remaining_lc, remaining_wd = _match_by_field(
            remaining_lc, remaining_wd, field
        )
        matches.extend(found)

    return matches, remaining_lc, remaining_wd
