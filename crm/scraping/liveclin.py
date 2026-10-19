"""LiveClin scraping module for patient data extraction."""

from crm.matching import SourceRecord


def parse_patient(raw: dict) -> SourceRecord:
    """
    Parse raw patient data from LiveClin into a SourceRecord.

    Args:
        raw: Dictionary with keys: name, phone (optional), birthdate (optional),
             email (optional), plan_type, start_date, end_date, contracted_sessions,
             used_sessions, modality, service, price (optional).

    Returns:
        SourceRecord with name, phone, birthdate, email extracted from raw,
        and the original raw dict stored unchanged.
    """
    return SourceRecord(
        name=raw["name"],
        phone=raw.get("phone"),
        birthdate=raw.get("birthdate"),
        email=raw.get("email"),
        raw=raw,
    )


def login(page, username: str, password: str) -> None:
    """
    Authenticate with LiveClin using Playwright.

    Args:
        page: Playwright page object.
        username: User credentials username.
        password: User credentials password.

    Raises:
        NotImplementedError: This function requires manual wiring of real selectors
                           against liveclin, verified interactively.

    TODO(manual): wire real selectors against liveclin, verified interactively;
                  document the CSS selectors used as a comment here once found.
    """
    raise NotImplementedError(
        "login() requires manual wiring of LiveClin selectors. "
        "See the TODO comment in this function."
    )


def extract_patients(page) -> list[dict]:
    """
    Extract patient data from LiveClin using Playwright.

    Args:
        page: Playwright page object (should be authenticated via login()).

    Returns:
        List of dictionaries with keys: name, phone (optional), birthdate (optional),
        email (optional), plan_type, start_date, end_date, contracted_sessions,
        used_sessions, modality, service, price (optional).

    Raises:
        NotImplementedError: This function requires manual wiring of real selectors
                           against liveclin, verified interactively.

    TODO(manual): wire real selectors against liveclin, verified interactively;
                  document the CSS selectors used as a comment here once found.

    Note: When implemented, this function must wrap the per-patient row extraction
          in try/except Exception, print the error to stderr with the patient's
          identifying text (name/row index) and continue to the next row. A single
          broken row must not raise out of extract_patients and abort the whole list.
    """
    raise NotImplementedError(
        "extract_patients() requires manual wiring of LiveClin selectors. "
        "See the TODO comment in this function."
    )
