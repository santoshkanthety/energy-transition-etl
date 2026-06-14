<div align="center">

# ⚡ Energy Transition ETL

### Tracking the US shift to clean power — a Databricks lakehouse from raw API to insight

[![Databricks](https://img.shields.io/badge/Databricks-Lakehouse-FF3621?logo=databricks&logoColor=white)](https://www.databricks.com/)
[![PySpark](https://img.shields.io/badge/PySpark-3.5-E25A1C?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Delta Lake](https://img.shields.io/badge/Delta_Lake-Medallion-00ADD8?logo=delta&logoColor=white)](https://delta.io/)
[![Asset Bundles](https://img.shields.io/badge/Deploy-Asset_Bundles-FF3621)](https://docs.databricks.com/dev-tools/bundles/)
[![EIA API v2](https://img.shields.io/badge/Source-EIA_API_v2-1f4e79)](https://www.eia.gov/opendata/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*Bronze → Silver → Gold pipeline that ingests 11 years of US electricity generation,
classifies every fuel, and quantifies the renewable & clean-energy transition.*

</div>

---

## 📈 The headline

<div align="center">
<img src="assets/transition_trend.png" alt="US generation mix 2015–present" width="92%">
</div>

> Renewables roughly **doubled** their share of US electricity in a decade — **13% → 25%** —
> while fossil generation fell from **66% → 57%**. Clean power (renewable + nuclear) now sits near **43%**.
> The sawtooth is real: renewable output peaks every spring (wind + hydro) and dips in late summer.

## 🔍 What the data says

| Metric (national)            | 2015  | 2025  | Δ        |
|------------------------------|-------|-------|----------|
| Renewable share              | 13.2% | 24.6% | **+11.4 pts** |
| Clean share (renew + nuclear)| 33.6% | 43.1% | +9.5 pts |
| Fossil share                 | 66.3% | 57.1% | −9.2 pts |

**Leaders are far ahead of the average** — a handful of states already run majority-renewable grids:

<div align="center">
<img src="assets/top_states.png" alt="Top 10 states by renewable share" width="80%">
</div>

*Analysis notebook-ready: every number above comes straight from the gold tables this pipeline builds.*

---

## 🏗️ Architecture

A classic **medallion lakehouse** — each layer is one notebook, wired into a dependent job DAG.

```mermaid
flowchart LR
    EIA["🛰️ EIA API v2<br/>monthly generation"] --> B
    subgraph Lakehouse["Unity Catalog · Delta"]
        B["🥉 Bronze<br/><i>01_bronze</i><br/>raw + ingest metadata"] --> S
        S["🥈 Silver<br/><i>02_silver</i><br/>typed · dated · deduped"] --> G
        G["🥇 Gold<br/><i>03_gold</i><br/>renewable / clean / fossil share"]
    end
    G --> V["📊 Dashboards & SQL"]
```

| Layer  | Notebook         | Output table(s)                                          | Job task |
|--------|------------------|----------------------------------------------------------|----------|
| 🥉 Bronze | `01_bronze.py` | `bronze_eia_generation` — raw API rows + ingest metadata | `bronze` |
| 🥈 Silver | `02_silver.py` | `silver_generation` — typed, month-dated, deduped        | `silver` |
| 🥇 Gold   | `03_gold.py`   | `gold_transition_trend`, `gold_generation_mix_state`     | `gold`   |

### Engineering decisions worth calling out
- **No double-counting.** EIA returns overlapping fuel codes (`ALL`, `REN`, `FOS`, sub-fuels…).
  The gold layer reads EIA's own **aggregate codes** rather than summing sub-fuels — the metrics
  reconcile exactly to the `ALL` total.
- **Idempotent.** Every layer is a full `overwrite` refresh; rerun any time, same result.
- **Self-sufficient DAG.** Bronze creates the catalog/schema, so the job runs cold with no manual setup.
- **Secrets stay out of git.** EIA key lives in a Databricks secret scope, read via `dbutils.secrets.get`.

---

## 🧱 Stack

`Databricks` · `Unity Catalog` · `Delta Lake` · `PySpark` · `Databricks Asset Bundles` · `EIA Open Data API v2`

## 🚀 Run it

```bash
# 1. Auth (profile-based, no tokens in repo)
databricks auth login --host https://dbc-036c0f5b-a5d8.cloud.databricks.com

# 2. EIA key into the secret scope  (free key: eia.gov/opendata/register.php)
databricks secrets create-scope energy_transition
databricks secrets put-secret  energy_transition eia_api_key

# 3. Deploy + run the bronze→silver→gold DAG
databricks bundle validate
databricks bundle deploy -t dev
databricks bundle run energy_transition_etl -t dev
```

Or open `notebooks/00 → 03` in VS Code and use the Databricks extension's **Run file on Databricks**.

### Sample query
```sql
SELECT date_format(period_date, 'yyyy') AS yr,
       round(avg(renewable_share) * 100, 1) AS renewable_pct
FROM   main.energy_transition.gold_transition_trend
GROUP  BY 1 ORDER BY 1;
```

### Regenerate the charts
```bash
python src/energy_transition/make_charts.py   # reads gold extracts → assets/*.png
```

---

## 🗂️ Repo layout
```
databricks.yml                          # bundle: dev/prod targets, variables
resources/energy_transition_etl.job.yml # 3-task DAG (bronze→silver→gold)
notebooks/00_setup.py … 03_gold.py      # the pipeline
src/energy_transition/make_charts.py    # README visualizations
assets/                                 # rendered charts
CLAUDE.md                               # context brief for AI assistants
```

## 📜 License
MIT — see [LICENSE](LICENSE). Data courtesy of the [US EIA](https://www.eia.gov/opendata/), public domain.
