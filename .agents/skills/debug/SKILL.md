---
name: debug
description: Debug failing tests, migrations, scripts, or runtime behavior using reproduce-isolate-fix-verify loops.
---

# Debug Skill

1. Reproduce the failure with the narrowest command.
2. Capture exact error output.
3. Identify the smallest relevant code path.
4. Form 1-3 hypotheses; test the strongest first.
5. Make the smallest safe fix.
6. Run the failing check again.
7. Run broader verification if the fix touches shared code.
8. Update the active plan/worklog if the issue changes scope.
