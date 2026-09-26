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


# --- fix wave: phone normalization (finding 2) ---

from crm.matching import normalize_phone


def test_normalize_phone_strips_brazilian_country_code():
    assert normalize_phone("+55 (11) 91111-2222") == normalize_phone("(11) 91111-2222")
    assert normalize_phone("+55 (11) 91111-2222") == "11911112222"
    assert normalize_phone("55 11 3333-4444") == "1133334444"  # fixo com DDI


def test_normalize_phone_keeps_numbers_without_country_code():
    # DDD 55 (RS) sem DDI: 11 dígitos, não pode perder o "55"
    assert normalize_phone("(55) 99999-8888") == "55999998888"
    assert normalize_phone("(55) 3222-1111") == "5532221111"


# --- fix wave: cross-name matching needs 2+ fields (finding 3) ---

def test_different_names_sharing_only_birthdate_do_not_match():
    lc = [_rec("Carla Mendes", phone="11911111111", birthdate="1990-04-04")]
    wd = [_rec("Paula Ribeiro", phone="11922222222", birthdate="1990-04-04")]
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert matches == []
    assert unmatched_lc == lc
    assert unmatched_wd == wd


def test_different_names_sharing_only_phone_do_not_match():
    lc = [_rec("Carla Mendes", phone="11911111111", birthdate="1990-04-04")]
    wd = [_rec("Paula Ribeiro", phone="11911111111", birthdate="1971-01-01")]
    matches, _, _ = match_patients(lc, wd)
    assert matches == []


def test_different_names_sharing_phone_and_birthdate_do_match():
    lc = [_rec("Carla Mendes", phone="11911111111", birthdate="1990-04-04")]
    wd = [_rec("Carla M. Souza", phone="(11) 91111-1111", birthdate="1990-04-04")]
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert len(matches) == 1
    assert matches[0].matched_field == "phone+birthdate"
    assert unmatched_lc == []
    assert unmatched_wd == []


def test_cross_name_two_field_match_must_be_unique_on_both_sides():
    lc = [_rec("Carla Mendes", phone="11911111111", birthdate="1990-04-04")]
    wd = [
        _rec("Carla M.", phone="11911111111", birthdate="1990-04-04"),
        _rec("C. Mendes", phone="11911111111", birthdate="1990-04-04"),
    ]
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert matches == []
    assert len(unmatched_lc) == 1
    assert len(unmatched_wd) == 2


# --- fix wave: missing tests (finding 7) ---

def test_name_normalization_matches_accents_case_and_spaces():
    lc = [_rec("  JOÃO   da  Silva ", phone="11911110000")]
    wd = [_rec("Joao da silva", phone="11988887777")]
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert len(matches) == 1
    assert matches[0].matched_field == "name"
    assert unmatched_lc == []
    assert unmatched_wd == []


def test_falls_back_to_email_when_name_phone_and_birthdate_dont_resolve():
    lc = [
        _rec("Lucas Prado", phone="11900000000", birthdate="2000-01-01", email="lucas.pai@x.com"),
        _rec("Lucas Prado", phone="11900000000", birthdate="2000-01-01", email="Lucas.Filho@x.com"),
    ]
    wd = [
        _rec("Lucas Prado", phone=None, birthdate=None, email=" lucas.filho@x.com "),
    ]
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert len(matches) == 1
    assert matches[0].matched_field == "email"
    assert matches[0].liveclin.email == "Lucas.Filho@x.com"
    assert [r.email for r in unmatched_lc] == ["lucas.pai@x.com"]
    assert unmatched_wd == []


def test_phone_match_with_different_formatting_and_country_code():
    lc = [
        _rec("Beto Guerra", phone="11911112222"),
        _rec("Beto Guerra", phone="11933334444"),
    ]
    wd = [_rec("Beto Guerra", phone="+55 (11) 91111-2222")]
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert len(matches) == 1
    assert matches[0].matched_field == "phone"
    assert matches[0].liveclin.phone == "11911112222"
    assert [r.phone for r in unmatched_lc] == ["11933334444"]
    assert unmatched_wd == []


def test_three_records_sharing_a_value_are_ambiguous_and_fall_through():
    # 3 registros com o mesmo nome E o mesmo telefone (telefone da família):
    # nome ambíguo, telefone ambíguo -> segue para nascimento, que resolve.
    lc = [
        _rec("Ana Souza", phone="11955550000", birthdate="1970-02-02"),
        _rec("Ana Souza", phone="11955550000", birthdate="1999-09-09"),
    ]
    wd = [_rec("Ana Souza", phone="(11) 95555-0000", birthdate="1999-09-09")]
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert len(matches) == 1
    assert matches[0].matched_field == "birthdate"
    assert matches[0].liveclin.birthdate == "1999-09-09"
    assert [r.birthdate for r in unmatched_lc] == ["1970-02-02"]
    assert unmatched_wd == []


def test_three_records_sharing_a_value_with_no_other_field_stay_unmatched():
    lc = [
        _rec("Ana Souza", phone="11955550000"),
        _rec("Ana Souza", phone="11955550000"),
    ]
    wd = [_rec("Ana Souza", phone="11955550000")]
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert matches == []
    assert len(unmatched_lc) == 2
    assert len(unmatched_wd) == 1
