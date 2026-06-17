# Design

## Source of truth
- Status: Active.
- Last refreshed: 2026-06-15.
- Primary product surfaces: server-rendered private operator UI under `/ui/*`; JSON APIs under `/operator-cases`, `/intake`, `/report-runs`, `/connector-review-queue`, and `/operations`; approved Markdown dossier and JSON artifact downloads.
- Canonical planning/design ownership: this repo-root `DESIGN.md`. Use docs and code as evidence, but do not create competing design briefs elsewhere.
- Evidence reviewed:
  - `docs/PRODUCT_SPEC.md`
  - `docs/ARCHITECTURE.md`
  - `docs/runbooks/mvp_operator.md`
  - `backend/app/api/ui.py`
  - `backend/app/api/ui_shared.py`
  - `backend/app/api/ui_review.py`
  - `backend/app/api/ui_operations.py`
  - `backend/app/api/ui_lineage.py`
  - `backend/app/api/operator_cases.py`
  - `backend/app/operator_cases/manifest.json`
  - `backend/app/main.py`
  - `backend/tests/api/test_ui_routes.py`
  - `backend/tests/api/test_operator_cases_api.py`
  - `backend/tests/private_mvp/test_operator_cases.py`

## Brand
- Personality: sober, evidence-first, operator-facing, private, precise, and cautious.
- Trust signals: explicit source lineage, approval gates, scoped reviewer sessions or credentials, optional approval notes, fixture/live-source boundaries, auditability, conservative caveats, and download links only after approval.
- Avoid: consumer real-estate polish, map-layer spectacle, marketing pages, unsupported legal/buildability/value conclusions, hidden uncertainty, and one-size-fits-all suitability scores.

## Product goals
- Goals: help a private operator produce screening-grade rural land diligence dossiers for selected North Carolina county cases and custom AOIs; expose report status, approval, retry, compare, lineage, connector review, and operations workflows; keep fixture-only and live-source-reviewed paths clearly separated.
- Non-goals: legal access determination, title/easement verification, surveyed boundary determination, wetland jurisdictional delineation, appraisal/value, lending/insurance eligibility, investment advice, protected-class or desirability scoring, and broad live paid-vendor coverage.
- Success signals: operators can create an approved selected-county fixture report, inspect caveats and lineage, compare report summaries, approve/retry with scoped credentials, and understand when a result is unknown, fixture-only, blocked, failed, or awaiting review.

## Personas and jobs
- Primary personas: private MVP operator; reviewer/QA operator; operations maintainer.
- User jobs: launch a selected-county fixture case; submit a custom Polygon or MultiPolygon AOI; monitor queued/running/succeeded/failed report runs; approve a report for delivery; retry failed jobs; review connector handoffs; resume a report after connector QA; inspect source-to-evidence-to-claim lineage; check queue health.
- Key contexts of use: trusted private network/local development, scoped browser reviewer sessions with per-action credential fallback, fixture-backed utility proof, and occasional DB-backed mode for persistence.

## Information architecture
- Primary navigation: home `/ui/`, report list `/ui/report-runs`, report detail `/ui/report-runs/{id}`, connector review queue `/ui/connector-review-queue`, operations `/ui/operations`, lineage `/ui/report-runs/{id}/lineage`, compare `/ui/compare`.
- Core routes/screens: selected-county fixture launcher, custom AOI intake form, report status/detail page with status-first action panel, approved dossier page/downloads, print/export page, report list with status filter, compare checkboxes, and next-action links, connector queue list with triage/next-action columns, connector detail/action forms, queue-health dashboard, evidence lineage tables; all operator support pages should include viewport-aware HTML heads.
- Content hierarchy: put current status and required operator action first; then key identifiers and links; then evidence, claims, caveats, downloads, or action forms; then secondary metadata.

## Design principles
- Principle 1: actionability before decoration. Every screen should answer "what state is this in, what can I do next, and what evidence supports it?"
- Principle 2: uncertainty is content, not an error to hide. Unknowns, source failures, fixture boundaries, and review blockers must be visible and plain.
- Principle 3: reuse the existing server-rendered UI patterns until a repo-confirmed product need justifies a broader UI layer.
- Tradeoffs: dense tables and forms are acceptable because the product is operator-facing; cautious language may feel less decisive but reduces false precision and liability.

## Visual language
- Color: keep the existing neutral work surface with blue-gray primary accents (`#2c3e50`, `#34495e`), light gray table/meta backgrounds (`#f8f9fa`), amber warnings (`#fff3cd`, `#ffc107`), green approvals (`#28a745`), red failures/errors (`#dc3545`, `#f8d7da`), and muted secondary text (`#666`). Do not broaden into a marketing gradient or decorative palette.
- Typography: system UI sans-serif for operator screens; monospace only for IDs, GeoJSON, raw metadata, and machine-readable snippets; print view may remain document-like.
- Spacing/layout rhythm: single-column pages with constrained widths around 800-1100px; compact form gaps; tables with scannable row padding.
- Shape/radius/elevation: 3-4px radius, borders over shadows, no nested decorative cards.
- Motion: minimal. Auto-refresh is appropriate for queued/running report pages; avoid nonessential animation.
- Imagery/iconography: none required for current operator workflows. If icons are introduced later, they must clarify actions rather than decorate.

## Components
- Existing components to reuse: `ui_shared.build_css`, `ui_shared.page_head`, `ui_shared.error_page`, `reviewer_credential_fields`, optional approval reason fields, status-filter forms, paginated tables, metadata panels, warning/error panels, action forms, compare checkboxes, lineage tags, and approved download links.
- New/changed components: the report-detail route uses a small shared report shell helper for queued/running, failed, missing, pending, and approved states. Prefer additional shared HTML/CSS helpers only after repeated use across UI modules; avoid a separate frontend framework until a repo-confirmed blocker exists.
- Variants and states: buttons and badges must distinguish primary, approve, reject, requeue, cancel, resume, retry, success, warning, failure, disabled/unavailable, and read-only dashboard states.
- Token/component ownership: current tokens are inline constants in the FastAPI UI modules, with shared base CSS in `backend/app/api/ui_shared.py`. Any future token consolidation should move toward that helper first.

## Accessibility
- Target standard: assume WCAG 2.1 AA for new UI work until a stricter project standard is chosen.
- Keyboard/focus behavior: preserve native links, forms, selects, textareas, buttons, checkboxes, and submit flows; keep all actions reachable without pointer-only controls; add visible focus styling when custom CSS would suppress browser defaults.
- Contrast/readability: maintain high contrast for body text and action buttons; do not rely on color alone for status, especially approval, warning, failure, and blocking issue states.
- Screen-reader semantics: use real headings, labels, captions where applicable, table headers, and concise link/button text that names the target action.
- Reduced motion and sensory considerations: avoid nonessential motion; queued/running auto-refresh pages must expose no-JavaScript pause/resume controls and a selectable refresh interval so monitoring does not interrupt inspection.

## Responsive behavior
- Supported breakpoints/devices: desktop and laptop browsers are primary; tablet/mobile should remain usable for inspection and emergency operations, not optimized as the main workflow.
- Layout adaptations: keep single-column forms fluid; allow tables and long UUIDs to wrap or scroll without overlapping; preserve action forms below the relevant status/context.
- Touch/hover differences: do not hide core actions behind hover; keep tap targets large enough for mobile use when the same route is viewed on touch devices.

## Interaction states
- Loading: queued/running report pages auto-refresh every 3 seconds by default, show status plainly with the report ID and expected next state, and expose 3/10/30/60-second interval, pause, manual-refresh, and resume controls without JavaScript.
- Empty: table screens should render explicit empty rows such as no report runs, no connector review items, no sources, no claims, or no evidence records.
- Monitoring: report-list and connector-review queue rows should expose the next existing operator surface for each state without duplicating credentialed mutation forms.
- Error: authentication, authorization, missing IDs, malformed UUIDs, invalid status filters, failed reports, and connector action conflicts must produce HTML pages or inline banners with a safe message and a return path.
- Success: redirects should land on the resulting report, queue detail, or refreshed list; approved reports should reveal dossier, artifact, print, and lineage links.
- Disabled: actions unavailable due to report state, review state, or missing scope should be absent or return the correct guarded response rather than implying completion.
- Offline/slow network, if applicable: assume private/local use; failed fetch or server errors should surface a plain error message and leave submitted content recoverable where feasible.

## Content voice
- Tone: direct, cautious, operational, and non-promotional.
- Terminology: use "screening", "selected-county private MVP fixture", "fixture-only", "not live coverage", "approved", "pending", "unknown", "source failure", "verification task", "reviewer credentials", "connector review", and "dossier" consistently.
- Microcopy rules: prefer "Available sources suggest...", "Mapped data indicates...", "No source was available to determine...", and "This requires confirmation by..."; avoid "You can build here", "legal access exists", "safe", "worth", "good investment", or other final professional conclusions.

## Implementation constraints
- Framework/styling system: FastAPI server-rendered HTML strings using inline CSS and shared helpers; no SPA, Storybook, Tailwind, or client build pipeline is repo-confirmed.
- Design-token constraints: keep existing color/radius/spacing conventions unless a specific workflow proves they fail; centralize only repeated patterns in `backend/app/api/ui_shared.py`.
- Performance constraints: avoid making the UI wait on arbitrary connector/raster/document work; use queued jobs, status pages, and review queues for long-running work.
- Compatibility constraints: the UI targets private trusted-network operation by default. When `REQUIRE_API_KEY=true`, JSON/API routes still require `X-API-Key`, while browser operators can use `/ui/auth` to exchange the configured API key for a signed, expiring, HttpOnly cookie scoped to `/ui`. Non-local API-key-locked app environments require `UI_AUTH_COOKIE_SECRET`; local/dev/development/test environments may use a per-process fallback. API reviewer tokens remain header-only and separate from API keys; browser reviewer actions can use `/ui/auth/reviewer` or first submitted action credentials to set a signed, expiring, HttpOnly reviewer session cookie scoped to `/ui`.
- Test/screenshot expectations: keep route behavior covered by existing FastAPI/TestClient UI tests; for browser validation, compare headed and headless Chrome when visual/browser behavior is material.

## Open questions
- [ ] Should `DESIGN.md` be promoted from this evidence-derived contract into a reviewed product/design baseline by a named product owner? Owner: product/operator lead. Impact: status and decision authority.
- [ ] What minimum browser/device support is required beyond current private desktop/laptop operation? Owner: operator lead. Impact: responsive testing scope.
- [ ] Should UI tokens remain inline/shared-helper based, or should a later production milestone introduce templates/components? Owner: engineering lead. Impact: maintainability and test approach.
- [ ] What is the approved external authentication posture for hosted/private beta environments? Owner: security/ops lead. Impact: UI access, API-key middleware, reviewer-token handling.
