from datetime import date

from crm import db
from crm.cli import run_update


def test_run_update_matches_persists_and_returns_candidates(tmp_path):
    conn = db.init_db(str(tmp_path / "test.db"))
    liveclin_raw = [{
        "name": "Arthur Fonseca", "phone": "11911110000", "birthdate": "1980-01-01",
        "plan_type": "mensal", "start_date": "2026-08-27", "end_date": "2026-09-27",
        "contracted_sessions": 1, "used_sessions": 1, "modality": "presencial",
        "service": "dieta", "price": 250.0,
    }]
    webdiet_raw = [{
        "name": "Arthur Fonseca", "phone": "11911110000", "birthdate": "1980-01-01",
        "email": None, "modality": "presencial", "diet_status": "ativo",
    }]
    result = run_update(liveclin_raw, webdiet_raw, conn, today=date(2026, 9, 26))
    assert len(result.candidates) == 1
    assert result.candidates[0].patient_name == "Arthur Fonseca"
    assert result.unmatched_liveclin == []
    assert result.unmatched_webdiet == []


def test_run_update_skips_a_bad_record_without_aborting(tmp_path, capsys):
    conn = db.init_db(str(tmp_path / "test.db"))
    liveclin_raw = [
        {"phone": "11900000000"},  # missing "name" -> parse_patient raises KeyError
        {
            "name": "Beto Guerra", "phone": "11922223333", "birthdate": "1988-03-10",
            "plan_type": "mensal", "start_date": "2026-08-16", "end_date": "2026-09-16",
            "contracted_sessions": 1, "used_sessions": 1, "modality": "presencial",
            "service": "dieta", "price": 300.0,
        },
    ]
    webdiet_raw = [{
        "name": "Beto Guerra", "phone": "11922223333", "birthdate": "1988-03-10",
        "email": None, "modality": "presencial", "diet_status": "ativo",
    }]
    result = run_update(liveclin_raw, webdiet_raw, conn, today=date(2026, 9, 26))
    assert len(result.candidates) == 1
    assert result.candidates[0].patient_name == "Beto Guerra"
    assert "erro" in capsys.readouterr().err.lower()


# --- fix wave: run_update idempotency (finding 1) ---

def _lc_raw(end_date="2026-09-27", used=1, contracted=1):
    return {
        "name": "Arthur Fonseca", "phone": "11911110000", "birthdate": "1980-01-01",
        "plan_type": "mensal", "start_date": "2026-08-27", "end_date": end_date,
        "contracted_sessions": contracted, "used_sessions": used, "modality": "presencial",
        "service": "dieta", "price": 250.0,
    }


def _wd_raw():
    return {
        "name": "Arthur Fonseca", "phone": "+55 (11) 91111-0000", "birthdate": "1980-01-01",
        "email": None, "modality": "presencial", "diet_status": "ativo",
    }


def _count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_run_update_twice_with_same_data_does_not_duplicate(tmp_path):
    conn = db.init_db(str(tmp_path / "test.db"))
    today = date(2026, 9, 26)
    first = run_update([_lc_raw()], [_wd_raw()], conn, today=today)
    second = run_update([_lc_raw()], [_wd_raw()], conn, today=today)
    assert _count(conn, "patients") == 1
    assert _count(conn, "plans") == 1
    assert _count(conn, "snapshots") == 2  # history keeps one snapshot per run
    assert len(first.candidates) == 1
    assert len(second.candidates) == 1
    assert second.candidates[0].patient_name == "Arthur Fonseca"


def test_run_update_updated_plan_replaces_old_one_in_renewal_list(tmp_path):
    conn = db.init_db(str(tmp_path / "test.db"))
    today = date(2026, 9, 26)
    first = run_update([_lc_raw(end_date="2026-09-27")], [_wd_raw()], conn, today=today)
    assert [c.end_date for c in first.candidates] == ["2026-09-27"]

    # patient renewed: new end date far away and sessions remaining
    second = run_update(
        [_lc_raw(end_date="2026-12-27", used=0, contracted=4)], [_wd_raw()], conn, today=today
    )
    assert second.candidates == []
    plans = db.get_all_plans(conn)
    assert len(plans) == 1
    assert plans[0]["end_date"] == "2026-12-27"
    assert _count(conn, "patients") == 1
