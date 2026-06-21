# Milestone and Qualification Mapping

## Purpose

`MILESTONE_MAP.md` and the empirical qualification framework answer different questions.

```text
Milestone map:
  How much governed implementation exists?

Qualification framework:
  What bounded claims are supported by empirical, operational, security,
  data-quality, and release evidence?
```

Neither substitutes for the other.

## Mapping

| Implementation state | Qualification state | Permitted description |
|---|---|---|
| Levels 1–8 incomplete | Any empirical gate | The lower implementation layer remains incomplete; higher evidence cannot establish repository maturity. |
| Level 9 fixture/regression workflow passes | `L9-R` | Repo-proven private MVP. No empirical accuracy, user-utility, production, or expansion claim. |
| Level 9 + P0/Q1 | `L9-E1` | Bounded empirically screened MVP for the exact frozen scope. |
| Level 9 + P0/Q1/Q2 | `L9-E2` | Bounded user-validated MVP for the exact frozen users/tasks/scope. |
| Level 10 local operational gates + L9-E2 | `L10-BP-LOCAL` | Production-grade only for the frozen local/single-user profile. |
| Level 10 hosted single-tenant gates + L9-E2 | `L10-BP-ST` | Production-grade only for the frozen hosted single-tenant profile. |
| Level 10 public multi-tenant gates + L9-E2 | `L10-BP-MT` | Production-grade only for the frozen public multi-tenant profile. |
| Valid bounded base + Q3A/Q3B | `X-US` | US expansion-ready architecture; not nationwide qualified coverage. |
| `X-US` + Q3C | `X-GLOBAL-ARCH` | Global architecture probed; not worldwide operational or legal diligence. |
| Exact jurisdiction's own gates pass | `J-QUALIFIED-<jurisdiction>` | That named jurisdiction/intent/domain/deployment scope is qualified. |

## Hard rules

1. Higher-level code built on an incomplete lower milestone does not raise maturity.
2. A large automated test suite establishes neither Q1 nor Q2.
3. A Q3 architecture probe establishes neither production readiness nor new-jurisdiction correctness.
4. A production-grade bounded scope does not require unrelated Q3 expansion work.
5. Enabling candidate generation, financial outputs, AI, or commercial operation activates CG, FIN, AI, or E respectively.
6. A classification expires or becomes invalid when mapped source, rule, report, geometry, DB, UI, deployment, or rights changes occur.
7. The repo state must record implementation milestone and qualification classification separately.

## Recommended state record

```yaml
implementation:
  achieved_milestone: 9
  target_milestone: 10
  status: CONDITIONAL_PASS

qualification:
  highest_valid_classification: L9-R
  selected_product_scope_profile: BOUNDED_USER_VALIDATED
  selected_deployment_profile: LOCAL_SINGLE_USER
  p0_status: NOT_RUN
  next_gate: P0
  evidence_path: null

expansion:
  q3a_status: NOT_RUN
  q3b_status: NOT_RUN
  q3c_status: NOT_RUN
```
