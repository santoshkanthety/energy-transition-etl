# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Silver — clean & conform
# MAGIC Types the bronze pull, parses `period` to a month date, renames to friendly columns,
# MAGIC and drops null-generation rows. Keeps every EIA `fuel_id` (including the aggregate
# MAGIC codes ALL / REN / FOS / NUC) — the gold layer selects the right ones, so we avoid the
# MAGIC fuel-hierarchy double-counting that comes from summing overlapping sub-fuels.

# COMMAND ----------

from pyspark.sql import functions as F

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "energy_transition_dev")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

bronze_table = f"{catalog}.{schema}.bronze_eia_generation"
silver_table = f"{catalog}.{schema}.silver_generation"

# COMMAND ----------

bronze = spark.table(bronze_table)

silver = (
    bronze
    .select(
        F.to_date(F.concat_ws("-", F.col("period"), F.lit("01")), "yyyy-MM-dd").alias("period_date"),
        F.col("location").alias("state"),
        F.col("stateDescription").alias("state_name"),
        F.col("fueltypeid").alias("fuel_id"),
        F.col("fuelTypeDescription").alias("fuel_name"),
        F.col("generation").cast("double").alias("generation_mwh"),
        bronze["generation-units"].alias("units"),
        F.col("_ingested_at"),
    )
    .filter(F.col("generation_mwh").isNotNull())
    .dropDuplicates(["period_date", "state", "fuel_id"])
)

(
    silver.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(silver_table)
)
print(f"Wrote {silver.count()} rows to {silver_table}")
