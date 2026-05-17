# v2_3_17 — Harness Hardening and Changelog Split

## Goal

Make the development harness more useful in future ChatGPT / Claude Code windows.

Before this pass, the harness checker and development harness docs had accumulated too much historical token-locking. That made them noisy and less useful as actual development constraints.

## Changes

- `agent.md` is now the short hard harness.
- `docs/DEVELOPMENT_HARNESS_V2.md` is the expanded harness explanation.
- `docs/CHANGELOG.md` is the canonical chronological version history.
- `tools/check_development_harness.py` is now a focused automated checker for:
  - version consistency;
  - required docs;
  - architecture import boundaries;
  - README/agent/changelog separation;
  - cleanup-sensitive paths;
  - HarmonyOS fixture presence;
  - required harness concepts.
- Added `tests/test_v2_3_17_harness_hardening_and_changelog_split.py`.

## Runtime Impact

No runtime music-generation behavior changed.

## Required Delivery Habit

Every future engineering delivery should run:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
```

Then run targeted pytest for the changed area.
