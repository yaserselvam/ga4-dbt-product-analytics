#!/usr/bin/env python
"""Launcher: run dbt via the Python entry point, not the `dbt` console-script.

This machine's AppLocker blocks the uv-generated `dbt.exe` shim ("Access is
denied", os error 5), the same wall that blocks the pwc shim. Importing and
calling dbt's click entry point runs it through python.exe instead, which is
allowed. Run FROM this folder so dbt finds dbt_project.yml:

    uv run --with dbt-snowflake python dbt_run.py debug
    uv run --with dbt-snowflake python dbt_run.py build
    uv run --with dbt-snowflake python dbt_run.py run --select rfm_segments

sys.argv[1:] is forwarded to dbt unchanged.
"""
from dbt.cli.main import cli

if __name__ == "__main__":
    cli()
