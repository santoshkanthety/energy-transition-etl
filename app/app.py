"""US Energy Transition — interactive what-if projector + explorer.

A Databricks App (Streamlit) over the gold lakehouse layer. Four views:
  • What-If   — model renewable growth → year the grid hits a milestone.
  • Fuel mix  — which clean source is doing the work (solar/wind/hydro/gas/coal).
  • Carbon    — lbs CO2 per MWh falling as renewables rise (joins the emissions feed).
  • States    — slice any state's renewable share over time.

Everything (pipeline, dashboard, this app) lives in one Databricks workspace.

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
def q(sql: str) -> pd.DataFrame:
    """Run SQL on the warehouse, return a numeric-coerced DataFrame."""
    w = WorkspaceClient()
    resp = w.statement_execution.execute_statement(
        statement=sql, warehouse_id=WAREHOUSE_ID, wait_timeout="50s"
    )
    rows = resp.result.data_array or []
    cols = [c.name for c in resp.manifest.schema.columns]
    df = pd.DataFrame(rows, columns=cols)
    return df.apply(pd.to_numeric, errors="ignore")


def load_annual() -> pd.DataFrame:
    return q(f"""
        SELECT year(period_date) AS yr,
               round(avg(renewable_share) * 100, 2) AS renewable_pct,
               round(avg(clean_share) * 100, 2)     AS clean_pct,
               round(avg(fossil_share) * 100, 2)    AS fossil_pct
        FROM   {CATALOG}.{SCHEMA}.gold_transition_trend
        GROUP  BY 1 ORDER BY 1
    """)


def project(start_year: int, start_pct: float, cagr: float, end_year: int) -> pd.DataFrame:
    """Compound a renewable-share path forward, capping at 100%."""
    years, vals, v = [], [], start_pct
    for y in range(start_year, end_year + 1):
        years.append(y)
        vals.append(min(v, 100.0))
        v *= 1 + cagr / 100.0
    return pd.DataFrame({"yr": years, "projected_pct": vals})


# ---- Shell -----------------------------------------------------------------
st.title("⚡ US Energy Transition")
st.caption("Live on Databricks · data from the EIA via the gold lakehouse layer.")

try:
    hist = load_annual()
except Exception as e:  # surface config issues clearly in the app
    st.error(f"Could not load data: {e}")
    st.info("Check DATABRICKS_WAREHOUSE_ID and that the app's service principal can read "
            f"{CATALOG}.{SCHEMA}.gold_transition_trend.")
    st.stop()

tab_proj, tab_fuel, tab_carbon, tab_states = st.tabs(
    ["🎛️ What-If", "🔥 Fuel mix", "🏭 Carbon intensity", "🗺️ States"]
)

# ---- Tab 1: What-If projector ----------------------------------------------
with tab_proj:
    last = hist.iloc[-1]
    last_year = int(last["yr"])
    last_ren = float(last["renewable_pct"])
    first = hist.iloc[0]
    span = max(last_year - int(first["yr"]), 1)
    hist_cagr = ((last_ren / float(first["renewable_pct"])) ** (1 / span) - 1) * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("Latest renewable share", f"{last_ren:.1f}%", f"as of {last_year}")
    c2.metric("Latest clean share", f"{float(last['clean_pct']):.1f}%")
    c3.metric("Historical renewable CAGR", f"{hist_cagr:.1f}%/yr", f"since {int(first['yr'])}")

    cagr = st.slider("Renewable annual growth (%/yr)", 0.0, 25.0, round(hist_cagr, 1), 0.5)
    target_year = st.slider("Project to year", last_year + 1, last_year + 30, last_year + 15)
    milestone = st.slider("Milestone to track (% renewable)", 30, 100, 50, 5)

    proj = project(last_year, last_ren, cagr, target_year)
    hit = proj[proj["projected_pct"] >= milestone]
    if not hit.empty:
        hit_year = int(hit.iloc[0]["yr"])
        st.success(f"At **{cagr:.1f}%/yr**, renewables reach **{milestone}%** in **{hit_year}** "
                   f"— {hit_year - last_year} years from now.")
    else:
        end_val = proj.iloc[-1]["projected_pct"]
        st.warning(f"At **{cagr:.1f}%/yr**, renewables reach only **{end_val:.1f}%** by {target_year} "
                   f"— short of the {milestone}% milestone.")

    chart = pd.DataFrame({"yr": list(range(int(hist["yr"].min()), target_year + 1))}).set_index("yr")
    chart["Historical renewable %"] = hist.set_index("yr")["renewable_pct"]
    chart["Projected renewable %"] = proj.set_index("yr")["projected_pct"]
    chart["Milestone"] = milestone
    st.line_chart(chart, height=420)

# ---- Tab 2: Per-fuel mix ---------------------------------------------------
with tab_fuel:
    st.caption("Which source is actually doing the decarbonizing — share of total US generation.")
    try:
        fuel = q(f"""
            SELECT year(period_date) AS yr, fuel_label,
                   round(avg(share) * 100, 2) AS pct
            FROM   {CATALOG}.{SCHEMA}.gold_fuel_breakdown
            GROUP  BY 1, 2 ORDER BY 1
        """)
        wide = fuel.pivot(index="yr", columns="fuel_label", values="pct").fillna(0)
        st.area_chart(wide, height=420)
        st.dataframe(wide.round(1), use_container_width=True)
    except Exception as e:
        st.info(f"`gold_fuel_breakdown` not available yet — run the pipeline. ({e})")

# ---- Tab 3: Carbon intensity -----------------------------------------------
with tab_carbon:
    st.caption("The bottom line of the transition: lbs CO2 emitted per MWh generated.")
    try:
        ci = q(f"""
            SELECT yr,
                   round(lbs_co2_per_mwh, 1)      AS lbs_co2_per_mwh,
                   round(renewable_share * 100, 1) AS renewable_pct
            FROM   {CATALOG}.{SCHEMA}.gold_carbon_intensity
            ORDER  BY yr
        """)
        first_ci, last_ci = ci.iloc[0], ci.iloc[-1]
        drop = (1 - last_ci["lbs_co2_per_mwh"] / first_ci["lbs_co2_per_mwh"]) * 100
        m1, m2 = st.columns(2)
        m1.metric("Carbon intensity now", f"{last_ci['lbs_co2_per_mwh']:.0f} lbs/MWh",
                  f"-{drop:.0f}% since {int(first_ci['yr'])}")
        m2.metric("Renewable share now", f"{last_ci['renewable_pct']:.1f}%")
        st.line_chart(ci.set_index("yr")[["lbs_co2_per_mwh"]], height=380)
        st.scatter_chart(ci, x="renewable_pct", y="lbs_co2_per_mwh", height=320)
    except Exception as e:
        st.info(f"`gold_carbon_intensity` not available yet — run the pipeline. ({e})")

# ---- Tab 4: State explorer -------------------------------------------------
with tab_states:
    st.caption("Slice any state's renewable share over time.")
    try:
        states = q(f"""
            SELECT DISTINCT state_name
            FROM   {CATALOG}.{SCHEMA}.gold_generation_mix_state
            WHERE  state_name IS NOT NULL ORDER BY state_name
        """)["state_name"].tolist()
        picks = st.multiselect("States", states,
                               default=[s for s in ("California", "Texas", "Iowa") if s in states])
        if picks:
            inlist = ",".join("'" + s.replace("'", "''") + "'" for s in picks)
            srows = q(f"""
                SELECT year(period_date) AS yr, state_name,
                       round(avg(renewable_share) * 100, 2) AS renewable_pct
                FROM   {CATALOG}.{SCHEMA}.gold_generation_mix_state
                WHERE  state_name IN ({inlist})
                GROUP  BY 1, 2 ORDER BY 1
            """)
            swide = srows.pivot(index="yr", columns="state_name", values="renewable_pct")
            st.line_chart(swide, height=420)
    except Exception as e:
        st.info(f"State table not available yet — run the pipeline. ({e})")
