from crm import db


def test_init_db_creates_all_tables(tmp_path):
    conn = db.init_db(str(tmp_path / "test.db"))
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert {"patients", "plans", "snapshots"} <= tables


def test_insert_patient_plan_snapshot_roundtrip(tmp_path):
    conn = db.init_db(str(tmp_path / "test.db"))
    patient_id = db.insert_patient(conn, {
        "name": "Arthur Fonseca",
        "phone_liveclin": "11999990000",
        "phone_webdiet": "11999990000",
        "birthdate": "1990-01-01",
        "email": None,
        "match_field": "phone",
    })
    db.insert_plan(conn, patient_id, {
        "source": "liveclin",
        "plan_type": "mensal",
        "start_date": "2026-08-27",
        "end_date": "2026-09-27",
        "contracted_sessions": 1,
        "used_sessions": 1,
        "modality": "presencial",
        "service": "dieta",
        "price": 250.0,
    })
    db.insert_snapshot(conn, patient_id, '{"raw": true}')

    plans = db.get_all_plans(conn)
    assert len(plans) == 1
    assert plans[0]["patient_name"] == "Arthur Fonseca"
    assert plans[0]["end_date"] == "2026-09-27"
    assert plans[0]["contracted_sessions"] == 1
