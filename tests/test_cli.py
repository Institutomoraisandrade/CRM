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
