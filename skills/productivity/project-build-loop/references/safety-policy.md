# Project safety policy

The conductor enforces this on every project. It is normative; "SHOULD" means a
documented exception is possible, "MUST" means fail-closed.

## Authorization & scope

- The conductor MUST confirm `authorized + scoped + isolated` before any action
  that touches a live or third-party target, or introduces an offensive
  capability flag. Authorization is a **gate**, never a score adjustment.
- Out-of-scope assets MUST NOT be scanned, captured, or targeted.

## Execution

- Each task declares its capability flags; the conductor MUST run
  `scripts/policy_check.sh` before routing execution.
- Destructive or irreversible actions MUST have an explicit confirmation and a
  recorded rollback point.
- The conductor MUST honor the kill-switch: halt on unexpected egress or
  live-malware beaconing.

## Secrets & git

- Default to **local private git, no remote**.
- Never `git add .`; stage an allowlist. Run `scripts/secret_scan.sh` before
  staging, committing, consulting, and publishing (fail-closed).
- Secrets, credentials, keys, raw captures, and `.vault/` MUST stay gitignored
  and MUST NOT enter a consult or publication.

## Classification

- Every project MUST carry a `classification` block. One confirmed tier or
  `review_required`; enforce the higher tier while unresolved.
- Upward reclassification is automatic; **downward** requires human rationale +
  an `event-log.jsonl` entry.
- Sensitivity MUST NOT be encoded in a path or any public index.

## Publication

- Publication reads **only** sanitized `publish/` artifacts, never raw build
  logs. The gate is the allowlisted publish manifest + redaction review + secret
  scan, not a disclaimer.
- Follow the refuse-to-publish conditions in `dual-use-rating.md`.

## Records

- `event-log.jsonl` is append-only and records every state transition, gate
  decision, checkpoint, and consult (model, prompt hash, artifact hash, result).
- Retain authorization, captures, and logs per the agreed retention/destruction
  schedule; support revocation/embargo of a published post if risk changes.
