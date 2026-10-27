# Development guide

## Requirements

- Python 3.10 or newer
- `uv` for environment and dependency management
- Node.js 22 only for the optional upstream parity harness
- `just` is optional; commands can be run directly with `uv`

## Setup

```sh
uv sync
```

## Quality checks

```sh
uv run prek run --all-files --show-diff-on-failure
uv run pytest -q
```

Run tests serially when debugging:

```sh
uv run pytest -n0 -q
```

Run a targeted test module:

```sh
uv run pytest -n0 tests/test_game_data.py -q
```

## Manual smoke tests

```sh
uv run pqcli --help
uv run pqcli --dump-data /tmp/pqcli-data
uv run pqcli --data-dir /tmp/pqcli-data --list-saves
```

The `--dump-data` command intentionally refuses to overwrite existing JSON
files. Use a new temporary directory when validating it.

## Save format caution

Native roster saves remain pickle-based for compatibility; only load save files
from trusted sources. Use `.pqw` for character exchange. See [the security
guide](../SECURITY.md).
