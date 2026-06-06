# Runbook: Security Static Analysis (bandit)

## Overview

This runbook covers the `security-scan` CI gate, which runs [bandit](https://bandit.readthedocs.io/) static analysis against `backend/app` on every push and pull request.

## Scope

| Dimension | Value |
|---|---|
| Tool | bandit |
| Scanned path | `backend/app` (source code only) |
| Excluded paths | `backend/tests`, migrations, scripts |
| Severity threshold | `-ll` (medium and above reported; HIGH/CRITICAL cause CI failure) |
| CI job | `security-scan` |
| Analysis type | Static (SAST) only |

This gate does **not** cover:

- Dynamic analysis (DAST) — not yet implemented.
- Dependency vulnerability scanning — handled by the `supply-chain` job (`pip-audit`).
- Container image CVE scanning — handled by the `container-image-scan` job.

## Running locally

**Windows (PowerShell):**

```powershell
# Full scan
.\scripts\run_security_scan.ps1

# Check bandit is installed without scanning
.\scripts\run_security_scan.ps1 -ValidateOnly
```

**Linux/macOS (bash):**

```bash
# Full scan
./scripts/run_security_scan.sh

# Check bandit is installed without scanning
./scripts/run_security_scan.sh --validate-only
```

**Direct bandit invocation (from repo root):**

```bash
cd backend
python -m bandit -r app -ll -q
```

Install bandit if needed:

```bash
pip install bandit
```

## Severity threshold

bandit is invoked with `-ll`, which reports issues at **medium severity and above**.

The CI gate fails only when the output contains **HIGH** or **CRITICAL** severity findings. Medium findings are reported but do not block the build; they should be reviewed periodically.

## Handling false positives

When a finding is a confirmed false positive, suppress it inline with a `# nosec` comment that includes:

1. The bandit rule ID (e.g., `B105`).
2. A short justification explaining why the finding is safe.

Example:

```python
password = "test_fixture_only"  # nosec B105 # hardcoded only in test fixture, never in production
```

Guidelines:

- Do not add `# nosec` without a rule ID and justification — broad suppressions obscure real issues.
- Prefer fixing the code over suppressing the finding where feasible.
- Keep a record of suppressions in code review so they can be revisited if the context changes.

## CI job definition

The job is defined in `.github/workflows/ci.yml` under the key `security-scan`:

```yaml
security-scan:
  runs-on: ubuntu-latest
  permissions:
    contents: read
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - name: Install backend and bandit
      run: |
        python -m pip install -e "backend[dev]"
        python -m pip install bandit
    - name: Run bandit security scan
      run: bandit -r backend/app -ll -q
```

## Escalation

If a HIGH or CRITICAL finding cannot be immediately fixed and requires a tracked exception:

1. Open an issue describing the finding, location, and proposed remediation timeline.
2. Do **not** merge the PR until the exception is formally accepted or the finding is resolved.
3. Record the exception in `docs/adr/` if it represents an architecture-level decision.
