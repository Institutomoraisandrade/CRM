# Núcleo de rastreamento de pacientes (v1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python module that logs into LiveClin and WebDiet, extracts
patient/plan data, cross-references patients between the two systems, stores
the result in a local SQLite database, and prints a renewal candidate list
sorted by due date — replacing the manual process of checking both systems by
hand.

**Architecture:** Five independent, pure-logic modules (`db`, `matching`,
`renewal`, plus the parsing halves of `scraping/liveclin` and
`scraping/webdiet`) that are fully unit-tested without a browser, wired
together by a thin `cli.py` orchestrator. The browser-driving halves of the
scraping modules (login, page navigation, DOM extraction) are exercised
manually against the real sites, per the spec's testing strategy — their
exact selectors cannot be pinned without live access and are documented as
code comments once found.

**Tech Stack:** Python 3.11+, `sqlite3` (stdlib), `dataclasses` (stdlib),
`pytest`, `playwright` (sync API) for browser automation.

**Spec:** `docs/superpowers/specs/2026-09-26-nucleo-rastreamento-pacientes-design.md`

## Global Constraints

- Credenciais do LiveClin e do WebDiet são lidas somente de variáveis de
  ambiente (`LIVECLIN_USER`, `LIVECLIN_PASSWORD`, `WEBDIET_USER`,
  `WEBDIET_PASSWORD`); nunca logadas, impressas ou persistidas em disco.
- O banco de dados vive em `data/crm.db` e nunca é versionado no git (já
  coberto por `.gitignore`).
- Cruzamento de pacientes segue a cascata: nome → telefone → data de
  nascimento → e-mail, parando no primeiro campo que resolver para
  exatamente um candidato de cada lado.
- Falha ao extrair ou cruzar um paciente específico não interrompe o
  processamento dos demais.
- Conteúdo clínico (observações de prontuário, texto livre de plano
  alimentar) nunca é armazenado nem logado — só os campos definidos no
  schema (spec, seção "Modelo de dados").

## Review Focus

- Dois registros com o mesmo campo vazio/`None` (ex: telefone ausente nos
  dois sistemas) não podem contar como "campo batendo" — cobrir com teste
  em `matching.py` (Task 3).
- Paciente presente em um sistema e ausente no outro deve aparecer como
  "não cruzado", nunca descartado silenciosamente nem lançar exceção —
  cobrir com teste em `matching.py` (Task 3).
- Plano com `contracted_sessions` igual a `0` ou `None` não pode causar
  `ZeroDivisionError` nem entrar como falso-positivo de renovação — cobrir
  com teste em `renewal.py` (Task 4).
- Nome duplicado (dois pacientes, mesmo nome, ex. pai e filho) precisa
  desambiguar por telefone/nascimento em vez de cruzar com o primeiro que
  aparecer — cobrir com teste em `matching.py` (Task 3).
- Uma exceção ao extrair um paciente no meio de uma lista maior (rede caiu,
  seletor sumiu) deve ser registrada e a extração deve seguir para os
  próximos — cobrir com teste em `cli.py` (Task 7) usando um fake que
  levanta exceção para um item da lista.

---

## Task 1: Project setup

**Files:**
- Create: `pyproject.toml`
- Create: `crm/__init__.py`
- Create: `crm/scraping/__init__.py`
- Create: `tests/__init__.py`
- Create: `.env.example`
- Create: `data/.gitkeep`

**Interfaces:**
- Produces: an installable `crm` package importable as `crm.db`,
  `crm.matching`, `crm.renewal`, `crm.scraping.liveclin`,
  `crm.scraping.webdiet`, `crm.cli`; `pytest` runnable from repo root.

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "crm"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["playwright>=1.40"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create empty package files**

`crm/__init__.py` and `crm/scraping/__init__.py` and `tests/__init__.py`, all
empty.

- [ ] **Step 3: Create `.env.example`**

```
LIVECLIN_USER=
LIVECLIN_PASSWORD=
WEBDIET_USER=
WEBDIET_PASSWORD=
```

- [ ] **Step 4: Create `data/.gitkeep`** (empty file, so the `data/` directory
  exists in git even though `data/crm.db` is ignored)

- [ ] **Step 5: Install dependencies and verify pytest runs**

Run: `pip install -e ".[dev]"` then `pytest --collect-only`
Expected: exits 0, "no tests ran" (no test files yet is fine)

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml crm/ tests/__init__.py .env.example data/.gitkeep
git commit -m "chore: scaffold crm package"
```

---

## Task 2: db.py — schema and persistence

**Files:**
- Create: `crm/db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Produces:
  - `init_db(db_path: str) -> sqlite3.Connection`
  - `insert_patient(conn: sqlite3.Connection, patient: dict) -> int` —
    `patient` keys: `name`, `phone_liveclin`, `phone_webdiet`, `birthdate`,
    `email`, `match_field` (all `str | None` except `name: str` and
    `match_field: str`); returns new `patients.id`.
  - `insert_plan(conn: sqlite3.Connection, patient_id: int, plan: dict) -> int`
    — `plan` keys: `source`, `plan_type`, `start_date`, `end_date`,
    `contracted_sessions: int`, `used_sessions: int`, `modality`, `service`,
    `price: float | None`; returns new `plans.id`.
  - `insert_snapshot(conn: sqlite3.Connection, patient_id: int, raw_json: str) -> int`
  - `get_all_plans(conn: sqlite3.Connection) -> list[dict]` — one dict per
    plan row, with an added `patient_name: str` key joined from `patients`.

- [ ] **Step 1: Write the failing test for schema creation**

```python
# tests/test_db.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db.py::test_init_db_creates_all_tables -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'crm.db'`

- [ ] **Step 3: Implement `init_db` and the schema in `crm/db.py`**

Schema (exact columns, per spec):
```sql
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone_liveclin TEXT,
    phone_webdiet TEXT,
    birthdate TEXT,
    email TEXT,
    match_field TEXT NOT NULL,
    created_at TEXT NOT NULL
);
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
);
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    executed_at TEXT NOT NULL,
    raw_json TEXT NOT NULL
);
```
`init_db` opens the connection (`sqlite3.connect(db_path)`), executes the
three `CREATE TABLE IF NOT EXISTS` statements, commits, and returns the
connection. `created_at`/`updated_at`/`executed_at` are ISO-8601 strings
(`datetime.now(timezone.utc).isoformat()`), set by the insert functions, not
by the caller.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_db.py::test_init_db_creates_all_tables -v`
Expected: PASS

- [ ] **Step 5: Write the failing test for insert/query round-trip**

```python
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
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/test_db.py::test_insert_patient_plan_snapshot_roundtrip -v`
Expected: FAIL (`insert_patient`/`insert_plan`/`insert_snapshot`/`get_all_plans` not defined)

- [ ] **Step 7: Implement `insert_patient`, `insert_plan`, `insert_snapshot`, `get_all_plans` in `crm/db.py`**

Each `insert_*` does a parameterized `INSERT`, commits, returns
`cursor.lastrowid`. `get_all_plans` runs `SELECT plans.*, patients.name AS
patient_name FROM plans JOIN patients ON plans.patient_id = patients.id` and
returns a list of `dict(row)` using `conn.row_factory = sqlite3.Row` (set in
`init_db`).

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/test_db.py -v`
Expected: PASS (both tests)

- [ ] **Step 9: Commit**

```bash
git add crm/db.py tests/test_db.py
git commit -m "feat: add db module for patients, plans, snapshots"
```

---

## Task 3: matching.py — cascading patient cross-reference

**Files:**
- Create: `crm/matching.py`
- Test: `tests/test_matching.py`

**Interfaces:**
- Produces:
  - `@dataclass SourceRecord: name: str; phone: str | None; birthdate: str | None; email: str | None; raw: dict`
  - `@dataclass MatchResult: liveclin: SourceRecord; webdiet: SourceRecord; matched_field: str`
  - `normalize_name(name: str) -> str`
  - `normalize_phone(phone: str | None) -> str | None`
  - `match_patients(liveclin: list[SourceRecord], webdiet: list[SourceRecord]) -> tuple[list[MatchResult], list[SourceRecord], list[SourceRecord]]`
    — returns `(matches, unmatched_liveclin, unmatched_webdiet)`.

**Matching algorithm** (fixed by this plan; the implementer writes it as
specified — this is the one algorithm the tests don't fully determine):

```python
FIELDS_IN_ORDER = ["name", "phone", "birthdate", "email"]
NORMALIZERS = {
    "name": normalize_name,
    "phone": normalize_phone,
    "birthdate": lambda v: v.strip() if v else None,
    "email": lambda v: v.strip().lower() if v else None,
}

def match_patients(liveclin, webdiet):
    remaining_lc, remaining_wd = list(liveclin), list(webdiet)
    matches = []
    for field in FIELDS_IN_ORDER:
        found, remaining_lc, remaining_wd = _match_by_field(
            remaining_lc, remaining_wd, field
        )
        matches.extend(found)
    return matches, remaining_lc, remaining_wd

def _match_by_field(lc_list, wd_list, field):
    normalize = NORMALIZERS[field]
    # group each side by normalized value, dropping None/empty values
    lc_by_value = _group_by_normalized(lc_list, field, normalize)
    wd_by_value = _group_by_normalized(wd_list, field, normalize)

    matched, matched_lc_ids, matched_wd_ids = [], set(), set()
    for value, lc_group in lc_by_value.items():
        wd_group = wd_by_value.get(value)
        # confident match only when exactly one record on each side
        # shares this normalized, non-empty value
        if wd_group and len(lc_group) == 1 and len(wd_group) == 1:
            matched.append(MatchResult(lc_group[0], wd_group[0], field))
            matched_lc_ids.add(id(lc_group[0]))
            matched_wd_ids.add(id(wd_group[0]))

    remaining_lc = [r for r in lc_list if id(r) not in matched_lc_ids]
    remaining_wd = [r for r in wd_list if id(r) not in matched_wd_ids]
    return matched, remaining_lc, remaining_wd

def _group_by_normalized(records, field, normalize):
    groups: dict[str, list[SourceRecord]] = {}
    for r in records:
        value = normalize(getattr(r, field))
        if value:  # None or "" never counts as a matching value
            groups.setdefault(value, []).append(r)
    return groups
```

- [ ] **Step 1: Write the failing test for unique-name matching**

```python
# tests/test_matching.py
from crm.matching import SourceRecord, match_patients

def _rec(name, phone=None, birthdate=None, email=None):
    return SourceRecord(name=name, phone=phone, birthdate=birthdate, email=email, raw={})

def test_matches_by_name_when_unique_on_both_sides():
    lc = [_rec("Beto Guerra", phone="11911112222")]
    wd = [_rec("Beto Guerra", phone="11933334444")]  # phone differs, name still resolves it
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert len(matches) == 1
    assert matches[0].matched_field == "name"
    assert unmatched_lc == []
    assert unmatched_wd == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_matching.py::test_matches_by_name_when_unique_on_both_sides -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `SourceRecord`, `MatchResult`, `normalize_name`, `normalize_phone`, `match_patients` in `crm/matching.py`**

`normalize_name(name)`: strip, collapse internal whitespace to single
spaces, lowercase, strip accents (use `unicodedata.normalize("NFKD", name)`
and drop combining marks).
`normalize_phone(phone)`: return `None` if `phone` is falsy; otherwise keep
only digit characters (`"".join(c for c in phone if c.isdigit())`), and
return `None` if the result is empty.
Implement the algorithm exactly as specified above.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_matching.py::test_matches_by_name_when_unique_on_both_sides -v`
Expected: PASS

- [ ] **Step 5: Write the failing test for duplicate-name disambiguation by phone**

```python
def test_falls_back_to_phone_when_name_is_duplicated():
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
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_matching.py::test_falls_back_to_phone_when_name_is_duplicated -v`
Expected: PASS (no new code needed if Step 3's algorithm is correct; this
step only proves it — if it fails, fix `_match_by_field`/`_group_by_normalized`
before continuing)

- [ ] **Step 7: Write the failing test for birthdate fallback when phone is missing**

```python
def test_falls_back_to_birthdate_when_name_and_phone_dont_resolve():
    lc = [_rec("Maria Silva", phone=None, birthdate="1985-05-20")]
    wd = [_rec("Maria Silva", phone=None, birthdate="1985-05-20")]
    # duplicate name on lc side forces fallback past "name"
    lc.append(_rec("Maria Silva", phone=None, birthdate="1992-01-01"))
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert len(matches) == 1
    assert matches[0].matched_field == "birthdate"
    assert matches[0].liveclin.birthdate == "1985-05-20"
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/test_matching.py::test_falls_back_to_birthdate_when_name_and_phone_dont_resolve -v`
Expected: PASS

- [ ] **Step 9: Write the failing test for the empty-field guard (Review Focus)**

```python
def test_missing_field_on_both_sides_never_counts_as_a_match():
    lc = [_rec("Paciente A", phone=None, birthdate=None, email=None)]
    lc.append(_rec("Paciente B", phone=None, birthdate=None, email=None))
    wd = [_rec("Paciente C", phone=None, birthdate=None, email=None)]
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert matches == []
    assert len(unmatched_lc) == 2
    assert len(unmatched_wd) == 1
```

- [ ] **Step 10: Run test to verify it passes**

Run: `pytest tests/test_matching.py::test_missing_field_on_both_sides_never_counts_as_a_match -v`
Expected: PASS

- [ ] **Step 11: Write the failing test for the unmatched case (Review Focus)**

```python
def test_patient_present_in_only_one_system_is_unmatched_not_dropped():
    lc = [_rec("Georges Jean Paul", phone="11955556666")]
    wd = []
    matches, unmatched_lc, unmatched_wd = match_patients(lc, wd)
    assert matches == []
    assert unmatched_lc == lc
    assert unmatched_wd == []
```

- [ ] **Step 12: Run test to verify it passes**

Run: `pytest tests/test_matching.py -v`
Expected: PASS (all tests in file)

- [ ] **Step 13: Commit**

```bash
git add crm/matching.py tests/test_matching.py
git commit -m "feat: add cascading patient matching (name -> phone -> birthdate -> email)"
```

---

## Task 4: renewal.py — renewal candidate calculation

**Files:**
- Create: `crm/renewal.py`
- Test: `tests/test_renewal.py`

**Interfaces:**
- Consumes: dicts shaped like `db.get_all_plans()` rows (keys:
  `patient_name`, `plan_type`, `end_date` [ISO `YYYY-MM-DD`],
  `contracted_sessions: int | None`, `used_sessions: int | None`).
- Produces:
  - `DEFAULT_RENEWAL_WINDOW_DAYS: int = 21`
  - `@dataclass RenewalCandidate: patient_name: str; plan_type: str; end_date: str; contracted_sessions: int | None; used_sessions: int | None; days_until_due: int`
  - `get_renewal_candidates(plans: list[dict], today: date, window_days: int = DEFAULT_RENEWAL_WINDOW_DAYS) -> list[RenewalCandidate]`
    — a plan qualifies when `used_sessions is not None and contracted_sessions
    and used_sessions >= contracted_sessions`, OR `(end_date_as_date -
    today).days <= window_days`. Result sorted ascending by `end_date`.

- [ ] **Step 1: Write the failing test for a plan ending tomorrow**

```python
# tests/test_renewal.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_renewal.py::test_plan_ending_tomorrow_is_a_candidate -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `RenewalCandidate` and `get_renewal_candidates` in `crm/renewal.py`**

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_renewal.py::test_plan_ending_tomorrow_is_a_candidate -v`
Expected: PASS

- [ ] **Step 5: Write the failing test for a plan with all sessions used but far from end date**

```python
def test_plan_with_all_sessions_used_is_candidate_even_if_end_date_is_far():
    today = date(2026, 9, 26)
    plans = [_plan("Renan Costa Rego", "2026-11-07", contracted=10, used=10)]
    result = get_renewal_candidates(plans, today)
    assert len(result) == 1
    assert result[0].patient_name == "Renan Costa Rego"
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_renewal.py::test_plan_with_all_sessions_used_is_candidate_even_if_end_date_is_far -v`
Expected: PASS

- [ ] **Step 7: Write the failing test for a plan that should NOT qualify**

```python
def test_plan_far_from_end_with_sessions_remaining_is_not_a_candidate():
    today = date(2026, 9, 26)
    plans = [_plan("Lais Sales", "2026-12-25", contracted=3, used=1)]
    result = get_renewal_candidates(plans, today)
    assert result == []
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/test_renewal.py::test_plan_far_from_end_with_sessions_remaining_is_not_a_candidate -v`
Expected: PASS

- [ ] **Step 9: Write the failing test for the zero/None-sessions guard (Review Focus)**

```python
def test_plan_with_zero_or_none_contracted_sessions_does_not_crash():
    today = date(2026, 9, 26)
    plans = [
        _plan("Sem Contrato A", "2026-12-25", contracted=0, used=0),
        _plan("Sem Contrato B", "2026-12-25", contracted=None, used=None),
    ]
    result = get_renewal_candidates(plans, today)  # must not raise
    assert result == []
```

- [ ] **Step 10: Run test to verify it passes**

Run: `pytest tests/test_renewal.py::test_plan_with_zero_or_none_contracted_sessions_does_not_crash -v`
Expected: PASS

- [ ] **Step 11: Write the failing test for sort order**

```python
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
```

- [ ] **Step 12: Run test to verify it passes**

Run: `pytest tests/test_renewal.py -v`
Expected: PASS (all tests in file)

- [ ] **Step 13: Commit**

```bash
git add crm/renewal.py tests/test_renewal.py
git commit -m "feat: add renewal candidate calculation"
```

---

## Task 5: scraping/liveclin.py — parsing layer (browser layer stubbed)

**Files:**
- Create: `crm/scraping/liveclin.py`
- Test: `tests/test_liveclin.py`

**Interfaces:**
- Consumes: `crm.matching.SourceRecord` (Task 3).
- Produces:
  - `parse_patient(raw: dict) -> SourceRecord` — pure function. `raw` keys
    (exact strings the live extraction step must eventually produce):
    `name: str`, `phone: str | None`, `birthdate: str | None`, `plan_type:
    str`, `start_date: str`, `end_date: str`, `contracted_sessions: int`,
    `used_sessions: int`, `modality: str`, `service: str`, `price: float |
    None`. The returned `SourceRecord.raw` holds the original `raw` dict
    unchanged (used later for the `snapshots` table).
  - `login(page, username: str, password: str) -> None` — Playwright
    interaction; **not unit-tested** (no fixed selectors exist yet). Body is
    `# TODO(manual): wire real selectors against liveclin, verified
    interactively; document the CSS selectors used as a comment here once
    found` plus a `raise NotImplementedError` placeholder.
  - `extract_patients(page) -> list[dict]` — same treatment as `login`:
    Playwright interaction returning a list of `raw` dicts shaped as above;
    stubbed with `NotImplementedError` and the same TODO comment. **When
    implemented manually (see "Manual follow-up" at the end of this plan),
    this function must wrap the per-patient row extraction in `try/except
    Exception`, print the error to stderr with the patient's identifying
    text (name/row index) and `continue` to the next row, per the spec's
    "falha de login ou mudança de layout... não derruba a extração inteira"
    requirement — a single broken row must not raise out of
    `extract_patients` and abort the whole list.**

- [ ] **Step 1: Write the failing test for `parse_patient`**

```python
# tests/test_liveclin.py
from crm.scraping.liveclin import parse_patient

def test_parse_patient_maps_raw_fields_to_source_record():
    raw = {
        "name": "Beto Guerra", "phone": "(11) 91111-2222", "birthdate": "1988-03-10",
        "plan_type": "mensal", "start_date": "2026-08-16", "end_date": "2026-09-16",
        "contracted_sessions": 1, "used_sessions": 1, "modality": "presencial",
        "service": "dieta", "price": 300.0,
    }
    record = parse_patient(raw)
    assert record.name == "Beto Guerra"
    assert record.phone == "(11) 91111-2222"  # normalization happens in matching, not here
    assert record.birthdate == "1988-03-10"
    assert record.raw == raw
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_liveclin.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `parse_patient`, `login`, `extract_patients` in `crm/scraping/liveclin.py`**

`parse_patient` builds and returns `SourceRecord(name=raw["name"],
phone=raw.get("phone"), birthdate=raw.get("birthdate"),
email=raw.get("email"), raw=raw)`. `login` and `extract_patients` are
stubs, exactly as specified in Interfaces above.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_liveclin.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add crm/scraping/liveclin.py tests/test_liveclin.py
git commit -m "feat: add liveclin parsing layer (browser layer stubbed for manual wiring)"
```

---

## Task 6: scraping/webdiet.py — parsing layer (browser layer stubbed)

**Files:**
- Create: `crm/scraping/webdiet.py`
- Test: `tests/test_webdiet.py`

**Interfaces:**
- Consumes: `crm.matching.SourceRecord` (Task 3).
- Produces: same shape as Task 5 but for WebDiet: `parse_patient(raw: dict)
  -> SourceRecord` with `raw` keys `name: str`, `phone: str | None`,
  `birthdate: str | None`, `email: str | None`, `modality: str`,
  `diet_status: str`; `login(page, username, password) -> None` and
  `extract_patients(page) -> list[dict]`, both stubbed identically to Task 5
  (including the same per-patient try/except isolation requirement for the
  manual implementation).

- [ ] **Step 1: Write the failing test for `parse_patient`**

```python
# tests/test_webdiet.py
from crm.scraping.webdiet import parse_patient

def test_parse_patient_maps_raw_fields_to_source_record():
    raw = {
        "name": "Lais Sales", "phone": "11933334444", "birthdate": "1995-07-02",
        "email": "lais@example.com", "modality": "online", "diet_status": "ativo",
    }
    record = parse_patient(raw)
    assert record.name == "Lais Sales"
    assert record.email == "lais@example.com"
    assert record.raw == raw
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_webdiet.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `parse_patient`, `login`, `extract_patients` in `crm/scraping/webdiet.py`**

Mirrors Task 5 Step 3, mapping `email` and `modality`/`diet_status` from
`raw` in addition to `name`/`phone`/`birthdate`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_webdiet.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add crm/scraping/webdiet.py tests/test_webdiet.py
git commit -m "feat: add webdiet parsing layer (browser layer stubbed for manual wiring)"
```

---

## Task 7: cli.py — orchestration

**Files:**
- Create: `crm/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes:
  - `crm.scraping.liveclin.extract_patients(page) -> list[dict]` (Task 5)
  - `crm.scraping.liveclin.parse_patient(raw: dict) -> SourceRecord` (Task 5)
  - `crm.scraping.webdiet.extract_patients(page) -> list[dict]` (Task 6)
  - `crm.scraping.webdiet.parse_patient(raw: dict) -> SourceRecord` (Task 6)
  - `crm.matching.match_patients(...)` (Task 3)
  - `crm.db.init_db/insert_patient/insert_plan/insert_snapshot/get_all_plans` (Task 2)
  - `crm.renewal.get_renewal_candidates(...)` (Task 4)
- Produces:
  - `@dataclass UpdateResult: candidates: list[RenewalCandidate]; unmatched_liveclin: list[SourceRecord]; unmatched_webdiet: list[SourceRecord]`
  - `run_update(liveclin_raw_patients: list[dict], webdiet_raw_patients: list[dict], conn: sqlite3.Connection, today: date) -> UpdateResult`
    — pure orchestration function (no I/O besides the given `conn`), used by
    both the CLI entrypoint and tests. Parses both raw lists with the
    respective `parse_patient` (catching and logging — via
    `print(f"[erro] ...", file=sys.stderr)` — any exception per-record and
    skipping that record rather than aborting), matches them, writes
    patients/plans/snapshots to `conn` for each `MatchResult` (the plan dict
    passed to `insert_plan` is `{**match.liveclin.raw, "source":
    "liveclin"}` — `SourceRecord.raw` never carries `"source"` itself, so
    this key is always added explicitly here), and returns an `UpdateResult`
    with `candidates=renewal.get_renewal_candidates(db.get_all_plans(conn),
    today)` plus the `unmatched_liveclin`/`unmatched_webdiet` lists returned
    by `match_patients` unchanged — per the spec, unmatched patients are
    never dropped, only surfaced separately from the renewal list.
  - `main() -> None` — real entrypoint: reads env vars, drives Playwright
    (`login` + `extract_patients` for both systems), calls `run_update`,
    prints each `RenewalCandidate` one per line as `f"{c.patient_name} —
    {c.plan_type} — vence {c.end_date} ({c.used_sessions}/{c.contracted_sessions} consultas)"`,
    then, if `unmatched_liveclin` or `unmatched_webdiet` is non-empty, prints
    a `"Não cruzados:"` heading followed by each unmatched record's `.name`
    (one per line, LiveClin ones then WebDiet ones). Not unit-tested
    (depends on live browser + env vars); manual smoke test only.

- [ ] **Step 1: Write the failing test for `run_update` happy path**

```python
# tests/test_cli.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_run_update_matches_persists_and_returns_candidates -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `UpdateResult` and `run_update` in `crm/cli.py`**

Wire the steps described in Interfaces above: `parse_patient` both lists
(wrap each record's parse in `try/except Exception`, print to stderr, skip
on failure) → `match_patients` → for each `MatchResult` in `matches`,
`insert_patient` using the matched pair's fields (`name` from
`.liveclin.name`, `phone_liveclin` from `.liveclin.phone`, `phone_webdiet`
from `.webdiet.phone`, `birthdate`/`email` from whichever side has them,
`match_field` from `.matched_field`) then `insert_plan` with plan dict
`{**m.liveclin.raw, "source": "liveclin"}` and `insert_snapshot` with
`json.dumps({"liveclin": m.liveclin.raw, "webdiet": m.webdiet.raw})` →
build `UpdateResult(candidates=renewal.get_renewal_candidates(db.get_all_plans(conn), today),
unmatched_liveclin=unmatched_lc, unmatched_webdiet=unmatched_wd)` using the
`unmatched_lc`/`unmatched_wd` lists `match_patients` returned.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py::test_run_update_matches_persists_and_returns_candidates -v`
Expected: PASS

- [ ] **Step 5: Write the failing test for per-record failure isolation (Review Focus)**

```python
def test_run_update_skips_a_bad_record_without_aborting(tmp_path, capsys):
    conn = db.init_db(str(tmp_path / "test.db"))
    liveclin_raw = [
        {"name": "Registro Quebrado"},  # missing required raw fields -> parse_patient raises
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
```

Note: `parse_patient` as implemented in Task 5 reads fields with `.get(...)`
except `raw["name"]`, so a dict missing `"name"` raises `KeyError` — this
test relies on that. If Task 5's `parse_patient` is implemented differently
such that this record does not raise, adjust the fixture to omit `"name"`
instead of another field so it still raises.

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS (all tests in file)

- [ ] **Step 7: Implement `main()` in `crm/cli.py`**

Reads `LIVECLIN_USER`/`LIVECLIN_PASSWORD`/`WEBDIET_USER`/`WEBDIET_PASSWORD`
from `os.environ`, opens a Playwright browser context, calls
`liveclin.login`/`liveclin.extract_patients`,
`webdiet.login`/`webdiet.extract_patients`, `db.init_db("data/crm.db")`,
`run_update(...)`, then prints each candidate. Not unit-tested — this
function only becomes runnable once Task 5/6's `login`/`extract_patients`
stubs are replaced with real selectors (manual follow-up, per spec).

- [ ] **Step 8: Commit**

```bash
git add crm/cli.py tests/test_cli.py
git commit -m "feat: add cli orchestration (run_update + main entrypoint)"
```

---

## Manual follow-up (not part of this plan's automated tests)

Once `LIVECLIN_USER`/`LIVECLIN_PASSWORD`/`WEBDIET_USER`/`WEBDIET_PASSWORD`
are available in the environment, replace the `NotImplementedError` stubs in
`crm/scraping/liveclin.py` and `crm/scraping/webdiet.py`'s `login` and
`extract_patients` with real Playwright code against the live sites, and run
`crm.cli.main()` end-to-end against real accounts as the manual smoke test
the spec's testing section calls for.
