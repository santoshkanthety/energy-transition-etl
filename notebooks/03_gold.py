# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Gold — energy transition metrics
# MAGIC Builds the analytics tables from EIA's **aggregate fuel codes** (no double-counting):
# MAGIC `ALL` = total, `REN` = renewables, `NUC` = nuclear, `FOS` = fossil.
# MAGIC - `gold_transition_trend` — national monthly renewable / clean / fossil share over time.
# MAGIC - `gold_generation_mix_state` — per-state monthly mix and renewable share.

# COMMAND ----------

from pyspark.sql import functions as F

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "energy_transition_dev")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

silver_table = f"{catalog}.{schema}.silver_generation"
gold_state = f"{catalog}.{schema}.gold_generation_mix_state"
gold_national = f"{catalog}.{schema}.gold_transition_trend"

AGG = ["ALL", "REN", "NUC", "FOS"]

# COMMAND ----------

# Pivot the aggregate codes into one row per (period, state): total / renewable / nuclear / fossil.
mix = (
    spark.table(silver_table)
    .filter(F.col("fuel_id").isin(AGG))
    .groupBy("period_date", "state", "state_name")
    .pivot("fuel_id", AGG)
    .agg(F.first("generation_mwh"))
    .withColumnRenamed("ALL", "total_mwh")
    .withColumnRenamed("REN", "renewable_mwh")
    .withColumnRenamed("NUC", "nuclear_mwh")
    .withColumnRenamed("FOS", "fossil_mwh")
    .na.fill(0, ["total_mwh", "renewable_mwh", "nuclear_mwh", "fossil_mwh"])
    .withColumn("clean_mwh", F.col("renewable_mwh") + F.col("nuclear_mwh"))
    .withColumn("renewable_share", F.try_divide("renewable_mwh", "total_mwh"))
    .withColumn("clean_share", F.try_divide("clean_mwh", "total_mwh"))
    .withColumn("fossil_share", F.try_divide("fossil_mwh", "total_mwh"))
)

# COMMAND ----------

# National trend = EIA's own US aggregate row.
national = mix.filter(F.col("state") == "US").orderBy("period_date")
(
    national.write.format("delta")
    .mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(gold_national)
)
print(f"Wrote {national.count()} rows to {gold_national}")

# Per-state mix (exclude the US aggregate so state rollups don't double-count).
state = mix.filter(F.col("state") != "US")
(
    state.write.format("delta")
    .mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(gold_state)
)
print(f"Wrote {state.count()} rows to {gold_state}")
display(national.select("period_date", "renewable_share", "clean_share", "fossil_share"))
