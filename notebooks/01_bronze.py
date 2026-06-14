# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Bronze — raw EIA pull
# MAGIC Pulls monthly net electricity generation by fuel type from the EIA API v2 and
# MAGIC lands it as-is (schema-on-read, plus ingest metadata) into the bronze Delta table.

# COMMAND ----------

import requests
from datetime import datetime, timezone
from pyspark.sql import functions as F

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "energy_transition_dev")
dbutils.widgets.text("secret_scope", "energy_transition")
dbutils.widgets.text("start_period", "2015-01")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
secret_scope = dbutils.widgets.get("secret_scope")
start_period = dbutils.widgets.get("start_period")

bronze_table = f"{catalog}.{schema}.bronze_eia_generation"

# COMMAND ----------

api_key = dbutils.secrets.get(scope=secret_scope, key="eia_api_key")

# EIA v2: monthly net generation by state and fuel type (electricity sector).
URL = "https://api.eia.gov/v2/electricity/electric-power-operational-data/data/"
PARAMS = {
    "api_key": api_key,
    "frequency": "monthly",
    "data[0]": "generation",
    "facets[sectorid][]": "98",  # electric power sector, all
    "start": start_period,
    "sort[0][column]": "period",
    "sort[0][direction]": "asc",
    "offset": 0,
    "length": 5000,
}

# COMMAND ----------

def fetch_all(params: dict) -> list:
    """Page through the EIA response (max 5000 rows/page)."""
    rows, offset = [], 0
    while True:
        params = {**params, "offset": offset}
        resp = requests.get(URL, params=params, timeout=60)
        resp.raise_for_status()
        payload = resp.json()["response"]
        batch = payload.get("data", [])
        rows.extend(batch)
        offset += len(batch)
        if len(batch) < params["length"] or offset >= int(payload.get("total", 0)):
            break
    return rows

raw = fetch_all(PARAMS)
print(f"Fetched {len(raw)} rows from EIA since {start_period}.")

# COMMAND ----------

if not raw:
    raise ValueError("EIA returned no rows — check API key, facets, and start_period.")

ingested_at = datetime.now(timezone.utc).isoformat()
df = (
    spark.createDataFrame(raw)
    .withColumn("_ingested_at", F.lit(ingested_at))
    .withColumn("_source", F.lit(URL))
)

(
    df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(bronze_table)
)
print(f"Wrote {df.count()} rows to {bronze_table}")
