from datetime import date
from crm.renewal import get_renewal_candidates


def _plan(name, end_date, contracted=3, used=1, plan_type="mensal"):
    return {
        "patient_name": name, "plan_type": plan_type, "end_date": end_date,
        "contracted_sessions": contracted, "used_sessions": used,
    }


def test_plan_ending_tomorrow_is_a_candidate():
    today = date(2026, 9, 26)
    plans = [_plan("Arthur Fonseca", "2026-09-27")]
    result = get_renewal_candidates(plans, today)
    assert len(result) == 1
    assert result[0].patient_name == "Arthur Fonseca"
    assert result[0].days_until_due == 1


def test_plan_with_all_sessions_used_is_candidate_even_if_end_date_is_far():
    today = date(2026, 9, 26)
    plans = [_plan("Renan Costa Rego", "2026-11-07", contracted=10, used=10)]
    result = get_renewal_candidates(plans, today)
    assert len(result) == 1
    assert result[0].patient_name == "Renan Costa Rego"


def test_plan_far_from_end_with_sessions_remaining_is_not_a_candidate():
    today = date(2026, 9, 26)
    plans = [_plan("Lais Sales", "2026-12-25", contracted=3, used=1)]
    result = get_renewal_candidates(plans, today)
    assert result == []


def test_plan_with_zero_or_none_contracted_sessions_does_not_crash():
    today = date(2026, 9, 26)
    plans = [
        _plan("Sem Contrato A", "2026-12-25", contracted=0, used=0),
        _plan("Sem Contrato B", "2026-12-25", contracted=None, used=None),
    ]
    result = get_renewal_candidates(plans, today)  # must not raise
    assert result == []


def test_candidates_sorted_by_end_date_ascending():
    today = date(2026, 9, 26)
    plans = [
        _plan("Joao Minosso", "2026-10-17"),
        _plan("Arthur Fonseca", "2026-09-27"),
        _plan("Gabriel Tondello", "2026-10-03"),
    ]
    result = get_renewal_candidates(plans, today)
    assert [c.patient_name for c in result] == [
        "Arthur Fonseca", "Gabriel Tondello", "Joao Minosso",
    ]
