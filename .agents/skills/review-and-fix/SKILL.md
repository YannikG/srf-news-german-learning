---
name: review-and-fix
description: >-
  Review + fix loop (not review-only): SRP, maintainability, clean arch, security,
  types, tests, docs. Classify severity, fix critical/high/medium actionable, run
  lint/type/test/build, re-review until done or true blocker. Triggers: review and
  fix, SRP review, maintainability/architecture/quality cleanup, doc pass.
---

# Review and fix

**Goal:** find concrete issues → fix them → validate → repeat until **done** or **blocker**. No review-only unless user says review-only (then skip fix loop).

## Triggers

`review and fix`, SRP review, maintainability cleanup, clean architecture review, code quality cleanup, documentation quality pass.

## Scan dimensions (touched scope)

- **SRP:** one job per fn/class/component/service.
- **Maintainability:** dup, complexity, coupling, names, brittle branches, untestable logic.
- **Clean arch:** dependency direction, layer boundaries, no feature bleed.
- **Security / safety:** validation, auth, secrets, deserialization, injection, dangerous side effects, data loss paths.
- **Cleanliness:** dead code, stale TODOs, pattern drift, weak types/APIs, error handling gaps.
- **Types:** concrete types; no `any`; no long-lived `unknown` — narrow at boundaries.
- **Docs:** public/reused APIs documented where needed; comments for non-obvious constraints; docs match behavior.
- **Tests:** behavior changes covered; lint/type/test expectations met.

## Loop (mandatory)

Repeat until done criteria:

1. **Scan** — changed files + impacted call paths. Findings = concrete (no vague style nits).

2. **Classify** — severity:
   - `critical`: broken behavior, data loss/security, arch break.
   - `high`: likely bug/regression or big maintainability risk.
   - `medium`: real debt, cheap fix now.
   - `low`: polish optional.
   Each: `actionable-now` vs `blocked`.

3. **Fix** — all `critical` / `high` / `medium` that are `actionable-now`. Smallest safe refactor, root cause. Behavior stable unless user asked behavior change.

4. **Validate** — lint / type / test / build for changed scope (what exists). Failures = new findings → fix in same loop.

5. **Re-review** — touched code + neighbors for second-order damage (coupling, complexity, doc drift).

6. **Repeat** — until done.

## Done (all true)

- No open `critical` or `high`.
- No `medium` left that is safe + feasible now.
- Validation passes for changed scope (or pre-existing failures **explicitly** noted).
- Anything left = real `blocked` + clear next input.

## Finding format

`<severity> | <location> | <problem> | <fix>`

Example: `high | src/orders/order.service.ts | validation+persistence+mapping one method (SRP) | extract validators+mappers, service orchestrates only`

## Blocker → stop auto-fix, report

- ambiguous requirement → needs product call.
- destructive / irreversible change.
- needs creds / system / user step agent lacks.
- constraint conflict → no safe fix in scope.

Report: status, what fixed, exact blocker, minimal next step for user.

## Boundaries

- Actionable findings remain → keep looping; no stop after first pass.
- No leave `critical`/`high` unfixed on purpose.
- No invent requirements; no unrelated arch rewrite.
- No silent skip validation.
- No DB normalization crusade unless user asks.
- Explicit types; `any`/`unknown` only at boundary + narrow fast.
