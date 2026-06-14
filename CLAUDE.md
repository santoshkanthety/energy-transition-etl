# CLAUDE.md — energy_transition_etl

Context brief for any AI assistant working in this repo. Read this first.

## What this is
A Databricks medallion ETL that tracks the US energy transition. It pulls electricity
generation by fuel type from the **EIA API v2**, classifies fuels as renewable / fossil /
nuclear / other, and produces gold tables for the renewable & clean-energy share over time.

## Architecture
- `notebooks/00_setup.py` — one-time: create catalog/schema, verify the EIA secret. Not in the DAG.
- `notebooks/01_bronze.py` — raw EIA pull → `bronze_eia_generation` (overwrite + ingest metadata).
- `notebooks/02_silver.py` — type/clean/classify → `silver_generation`.
- `notebooks/03_gold.py` — aggregate → `gold_generation_mix_state`, `gold_transition_trend`.
- Job DAG: **bronze → silver → gold** (`resources/energy_transition_etl.job.yml`).

## Conventions
- Tables live in `${catalog}.${schema}`. Defaults: catalog `main`, schema `energy_transition`
  (prod) / `energy_transition_dev` (dev). Passed to notebooks as `base_parameters` widgets.
- All writes are idempotent `overwrite` + `overwriteSchema` — full refresh each run.
- Secrets: EIA key in the **`energy_transition`** secret scope, key `eia_api_key`.
  Never hardcode it; read via `dbutils.secrets.get`. Nothing sensitive in repo or `databricks.yml`.

## Workspace
- Host: `https://dbc-036c0f5b-a5d8.cloud.databricks.com`
- CLI auth: `databricks auth login --host <host>` (profile-based, no repo tokens).

## Run it
Interactive: open `00 → 03`, "Run file on Databricks".
As a job:
```bash
databricks bundle validate
databricks bundle deploy -t dev
databricks bundle run energy_transition_etl -t dev
```

## Next steps
1. Auth CLI + create the `energy_transition` secret scope and `eia_api_key`.
2. Run `00_setup` once to create catalog/schema and confirm the secret resolves.
3. `bundle validate` → `deploy -t dev` → `run`.
4. Build a dashboard / SQL view on `gold_transition_trend` (renewable_share over time).
