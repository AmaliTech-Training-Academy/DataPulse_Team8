# Temporary Artifacts (Do Not Use in Production)

This folder groups one-off files created during local troubleshooting.

## Structure
1. `airflow/`
- Local Airflow loading/debug helpers.
2. `sql/`
- Temporary SQL scripts used to bootstrap missing source objects in a local test stack.
3. `runtime/`
- Local runtime artifacts (`test.db`, uploaded files) from manual tests.

These files are not part of the stable DE1-to-DE2 data contract.
