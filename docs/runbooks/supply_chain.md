# Supply Chain Runbook

## Purpose

Use the CI `supply-chain` job in `.github/workflows/ci.yml` as the repo-local Level 10
dependency vulnerability and provenance gate. The job first validates the hashed
production lock and SBOM, then installs the backend with development dependencies in a
clean GitHub Actions Python 3.12 environment, installs `pip-audit`, and runs
`pip-audit --local` against the installed backend dependency environment.

The CI workflow also includes a separate `dependency-attestations` job for GitHub
artifact attestations of the production lock and SBOM, plus a `container-image-scan` job
for backend image and base-image packages with CVEs. This runbook covers Python
dependency vulnerability scanning, dependency-update hygiene, and the boundaries to the
attestation and container scan jobs only. It does not change runtime behavior,
source-rights decisions, evidence semantics, report claims, or deployment authority.

## Validation

Run the static supply-chain configuration proof from the repository root:

```powershell
.\scripts\run_supply_chain_check.ps1
```

The Windows and POSIX wrappers delegate to `scripts/supply_chain_check.py` so local
and CI validation use the same validate-only logic.

The check is validate-only. It verifies that:

- `.github/workflows/ci.yml` has a `supply-chain` job.
- the job uses Python 3.12;
- the job installs `PyYAML` for static catalog parsing;
- the job runs `scripts/run_provenance_check.sh`;
- the job installs `backend[dev]`;
- the job installs `pip-audit`;
- the job runs `pip-audit --local`;
- `.github/workflows/ci.yml` has a `dependency-attestations` job using
  `actions/attest@v4` with GitHub OIDC, attestation, and artifact metadata permissions;
- `.github/dependabot.yml` covers GitHub Actions and backend Python dependencies;
- this runbook records known limits and incident escalation.

Run the production dependency provenance proof directly when dependency metadata changes:

```powershell
.\scripts\run_provenance_check.ps1
```

See `docs/runbooks/dependency_provenance.md` for the lock, SBOM, and refresh workflow.
See `docs/runbooks/container_image_scan.md` for the Docker Scout backend image scan.

## Operator Workflow

1. Treat a failing `supply-chain` job as a release blocker until the affected package,
   severity, exploitability, and reachable code path are reviewed.
2. Prefer upgrading the vulnerable package when the fix is compatible with the pinned
   product and evidence/report contracts.
3. If no safe upgrade exists, document the advisory, affected dependency, current
   exposure, compensating controls, and re-check date before accepting residual risk.
4. Do not suppress or ignore a scanner finding just to make CI pass.
5. Escalate through `docs/runbooks/incident_response.md` when a dependency issue could
   expose private data, corrupt evidence/claim/report state, bypass review gates, or
   materially mislead users.

## Dependabot Scope

`.github/dependabot.yml` requests weekly update checks for:

- GitHub Actions used by CI;
- backend Python packaging metadata under `/backend`.

Dependency update PRs still require the normal verification gates. A Dependabot PR alone
is not proof that dependency risk is gone; the CI supply-chain job must pass.

## Known Limits

- The CI scan depends on the advisory data available to `pip-audit` at run time.
- `backend/requirements-prod.lock` and `docs/sbom/backend-prod-sbom.json` are repo-local
  production dependency artifacts. CI publishes GitHub artifact attestations for those
  files only when repository entitlement is available. Private user-owned repositories
  without that entitlement record `Dependency attestations blocked` instead of claiming a
  live attestation. The repo does not yet publish a release package or registry image with
  an attached attestation.
- `pip-audit --local` audits the installed Python environment; Docker base-image package
  CVEs are handled by the separate `container-image-scan` job.
- The current CI gates do not scan GitHub Actions internals, hosted deployment runtime
  state, frontend packages, source licensing, or vendor data rights.
- Local validation proves the CI configuration shape. The live vulnerability scan itself
  runs in CI or when an operator explicitly installs and runs `pip-audit`.
