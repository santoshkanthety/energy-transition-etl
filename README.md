# Energy Transition ETL — Databricks

A production-style **medallion lakehouse pipeline** on Databricks that tracks the US energy
transition. It ingests electricity generation by fuel type from the [EIA API v2](https://www.eia.gov/opendata/),
classifies each fuel as renewable / fossil / nuclear, and publishes analytics tables for the
**renewable and clean-energy share of generation over time**.

> Portfolio project demonstrating: Databricks Asset Bundles, Unity Catalog, the
> bronze→silver→gold medallion pattern, secret management, and CI-friendly job DAGs.

## Architecture

```
EIA API v2 ──▶ 01 bronze ──▶ 02 silver ──▶ 03 gold ──▶ dashboard
              (raw pull)     (clean +       (renewable /
                              classify)      clean share)
```

| Layer  | Notebook            | Output table(s)                                          |
|--------|---------------------|----------------------------------------------------------|
| Bronze | `01_bronze.py`      | `bronze_eia_generation` — raw API rows + ingest metadata |
| Silver | `02_silver.py`      | `silver_generation` — typed, dated, fuel-classified      |
| Gold   | `03_gold.py`        | `gold_generation_mix_state`, `gold_transition_trend`     |

The three notebooks run as a dependent **bronze → silver → gold** job DAG defined in
`resources/energy_transition_etl.job.yml`.

## Stack
- **Databricks** (Unity Catalog, Delta, serverless jobs)
- **PySpark**
- **Databricks Asset Bundles** for deploy/run as code
- **EIA Open Data API v2** as the source

## Setup

1. **Auth** the CLI to the workspace:
   ```bash
   databricks auth login --host https://dbc-036c0f5b-a5d8.cloud.databricks.com
   ```
2. **Create the secret** (EIA key never touches the repo):
   ```bash
   databricks secrets create-scope energy_transition
   databricks secrets put-secret energy_transition eia_api_key
   ```
   Get a free key at <https://www.eia.gov/opendata/register.php>.
3. **One-time setup** — run `notebooks/00_setup.py` to create the catalog/schema and verify the secret.

## Run

**Interactive** — open `00 → 03` in VS Code and use the Databricks extension's
"Run file on Databricks".

**As a job (Asset Bundle):**
```bash
databricks bundle validate
databricks bundle deploy -t dev
databricks bundle run energy_transition_etl -t dev
```

## Repo layout
```
databricks.yml                         # bundle: targets, variables
resources/energy_transition_etl.job.yml # 3-task DAG
notebooks/00_setup.py … 03_gold.py     # the pipeline
CLAUDE.md                              # context brief for AI assistants
.vscode/                               # recommended extensions + settings
```

## License
MIT — see [LICENSE](LICENSE).
