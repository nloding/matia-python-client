# Changelog

## 1.0.0a2

- Renamed the distribution from `matia-client` to `matia-python-client`.
- Fixed Python 3.9 compatibility by adding `eval-type-backport` as a conditional
  dependency (required for `pydantic` to resolve `X | None` style annotations
  on 3.9).
- Bumped CI workflow actions (`checkout`, `setup-python`, `upload-artifact`,
  `download-artifact`) to versions that run natively on Node.js 24.

## 1.0.0a1

First alpha release. The API surface may still change before `1.0.0`.

- **Assets** — create and update source/destination assets.
- **Integrations** — full CRUD, chainable connector builders for Postgres and
  Google Analytics 4, triggering and polling sync runs, and source
  schema/table/column config (enable/disable, hashing, primary keys).
- **Tags** — create, edit, delete, and assign/unassign tags to resources.
- **Audit logs** — paginated, filterable access to account activity, with a
  generator helper for walking every page.
- **Users** — list account users.
