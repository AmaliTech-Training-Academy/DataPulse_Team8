# DataPulse — QA Test Suite

**QA Engineer:** Tob Adoba | **Team 8**

---

## Setup

```bash
cd backend
pip install -r requirements.txt
```

---

## Running Tests

```bash
# Run everything
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run a specific file
pytest tests/test_auth.py -v

# Run only currently-passing tests (skip xfail)
pytest -v --ignore=tests/test_e2e.py

# Run only unit tests (validation engine, scoring)
pytest tests/test_validation_engine.py tests/test_scoring.py -v

# Show xfail reasons explicitly
pytest -v --runxfail
```

---

## Test Files & Coverage

| File | TC IDs | What It Tests |
|------|--------|---------------|
| `test_auth.py` | TC-A01–A10 | Register, login, JWT protection |
| `test_upload.py` | TC-U01–U12 | CSV/JSON upload, listing, pagination |
| `test_rules.py` | TC-R01–R13 | Rule CRUD, filtering, validation |
| `test_validation_engine.py` | TC-V01–V22 | All 5 rule types, edge cases |
| `test_scoring.py` | TC-S01–S06 | Weighted quality score calculation |
| `test_checks.py` | TC-C01–C07 | Run checks endpoint, get results |
| `test_reports.py` | TC-P01–P08 | Report generation, trends |
| `test_e2e.py` | TC-E01–E06 | Full user journey flows |

---

## xfail Tests

Tests marked `@pytest.mark.xfail` correspond to **unimplemented endpoints** (BUG-001 through BUG-010 in the Test Plan). They will:
- Show as `XFAIL` when the endpoint is still a stub (expected)
- Automatically turn `XPASS` (unexpected pass) once the backend team implements them

**Current stubs (as of sprint start):**
- BUG-001: `POST /api/checks/run/{id}`
- BUG-002: `GET /api/checks/results/{id}`
- BUG-003: `GET /api/reports/{id}`
- BUG-004: `GET /api/reports/trends`
- BUG-005: `PUT /api/rules/{id}`
- BUG-006: `DELETE /api/rules/{id}`
- BUG-007: `validation_engine.type_check`
- BUG-008: `validation_engine.range_check`
- BUG-009: `validation_engine.unique_check`
- BUG-010: `scoring_service.calculate_quality_score`

---

## Test Data

| File | Description |
|------|-------------|
| `qa/test-data/valid_test.csv` | 5-row clean dataset |
| `qa/test-data/invalid_test.csv` | 5-row dirty dataset (nulls, bad types) |
| Inline in `conftest.py` | `CLEAN_CSV`, `DIRTY_CSV`, `MIXED_CSV` constants |
