"""US Energy Transition — interactive what-if projector.

A Databricks App (Streamlit) that reads the gold trend table and lets you model
forward scenarios: pick an annual growth rate for renewables and see when the US
grid crosses clean-energy milestones. Replaces a separate BI tool — everything
(pipeline, dashboard, this app) lives in one Databricks workspace.

Auth: runs as the app's service principal; the Databricks SDK picks up credentials
from the App environment automatically. The target SQL warehouse comes from the
DATABRICKS_WAREHOUSE_ID env var (set in app.yaml / bundle resource).
"""
import os

import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient

CATALOG = os.getenv("ETL_CATALOG", "main")
SCHEMA = os.getenv("ETL_SCHEMA", "energy_transition_dev")
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")

st.set_page_config(page_title="Energy Transition · What-If", page_icon="⚡", layout="wide")


@st.cache_data(ttl=3600)
def load_annual() -> pd.DataFrame:
    """Annual national renewable / clean / fossil share from the gold trend table."""
    w = WorkspaceClient()
    sql = f"""
        SELECT year(period_date) AS yr,
               round(avg(renewable_share) * 100, 2) AS renewable_pct,
               round(avg(clean_share) * 100, 2)     AS clean_pct,
               round(avg(fossil_share) * 100, 2)    AS fossil_pct
        FROM   {CATALOG}.{SCHEMA}.gold_transition_trend
        GROUP  BY 1 ORDER BY 1
    """
    resp = w.statement_execution.execute_statement(
        statement=sql, warehouse_id=WAREHOUSE_ID, wait_timeout="50s"
    )
    rows = resp.result.data_array or []
    cols = [c.name for c in resp.manifest.schema.columns]
    df = pd.DataFrame(rows, columns=cols)
    return df.apply(pd.to_numeric)


def project(start_year: int, start_pct: float, cagr: float, end_year: int) -> pd.DataFrame:
    """Compound a renewable-share path forward, capping at 100%."""
    years, vals, v = [], [], start_pct
    for y in range(start_year, end_year + 1):
        years.append(y)
        vals.append(min(v, 100.0))
        v *= 1 + cagr / 100.0
    return pd.DataFrame({"yr": years, "projected_pct": vals})


# ---- UI --------------------------------------------------------------------
st.title("⚡ US Energy Transition — What-If Projector")
st.caption("Historical data from the EIA via the gold lakehouse layer. Move the sliders to model a scenario.")

try:
    hist = load_annual()
except Exception as e:  # surface config issues clearly in the app
    st.error(f"Could not load data: {e}")
    st.info("Check DATABRICKS_WAREHOUSE_ID and that the app's service principal can read "
            f"{CATALOG}.{SCHEMA}.gold_transition_trend.")
    st.stop()

last = hist.iloc[-1]
last_year = int(last["yr"])
last_ren = float(last["renewable_pct"])

# 10-yr historical renewable CAGR as a sensible slider default.
first = hist.iloc[0]
span = max(last_year - int(first["yr"]), 1)
hist_cagr = ((last_ren / float(first["renewable_pct"])) ** (1 / span) - 1) * 100

c1, c2, c3 = st.columns(3)
c1.metric("Latest renewable share", f"{last_ren:.1f}%", f"as of {last_year}")
c2.metric("Latest clean share", f"{float(last['clean_pct']):.1f}%")
c3.metric("Historical renewable CAGR", f"{hist_cagr:.1f}%/yr", f"since {int(first['yr'])}")

st.sidebar.header("Scenario")
cagr = st.sidebar.slider("Renewable annual growth (%/yr)", 0.0, 25.0, round(hist_cagr, 1), 0.5)
target_year = st.sidebar.slider("Project to year", last_year + 1, last_year + 30, last_year + 15)
milestone = st.sidebar.slider("Milestone to track (% renewable)", 30, 100, 50, 5)

proj = project(last_year, last_ren, cagr, target_year)

# Year the scenario crosses the milestone.
hit = proj[proj["projected_pct"] >= milestone]
if not hit.empty:
    hit_year = int(hit.iloc[0]["yr"])
    st.success(f"At **{cagr:.1f}%/yr**, renewables reach **{milestone}%** of US generation in **{hit_year}** "
               f"— {hit_year - last_year} years from now.")
else:
    end_val = proj.iloc[-1]["projected_pct"]
    st.warning(f"At **{cagr:.1f}%/yr**, renewables reach only **{end_val:.1f}%** by {target_year} "
               f"— short of the {milestone}% milestone.")

# ---- Chart: history + projection ------------------------------------------
chart = pd.DataFrame({"yr": list(range(int(hist["yr"].min()), target_year + 1))}).set_index("yr")
chart["Historical renewable %"] = hist.set_index("yr")["renewable_pct"]
chart["Projected renewable %"] = proj.set_index("yr")["projected_pct"]
chart["Milestone"] = milestone
st.line_chart(chart, height=420)

with st.expander("Show historical data"):
    st.dataframe(hist, use_container_width=True, hide_index=True)
