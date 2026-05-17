from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"HARNESS FAIL: {message}")
    raise SystemExit(1)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def iter_py_files(root: Path) -> list[Path]:
    ignored = {".git", ".venv", "__pycache__", ".pytest_cache"}
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in ignored for part in path.parts):
            continue
        files.append(path)
    return files


def imports_from(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        fail(f"cannot parse {path.relative_to(ROOT)}: {exc}")
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def check_versions() -> None:
    version = read("VERSION").strip()
    if not re.fullmatch(r"v\d+_\d+_\d+", version):
        fail(f"VERSION has unexpected format: {version!r}")
    expected_py = version.removeprefix("v").replace("_", ".")
    if f'version = "{expected_py}"' not in read("pyproject.toml"):
        fail("pyproject.toml version does not match VERSION")
    if f'ENGINE_VERSION_TAG = "{version}"' not in read("src/jammate_engine/api/version.py"):
        fail("ENGINE_VERSION_TAG does not match VERSION")
    if version not in read("README.md"):
        fail("README.md does not mention active VERSION")
    if version not in read("agent.md"):
        fail("agent.md does not mention active VERSION")
    if version not in read("docs/CHANGELOG.md"):
        fail("docs/CHANGELOG.md does not mention active VERSION")
    if f'CONTRACT_VERSION = "{version}"' not in read("src/jammate_agent/core/contract_codegen.py"):
        fail("contract_codegen CONTRACT_VERSION does not match VERSION")


def check_required_docs() -> None:
    required = [
        "README.md",
        "agent.md",
        "docs/ARCHITECTURE_V2.md",
        "docs/API_CONTRACT_V2.md",
        "docs/DEVELOPMENT_TASK_PLAN_V2.md",
        "docs/DEVELOPMENT_HARNESS_V2.md",
        "docs/NEW_FILE_PLACEMENT_GUIDE_V2.md",
        "docs/GENERATION_RULES_SUMMARY_V2.md",
        "docs/STYLE_RULE_BASELINE_V2.md",
        "docs/STYLE_TUNING_ENTRY_POINT_V2.md",
        "docs/FUTURE_IDEAS_BACKLOG_V2.md",
        "docs/CHANGELOG.md",
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            fail(f"missing required doc: {rel}")


def check_document_roles() -> None:
    readme = read("README.md")
    agent = read("agent.md")
    changelog = read("docs/CHANGELOG.md")
    if re.search(r"^##\s+v\d+_\d+_\d+", readme, flags=re.MULTILINE):
        fail("README.md must not contain chronological version-heading changelog blocks")
    if len(agent.splitlines()) > 180:
        fail("agent.md should remain compact; move details to docs/DEVELOPMENT_HARNESS_V2.md")
    for token in ("Core Design Principles", "Directory Architecture", "Current Main Capabilities"):
        if token not in readme:
            fail(f"README.md missing project overview token: {token}")
    for token in ("Mandatory Architecture Boundary", "Cleanup Before Every Delivery", "Minimal File Split Principle"):
        if token not in agent:
            fail(f"agent.md missing hard harness token: {token}")
    current_version = read("VERSION").strip()
    if current_version not in changelog or "v2_3_17" not in changelog or "v2_3_10" not in changelog:
        fail("CHANGELOG.md must contain current and recent project history")


def check_architecture_boundaries() -> None:
    for path in iter_py_files(ROOT / "src" / "jammate_engine"):
        for module in imports_from(path):
            if module == "jammate_agent" or module.startswith("jammate_agent."):
                fail(f"engine must not import agent: {path.relative_to(ROOT)}")

    agent_root = ROOT / "src" / "jammate_agent"
    adapters_root = agent_root / "adapters"
    for path in iter_py_files(agent_root):
        if adapters_root in path.parents:
            continue
        for module in imports_from(path):
            if module == "jammate_engine" or module.startswith("jammate_engine."):
                fail(f"agent may use engine only through adapters: {path.relative_to(ROOT)}")


def check_harness_rules_documented() -> None:
    combined = "\n".join(
        read(rel)
        for rel in [
            "agent.md",
            "docs/DEVELOPMENT_HARNESS_V2.md",
            "docs/NEW_FILE_PLACEMENT_GUIDE_V2.md",
        ]
    )
    for token in (
        "Capability Reuse Before New Construction",
        "reuse audit",
        "local implementation",
        "adapter",
        "facade",
        "metadata",
        "core/harmony/harmonic_context.py",
        "Minimal File Split Principle",
        "Future Ideas Backlog",
        "GENERATION_RULES_SUMMARY_V2.md",
    ):
        if token not in combined:
            fail(f"harness docs missing token: {token}")


def check_harmonyos_contract_pack() -> None:
    required = [
        "frontend_fixtures/harmonyos/README.md",
        "frontend_fixtures/harmonyos/types/AgentTypes.ets",
        "frontend_fixtures/harmonyos/types/PracticeTypes.ets",
        "frontend_fixtures/harmonyos/types/PlaybackTypes.ets",
        "frontend_fixtures/harmonyos/api/JamMateApiClient.ets",
        "frontend_fixtures/harmonyos/api/CaseAdapter.ets",
        "frontend_fixtures/harmonyos/fixtures/PracticeFixtures.json",
        "frontend_fixtures/harmonyos/smoke/curl_smoke.sh",
        "frontend_fixtures/harmonyos/smoke/smoke_pack.json",
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            fail(f"missing HarmonyOS fixture/contract file: {rel}")


def check_cleanup_sensitive_files() -> None:
    forbidden_names = {".env", ".DS_Store"}
    forbidden_dirs = {"agent_traces"}
    for path in ROOT.rglob("*"):
        parts = set(path.parts)
        if ".git" in parts or ".venv" in parts or "__pycache__" in parts or ".pytest_cache" in parts:
            continue
        if path.name in forbidden_names:
            fail(f"forbidden local file in package: {path.relative_to(ROOT)}")
        if path.is_dir() and path.name in forbidden_dirs:
            fail(f"transient trace directory should not be packaged: {path.relative_to(ROOT)}")


def check_capability_reuse_before_new_construction_documented() -> None:
    # Kept as a stable named check because older targeted tests and developer habits reference it.
    check_harness_rules_documented()


def main() -> int:
    checks = [
        check_versions,
        check_required_docs,
        check_document_roles,
        check_architecture_boundaries,
        check_harness_rules_documented,
        check_harmonyos_contract_pack,
        check_cleanup_sensitive_files,
    ]
    for check in checks:
        check()
    print("HARNESS OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
