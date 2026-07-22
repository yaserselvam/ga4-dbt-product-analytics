# Prompt Library

The prompts used to build this project with Claude, published for transparency. The rule throughout: **AI drafts, I verify.** dbt tests must pass and the numbers must reconcile against the raw GA4 events before anything is trusted.

## 1. Flattening GA4

> "Given the GA4 BigQuery export schema (event-per-row, nested event_params array of key/value structs, top-level device/geo/traffic_source records), write a dbt staging model that returns one clean typed row per event, extracting ga_session_id, page_location, device category, country, traffic medium/source, and purchase revenue. Keep the _TABLE_SUFFIX filter so cost stays low."

**Verified:** checked each `unnest(event_params)` subquery returns one value per event; confirmed `ecommerce.purchase_revenue_in_usd` is populated on purchase events and null elsewhere; kept the `_TABLE_SUFFIX` bound so a run scans months, not the whole wildcard.

## 2. Session grain

> "Roll the event stream up to one row per (user_pseudo_id, ga_session_id) with boolean funnel flags (view_item, add_to_cart, begin_checkout, purchase) and summed revenue."

**Verified:** used `logical_or()` for the flags (not max/int casts); confirmed the `session_key` is unique via a dbt `unique` test before building anything downstream.

## 3. Funnel

> "Turn the session flags into a user-level funnel in long format: one row per step with users reaching it, share of the top step, and step-over-step conversion."

**Verified:** confirmed step counts are monotonically non-increasing (view >= cart >= checkout >= purchase); used `safe_divide` to avoid divide-by-zero; sanity-checked the conversion rates against a manual COUNT query.

## 4. Retention cohorts

> "Build a weekly acquisition-cohort retention model: cohort_week = week of first visit, weeks_since = weeks between active week and cohort week, count distinct active users, capped at 8 weeks."

**Verified:** confirmed week 0 equals the cohort size and every later week is <= week 0; checked `date_trunc(..., week(monday))` aligns cohort and activity weeks consistently.

## 5. RFM

> "Score purchasing users on recency, frequency, monetary with ntile(5), using a fixed reference date (day after the sample ends) for reproducibility, then map scores to named segments."

**Verified:** checked the ntile ordering so most-recent/most-frequent/highest-value map to 5 (not 1); confirmed segment labels partition all users (no nulls) via an `accepted_values` test.

---

*Every model above was drafted with AI and then gated on dbt tests + a manual reconciliation against the raw events. The models are the AI's; the trust is mine to establish.*
