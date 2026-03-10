# Running CI/CD Pipeline Locally

This guide explains how to run the DataPulse CI/CD pipeline locally on your machine.

## Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for linting step)
- Git

## Pipeline Overview

The CI/CD pipeline consists of three jobs:

1. **Lint** - Runs flake8 to check for syntax errors
2. **Test** - Runs pytest with PostgreSQL database
3. **Build** - Builds Docker image and performs health check

---

## Method 1: Full Pipeline with Docker Compose (Recommended)

Run the entire test suite using Docker Compose:

```bash
# Run tests (lint + pytest + PostgreSQL)
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

This will:

- Start a PostgreSQL container
- Build the API container
- Run all tests
- Output results

**Note:** Tests have some failures due to missing test data files - this is expected until the test data is created.

---

## Method 2: Individual Steps

### Step 1: Lint (flake8)

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install flake8
pip install flake8

# Run linting
flake8 backend/app/ --count --select=E9,F63,F7,F82 --show-source --statistics
```

**Expected:** Exit code 0 with 0 errors

---

### Step 2: Tests (pytest)

Option A: Using Docker Compose (includes PostgreSQL):

```bash
docker-compose -f docker-compose.test.yml up --build api_test
```

Option B: Local with PostgreSQL:

```bash
# Start PostgreSQL
docker run -d --name datapulse-postgres \
  -e POSTGRES_USER=datapulse_user \
  -e POSTGRES_PASSWORD=datapulse_pass \
  -e POSTGRES_DB=datapulse_db_test \
  -p 5432:5432 postgres:15-alpine

# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Run tests
DATABASE_URL=postgresql://datapulse_user:datapulse_pass@localhost:5432/datapulse_db_test \
TEST_DATABASE_URL=postgresql://datapulse_user:datapulse_pass@localhost:5432/datapulse_db_test \
APP_ENV=test \
pytest backend/tests/ -v
```

---

### Step 3: Build Docker Image

```bash
# Build the image
docker build -t datapulse-api:latest -f backend/Dockerfile ./backend

# Run container health check
docker run -d --name test-api datapulse-api:latest
sleep 5
docker logs test-api
docker stop test-api
docker rm test-api
```

**Note:** The container will fail to start if no database is connected - this is expected. The build itself is successful.

---

## Git Branches

To pull all branches from remote:

```bash
# Fetch all branches
git fetch --all

# Create local tracking branches for each remote branch
for branch in $(git branch -r | grep -v HEAD); do
  git branch --track "${branch#origin/}" "$branch" 2>/dev/null || true
done

# Pull all branches
git pull --all
```

---

## Troubleshooting

### psycopg2-binary installation fails

If you get `pg_config executable not found`, use Docker instead of local Python.

### Port 5432 already in use

Either stop the existing PostgreSQL container or modify the port in docker-compose.test.yml.

### Test failures

Current test failures are due to:

1. Missing test data files in `tests/data/`
2. Test helpers not matching current API schema (e.g., `severity` field required for rules)

---

## References

- CI Workflow: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
- Test Config: [`docker-compose.test.yml`](docker-compose.test.yml)
- Backend Dockerfile: [`backend/Dockerfile`](backend/Dockerfile)
