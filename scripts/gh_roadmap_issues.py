#!/usr/bin/env python3
"""One-off: create GitHub issues from docs/roadmap issue specs. Requires gh auth."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP = REPO_ROOT / "docs" / "roadmap"
OWNER_REPO = "YannikG/srf-news-german-learning"
DEFAULT_BRANCH = "master"

# Titel exakt wie in docs/roadmap/phase-N/README.md (Spalte Titel)
TITLES: dict[str, str] = {
    "P1-I01": "Monorepo-Layout und Docker Compose",
    "P1-I02": "Flask App Factory und Health",
    "P1-I03": "Formatierer, Prettier und GitHub Actions (Quality Gates)",
    "P2-I01": "app.db Schema und Migrationen",
    "P2-I02": "Wörterbuch REST API",
    "P2-I03": "Artikel lesen und FTS",
    "P2-I04": "Einstellungen API",
    "P3-I01": "SRG OAuth Client",
    "P3-I02": "Articles API Mapping und Felder",
    "P3-I03": "News Refresh und Ingest",
    "P4-I01": "Docker Sidecar Ollama",
    "P4-I02": "Idle Warnung Sleep und Cancel",
    "P4-I03": "SSE Event Stream",
    "P5-I01": "sqlite-vec und vectors.db",
    "P5-I02": "Embeddings und Retrieval",
    "P5-I03": "Vereinfachen Stream und Persistenz",
    "P6-I01": "Vue Tooling und App Shell",
    "P6-I02": "News UI",
    "P6-I03": "Wörterbuch UI",
    "P6-I04": "Einstellungen UI",
    "P6-I05": "Realtime Ollama und LLM UX",
    "P6-I06": "Optional PONS On-Demand und „Übersetzung anzeigen“",
    "P7-I01": "Backend Test Suite",
    "P7-I02": "Frontend Test Suite",
    "P7-I03": "Lint CI und README",
}

ISSUE_ID_RE = re.compile(r"^(P\d+-I\d+)-")


def discover_specs() -> dict[str, tuple[int, Path]]:
    """issue_id -> (phase, path relative to repo)."""
    out: dict[str, tuple[int, Path]] = {}
    for p in range(1, 8):
        d = ROADMAP / f"phase-{p}" / "issues"
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            m = ISSUE_ID_RE.match(f.name)
            if not m:
                print(f"skip (no id prefix): {f}", file=sys.stderr)
                continue
            iid = m.group(1)
            out[iid] = (p, f)
    return out


def parse_dependencies(spec_path: Path) -> list[str]:
    text = spec_path.read_text(encoding="utf-8")
    m = re.search(r"^## Dependencies\n(?P<body>.*?)(?=^## )", text, re.M | re.S)
    if not m:
        return []
    body = m.group("body")
    found: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        # Downstream only: linked issue waits for this spec, not a prerequisite.
        if stripped.lower().startswith("**blockiert"):
            continue
        if not stripped.startswith("- "):
            continue
        if re.match(r"^-\s*none\b", stripped, re.I):
            continue
        for mid in re.findall(r"\[([P][0-9]+-I[0-9]+)\]", line):
            found.append(mid)
    # dedupe, preserve order
    seen = set()
    out = []
    for x in found:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def topological_order(
    nodes: set[str], edges: dict[str, list[str]]
) -> list[str] | None:
    """edges[A] = list of nodes A depends on (prerequisites)."""
    indeg = {n: 0 for n in nodes}
    rev: dict[str, list[str]] = defaultdict(list)
    for n in nodes:
        for p in edges.get(n, []):
            if p not in nodes:
                print(f"warn: {n} depends on missing {p}, ignored", file=sys.stderr)
                continue
            rev[p].append(n)
            indeg[n] += 1
    q = deque(sorted([n for n in nodes if indeg[n] == 0]))
    order: list[str] = []
    while q:
        n = q.popleft()
        order.append(n)
        for c in sorted(rev[n]):
            indeg[c] -= 1
            if indeg[c] == 0:
                q.append(c)
    if len(order) != len(nodes):
        print("cycle or unsorted remainder; falling back to phase+id order", file=sys.stderr)
        return None
    return order


def gh_json(cmd: list[str]) -> dict | list:
    r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def main() -> int:
    specs = discover_specs()
    if len(specs) != 25:
        print(f"expected 25 specs, got {len(specs)}", file=sys.stderr)

    edges: dict[str, list[str]] = {}
    for iid, (_, path) in specs.items():
        deps = parse_dependencies(path)
        edges[iid] = [d for d in deps if d in specs and d != iid]

    order = topological_order(set(specs), edges)
    if order is None:
        order = sorted(
            specs.keys(),
            key=lambda x: (int(x.split("-")[0][1:]), int(x.split("-I")[1])),
        )

    for p in range(1, 8):
        subprocess.run(
            [
                "gh",
                "label",
                "create",
                f"phase-{p}",
                "--color",
                "0E8A16",
                "--description",
                f"Roadmap phase {p}",
                "--force",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
        )

    id_to_number: dict[str, int] = {}
    for iid in order:
        phase, path = specs[iid]
        rel = path.relative_to(REPO_ROOT).as_posix()
        title = TITLES.get(iid)
        if not title:
            print(f"missing title for {iid}", file=sys.stderr)
            return 1
        permalink = (
            f"https://github.com/{OWNER_REPO}/blob/{DEFAULT_BRANCH}/{rel}"
        )
        body = (
            f"Roadmap-Spezifikation Phase {phase}; kanonische Details nur im verlinkten Markdown.\n\n"
            f"{permalink}\n"
        )
        body_file = REPO_ROOT / ".tmp-issue-body.md"
        body_file.write_text(body, encoding="utf-8")
        try:
            r = subprocess.run(
                [
                    "gh",
                    "issue",
                    "create",
                    "--title",
                    title,
                    "--body-file",
                    str(body_file),
                    "--label",
                    f"phase-{phase}",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            if r.returncode != 0:
                print(r.stderr, file=sys.stderr)
                return r.returncode
            # gh prints URL https://github.com/owner/repo/issues/N
            url = (r.stdout or "").strip()
            num = int(url.rsplit("/", 1)[-1])
            id_to_number[iid] = num
            print(f"{iid} -> #{num}")
        finally:
            body_file.unlink(missing_ok=True)

    for iid in order:
        deps = edges.get(iid, [])
        nums = [id_to_number[d] for d in deps if d in id_to_number]
        if not nums:
            continue
        n = id_to_number[iid]
        refs = ", ".join(f"#{x}" for x in sorted(nums))
        comment = f"Abhängigkeiten (Spec): {refs}"
        subprocess.run(
            ["gh", "issue", "comment", str(n), "--body", comment],
            cwd=REPO_ROOT,
            check=True,
        )
        print(f"comment on #{n}: {comment}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
