#!/usr/bin/env python
"""Step 2b of the runbook: PUT the gzipped NDJSON shards from load_from_bq.py
into a Snowflake stage and COPY them into GA4_DEMO.RAW.EVENTS.

Credentials come from env vars (never hard-coded / committed):
    SNOWFLAKE_ACCOUNT   e.g. ABCDEFG-XY12345   (your account identifier)
    SNOWFLAKE_USER      e.g. YASERSELVAM
    SNOWFLAKE_PASSWORD  your trial password    (omit to use browser SSO)

Run (from the snowflake/ folder), PowerShell:
    $env:SNOWFLAKE_ACCOUNT="ABCDEFG-XY12345"
    $env:SNOWFLAKE_USER="YASERSELVAM"
    $env:SNOWFLAKE_PASSWORD="..."
    uv run --with snowflake-connector-python python load_to_snowflake.py

Idempotent: truncates RAW.EVENTS and reloads, so you can re-run safely.
"""
import glob
import os
from pathlib import Path

import snowflake.connector

LOAD_DIR = Path(__file__).parent / "_load"
STAGE = "GA4_DEMO.RAW.GA4_STAGE"
TABLE = "GA4_DEMO.RAW.EVENTS"

COPY_SQL = f"""
copy into {TABLE}
  (event_date, event_timestamp, event_name, user_pseudo_id,
   event_params, device, geo, traffic_source, ecommerce, items)
from (
  select
    $1:event_date::string,
    $1:event_timestamp::number,
    $1:event_name::string,
    $1:user_pseudo_id::string,
    $1:event_params,
    $1:device,
    $1:geo,
    $1:traffic_source,
    $1:ecommerce,
    $1:items
  from @{STAGE}
)
file_format = (type = json)
on_error = 'abort_statement';
"""


def main() -> None:
    shards = sorted(glob.glob(str(LOAD_DIR / "events_*.ndjson.gz")))
    if not shards:
        raise SystemExit(f"No shards in {LOAD_DIR}. Run load_from_bq.py first.")

    account = os.environ["SNOWFLAKE_ACCOUNT"]
    user = os.environ["SNOWFLAKE_USER"]
    password = os.environ.get("SNOWFLAKE_PASSWORD")

    conn_kwargs = dict(
        account=account,
        user=user,
        warehouse="COMPUTE_WH",
        role="ACCOUNTADMIN",
        database="GA4_DEMO",
        schema="RAW",
    )
    if password:
        # Snowflake enforces MFA on password logins. 'username_password_mfa'
        # sends a Duo push on first connect (enrol MFA in Snowsight first) and,
        # with the secure-local-storage extra, caches a token so re-runs are
        # silent. A TOTP code can be passed via SNOWFLAKE_PASSCODE instead.
        conn_kwargs["password"] = password
        passcode = os.environ.get("SNOWFLAKE_PASSCODE")
        if passcode:
            # TOTP (authenticator-app) MFA: default authenticator + a fresh code.
            conn_kwargs["passcode"] = passcode
        else:
            # Duo-push MFA with token caching (secure-local-storage extra).
            conn_kwargs["authenticator"] = "username_password_mfa"
    else:
        conn_kwargs["authenticator"] = "externalbrowser"

    print(f"Connecting to {account} as {user} ...")
    conn = snowflake.connector.connect(**conn_kwargs)
    cur = conn.cursor()
    try:
        cur.execute(f"create stage if not exists {STAGE} "
                    "file_format = (type = json)")
        cur.execute(f"truncate table {TABLE}")

        for i, shard in enumerate(shards, 1):
            posix = Path(shard).as_posix()
            print(f"  PUT {i}/{len(shards)}: {Path(shard).name}")
            cur.execute(
                f"put 'file://{posix}' @{STAGE} "
                "auto_compress=false overwrite=true"
            )

        print("COPY INTO RAW.EVENTS ...")
        cur.execute(COPY_SQL)

        cur.execute(f"select count(*) from {TABLE}")
        print(f"Loaded rows: {cur.fetchone()[0]:,}")
        cur.execute(f"remove @{STAGE}")  # tidy the stage; table keeps the data
    finally:
        cur.close()
        conn.close()
    print("Done. Next: dbt build.")


if __name__ == "__main__":
    main()
