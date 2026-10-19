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
    - Strip the Brazilian country code (DDI "55") when present: Brazilian
      numbers have 10 (landline) or 11 (mobile) digits without DDI, so a
      result longer than 11 digits starting with "55" has the prefix removed
    - Return None if result is empty
    """
    if not phone:
        return None

    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) > 11 and digits.startswith("55"):
        digits = digits[2:]
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


def _normalizers():
    return {
        "name": normalize_name,
        "phone": normalize_phone,
        "birthdate": lambda v: v.strip() if v else None,
        "email": lambda v: v.strip().lower() if v else None,
    }


def _match_by_field(lc_list, wd_list, field):
    """
    Match records from two lists by a specific normalized field.

    Only matches records when exactly one record on each side
    shares the normalized, non-empty value for that field. A value shared by
    three or more records overall (2+ on either side) is ambiguous and never
    matches on this field.

    Returns:
        (matched_list, remaining_lc, remaining_wd)
    """
    normalize = _normalizers()[field]

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


def _agreeing_fields(lc, wd, fields):
    """Return the fields (in order) whose normalized, non-empty values agree."""
    normalizers = _normalizers()
    agreeing = []
    for field in fields:
        normalize = normalizers[field]
        a = normalize(getattr(lc, field))
        b = normalize(getattr(wd, field))
        if a and b and a == b:
            agreeing.append(field)
    return agreeing


def _match_by_multiple_fields(lc_list, wd_list, fields, min_agreeing):
    """
    Match records whose names did not resolve to any candidate.

    A pair (lc, wd) qualifies only when at least `min_agreeing` of `fields`
    agree between the two records. A pair is confirmed only when it is the
    single qualifying pair for both its lc record and its wd record; anything
    else is ambiguous and left unmatched.

    The recorded matched_field is the agreeing fields joined by "+"
    (e.g. "phone+birthdate").
    """
    qualifying = []
    for lc in lc_list:
        for wd in wd_list:
            agreeing = _agreeing_fields(lc, wd, fields)
            if len(agreeing) >= min_agreeing:
                qualifying.append((lc, wd, agreeing))

    lc_counts: dict[int, int] = {}
    wd_counts: dict[int, int] = {}
    for lc, wd, _ in qualifying:
        lc_counts[id(lc)] = lc_counts.get(id(lc), 0) + 1
        wd_counts[id(wd)] = wd_counts.get(id(wd), 0) + 1

    matched, matched_lc_ids, matched_wd_ids = [], set(), set()
    for lc, wd, agreeing in qualifying:
        if lc_counts[id(lc)] == 1 and wd_counts[id(wd)] == 1:
            matched.append(MatchResult(lc, wd, "+".join(agreeing)))
            matched_lc_ids.add(id(lc))
            matched_wd_ids.add(id(wd))

    remaining_lc = [r for r in lc_list if id(r) not in matched_lc_ids]
    remaining_wd = [r for r in wd_list if id(r) not in matched_wd_ids]
    return matched, remaining_lc, remaining_wd


def match_patients(liveclin, webdiet):
    """
    Match patients between LiveClin and WebDiet systems.

    1. Name: records whose normalized name is unique on both sides match
       directly (matched_field "name").
    2. Duplicated/ambiguous name (the name has candidates on the other side,
       but not exactly one on each side, e.g. father and son with the same
       name): among the records sharing that name only, cascade
       phone -> birthdate -> email, where a single field is enough to break
       the tie (exactly one record on each side must share the value).
    3. Name resolved to no candidate (or the record was left over from an
       ambiguous name group): a cross-name match is confirmed only when at
       least TWO of phone, birthdate and email agree between the same pair of
       records, and that pair is unique for both records. A single weak field
       (e.g. only the birthdate) never links records with different names.

    Records that remain are returned as unmatched.

    Args:
        liveclin: list of SourceRecord from LiveClin
        webdiet: list of SourceRecord from WebDiet

    Returns:
        (matches, unmatched_liveclin, unmatched_webdiet)
        where matches is a list of MatchResult objects
    """
    TIEBREAK_FIELDS = ["phone", "birthdate", "email"]
    MIN_AGREEING_FIELDS_WITHOUT_NAME = 2

    # Step 1: unique name on both sides
    matches, remaining_lc, remaining_wd = _match_by_field(
        list(liveclin), list(webdiet), "name"
    )

    # Step 2: ambiguous name groups, tie-broken by a single field within the group
    lc_by_name = _group_by_normalized(remaining_lc, "name", normalize_name)
    wd_by_name = _group_by_normalized(remaining_wd, "name", normalize_name)
    matched_ids: set[int] = set()
    for name, lc_group in lc_by_name.items():
        wd_group = wd_by_name.get(name)
        if not wd_group:
            continue  # name has no candidate on the other side -> step 3
        group_lc, group_wd = lc_group, wd_group
        for field in TIEBREAK_FIELDS:
            found, group_lc, group_wd = _match_by_field(group_lc, group_wd, field)
            for m in found:
                matches.append(m)
                matched_ids.add(id(m.liveclin))
                matched_ids.add(id(m.webdiet))

    remaining_lc = [r for r in remaining_lc if id(r) not in matched_ids]
    remaining_wd = [r for r in remaining_wd if id(r) not in matched_ids]

    # Step 3: no name candidate -> require 2+ agreeing fields on the same pair
    found, remaining_lc, remaining_wd = _match_by_multiple_fields(
        remaining_lc,
        remaining_wd,
        TIEBREAK_FIELDS,
        MIN_AGREEING_FIELDS_WITHOUT_NAME,
    )
    matches.extend(found)

    return matches, remaining_lc, remaining_wd
