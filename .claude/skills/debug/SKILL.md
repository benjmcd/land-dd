---
name: debug
description: Diagnose and fix failing tests, broken scripts, runtime errors, or inconsistent agent state without broad refactors.
---

# Debug Skill

## Procedure

1. Reproduce the failure with the narrowest command.
2. Capture the exact error and affected files.
3. Identify whether the problem is test, code, environment, or data/fixture.
4. Make the smallest fix that addresses the root cause.
5. Re-run the narrow command, then `./scripts/verify.sh` if the fix is material.
6. Update `state/VALIDATION_LOG.md` with command, result, and residual risk.

Do not skip, weaken, or delete tests to create a passing state unless the active plan explicitly calls for replacing them with stronger tests.
