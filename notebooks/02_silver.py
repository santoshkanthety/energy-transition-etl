# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Silver — clean & conform
# MAGIC Types the bronze pull, parses the period to a date, classifies each fuel type as
# MAGIC renewable / fossil / nuclear / other, and drops null-generation rows.

# COMMAND ----------

from pyspark.sql import functions as F

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "energy_transition_dev")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

bronze_table = f"{catalog}.{schema}.bronze_eia_generation"
silver_table = f"{catalog}.{schema}.silver_generation"

# COMMAND ----------

# EIA fueltypeid -> energy category. Solar/wind/hydro/geothermal/biomass = renewable.
RENEWABLE = ["SUN", "WND", "HYC", "HPS", "GEO", "WWW", "WAS", "ORW"]
FOSSIL = ["COW", "NG", "PEL", "PC", "OOG"]
NUCLEAR = ["NUC"]

# COMMAND ----------

bronze = spark.table(bronze_table)

silver = (
    bronze
    .select(
        F.to_date(F.concat_ws("-", F.col("period"), F.lit("01")), "yyyy-MM-dd").alias("period_date"),
        F.col("stateid").alias("state"),
        F.col("stateDescription").alias("state_name"),
        F.col("fueltypeid").alias("fuel_id"),
        F.col("fuelTypeDescription").alias("fuel_name"),
        F.col("generation").cast("double").alias("generation_mwh"),
        F.col("generation-units").alias("units"),
        F.col("_ingested_at"),
    )
    .filter(F.col("generation_mwh").isNotNull())
    .withColumn(
        "energy_category",
        F.when(F.col("fuel_id").isin(RENEWABLE), "renewable")
        .when(F.col("fuel_id").isin(FOSSIL), "fossil")
        .when(F.col("fuel_id").isin(NUCLEAR), "nuclear")
        .otherwise("other"),
    )
    .withColumn("is_clean", F.col("energy_category").isin("renewable", "nuclear"))
)

(
    silver.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(silver_table)
)
print(f"Wrote {silver.count()} rows to {silver_table}")
