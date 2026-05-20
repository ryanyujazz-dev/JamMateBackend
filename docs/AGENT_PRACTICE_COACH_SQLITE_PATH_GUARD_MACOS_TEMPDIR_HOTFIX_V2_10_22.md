# v2_10_22 — Practice Coach SQLite Path Guard macOS Tempdir Hotfix

## Summary

`v2_10_22` fixes a local-development compatibility issue in the Practice Coach Session SQLite state store path guard.

The previous guard allowed absolute SQLite paths under `/mnt/data/` and `/tmp/`. That worked in the Linux/sandbox environment, but macOS pytest commonly creates temporary paths under `/private/var/folders/...`, which caused valid local tests to fail with:

```text
blockedReasons: ["sqlite_db_path_not_allowed_for_practice_coach_state_store"]
```

This was not an LLM action decision bug and not a Practice Coach response repair bug. The failure came from the DB-path safety allowlist being too Linux-specific.

## Fix

The guard now allows SQLite paths under the current OS tempdir root:

```python
Path(tempfile.gettempdir()).resolve(strict=False)
```

The full allowed local-development roots are:

```text
/mnt/data
/tmp
Path(tempfile.gettempdir()).resolve(strict=False)
```

This keeps Linux, sandbox, and macOS local pytest compatible while still rejecting unsafe absolute paths outside approved dev temp roots.

## Safety retained

The guard still rejects:

```text
paths containing ..
paths containing production/prod/secrets/private_key/api_key markers
paths not ending in .db / .sqlite / .sqlite3
unsafe absolute paths outside approved local-development roots
```

Relative local SQLite filenames are still allowed for development/test use.

## Scope boundary

This is an Agent / Integration compatibility hotfix only.

Unchanged boundaries:

```text
不启动 Routine
不调用 Engine
不生成 MIDI
不播放
不写 HarmonyOS 本地状态
```

No Engine music generation code was changed.

## Test coverage

Added:

```text
tests/test_v2_10_22_agent_practice_coach_sqlite_path_guard_macos_tempdir_hotfix.py
```

The tests verify:

```text
macOS-style /private/var/folders/... tempdir paths are allowed when they are under tempfile.gettempdir()
unsafe absolute paths remain blocked
the unified Practice Coach endpoint can persist state with a macOS-style tempdir SQLite path
API/docs/changelog record the v2_10_22 hotfix
```
