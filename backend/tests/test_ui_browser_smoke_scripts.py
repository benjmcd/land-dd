from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ui_browser_smoke.mjs"
POWERSHELL_WRAPPER = REPO_ROOT / "scripts" / "run_ui_browser_smoke.ps1"
POSIX_WRAPPER = REPO_ROOT / "scripts" / "run_ui_browser_smoke.sh"


def test_ui_browser_smoke_scripts_exist() -> None:
    assert SCRIPT.is_file()
    assert POWERSHELL_WRAPPER.is_file()
    assert POSIX_WRAPPER.is_file()


def test_ui_browser_smoke_contract_is_non_mutating_and_configurable() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert "LAND_DD_UI_SMOKE_BASE_URL" in script
    assert "--base-url" in script
    assert "LAND_DD_CHROME_PATH" in script
    assert "--chrome-path" in script
    assert "LAND_DD_UI_SMOKE_SCREENSHOT_DIR" in script
    assert "mkdtemp(join(tmpdir(), \"land-dd-ui-smoke-\"))" in script
    assert "await rm(profileDir, { recursive: true, force: true })" in script
    assert "local_artifacts" not in script
    assert "writeFile" in script
    assert "if (!screenshotDir)" in script
    assert "/areas" not in script
    assert "geom_geojson" not in script
    assert "area_id" not in script
    assert "intent_code" not in script


def test_ui_browser_smoke_checks_core_routes_and_viewports() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    for path in (
        "/ui/",
        "/ui/report-runs",
        "/ui/connector-review-queue",
        "/ui/auth",
        "/ui/auth/reviewer",
        "/ui/operations",
    ):
        assert path in script

    assert "{ name: \"desktop\", width: 1366, height: 900, mobile: false }" in script
    assert "{ name: \"mobile\", width: 390, height: 844, mobile: true }" in script
    assert "headless" in script
    assert "headed" in script
    assert "page-level horizontal overflow" in script
    assert "missing viewport meta" in script
    assert "found forbidden text" in script
    assert "Using reviewer session" in script
    assert "name=\"reviewer_token\"" in script


def test_ui_browser_smoke_wrappers_keep_check_explicit() -> None:
    powershell = POWERSHELL_WRAPPER.read_text(encoding="utf-8")
    posix = POSIX_WRAPPER.read_text(encoding="utf-8")

    assert "ui_browser_smoke.mjs" in powershell
    assert "ui_browser_smoke.mjs" in posix
    assert "LAND_DD_UI_SMOKE_BASE_URL" in powershell
    assert "LAND_DD_UI_SMOKE_BASE_URL" in posix
    assert "node @argsList" in powershell
    assert 'exec node "${args[@]}" "$@"' in posix

    verify_ps = (REPO_ROOT / "scripts" / "verify.ps1").read_text(encoding="utf-8")
    verify_sh = (REPO_ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8")
    assert "ui_browser_smoke" not in verify_ps
    assert "ui_browser_smoke" not in verify_sh


def test_mvp_operator_runbook_documents_ui_browser_smoke() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "mvp_operator.md").read_text(
        encoding="utf-8",
    )

    assert "## UI Browser Smoke" in runbook
    assert ".\\scripts\\run_ui_browser_smoke.ps1" in runbook
    assert "ui_runtime_smoke.py" in runbook
    assert "does not create areas, report runs, connector-review items" in runbook
    assert "--operator-case-id BUN-slope" in runbook
    assert "creates an in-memory approved report" in runbook
    assert "LAND_DD_UI_SMOKE_SCREENSHOT_DIR" in runbook


def test_manifest_routes_to_explicit_ui_smoke_gates() -> None:
    manifest = (REPO_ROOT / "MANIFEST.md").read_text(encoding="utf-8")

    for path in (
        "scripts/run_ui_browser_smoke.ps1",
        "scripts/run_ui_browser_smoke.sh",
        "scripts/ui_browser_smoke.mjs",
        "scripts/ui_runtime_smoke.py",
    ):
        assert path in manifest


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not available")
def test_ui_browser_smoke_script_has_valid_node_syntax() -> None:
    result = subprocess.run(
        ["node", "--check", str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
