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

### [▶ &nbsp;Launch the live What-If app](https://energy-transition-whatif-4258774216266378.aws.databricksapps.com)

[![Open the live app](https://img.shields.io/badge/▶_Live_App-Databricks-FF3621?style=for-the-badge&logo=databricks&logoColor=white)](https://energy-transition-whatif-4258774216266378.aws.databricksapps.com)
&nbsp;
[![Refreshed daily](https://img.shields.io/badge/Data-Refreshed_daily-2e8b57?style=for-the-badge)](resources/energy_transition_etl.job.yml)

<sub>Model a renewable-growth scenario, break down the mix by fuel, watch carbon intensity fall, and slice any state — all on live EIA data.</sub>

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

## 🖥️ Live on Databricks — dashboard + interactive app

Everything stays in one platform (no separate BI tool). The pipeline feeds an **AI/BI dashboard**
and a **Streamlit "what-if" app**, both deployed as code via the Asset Bundle.

| | What it is | Link |
|---|---|---|
| 📊 **AI/BI Dashboard** | KPIs + trend + top-states, published with embedded credentials | [`/dashboardsv3/…/published`](https://dbc-036c0f5b-a5d8.cloud.databricks.com/dashboardsv3/01f167fb84e01d88acaf62a3e633ad3e/published) |
| 🎛️ **What-If App** | Four views: scenario projector · per-fuel mix · carbon intensity · state explorer | [`energy-transition-whatif…`](https://energy-transition-whatif-4258774216266378.aws.databricksapps.com) |

The dashboard **embeds into any site** (e.g. my portfolio) via iframe — see
[`dashboards/EMBED.md`](dashboards/EMBED.md) for the React/HTML snippet and the one-time
domain-whitelist step.

```tsx
<iframe src="https://dbc-036c0f5b-a5d8.cloud.databricks.com/embed/dashboardsv3/01f167fb84e01d88acaf62a3e633ad3e"
        width="100%" height="800" title="US Energy Transition" />
```

> **Access note:** published dashboards/apps require a workspace login by default. A no-login
> public view needs an account-admin embedding/whitelist setting (see `EMBED.md`).

### Inside the app

<table>
<tr>
<td width="50%"><img src="assets/app_whatif.png" alt="What-If projector tab"><br><sub><b>🎛️ What-If</b> — slide a growth rate, see the year renewables cross a milestone.</sub></td>
<td width="50%"><img src="assets/app_fuel.png" alt="Per-fuel mix tab"><br><sub><b>🔥 Fuel mix</b> — solar/wind/hydro/gas/coal as a share of generation over time.</sub></td>
</tr>
<tr>
<td width="50%"><img src="assets/app_carbon.png" alt="Carbon intensity tab"><br><sub><b>🏭 Carbon intensity</b> — lbs CO₂/MWh falling (1069→829) as renewables rise.</sub></td>
<td width="50%"><img src="assets/app_states.png" alt="State explorer tab"><br><sub><b>🗺️ States</b> — compare any states' renewable trajectories.</sub></td>
</tr>
</table>

---

## 🏗️ Architecture

A classic **medallion lakehouse** — each layer is one notebook, wired into a dependent job DAG.

```mermaid
flowchart LR
    EIA["🛰️ EIA API v2<br/>monthly generation"] --> B
    EIA2["🛰️ EIA CO₂<br/>annual emissions"] --> BE
    subgraph Lakehouse["Unity Catalog · Delta"]
        B["🥉 Bronze<br/><i>01_bronze</i><br/>raw + ingest metadata"] --> S
        BE["🥉 Bronze<br/><i>01b_emissions</i>"] --> GE
        S["🥈 Silver<br/><i>02_silver</i><br/>typed · dated · deduped"] --> G
        S --> GF["🥇 Gold<br/><i>05_fuel_breakdown</i><br/>per-fuel share"]
        G["🥇 Gold<br/><i>03_gold</i><br/>renewable / clean / fossil share"] --> GE
        GE["🥇 Gold<br/><i>04_emissions</i><br/>CO₂ trend · carbon intensity"]
    end
    G --> V["📊 Dashboards · App · SQL"]
    GF --> V
    GE --> V
```

| Layer  | Notebook                 | Output table(s)                                          | Job task |
|--------|--------------------------|----------------------------------------------------------|----------|
| 🥉 Bronze | `01_bronze.py`         | `bronze_eia_generation` — raw API rows + ingest metadata | `bronze` |
| 🥉 Bronze | `01b_bronze_emissions.py` | `bronze_eia_emissions` — annual electric-power CO₂    | `bronze_emissions` |
| 🥈 Silver | `02_silver.py`         | `silver_generation` — typed, month-dated, deduped        | `silver` |
| 🥇 Gold   | `03_gold.py`           | `gold_transition_trend`, `gold_generation_mix_state`     | `gold`   |
| 🥇 Gold   | `04_gold_emissions.py` | `gold_emissions_trend`, `gold_carbon_intensity`         | `gold_emissions` |
| 🥇 Gold   | `05_gold_fuel_breakdown.py` | `gold_fuel_breakdown` — solar/wind/hydro/gas/coal  | `gold_fuel_breakdown` |

The job runs **daily at 09:10 UTC** (`schedule` block in the job YAML). EIA revises recent
months after first publish, so a daily full-refresh keeps every number current with almost no
compute (serverless, idempotent overwrite). Dev is `PAUSED`, prod is `UNPAUSED` — flip via the
`schedule_pause` bundle variable.

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

## 🛰️ Sources & credibility

Every number traces to the **US Energy Information Administration** — the official federal
statistics agency for energy, public domain, citable.

| Feed | EIA API endpoint | Grain | Powers |
|------|------------------|-------|--------|
| Net generation | `electricity/electric-power-operational-data` | monthly · state · fuel | renewable / clean / fossil share, per-fuel mix |
| CO₂ emissions  | `co2-emissions/co2-emissions-aggregates`       | annual · state · sector | emissions trend, carbon intensity (lbs CO₂/MWh) |

Both share one API key and one secret scope. **Candidate next feeds** (same credibility bar):
EIA `electricity/operating-generator-capacity` (capacity vs. generation gap), EPA **eGRID**
(plant-level emission factors), and **Ember** / **Our World in Data** for an international
benchmark — each slots in as another `bronze_*` notebook behind the same medallion contract.

## 🔪 What you can slice

- **Transition trend** — renewable / clean / fossil share, monthly, national + per state.
- **Per-fuel mix** — solar vs. wind vs. hydro vs. gas vs. coal individually (`gold_fuel_breakdown`).
- **Carbon intensity** — lbs CO₂ per MWh falling as renewables rise (`gold_carbon_intensity`).
- **Emissions YoY** — annual electric-power CO₂ and year-over-year change per state.
- **State explorer** — pick any states, compare renewable trajectories (live in the app).

## 🗺️ Roadmap

- [ ] Embed the per-fuel and carbon-intensity charts in the AI/BI dashboard.
- [ ] Add capacity feed → **capacity factor** and "capacity built vs. energy delivered".
- [ ] Seasonal decomposition of the renewable sawtooth (wind/hydro spring peak).
- [ ] Data-quality expectations (DLT / `assert` on share ∈ [0,1], `ALL` reconciles to sum).
- [ ] Public no-login embed once the account-admin whitelist is set (see `EMBED.md`).

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
databricks.yml                          # bundle: dev/prod targets, variables, daily schedule var
resources/energy_transition_etl.job.yml # 6-task DAG + daily schedule
resources/dashboard.yml · app.yml       # AI/BI dashboard + Streamlit app as code
notebooks/00_setup.py … 05_gold_*.py    # the pipeline (generation + emissions + per-fuel)
dashboards/energy_transition.lvdash.json# dashboard definition + EMBED.md
app/app.py · app.yaml                    # interactive what-if + explorer Databricks App
src/energy_transition/make_charts.py    # README visualizations
assets/                                 # rendered charts
CLAUDE.md                               # context brief for AI assistants
```

## 📜 License
MIT — see [LICENSE](LICENSE). Data courtesy of the [US EIA](https://www.eia.gov/opendata/), public domain.
