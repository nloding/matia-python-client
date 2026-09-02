# Contributing

Thanks for considering a contribution to `matia-client`.

## Setup

```bash
poetry install
poetry run pytest
```

To work on the docs:

```bash
poetry install --with docs
poetry run mkdocs serve   # live preview at http://127.0.0.1:8000
```

## Making a change

1. Open an issue first for anything beyond a small fix, so we can agree on
   the approach before you put time into it.
2. Follow the existing conventions in the resource you're touching —
   `matia/resources/*.py` for API-calling methods, `matia/models/*.py` for
   the Pydantic models they return, `tests/test_*.py` (using `respx` to mock
   HTTP) for coverage of anything new.
3. Add or update tests for any behavior change. `poetry run pytest` must
   pass, and `poetry check` must stay clean.
4. Update `docs/reference/*.md` and `CHANGELOG.md` if the change is
   user-visible.
5. Open a pull request describing the change and why it's needed.

## Reporting bugs

Open a GitHub issue with a minimal reproduction. For security
vulnerabilities, see [SECURITY.md](SECURITY.md) instead of filing a public
issue.
