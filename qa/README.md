# QA — DataPulse

This folder previously contained the QA test suite for DataPulse. The API tests have been migrated to a dedicated repository for better separation of concerns and independent CI execution.

---

## 🔗 API Test Repository

The full black-box API test suite is maintained here:

**[DataPulse API Test Suite — REST Assured](https://github.com/AmaliTech-Training-Academy/datapulse-api-tests)**

> Built with **REST Assured 5.4**, **JUnit 5**, and **Allure Reports**.

---

## 📋 Test Plan

The full test plan document is available here:

**[DataPulse QA Test Plan](https://amalitech-my.sharepoint.com/:w:/p/tob_adoba/IQAAn8sGCSbQT4gssbyXxAzOAdzFYX_Qs_bMx_pRqDv3oFw?e=MGu9eu)**

---

## ⚠️ Prerequisites — Start Docker First

Before running any tests, the DataPulse backend must be running.
From the `DataPulse_Team8` project root:

```bash
docker-compose up --build
```

Wait until the backend is healthy — verify at:

- `http://localhost:8000/health` → `{"status": "healthy"}`
- `http://localhost:8000/docs` → Swagger UI

---

## 🧪 Test Coverage

| Class | Tests | Covers |
|---|---|---|
| `AuthTest` | 14 | Register, login, weak passwords (parameterized), missing fields |
| `UploadTest` | 14 | CSV/JSON upload, file type/size/empty validation, auth, RBAC |
| `RulesTest` | 27 | All 5 rule types, invalid params, CRUD, RBAC |
| `ChecksTest` | 12 | Run, idempotency, score range, RBAC |
| `ReportsTest` | 19 | JSON + CSV format, field consistency, trend filters, RBAC |
| **Total** | **86** | Full API surface |

---

## 🚀 Quick Start

### Run all tests
```bash
mvn clean test
```

### Run a specific test class
```bash
mvn test -Dtest=AuthTest
mvn test -Dtest=RulesTest
```

### Generate Allure report
```bash
allure serve target/allure-results
```

For full setup and usage instructions, see the [API test repository](https://github.com/AmaliTech-Training-Academy/datapulse-api-tests).

---

## 📁 Files

| Folder | Contents |
|---|---|
| `api-tests/` | Legacy API test references |
| `test-plan/` | Test plan documents |
| `test-data/` | CSV files used for upload testing |