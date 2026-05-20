# v2_10_28 — Context Persistence SQLite Path Guard macOS Tempdir Hotfix

## Problem

`routine-completion-record/execute` uses the context persistence SQLite store in `tool_invocation.py`.

The Practice Coach session-state guard was already fixed in v2_10_22 to allow the current OS tempdir via:

```python
Path(tempfile.gettempdir()).resolve(strict=False)
```

But the routine completion context persistence guard still only allowed `/mnt/data/`, `/tmp/`, or relative paths.

On macOS, `pytest` temp paths commonly resolve under:

```text
/private/var/folders/.../T/...
```

That caused route tests involving routine completion history persistence to fail with:

```text
blockedReasons: ["sqlite_db_path_not_allowed_for_practice_coach_state_store"]
```

## Fix

`_is_allowed_context_persistence_sqlite_path()` now:

- Allows relative `.db` / `.sqlite` / `.sqlite3` paths.
- Allows paths under `/mnt/data`.
- Allows paths under `/tmp`.
- Allows paths under the current resolved system tempdir from `tempfile.gettempdir()`.
- Still rejects path traversal, production/secrets/private-key/API-key paths, and non-SQLite extensions.

## Scope

Agent / Integration only.

No Engine generation logic changed.

## Regression tests

Added:

```text
tests/test_v2_10_28_agent_context_persistence_sqlite_path_guard_macos_tempdir_hotfix.py
```

Coverage:

- Direct guard accepts current system tempdir.
- Direct guard accepts macOS `/private/var/folders/.../T/...` shape when that is the current tempdir.
- Direct guard still rejects dangerous paths.
- `routine-completion-record/execute` can persist into the current system tempdir.
