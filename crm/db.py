import sqlite3
from datetime import datetime, timezone

from crm.matching import normalize_name, normalize_phone


def init_db(db_path: str) -> sqlite3.Connection:
    """Initialize SQLite database with schema for patients, plans, and snapshots."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone_liveclin TEXT,
            phone_webdiet TEXT,
            birthdate TEXT,
            email TEXT,
            match_field TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            source TEXT NOT NULL,
            plan_type TEXT,
            start_date TEXT,
            end_date TEXT,
            contracted_sessions INTEGER,
            used_sessions INTEGER,
            modality TEXT,
            service TEXT,
            price REAL,
            updated_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            executed_at TEXT NOT NULL,
            raw_json TEXT NOT NULL
        )
    """)

    conn.commit()
    return conn


def insert_patient(conn: sqlite3.Connection, patient: dict) -> int:
    """
    Insert a patient record.

    Args:
        conn: SQLite connection
        patient: dict with keys name, phone_liveclin, phone_webdiet, birthdate, email, match_field

    Returns:
        New patient.id
    """
    created_at = datetime.now(timezone.utc).isoformat()

    cursor = conn.execute(
        """
        INSERT INTO patients (name, phone_liveclin, phone_webdiet, birthdate, email, match_field, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            patient["name"],
            patient.get("phone_liveclin"),
            patient.get("phone_webdiet"),
            patient.get("birthdate"),
            patient.get("email"),
            patient["match_field"],
            created_at,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def find_patient_by_identity(conn: sqlite3.Connection, patient: dict) -> int | None:
    """
    Find an existing patient with the same identity as `patient`.

    Identity = same normalized name AND at least one phone in common (any of
    phone_liveclin/phone_webdiet on either side, compared normalized, so
    formatting and the +55 country code do not matter). When neither the
    stored nor the incoming record has any phone, the same normalized name
    plus the same non-empty birthdate is accepted instead.

    Returns:
        The lowest matching patient.id, or None when no patient matches.
    """
    name = normalize_name(patient["name"])
    new_phones = {
        p
        for p in (
            normalize_phone(patient.get("phone_liveclin")),
            normalize_phone(patient.get("phone_webdiet")),
        )
        if p
    }
    new_birthdate = (patient.get("birthdate") or "").strip()

    rows = conn.execute(
        "SELECT id, name, phone_liveclin, phone_webdiet, birthdate FROM patients ORDER BY id"
    ).fetchall()
    for row in rows:
        if normalize_name(row["name"]) != name:
            continue
        existing_phones = {
            p
            for p in (normalize_phone(row["phone_liveclin"]), normalize_phone(row["phone_webdiet"]))
            if p
        }
        if new_phones & existing_phones:
            return row["id"]
        if (
            not new_phones
            and not existing_phones
            and new_birthdate
            and new_birthdate == (row["birthdate"] or "").strip()
        ):
            return row["id"]
    return None


def update_patient(conn: sqlite3.Connection, patient_id: int, patient: dict) -> None:
    """Overwrite the identity/contact fields of an existing patient (created_at is kept)."""
    conn.execute(
        """
        UPDATE patients
        SET name = ?, phone_liveclin = ?, phone_webdiet = ?, birthdate = ?, email = ?,
            match_field = ?
        WHERE id = ?
        """,
        (
            patient["name"],
            patient.get("phone_liveclin"),
            patient.get("phone_webdiet"),
            patient.get("birthdate"),
            patient.get("email"),
            patient["match_field"],
            patient_id,
        ),
    )
    conn.commit()


def upsert_patient(conn: sqlite3.Connection, patient: dict) -> int:
    """Update the patient with the same identity if it exists, else insert it. Returns its id."""
    existing_id = find_patient_by_identity(conn, patient)
    if existing_id is None:
        return insert_patient(conn, patient)
    update_patient(conn, existing_id, patient)
    return existing_id


def delete_plans(conn: sqlite3.Connection, patient_id: int, source: str) -> int:
    """
    Remove every plan of `patient_id` coming from `source`.

    Used before inserting the latest plan so `plans` keeps only the most
    recent plan per patient+source (full history lives in `snapshots`).

    Returns:
        Number of rows removed.
    """
    cursor = conn.execute(
        "DELETE FROM plans WHERE patient_id = ? AND source = ?", (patient_id, source)
    )
    conn.commit()
    return cursor.rowcount


def insert_plan(conn: sqlite3.Connection, patient_id: int, plan: dict) -> int:
    """
    Insert a plan record.

    Args:
        conn: SQLite connection
        patient_id: ID of the patient
        plan: dict with keys source, plan_type, start_date, end_date, contracted_sessions,
              used_sessions, modality, service, price

    Returns:
        New plan.id
    """
    updated_at = datetime.now(timezone.utc).isoformat()

    cursor = conn.execute(
        """
        INSERT INTO plans (patient_id, source, plan_type, start_date, end_date, contracted_sessions,
                          used_sessions, modality, service, price, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            patient_id,
            plan["source"],
            plan.get("plan_type"),
            plan.get("start_date"),
            plan.get("end_date"),
            plan.get("contracted_sessions"),
            plan.get("used_sessions"),
            plan.get("modality"),
            plan.get("service"),
            plan.get("price"),
            updated_at,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def insert_snapshot(conn: sqlite3.Connection, patient_id: int, raw_json: str) -> int:
    """
    Insert a snapshot record.

    Args:
        conn: SQLite connection
        patient_id: ID of the patient
        raw_json: Raw JSON string

    Returns:
        New snapshot.id
    """
    executed_at = datetime.now(timezone.utc).isoformat()

    cursor = conn.execute(
        """
        INSERT INTO snapshots (patient_id, executed_at, raw_json)
        VALUES (?, ?, ?)
        """,
        (patient_id, executed_at, raw_json),
    )
    conn.commit()
    return cursor.lastrowid


def get_all_plans(conn: sqlite3.Connection) -> list[dict]:
    """
    Retrieve all plans with patient names joined.

    Returns:
        List of dicts with plan columns plus patient_name
    """
    cursor = conn.execute(
        """
        SELECT plans.*, patients.name AS patient_name
        FROM plans
        JOIN patients ON plans.patient_id = patients.id
        """
    )
    return [dict(row) for row in cursor.fetchall()]
