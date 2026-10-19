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


# --- fix wave: idempotent persistence (finding 1) ---

def _patient(name="Arthur Fonseca", phone_lc="11999990000", phone_wd="11999990000",
             birthdate="1990-01-01", email=None, match_field="name"):
    return {
        "name": name, "phone_liveclin": phone_lc, "phone_webdiet": phone_wd,
        "birthdate": birthdate, "email": email, "match_field": match_field,
    }


def _count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_find_patient_by_identity_requires_same_name_and_a_common_phone(tmp_path):
    conn = db.init_db(str(tmp_path / "test.db"))
    pid = db.insert_patient(conn, _patient())
    # same name (different accents/case), phone formatted with DDI -> same patient
    assert db.find_patient_by_identity(
        conn, _patient(name="ARTHUR  fonseca", phone_lc="+55 (11) 99999-0000", phone_wd=None)
    ) == pid
    # same name, different phones (e.g. father/son) -> not the same patient
    assert db.find_patient_by_identity(
        conn, _patient(phone_lc="11922220000", phone_wd="11922220000")
    ) is None
    # different name, same phone -> not the same patient
    assert db.find_patient_by_identity(conn, _patient(name="Outra Pessoa")) is None


def test_find_patient_by_identity_without_phones_falls_back_to_birthdate(tmp_path):
    conn = db.init_db(str(tmp_path / "test.db"))
    pid = db.insert_patient(conn, _patient(phone_lc=None, phone_wd=None))
    assert db.find_patient_by_identity(conn, _patient(phone_lc=None, phone_wd=None)) == pid
    assert db.find_patient_by_identity(
        conn, _patient(phone_lc=None, phone_wd=None, birthdate="2001-01-01")
    ) is None


def test_upsert_patient_updates_instead_of_duplicating(tmp_path):
    conn = db.init_db(str(tmp_path / "test.db"))
    first = db.upsert_patient(conn, _patient())
    second = db.upsert_patient(conn, _patient(email="arthur@x.com", match_field="phone"))
    assert first == second
    assert _count(conn, "patients") == 1
    row = conn.execute("SELECT email, match_field FROM patients").fetchone()
    assert row["email"] == "arthur@x.com"
    assert row["match_field"] == "phone"


def test_delete_plans_removes_only_that_patient_and_source(tmp_path):
    conn = db.init_db(str(tmp_path / "test.db"))
    a = db.insert_patient(conn, _patient())
    b = db.insert_patient(conn, _patient(name="Beto Guerra"))
    db.insert_plan(conn, a, {"source": "liveclin", "end_date": "2026-09-27"})
    db.insert_plan(conn, a, {"source": "webdiet", "end_date": "2026-09-27"})
    db.insert_plan(conn, b, {"source": "liveclin", "end_date": "2026-09-27"})
    assert db.delete_plans(conn, a, "liveclin") == 1
    remaining = {(p["patient_id"], p["source"]) for p in db.get_all_plans(conn)}
    assert remaining == {(a, "webdiet"), (b, "liveclin")}
