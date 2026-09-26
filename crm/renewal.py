from dataclasses import dataclass
from datetime import date


DEFAULT_RENEWAL_WINDOW_DAYS = 21


@dataclass
class RenewalCandidate:
    patient_name: str
    plan_type: str
    end_date: str
    contracted_sessions: int | None
    used_sessions: int | None
    days_until_due: int


def get_renewal_candidates(
    plans: list[dict], today: date, window_days: int = DEFAULT_RENEWAL_WINDOW_DAYS
) -> list[RenewalCandidate]:
    """
    Identify plans that qualify for renewal based on:
    1. All contracted sessions have been used (used_sessions >= contracted_sessions)
    2. Plan end_date is within the renewal window (days <= window_days)

    Results are sorted by end_date in ascending order.
    """
    candidates = []

    for plan in plans:
        patient_name = plan["patient_name"]
        plan_type = plan["plan_type"]
        end_date_str = plan["end_date"]
        contracted_sessions = plan["contracted_sessions"]
        used_sessions = plan["used_sessions"]

        # Parse end_date
        end_date_obj = date.fromisoformat(end_date_str)
        days_until_due = (end_date_obj - today).days

        # Check if plan qualifies for renewal
        qualifies = False

        # Condition 1: All sessions used
        if (
            used_sessions is not None
            and contracted_sessions
            and used_sessions >= contracted_sessions
        ):
            qualifies = True

        # Condition 2: Within renewal window
        if days_until_due <= window_days:
            qualifies = True

        if qualifies:
            candidate = RenewalCandidate(
                patient_name=patient_name,
                plan_type=plan_type,
                end_date=end_date_str,
                contracted_sessions=contracted_sessions,
                used_sessions=used_sessions,
                days_until_due=days_until_due,
            )
            candidates.append(candidate)

    # Sort by end_date ascending
    candidates.sort(key=lambda c: c.end_date)

    return candidates
