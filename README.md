# DataPulse — Complete Working Project

Data Quality Monitoring Platform · Team 8 · AmaliTech Training Academy

---

## What's Inside

This is the **fully implemented** version of DataPulse with all TODO stubs completed:

| Component | Status |
|-----------|--------|
| Auth (register/login/JWT) | ✅ Done |
| File Upload (CSV + JSON) | ✅ Done |
| Validation Rules CRUD | ✅ Done (incl. PUT + DELETE) |
| Validation Engine (all 5 rule types) | ✅ Done |
| Quality Scoring (weighted) | ✅ Done |
| Run Checks endpoint | ✅ Done |
| Reports endpoint | ✅ Done |
| Trends endpoint | ✅ Done |
| Full pytest test suite (84+ tests) | ✅ Done |

---

## Quick Start

### 1. Prerequisites
- Docker Desktop installed and running
- Git

### 2. Clone and run
```bash
git clone <your-repo-url>
cd 3-DataPulse
docker-compose up --build
```

API is live at: **http://localhost:8000**
Swagger docs at: **http://localhost:8000/docs**
User Interface at: **UI: http://localhost:3000**

### 3. Default credentials
| Role  | Email                  | Password    |
|-------|------------------------|-------------|
| Admin | admin@amalitech.com    | password123 |
| User  | user@amalitech.com     | password123 |

---

## Try It Manually (via Swagger)

1. Open **http://localhost:8000/docs**
2. **POST /api/auth/register** → create account → copy `access_token`
3. Click **Authorize** (top right) → paste token
4. **POST /api/datasets/upload** → upload a CSV from `qa/test-data/`
5. **POST /api/rules** → create a NOT_NULL rule for column `name`
6. **POST /api/checks/run/{dataset_id}** → run the check
7. **GET /api/reports/{dataset_id}** → see the quality report
8. **GET /api/reports/trends** → see trend data

---

## Run the Tests

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

### Run specific test groups
```bash
pytest tests/test_auth.py -v                  # Auth tests
pytest tests/test_upload.py -v                # Upload tests
pytest tests/test_rules.py -v                 # Rules CRUD tests
pytest tests/test_validation_engine.py -v     # Validation engine unit tests
pytest tests/test_scoring.py -v               # Scoring logic tests
pytest tests/test_checks.py -v                # Checks API tests
pytest tests/test_reports.py -v               # Reports & trends tests
pytest tests/test_e2e.py -v                   # End-to-end flows
```

### With coverage report
```bash
pytest --cov=app --cov-report=term-missing
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Login, get JWT token |
| POST | /api/datasets/upload | Upload CSV or JSON file |
| GET  | /api/datasets | List all datasets |
| POST | /api/rules | Create validation rule |
| GET  | /api/rules | List active rules |
| PUT  | /api/rules/{id} | Update a rule |
| DELETE | /api/rules/{id} | Soft-delete a rule |
| POST | /api/checks/run/{id} | Run checks on dataset |
| GET  | /api/checks/results/{id} | Get check results |
| GET  | /api/reports/{id} | Get quality report |
| GET  | /api/reports/trends | Get score trend data |

---

## Validation Rule Types

| Rule Type | Parameters | Description |
|-----------|-----------|-------------|
| NOT_NULL | — | Column must have no null values |
| DATA_TYPE | `{"expected_type": "int"}` | Values must be castable to int/float/str/bool |
| RANGE | `{"min": 0, "max": 100}` | Numeric values must fall within range |
| UNIQUE | — | All values in column must be unique |
| REGEX | `{"pattern": "^\\d{3}$"}` | Values must match regex pattern |

---

## Quality Score

Score = (weighted passing rules / total weight) × 100

| Severity | Weight |
|----------|--------|
| HIGH     | 3×     |
| MEDIUM   | 2×     |
| LOW      | 1×     |

---

## Tech Stack

- **Backend**: Python 3.11 / FastAPI / SQLAlchemy
- **Database**: PostgreSQL 15
- **Data Processing**: Pandas
- **Testing**: pytest + FastAPI TestClient
- **Infrastructure**: Docker / Docker Compose

✅ FIXED! Authentication is now working!
What we Fixed:
bcrypt compatibility issue - Replaced problematic bcrypt/passlib with a simple SHA-256 + salt hashing method
User credentials - Created user with proper hash in database
Login verification - Confirmed authentication works
Your Login Credentials:
Email: qa_user@datapulse.com
Password: qapassword12
Name: [Name]
Access Your Application:
UI: http://localhost:3000
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
Current Status:
✅ Backend: Running on port 8000
✅ Database: PostgreSQL running with user data
✅ Authentication: Working properly
✅ UI Server: Running on port 3000
Next Steps:
Open http://localhost:3000 in your browser
Click the login form (it should show the auth overlay)
Use credentials: qa_user@datapulse.com / qapassword12 or Create a new Account 
You should be able to access the full DataPulse dashboard!
