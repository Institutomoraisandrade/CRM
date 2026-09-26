"""CLI orchestration: parse raw scraped data, match, persist, and report renewals."""

import json
import os
import sys
from dataclasses import dataclass
from datetime import date

from crm import db, matching, renewal
from crm.matching import SourceRecord
from crm.scraping import liveclin, webdiet


@dataclass
class UpdateResult:
    candidates: list[renewal.RenewalCandidate]
    unmatched_liveclin: list[SourceRecord]
    unmatched_webdiet: list[SourceRecord]


def _parse_all(raw_patients: list[dict], parse_patient) -> list[SourceRecord]:
    """Parse each raw dict with parse_patient, skipping and logging failures."""
    records = []
    for raw in raw_patients:
        try:
            records.append(parse_patient(raw))
        except Exception as exc:
            print(f"[erro] falha ao parsear registro: {exc}", file=sys.stderr)
    return records


def run_update(
    liveclin_raw_patients: list[dict],
    webdiet_raw_patients: list[dict],
    conn,
    today: date,
) -> UpdateResult:
    """Parse, match, persist, and compute renewal candidates. Pure orchestration."""
    liveclin_records = _parse_all(liveclin_raw_patients, liveclin.parse_patient)
    webdiet_records = _parse_all(webdiet_raw_patients, webdiet.parse_patient)

    matches, unmatched_lc, unmatched_wd = matching.match_patients(
        liveclin_records, webdiet_records
    )

    for m in matches:
        patient_id = db.insert_patient(
            conn,
            {
                "name": m.liveclin.name,
                "phone_liveclin": m.liveclin.phone,
                "phone_webdiet": m.webdiet.phone,
                "birthdate": m.liveclin.birthdate or m.webdiet.birthdate,
                "email": m.liveclin.email or m.webdiet.email,
                "match_field": m.matched_field,
            },
        )
        db.insert_plan(conn, patient_id, {**m.liveclin.raw, "source": "liveclin"})
        db.insert_snapshot(
            conn,
            patient_id,
            json.dumps({"liveclin": m.liveclin.raw, "webdiet": m.webdiet.raw}),
        )

    candidates = renewal.get_renewal_candidates(db.get_all_plans(conn), today)

    return UpdateResult(
        candidates=candidates,
        unmatched_liveclin=unmatched_lc,
        unmatched_webdiet=unmatched_wd,
    )


def main() -> None:
    """Real entrypoint: drives Playwright scraping, runs the update, and prints results."""
    from playwright.sync_api import sync_playwright

    liveclin_user = os.environ["LIVECLIN_USER"]
    liveclin_password = os.environ["LIVECLIN_PASSWORD"]
    webdiet_user = os.environ["WEBDIET_USER"]
    webdiet_password = os.environ["WEBDIET_PASSWORD"]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            context = browser.new_context()

            liveclin_page = context.new_page()
            liveclin.login(liveclin_page, liveclin_user, liveclin_password)
            liveclin_raw = liveclin.extract_patients(liveclin_page)

            webdiet_page = context.new_page()
            webdiet.login(webdiet_page, webdiet_user, webdiet_password)
            webdiet_raw = webdiet.extract_patients(webdiet_page)
        finally:
            browser.close()

    conn = db.init_db("data/crm.db")
    result = run_update(liveclin_raw, webdiet_raw, conn, today=date.today())

    for c in result.candidates:
        print(
            f"{c.patient_name} — {c.plan_type} — vence {c.end_date} "
            f"({c.used_sessions}/{c.contracted_sessions} consultas)"
        )

    if result.unmatched_liveclin or result.unmatched_webdiet:
        print("Não cruzados:")
        for r in result.unmatched_liveclin:
            print(r.name)
        for r in result.unmatched_webdiet:
            print(r.name)


if __name__ == "__main__":
    main()
