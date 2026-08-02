#!/usr/bin/env python
"""Production-model standards gate (Monzo-style, enforced in CI).

Monzo runs a governed data mesh across 12,000+ dbt models by enforcing a shared
checklist in CI on every pull request: every model has an owner, documentation,
and tests. This script is a small version of that guardrail. It reads the parsed
manifest and fails the build if any presentation model (marts / observability)
is missing:

  1. an owning team          (meta.owner)
  2. a description           (documentation)
  3. at least one data test  (trust)

Run after `dbt parse` (which writes target/manifest.json):

    python observability/check_standards.py

Exit 1 on any violation so CI blocks the PR, exactly like Monzo's guardrails.
"""
import json
import sys
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent.parent / "target" / "manifest.json"
GOVERNED_LAYERS = ("marts", "observability")


def meta_owner(node: dict) -> str:
    meta = node.get("meta") or node.get("config", {}).get("meta", {}) or {}
    return meta.get("owner", "")


def main() -> None:
    if not MANIFEST.exists():
        sys.exit(f"{MANIFEST} not found. Run `dbt parse` first.")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    nodes = manifest.get("nodes", {})
    child_map = manifest.get("child_map", {})

    violations = []
    checked = 0
    for uid, node in nodes.items():
        if node.get("resource_type") != "model":
            continue
        if not any(layer in node.get("fqn", []) for layer in GOVERNED_LAYERS):
            continue

        checked += 1
        name = node.get("name", uid)
        missing = []
        if not meta_owner(node):
            missing.append("owner (meta.owner)")
        if not (node.get("description") or "").strip():
            missing.append("description")
        if not any(c.startswith("test.") for c in child_map.get(uid, [])):
            missing.append("a data test")
        if missing:
            violations.append(f"  - {name}: missing {', '.join(missing)}")

    if violations:
        print(f"FAILED: {len(violations)} of {checked} governed models miss standards:")
        print("\n".join(violations))
        print("\nEvery marts/observability model needs an owner, docs, and a test.")
        sys.exit(1)

    print(f"OK: all {checked} governed models have an owner, docs, and a test.")


if __name__ == "__main__":
    main()
