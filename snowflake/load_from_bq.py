#!/usr/bin/env python
"""Step 2a of the Snowflake runbook: pull the GA4 public sample from BigQuery
and write it as gzipped NDJSON shards, ready to PUT + COPY into Snowflake.

Why via BigQuery: the GA4 obfuscated e-commerce sample lives only in
bigquery-public-data. This exports the SAME rows and date window the BigQuery
build uses (2020-11-01 to 2021-01-31), so the Snowflake marts produce the same
numbers as outputs/readout.md. Nested GA4 fields are kept as real JSON
(TO_JSON_STRING in BQ -> json.loads here) so they land in Snowflake as VARIANT.

Auth reuses the existing service-account keyfile from ~/.dbt/profiles.yml
(bigquery target). No GCS, no cloud storage.

Run (from the snowflake/ folder):
    uv run --with google-cloud-bigquery --with google-cloud-bigquery-storage \
        python load_from_bq.py

Output: ./_load/events_000.ndjson.gz, events_001.ndjson.gz, ...
Then run load_to_snowflake.py to PUT + COPY them.
"""
import gzip
import json
import os
from pathlib import Path

from google.cloud import bigquery
from google.oauth2 import service_account

# --- config (override with env vars if needed) -----------------------------
KEYFILE = os.environ.get("BQ_KEYFILE", r"C:/Users/YaserSe/keys/ga4-dbt-key.json")
BILLING_PROJECT = os.environ.get("BQ_PROJECT", "ga4-portfolio-503211")
DATE_START = os.environ.get("GA4_START", "20201101")
DATE_END = os.environ.get("GA4_END", "20210131")
ROWS_PER_SHARD = int(os.environ.get("ROWS_PER_SHARD", "250000"))
OUT_DIR = Path(__file__).parent / "_load"

# Same columns the Snowflake RAW.EVENTS table expects. Nested RECORDs are
# serialised to JSON strings in BQ, then reparsed to real objects below so the
# NDJSON has proper nesting (lands as VARIANT, not as a quoted string).
QUERY = f"""
select
    event_date,
    event_timestamp,
    event_name,
    user_pseudo_id,
    to_json_string(event_params)   as event_params,
    to_json_string(device)         as device,
    to_json_string(geo)            as geo,
    to_json_string(traffic_source) as traffic_source,
    to_json_string(ecommerce)      as ecommerce,
    to_json_string(items)          as items
from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
where _table_suffix between '{DATE_START}' and '{DATE_END}'
"""

NESTED = ("event_params", "device", "geo", "traffic_source", "ecommerce", "items")


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    creds = service_account.Credentials.from_service_account_file(KEYFILE)
    client = bigquery.Client(project=BILLING_PROJECT, credentials=creds)

    print(f"Querying GA4 sample {DATE_START}..{DATE_END} (billing: {BILLING_PROJECT})")
    rows = client.query(QUERY).result()  # blocks until the job completes

    shard, n, total = 0, 0, 0
    fh = None

    def open_shard(i: int):
        path = OUT_DIR / f"events_{i:03d}.ndjson.gz"
        return gzip.open(path, "wt", encoding="utf-8"), path

    fh, path = open_shard(shard)
    for row in rows:
        rec = {
            "event_date": row["event_date"],
            "event_timestamp": row["event_timestamp"],
            "event_name": row["event_name"],
            "user_pseudo_id": row["user_pseudo_id"],
        }
        for col in NESTED:
            raw = row[col]
            rec[col] = json.loads(raw) if raw not in (None, "null") else None
        fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
        n += 1
        total += 1
        if n >= ROWS_PER_SHARD:
            fh.close()
            print(f"  wrote {path.name} ({n} rows)")
            shard += 1
            n = 0
            fh, path = open_shard(shard)
    if fh:
        fh.close()
        if n:
            print(f"  wrote {path.name} ({n} rows)")

    print(f"Done. {total} rows across {shard + 1} shard(s) in {OUT_DIR}")


if __name__ == "__main__":
    main()
