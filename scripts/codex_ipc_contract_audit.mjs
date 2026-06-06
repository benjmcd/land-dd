#!/usr/bin/env node
// Static/read-only requirement audit for the Claude Code -> Codex Desktop IPC system.
//
// This emits a requirement matrix from current repo files. It does not connect
// to the IPC pipe, does not inspect SQLite, does not send prompts, and does not
// write artifacts. Use codex_ipc_revalidate.mjs for runtime/presence checks.

import { existsSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

const REQUIRED_FILES = [
  "scripts/handoff_to_codex.sh",
  "scripts/codex_ipc_client.mjs",
  "scripts/codex_ipc_owner_probe.mjs",
  "scripts/codex_ipc_probe.mjs",
  "scripts/codex_ipc_revalidate.mjs",
  "scripts/codex_ipc_session_inspect.mjs",
  "scripts/codex_ipc_snapshot.mjs",
  "scripts/codex_ipc_thread_locator.mjs",
  "scripts/codex_ipc_write_proof.mjs",
  "scripts/check_json_files.py",
  "state/agent-inbox/README.md",
  ".claude/skills/ipc/SKILL.md",
  ".claude/commands/ipc.md",
  ".claude/skills/handoff-to-codex",
  "plans/2026-06-04-codex-ipc-injection.md",
  ".omc/prd.json",
  ".omc/progress.txt",
  "state/WORKLOG.md",
  "state/VALIDATION_LOG.md",
];

function usage() {
  return `Usage:
  node scripts/codex_ipc_contract_audit.mjs

Safety:
  Static/read-only audit only. Reads repo files and emits JSON. It does not
  connect to IPC, inspect SQLite, send prompts, or write artifacts.`;
}

function readText(filePath) {
  return readFileSync(filePath, "utf8");
}

function fileInfo(filePath) {
  if (!existsSync(filePath)) {
    return { ok: false, path: filePath, exists: false };
  }
  const stat = statSync(filePath);
  return {
    ok: stat.isFile(),
    path: filePath,
    exists: true,
    isFile: stat.isFile(),
    size: stat.size,
    mtimeMs: stat.mtimeMs,
  };
}

function contains(filePath, pattern) {
  if (!existsSync(filePath)) {
    return false;
  }
  const text = readText(filePath);
  if (pattern instanceof RegExp) {
    return pattern.test(text);
  }
  return text.includes(pattern);
}

function jsonParses(filePath) {
  try {
    JSON.parse(readText(filePath));
    return true;
  } catch {
    return false;
  }
}

function check(id, requirement, evidenceChecks, residualRisk = null) {
  const evidence = evidenceChecks.map((item) => ({
    label: item.label,
    file: item.file || null,
    ok: Boolean(item.ok),
  }));
  return {
    id,
    requirement,
    status: evidence.every((item) => item.ok) ? "evidenced" : "missing-or-weak",
    evidence,
    residualRisk,
  };
}

function main() {
  const files = Object.fromEntries(REQUIRED_FILES.map((filePath) => [filePath, fileInfo(filePath)]));
  const requirements = [
    check("REQ-001", "The default handoff path remains file-drop and GUI-safe.", [
      {
        label: "handoff script defaults to filedrop",
        file: "scripts/handoff_to_codex.sh",
        ok: contains("scripts/handoff_to_codex.sh", 'MODE="filedrop"'),
      },
      {
        label: "inbox README presents file-drop as recommended/default",
        file: "state/agent-inbox/README.md",
        ok:
          contains("state/agent-inbox/README.md", "file-drop, recommended") &&
          contains("state/agent-inbox/README.md", "read state/agent-inbox/for-codex.md and proceed"),
      },
    ]),
    check("REQ-002", "Live IPC is opt-in, explicit-target, and starts from a caller-supplied UUID.", [
      {
        label: "handoff script exposes --ipc mode",
        file: "scripts/handoff_to_codex.sh",
        ok: contains("scripts/handoff_to_codex.sh", "--ipc <conversationId>"),
      },
      {
        label: "handoff script validates IPC conversationId as UUID",
        file: "scripts/handoff_to_codex.sh",
        ok: contains("scripts/handoff_to_codex.sh", "is_uuid"),
      },
      {
        label: "client requires --thread UUID and live-write acknowledgement",
        file: "scripts/codex_ipc_client.mjs",
        ok:
          contains("scripts/codex_ipc_client.mjs", "--thread <uuid>") &&
          contains("scripts/codex_ipc_client.mjs", "--ack-live-write"),
      },
    ]),
    check("REQ-003", "IPC sends are thread-scoped and reject heuristic write targeting.", [
      {
        label: "client sends explicit conversationId",
        file: "scripts/codex_ipc_client.mjs",
        ok: contains("scripts/codex_ipc_client.mjs", "conversationId: opts.threadId"),
      },
      {
        label: "/ipc skill forbids title/cwd/recency target inference when UUID is present",
        file: ".claude/skills/ipc/SKILL.md",
        ok: contains(".claude/skills/ipc/SKILL.md", "Do not infer a different target from title"),
      },
      {
        label: "plan records no heuristic targeting for writes",
        file: "plans/2026-06-04-codex-ipc-injection.md",
        ok: contains("plans/2026-06-04-codex-ipc-injection.md", "no heuristic targeting"),
      },
    ]),
    check("REQ-004", "IPC path is fallback-backed by writing file-drop first.", [
      {
        label: "IPC branch writes OUTBOUND before live delivery",
        file: "scripts/handoff_to_codex.sh",
        ok: contains("scripts/handoff_to_codex.sh", 'printf \'%s\\n\' "$PAYLOAD" > "$OUTBOUND"'),
      },
      {
        label: "IPC branch has fallback function and file-drop instruction",
        file: "scripts/handoff_to_codex.sh",
        ok:
          contains("scripts/handoff_to_codex.sh", "fallback()") &&
          contains("scripts/handoff_to_codex.sh", "FALLBACK -- file-drop is ready"),
      },
    ]),
    check("REQ-005", "Receiving Codex can inspect Claude context when needed.", [
      {
        label: "handoff payload includes Claude session context block",
        file: "scripts/handoff_to_codex.sh",
        ok: contains("scripts/handoff_to_codex.sh", "## Claude session context"),
      },
      {
        label: "docs record verified Codex-to-Claude transcript readability",
        file: "state/agent-inbox/README.md",
        ok:
          contains("state/agent-inbox/README.md", "Cross-session context inspection") &&
          contains("state/agent-inbox/README.md", "Codex can read it (verified)"),
      },
    ], "Transcript pointers expose full local session context; use only when needed."),
    check("REQ-006", "Existing-session /ipc inspects before sending.", [
      {
        label: "session inspector exists",
        file: "scripts/codex_ipc_session_inspect.mjs",
        ok: existsSync("scripts/codex_ipc_session_inspect.mjs"),
      },
      {
        label: "/ipc skill says always inspect before sending",
        file: ".claude/skills/ipc/SKILL.md",
        ok: contains(".claude/skills/ipc/SKILL.md", "Always inspect before sending any message."),
      },
    ]),
    check("REQ-007", "No-UUID /ipc has read-only candidate discovery before target selection.", [
      {
        label: "thread locator exists",
        file: "scripts/codex_ipc_thread_locator.mjs",
        ok: existsSync("scripts/codex_ipc_thread_locator.mjs"),
      },
      {
        label: "locator warns candidate is not write authority",
        file: "scripts/codex_ipc_thread_locator.mjs",
        ok: contains("scripts/codex_ipc_thread_locator.mjs", "Candidate discovery is not write authority"),
      },
      {
        label: "/ipc skill uses locator and requires follow-up inspection",
        file: ".claude/skills/ipc/SKILL.md",
        ok:
          contains(".claude/skills/ipc/SKILL.md", "codex_ipc_thread_locator.mjs") &&
          contains(".claude/skills/ipc/SKILL.md", "run `codex_ipc_session_inspect.mjs`"),
      },
    ]),
    check("REQ-008", "Post-update robustness has a validate-only revalidation surface.", [
      {
        label: "revalidation wrapper exists",
        file: "scripts/codex_ipc_revalidate.mjs",
        ok: existsSync("scripts/codex_ipc_revalidate.mjs"),
      },
      {
        label: "revalidation wrapper forbids prompt/follower/config/sqlite writes",
        file: "scripts/codex_ipc_revalidate.mjs",
        ok:
          contains("scripts/codex_ipc_revalidate.mjs", "No prompt injection") &&
          contains("scripts/codex_ipc_revalidate.mjs", "no follower-start-turn") &&
          contains("scripts/codex_ipc_revalidate.mjs", "no SQLite writes"),
      },
      {
        label: "docs expose post-update revalidation command",
        file: "state/agent-inbox/README.md",
        ok: contains("state/agent-inbox/README.md", "Post-update revalidation"),
      },
    ], "A future Desktop update can still require controlled write re-proof if read-only checks detect drift."),
    check("REQ-009", "No direct SQLite writes or forbidden global/destructive IPC methods are part of tooling.", [
      {
        label: "read-only SQLite helpers open with readOnly:true",
        file: "scripts/codex_ipc_session_inspect.mjs",
        ok:
          contains("scripts/codex_ipc_session_inspect.mjs", "readOnly: true") &&
          contains("scripts/codex_ipc_thread_locator.mjs", "readOnly: true") &&
          contains("scripts/codex_ipc_snapshot.mjs", "readOnly: true"),
      },
      {
        label: "plan forbids config/account/plugin/destructive methods",
        file: "plans/2026-06-04-codex-ipc-injection.md",
        ok:
          contains("plans/2026-06-04-codex-ipc-injection.md", "config/*") &&
          contains("plans/2026-06-04-codex-ipc-injection.md", "account/*") &&
          contains("plans/2026-06-04-codex-ipc-injection.md", "plugin/*"),
      },
    ]),
    check("REQ-010", "The system is externally auditable from repo artifacts.", [
      {
        label: "contract audit command exists",
        file: "scripts/codex_ipc_contract_audit.mjs",
        ok: existsSync("scripts/codex_ipc_contract_audit.mjs"),
      },
      {
        label: "validation log records commands/results",
        file: "state/VALIDATION_LOG.md",
        ok:
          contains("state/VALIDATION_LOG.md", "codex_ipc_revalidate.mjs") &&
          contains("state/VALIDATION_LOG.md", "Full `.\\scripts\\verify.ps1` passed"),
      },
      {
        label: ".omc acceptance record parses",
        file: ".omc/prd.json",
        ok: jsonParses(".omc/prd.json"),
      },
    ]),
    check("REQ-011", "Future controlled write re-proof is dry-run-first and evidence-backed.", [
      {
        label: "write proof harness exists",
        file: "scripts/codex_ipc_write_proof.mjs",
        ok: existsSync("scripts/codex_ipc_write_proof.mjs"),
      },
      {
        label: "write proof harness requires explicit live-send gates",
        file: "scripts/codex_ipc_write_proof.mjs",
        ok:
          contains("scripts/codex_ipc_write_proof.mjs", "Dry-run is the default") &&
          contains("scripts/codex_ipc_write_proof.mjs", "--send requires --ack-live-write"),
      },
      {
        label: "write proof harness inspects, revalidates, snapshots, polls, and compares",
        file: "scripts/codex_ipc_write_proof.mjs",
        ok:
          contains("scripts/codex_ipc_write_proof.mjs", "inspectTarget") &&
          contains("scripts/codex_ipc_write_proof.mjs", "revalidateRuntime") &&
          contains("scripts/codex_ipc_write_proof.mjs", "compareSnapshots") &&
          contains("scripts/codex_ipc_write_proof.mjs", "pollRolloutForMarker"),
      },
      {
        label: "docs expose controlled write re-proof as post-update contingent path",
        file: "state/agent-inbox/README.md",
        ok:
          contains("state/agent-inbox/README.md", "controlled proof harness") &&
          contains("state/agent-inbox/README.md", "codex_ipc_write_proof.mjs"),
      },
      {
        label: "post-update revalidation includes proof harness syntax",
        file: "scripts/codex_ipc_revalidate.mjs",
        ok: contains("scripts/codex_ipc_revalidate.mjs", "scripts/codex_ipc_write_proof.mjs"),
      },
    ], "Live write re-proof still starts a real turn and must remain explicit/operator-approved."),
  ];

  const ok = Object.values(files).every((item) => item.ok) &&
    requirements.every((item) => item.status === "evidenced");
  const result = {
    ok,
    mode: "codex-ipc-contract-audit",
    generatedAt: new Date().toISOString(),
    files,
    requirements,
    summary: {
      evidenced: requirements.filter((item) => item.status === "evidenced").length,
      missingOrWeak: requirements.filter((item) => item.status !== "evidenced").map((item) => item.id),
    },
    warnings: [
      "Static repo-file audit only; it does not prove the current Desktop runtime is open or that a future write will succeed.",
      "Run codex_ipc_revalidate.mjs for current runtime checks, and codex_ipc_write_proof.mjs for any future controlled write re-proof.",
    ],
  };

  console.log(JSON.stringify(result, null, 2));
  if (!ok) {
    process.exit(1);
  }
}

if (process.argv.includes("--help") || process.argv.includes("-h")) {
  console.log(usage());
} else {
  main();
}
