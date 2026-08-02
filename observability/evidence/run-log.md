# Live run log

Observability layer run against the real GA4 build on BigQuery (not just parsed).

## Build + tests: all green

```
$ dbt build --select session_quality_flags assert_dq_flag_rate_under_threshold assert_fct_sessions_volume

PASS assert_fct_sessions_volume
PASS assert_dq_flag_rate_under_threshold
PASS not_null_session_quality_flags_has_dq_flag
PASS not_null_session_quality_flags_dq_flag_count
PASS not_null_session_quality_flags_session_key
PASS unique_session_quality_flags_session_key
Done. PASS=7 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=7
```

## A real bug the run caught (and the fix)

The first live build **failed** on `not_null_session_quality_flags_has_dq_flag`
with 355,266 nulls. Cause: `revenue_usd` is a `SUM` over purchase events, which
is `NULL` for the many sessions with no purchase, so `revenue_usd < 0` evaluated
to `NULL`, and `NULL` propagated through the `OR` into `has_dq_flag`. Fix:
`coalesce(revenue_usd, 0)` in the revenue flags so a "no revenue" session is a
real boolean `false`, not a null. This is exactly the defensive edge-case
handling the layer is meant to demonstrate: the test caught it before the column
could quietly mislead a consumer.

## Ownership-tagged alert (demonstration)

With the volume monitor's threshold deliberately tripped, the alerter routes the
warning to the owning team (the whole point of Monzo's `#data-monitoring`
pattern: an alert is only actionable if it names an owner):

```
$ python observability/monitor.py

Data-quality alerts (1) from the latest dbt run:
- [WARN] assert_fct_sessions_volume on `fct_sessions` (owner @yaser): 1 failing rows

(dry-run: set SLACK_WEBHOOK_URL to post these to Slack)
```

The threshold was reverted to its real band immediately after; the committed
tests pass on the real data (above).

## Governance gate

```
$ python observability/check_standards.py
OK: all 5 governed models have an owner, docs, and a test.
```

This runs in CI on every pull request; a model added without an owner, docs, or a
test fails the build.
