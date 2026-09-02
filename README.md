# matia-python-client

An idiomatic, fluent Python client library for the [Matia](https://matia.io) API.

This is a library only — import it into your own scripts/services. It is not a CLI tool.

## Install

```bash
poetry add matia-python-client
```

> **Note:** the current release is a pre-1.0 alpha (`1.0.0a2`). Plain
> `pip install matia-python-client` / `poetry add matia-python-client` will not pull it in,
> since package managers skip pre-releases by default. Use
> `pip install --pre matia-python-client` or pin the exact version
> (`pip install matia-python-client==1.0.0a2`) to try it.

## Usage

```python
from matia import MatiaClient

client = MatiaClient(api_key="...")
integrations = client.integrations.list()
```

See [`docs/quickstart.md`](docs/quickstart.md) for the full usage guide (fluent model
methods, the chainable integration builder, audit log pagination), and
[`docs/reference/`](docs/reference) for the complete API reference.

## Development

```bash
poetry install
poetry run pytest
```

## Documentation

Docs are built with [MkDocs](https://www.mkdocs.org/) + [mkdocstrings](https://mkdocstrings.github.io/).

```bash
poetry install --with docs
poetry run mkdocs serve   # live preview at http://127.0.0.1:8000
poetry run mkdocs build   # static site output in site/
```
