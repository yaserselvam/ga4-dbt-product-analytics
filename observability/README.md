# Data observability & governance layer

## The tension this solves

A dbt project that passes its tests once is not the hard part. The hard part a
data team lives with is the day after: a source silently changes, a load runs
half, a tracking bug ships, and **bad data reaches a dashboard before anyone
notices, with no one clear on whose problem it is.** In a fintech that is not a
cosmetic issue: the same tables feed reporting, reconciliation, and regulatory
returns.

This layer is the operational answer to that tension. It is deliberately not a
new tech stack bolted on; it is the small set of habits top UK fintech data
teams actually run in production:

- **Monzo** posts every dbt model run status to a `#data-monitoring` Slack
  channel and **tags the person who last touched the code**, and enforces a
  shared model checklist (owner, tests, docs, naming) in CI across 12,000+ models.
- **Wise** runs automated checks to catch data drift and feature inconsistencies
  *before* they become incidents.
- **GoCardless** treats a dataset as an API with an owner and a contract.

The common thread is not the tooling. It is **ownership, alerting, and flagging
over discarding.** That is what this layer demonstrates.

## What it adds to the dbt project

| Piece | What it does | The judgment in it |
|---|---|---|
| `models/observability/session_quality_flags.sql` | Flags sessions that violate funnel or revenue integrity rules, keeping every row | **Flag, never drop.** Discarding "bad" rows hides the issue and loses real signal (Monzo's `CHECK_ZERO` pattern) |
| `tests/assert_dq_flag_rate_under_threshold.sql` | Warns if >2% of sessions carry a flag | A distribution monitor: a spike in flags is a *new* upstream problem, surfaced as a warning not a hard failure |
| `tests/assert_fct_sessions_volume.sql` | Warns if the session count falls outside its expected band | A volume monitor: a partial or broken load shows up as a size anomaly |
| `meta.owner` on every model | Names an owning team per model | An alert is only actionable if it says whose problem it is |
| `observability/monitor.py` | Reads `run_results.json`, finds fails/warns, and emits an alert **tagged with the model's owner** (Slack or dry-run) | Reproduces Monzo's "tag the owner" alerting, in ~60 lines and no vendor SaaS |
| `observability/check_standards.py` (in CI) | Fails the PR if any marts/observability model lacks an owner, docs, or a test | Monzo's governance checklist as an automated guardrail, not a wiki page |

## Design decisions (the part AI cannot write for you)

- **Warn, do not error, on data-quality anomalies.** A hard failure blocks the
  build and pressures people to weaken the test. A warning keeps data flowing,
  routes the signal to the owner, and preserves the row for review. Correctness
  *and* availability.
- **Flag, do not filter.** Every quality rule adds a boolean column, never a
  `WHERE` clause. Consumers opt into `has_dq_flag`; nothing is silently removed.
- **Ownership is a first-class field, not a comment.** `meta.owner` is enforced
  in CI and consumed by the alerter, so ownership cannot rot.
- **Open-source, not a SaaS.** The detection and alerting are plain dbt + Python
  so the logic is visible and portable, rather than a Monte Carlo config screen.

## Run it

```bash
# 1. Build the models and run the monitors (needs the warehouse configured)
dbt build

# 2. Route any fails/warns to their owners (dry-run prints; webhook posts)
python observability/monitor.py
SLACK_WEBHOOK_URL="https://hooks.slack.com/..." python observability/monitor.py

# 3. The governance gate that runs in CI on every PR
dbt parse
python observability/check_standards.py
```

## Honest scope, and the live-data extension

The public GA4 sample is a **static** historical dataset (Nov 2020 to Jan 2021),
so freshness and time-series anomalies cannot fire naturally here; the volume and
distribution monitors use fixed, reproducible bands as the honest equivalent, and
the flag-not-discard model and the ownership/governance gate work fully as shown.

For true time-series anomaly detection (freshness, volume, and schema drift
learned from run history), the production tool is **[Elementary](https://www.elementary-data.com/)**,
pointed at a **live-updating** source. Minimal setup:

```yaml
# packages.yml
packages:
  - package: elementary-data/elementary
    version: [">=0.16.0", "<0.20.0"]

# then, on a monitored model:
#   tests:
#     - elementary.volume_anomalies
#     - elementary.freshness_anomalies:
#         timestamp_column: session_start
#     - elementary.schema_changes
```

A good live source for the freshness/volume story is the UK **Bus Open Data
Service** (continuously updated timetables and vehicle positions), which is what
this layer would monitor in a production setting.
