# Open Questions

## codex-handoff-hardening - 2026-06-04

- [ ] Should the model pin be `gpt-5.5` (matching current config) or a different model? The plan assumes `gpt-5.5` since that is what `~/.codex/config.toml` currently specifies. -- Affects Step 1.5.
- [ ] Should reasoning effort be `xhigh` for all handoff tasks, or should the script accept an optional second argument to override? Some tasks (simple PR creation) may not need xhigh. -- Affects Step 1.6 and cost.
- [ ] The global config has `model_reasoning_effort = "low"`. Was this intentional for interactive Codex use, or was it set during testing? If intentional, the per-invocation override in the handoff script is correct. If accidental, fixing the global config would also help. -- Context for Step 1.6.
- [ ] If `--last --all` still mis-targets (picks a session from a different project), should we fall back to Option B (session registry)? -- Follow-up monitoring item.
