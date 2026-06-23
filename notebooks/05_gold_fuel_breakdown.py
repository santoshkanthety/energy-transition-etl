# Databricks notebook source
# MAGIC %md
# MAGIC # 05 · Gold — per-fuel breakdown
# MAGIC The aggregate codes (REN/FOS/NUC) answer "how clean". This answers "**which** clean":
# MAGIC solar vs wind vs hydro vs gas vs coal individually, as a share of total generation.
# MAGIC Reads the granular EIA fuel codes already kept in silver — no extra API calls.
# MAGIC - `gold_fuel_breakdown` — national monthly share per individual fuel.

# COMMAND ----------

from pyspark.sql import functions as F

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "energy_transition_dev")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

silver_table = f"{catalog}.{schema}.silver_generation"
gold_fuel = f"{catalog}.{schema}.gold_fuel_breakdown"

# Granular EIA fuel codes (exclude aggregates ALL/REN/FOS/NUC and "other").
FUELS = {
    "SUN": "Solar",
    "WND": "Wind",
    "HYC": "Hydro",
    "GEO": "Geothermal",
    "WWW": "Biomass/Wood",
    "NG":  "Natural gas",
    "COW": "Coal",
    "PEL": "Petroleum",
    "NUC": "Nuclear",
}

# COMMAND ----------

silver = spark.table(silver_table).filter(F.col("state") == "US")

# National total per month (EIA's own ALL aggregate).
totals = (
    silver.filter(F.col("fuel_id") == "ALL")
    .select("period_date", F.col("generation_mwh").alias("total_mwh"))
)

mapping = F.create_map(*[x for kv in FUELS.items() for x in (F.lit(kv[0]), F.lit(kv[1]))])

fuels = (
    silver.filter(F.col("fuel_id").isin(list(FUELS.keys())))
    .select(
        "period_date",
        F.col("fuel_id"),
        mapping[F.col("fuel_id")].alias("fuel_label"),
        F.col("generation_mwh"),
    )
    .join(totals, "period_date", "left")
    .withColumn("share", F.try_divide("generation_mwh", "total_mwh"))
)

(
    fuels.write.format("delta")
    .mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(gold_fuel)
)
print(f"Wrote {fuels.count()} rows to {gold_fuel}")
display(
    fuels.filter(F.col("period_date") == fuels.agg(F.max("period_date")).first()[0])
    .select("fuel_label", "generation_mwh", "share")
    .orderBy(F.desc("share"))
)
