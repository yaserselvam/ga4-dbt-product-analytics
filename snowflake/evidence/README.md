# Evidence: dbt + Snowflake + Fivetran, verified live (2026-08-01 / 02)

Written record of the live run, so the proof survives even without the images.
The three screenshots are saved in this folder under the filenames referenced below.

## 1. dbt build on Snowflake: 16/16 passed

`dbt build` against `GA4_DEMO`, key-pair auth, XSMALL warehouse:

```
Found 5 models, 1 operation, 10 data tests, 1 source, 545 macros
...
Completed successfully
Done. PASS=16 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=16
```

Model row counts (build log):
- `stg_ga4__events` (view)
- `fct_sessions` = 360,129
- `funnel_conversion` = 4
- `retention_cohorts` = 90
- `rfm_segments` = 4,419

**Screenshot:** `dbt-build-pass.png`

## 2. Numbers match the BigQuery build

`select * from GA4_DEMO.ANALYTICS.rfm_segments;` returns **4,419 rows** in
Snowsight, identical to the BigQuery readout's 4,419 purchasing users
(`../outputs/readout.md`). Same dbt project, same logic, both warehouses, same result.

**Screenshot:** `rfm-segments-4419.png`

## 3. Fivetran -> Snowflake, real sync

Connector: **Google Sheets (source) -> Snowflake (destination)**, key-pair auth,
landing DB `FIVETRAN_DEMO`. Initial sync completed. Verified with:

```sql
SELECT * FROM FIVETRAN_DEMO.GOOGLE_SHEETS.DEMO_SHEET;
```

Result carried Fivetran's system columns (`_FIVETRAN_SYNCED`, `_ROW`) alongside
the sheet data, confirming Fivetran performed the ingestion (not a manual load).

**Screenshot:** `fivetran-sync-demo-sheet.png`

## How it was built (reproducible)

`setup.sql` -> `load_from_bq.py` (BigQuery -> NDJSON, 4,295,584 events) ->
`load_to_snowflake.py` (PUT + COPY) -> `gen_keypair.py` + register public key ->
`dbt build`. Fivetran side: Google Sheets connector -> Snowflake destination.

## Interview notes (honest framing)

- Ingestion into the dbt pipeline was a bulk COPY (Path B); the Fivetran connector
  is a separate, genuine demo (Google Sheets -> Snowflake). So "Fivetran-style" for
  the GA4 pipeline, and real hands-on Fivetran for the connector.
- The Fivetran destination reused the ACCOUNTADMIN user for a trial demo; the
  production-correct pattern is a dedicated FIVETRAN_USER + role + warehouse.
