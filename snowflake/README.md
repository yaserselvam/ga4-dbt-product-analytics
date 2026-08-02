# Snowflake + Fivetran port

The project one directory up runs the GA4 product-analytics models on **BigQuery**.
This folder is the same build ported to **Snowflake**, fed by a **Fivetran-style
ingestion** layer. Same marts, same tests, same business logic; only the warehouse
dialect and the ingestion path change.

Why this exists: the modern-data-stack roles this project targets (analytics
engineer) name **dbt + Snowflake + Fivetran** specifically. The transformation
skill is warehouse-portable; this folder proves it rather than asserting it.

## What changed from the BigQuery build

| Concern | BigQuery | Snowflake (this folder) |
|---|---|---|
| Nested `event_params` | `UNNEST(event_params)` | `LATERAL FLATTEN(input => event_params)` |
| Conditional count | `COUNTIF(x)` | `COUNT_IF(x)` |
| Boolean aggregate | `LOGICAL_OR(x)` | `BOOLOR_AGG(x)` |
| Safe division | `SAFE_DIVIDE(a, b)` | `IFF(b = 0, NULL, a / b)` |
| Micros to timestamp | `TIMESTAMP_MICROS(x)` | `TO_TIMESTAMP_NTZ(x, 6)` |
| Parse date string | `PARSE_DATE('%Y%m%d', x)` | `TO_DATE(x, 'YYYYMMDD')` |
| Monday-start week | `DATE_TRUNC(d, WEEK(MONDAY))` | `DATEADD(day, 1 - DAYOFWEEKISO(d), d)` |
| Week difference | `DATE_DIFF(a, b, WEEK)` | `DATEDIFF(day, b, a) / 7` |
| String concat | `CONCAT(a, '-', CAST(b AS STRING))` | `a \|\| '-' \|\| b::string` |

The marts (`fct_sessions`, `funnel_conversion`, `retention_cohorts`, `rfm_segments`)
and their tests are otherwise identical, so the two warehouses produce the same
numbers.

## Ingestion: two paths, one lands in `GA4_DEMO.RAW.EVENTS`

**Path A: Fivetran (the modern-stack way, ~1 hour on a 14-day trial).**
Fivetran syncs a source into Snowflake on a schedule with no hand-written extract
code. Set up one real connector to get genuine hands-on:
1. Start a Fivetran free trial and connect Snowflake as the destination
   (database `GA4_DEMO`).
2. Add a connector for a source you control (Google Sheets or a small Postgres is
   the fastest for a demo; the **Google Analytics 4** connector is the on-theme
   choice if you have a GA4 property). Fivetran creates the schema and lands the
   rows, semi-structured fields as `VARIANT`.
3. Point the dbt source (`_ga4_raw__sources.yml`) at the Fivetran-created schema.

**Path B: bulk COPY (no third party, for the GA4 public sample specifically).**
The public GA4 sample lives in BigQuery, so to model *that exact dataset* in
Snowflake: export the staging rows to GCS/S3 as JSON, create an external stage,
then `COPY INTO GA4_DEMO.RAW.EVENTS`. Use this if you want identical numbers to
the BigQuery build; use Path A to demonstrate Fivetran.

## Runbook: make it live (2 to 3 hours, free)

1. **Snowflake trial** (30 days, no card): create account, note the account
   identifier, keep the default `COMPUTE_WH`. Create `GA4_DEMO`, schemas `RAW`
   and `ANALYTICS`.
2. **Land data** via Path A or B above into `GA4_DEMO.RAW.EVENTS`.
3. **Configure dbt:** `pip install dbt-snowflake`, copy `profiles.example.yml`
   into `~/.dbt/profiles.yml`, fill in your account details.
4. **Run:** from this folder, `dbt build` (runs models + tests). Confirm the
   tests pass and spot-check `rfm_segments` against the BigQuery readout in
   `../outputs/readout.md`.
5. **Screenshot** the `dbt build` success + a `select * from rfm_segments limit 20`
   for the portfolio.

## Status: verified run (2026-08-01)

This port has been **run live on Snowflake**, not just written. The full public
GA4 sample (2020-11-01 to 2021-01-31, **4,295,584 raw events**) was loaded into
`GA4_DEMO.RAW.EVENTS` and built with `dbt build`: **16/16 nodes passed (5 models,
10 tests)**, and the results match the BigQuery build exactly (e.g. `rfm_segments`
= 4,419 purchasing users in both). Auth is Snowflake key-pair (MFA-proof), so the
build runs non-interactively.

Reproduce from scratch: `setup.sql` (objects) -> `load_from_bq.py` (BigQuery ->
NDJSON shards) -> `load_to_snowflake.py` (PUT + COPY) -> `gen_keypair.py` + register
the public key -> `dbt build`. Ingestion here is a bulk COPY (Path B); "Fivetran"
on the CV remains "Fivetran-*style*" until a real connector is configured (Path A).
