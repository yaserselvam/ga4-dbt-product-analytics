#!/usr/bin/env python
"""Ownership-tagged data-quality alerter.

After a `dbt build` (or `dbt test`), this reads target/run_results.json, finds
every failing or warning node, looks up the OWNER of the affected model from the
manifest, and emits an alert that names that owner. This is the differentiating
move from Monzo's #data-monitoring channel: an alert is only actionable if it
says whose problem it is. A silent check that no one owns gets ignored.

    python observability/monitor.py            # dry-run: prints the alert
    SLACK_WEBHOOK_URL=https://... python observability/monitor.py   # posts to Slack

Exit code is always 0 (alerting is not a build gate); the dbt test severities
decide what blocks. This just routes the signal to a human.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

TARGET = Path(__file__).resolve().parent.parent / "target"
ALERT_STATUSES = {"fail", "error", "warn"}


def load(name: str) -> dict:
    path = TARGET / name
    if not path.exists():
        sys.exit(f"{path} not found. Run `dbt build` first.")
    return json.loads(path.read_text(encoding="utf-8"))


def owner_of(node: dict) -> str:
    meta = node.get("meta") or node.get("config", {}).get("meta", {}) or {}
    return meta.get("owner_slack") or meta.get("owner") or "unowned"


def main() -> None:
    run_results = load("run_results.json")
    manifest = load("manifest.json")
    nodes = manifest.get("nodes", {})

    alerts = []
    for result in run_results.get("results", []):
        status = str(result.get("status", "")).lower()
        if status not in ALERT_STATUSES:
            continue

        uid = result.get("unique_id", "")
        node = nodes.get(uid, {})

        # For a test, attribute the alert to the model it tests.
        subject = node
        subject_name = node.get("name", uid)
        if node.get("resource_type") == "test":
            model_ids = [n for n in node.get("depends_on", {}).get("nodes", [])
                         if n.startswith("model.")]
            if model_ids:
                subject = nodes.get(model_ids[0], node)
                subject_name = subject.get("name", subject_name)

        failures = result.get("failures")
        detail = f"{failures} failing rows" if failures is not None else result.get("message", "")
        alerts.append(
            f"[{status.upper()}] {node.get('name', uid)} "
            f"on `{subject_name}` (owner {owner_of(subject)}) — {detail}".strip()
        )

    if not alerts:
        print("All models and tests healthy. No alerts.")
        return

    header = f"Data-quality alerts ({len(alerts)}) from the latest dbt run:"
    body = header + "\n" + "\n".join(f"- {a}" for a in alerts)
    print(body)

    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if webhook:
        req = urllib.request.Request(
            webhook,
            data=json.dumps({"text": body}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
        print(f"\nPosted {len(alerts)} alert(s) to Slack.")
    else:
        print("\n(dry-run: set SLACK_WEBHOOK_URL to post these to Slack)")


if __name__ == "__main__":
    main()
