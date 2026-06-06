# Container Image Scan Runbook

## Purpose

Use the CI `container-image-scan` job in `.github/workflows/ci.yml` as the
repo-local Level 10 container vulnerability gate. The job builds the backend image from
`backend/Dockerfile`, keeps it in the GitHub Actions runner local image store, and runs
Docker Scout `cves` against `local://land-diligence-backend:${{ github.sha }}` for
critical and high severity CVEs. The backend Dockerfile pins the runtime base image to
the current `python:3.12-slim` OCI index digest:
`sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203`.

This runbook covers backend container image vulnerability scanning only. It does not
change runtime behavior, source-rights decisions, evidence semantics, report claims, or
deployment authority.

## Validation

Run the static container scan configuration proof from the repository root:

```powershell
.\scripts\run_container_scan_check.ps1
```

The check is validate-only. It verifies that:

- `.github/workflows/ci.yml` has a `container-image-scan` job.
- the job builds `backend/Dockerfile` into a local backend image tag.
- the job runs `docker/scout-action@v1` with `command: cves`.
- the Scout image reference uses `local://` so the runner scans the just-built image.
- the Scout action is scoped to `critical,high` severities and fails closed with
  `exit-code: true`.
- `backend/Dockerfile` records the current runtime base image tag and digest.
- `.dockerignore` excludes repo-local state, archives, tests, and planning-pack content
  from the image build context.

## Operator Workflow

1. Treat a failing `container-image-scan` job as a release blocker until the affected
   package, severity, exploitability, and reachable code path are reviewed.
2. Prefer refreshing the pinned base image digest or upgrading the vulnerable package
   when the fix is compatible with the pinned product and evidence/report contracts.
3. If no safe upgrade exists, document the CVE, affected image/package, current
   exposure, compensating controls, and re-check date before accepting residual risk.
4. Do not suppress, ignore, or blanket-exempt critical/high image findings just to make
   CI pass.
5. Escalate through `docs/runbooks/incident_response.md` when an image vulnerability
   could expose private data, corrupt evidence/claim/report state, bypass review gates,
   or materially mislead users.

## Known Limits

- The CI scan depends on Docker Scout advisory data available at run time.
- The job scans the backend image built locally in CI; it does not prove any separately
  published registry image.
- The current base image is pinned to the `python:3.12-slim` OCI index digest above.
- This repo does not yet publish a signed image SBOM or SLSA provenance attestation.
- This scan does not evaluate GitHub Actions internals, hosted deployment runtime state,
  frontend packages, source licensing, or vendor data rights.
