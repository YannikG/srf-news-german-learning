---
name: check-for-review-or-wait
description: >-
  After fixing PR review comments, re-run review-and-fix, resolve fixed GitHub
  review threads via API, and loop until no unresolved actionable threads remain
  (including low severity). Optional wait before polling. Use when user wants PR
  feedback addressed, threads resolved, and quality pass repeated; triggers:
  check-for-review-or-wait, wait for review then fix, resolve review comments loop.
disable-model-invocation: true
---

# Check for review or wait

**Companion:** full quality pass → [`.agents/skills/review-and-fix/SKILL.md`](../review-and-fix/SKILL.md). PR branch workflow → [`.agents/skills/implement-plan-workflow/SKILL.md`](../implement-plan-workflow/SKILL.md). `gh` usage → [`docs/agents-docs/github-cli.md`](../../../docs/agents-docs/github-cli.md).

## Goal

1. Optionally **wait** (time or CI) so reviewers or checks can finish.
2. **Ingest** all open PR review inline threads (including **low** / nit suggestions from bots or humans).
3. **Fix** every actionable thread in code or docs; validate (tests, lint, type, build as applicable).
4. **Commit and push** the fixes.
5. Immediately run a full **review-and-fix** pass on the same scope (same criteria as that skill, but treat **low** items from this PR’s review comments as **must fix** while this loop is active).
6. If review-and-fix surfaces new changes: commit, push, repeat from step 5 until that pass is clean.
7. **Resolve** each GitHub review thread that is now addressed (GraphQL below). Re-fetch threads; if new unresolved threads appeared, go to step 2.
8. **Loop** until no unresolved review threads remain or a **blocker** stops progress (max iterations).

## Preconditions

- `gh auth status` OK; repo remote is GitHub.
- Know **PR number** (from user, or `gh pr view --json number,url` on the current branch).
- Working tree: commit fixes before resolving threads so line anchors stay meaningful.

## Parameters (ask or infer once)

| Parameter | Default | Notes |
|-----------|---------|--------|
| `PR_NUMBER` | current branch’s open PR | `gh pr list --head <branch>` if needed |
| `WAIT_SECONDS` | `0` | If user asked to wait (e.g. 300), `sleep` or poll before first fetch |
| `MAX_LOOPS` | `15` | Stop with summary; avoid infinite loop |
| `OWNER/REPO` | from `gh repo view --json nameWithOwner -q .nameWithOwner` | For API calls |

## Step A: Optional wait

- If user specified a wait duration: wait that long once, then continue.
- If user asked to wait for CI: poll `gh pr checks <PR_NUMBER>` (or `gh pr view <N> --json statusCheckRollup`) until all required checks succeed or timeout; then continue.

## Step B: Fetch unresolved review threads

Use GraphQL (REST alone does not list thread IDs needed to resolve).

**List threads** (replace owner, name, number):

```graphql
query {
  repository(owner: "OWNER", name: "REPO") {
    pullRequest(number: PR_NUMBER) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 20) {
            nodes {
              databaseId
              body
              path
              line
              author { login }
              commit { oid }
            }
          }
        }
      }
    }
  }
}
```

Run: `gh api graphql -f query='...'` (escape quotes in shell as needed).

Treat a thread as **actionable** if `isResolved` is false and there is at least one comment with a body (ignore empty).

## Step C: Fix all threads (severity agnostic)

For **each** unresolved thread:

- Parse suggestion (diff in markdown, wording, path/line).
- Apply the smallest correct fix. **Low** and bot nits are **in scope**; do not skip them in this workflow.
- If a comment is wrong or outdated: reply briefly on the PR (optional) and still resolve only if team policy allows; otherwise leave unresolved and report **blocked** with reason.

## Step D: Validate, commit, push

Project’s normal checks for touched stack (e.g. backend `pytest`, `ruff`; frontend `npm test` if frontend changed).

## Step E: Review-and-fix pass (mandatory after push)

1. Read [`.agents/skills/review-and-fix/SKILL.md`](../review-and-fix/SKILL.md).
2. Run its full loop on **PR diff vs base** plus neighbors: scan → classify → fix **critical / high / medium** per that skill **and** any **low** you can fix cheaply in the same files.
3. If you made further edits: validate, commit, push; repeat **E** until review-and-fix **done** criteria are met for that scope.

## Step F: Resolve fixed threads (GraphQL)

Only after the fixing commit(s) are on the remote branch.

For each thread ID from step B that is **fully addressed** by the current tree:

```graphql
mutation {
  resolveReviewThread(input: { threadId: "THREAD_NODE_ID" }) {
    thread { isResolved }
  }
}
```

Re-run the **list threads** query. Any thread still `isResolved: false` either needs another fix iteration or is blocked.

## Step G: Outer loop

1. If `MAX_LOOPS` exceeded: stop; report remaining thread IDs and bodies.
2. If unresolved threads remain: go to **Step C** (do not resolve until fixed).
3. If none remain: optionally post a short PR comment listing commits that addressed review; exit **done**.

## Blockers (stop auto-fix; report)

- GraphQL `resolveReviewThread` fails (token lacks `repo` scope or not maintainer).
- Comment requires product or security decision.
- CI red with unrelated flake after two retries (note explicitly).

## Done criteria

- No unresolved `reviewThreads` with actionable comments, **or** blocker documented.
- Latest commits include all fixes; **review-and-fix** pass completed clean on that scope.
- Resolved threads match what was actually fixed (no resolve empty promises).
