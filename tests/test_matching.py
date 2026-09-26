"""Tests for patient matching algorithm."""

from crm.matching import SourceRecord, match_patients


def _rec(name, phone=None, birthdate=None, email=None):
    """Helper to create a SourceRecord for testing."""
    return SourceRecord(name=name, phone=phone, birthdate=birthdate, email=email, raw={})


def test_matches_by_name_when_unique_on_both_sides():
    """Test matching by name when the name is unique on both sides."""
    lc = [_rec("Beto Guerra", phone="11911112222")]
    wd = [_rec("Beto Guerra", phone="11933334444")]  # phone differs, name still resolves it
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert len(matches) == 1
    assert matches[0].matched_field == "name"
    assert unmatched_lc == []
    assert unmatched_wd == []


def test_falls_back_to_phone_when_name_is_duplicated():
    """Test falling back to phone when names are duplicated."""
    lc = [
        _rec("Arthur Fonseca", phone="11911110000"),  # pai
        _rec("Arthur Fonseca", phone="11922220000"),  # filho
    ]
    wd = [
        _rec("Arthur Fonseca", phone="11922220000"),  # filho
        _rec("Arthur Fonseca", phone="11911110000"),  # pai
    ]
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert len(matches) == 2
    assert all(m.matched_field == "phone" for m in matches)
    assert {m.liveclin.phone for m in matches} == {"11911110000", "11922220000"}
    for m in matches:
        assert m.liveclin.phone == m.webdiet.phone


def test_falls_back_to_birthdate_when_name_and_phone_dont_resolve():
    """Test falling back to birthdate when name and phone don't resolve."""
    lc = [_rec("Maria Silva", phone=None, birthdate="1985-05-20")]
    wd = [_rec("Maria Silva", phone=None, birthdate="1985-05-20")]
    # duplicate name on lc side forces fallback past "name"
    lc.append(_rec("Maria Silva", phone=None, birthdate="1992-01-01"))
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert len(matches) == 1
    assert matches[0].matched_field == "birthdate"
    assert matches[0].liveclin.birthdate == "1985-05-20"


def test_missing_field_on_both_sides_never_counts_as_a_match():
    """Test that missing fields never cause matches."""
    lc = [_rec("Paciente A", phone=None, birthdate=None, email=None)]
    lc.append(_rec("Paciente B", phone=None, birthdate=None, email=None))
    wd = [_rec("Paciente C", phone=None, birthdate=None, email=None)]
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert matches == []
    assert len(unmatched_lc) == 2
    assert len(unmatched_wd) == 1


def test_patient_present_in_only_one_system_is_unmatched_not_dropped():
    """Test that patients in only one system are preserved as unmatched."""
    lc = [_rec("Georges Jean Paul", phone="11955556666")]
    wd = []
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert matches == []
    assert unmatched_lc == lc
    assert unmatched_wd == []
