# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Gold — energy transition metrics
# MAGIC Aggregates silver into the analytics tables that drive the dashboard:
# MAGIC monthly renewable / clean share of generation, by state and nationally.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql import Window

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "energy_transition_dev")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

silver_table = f"{catalog}.{schema}.silver_generation"
gold_state = f"{catalog}.{schema}.gold_generation_mix_state"
gold_national = f"{catalog}.{schema}.gold_transition_trend"

# COMMAND ----------

silver = spark.table(silver_table)

# Generation mix by state x month x category, with share of monthly state total.
by_cat = (
    silver.groupBy("period_date", "state", "state_name", "energy_category")
    .agg(F.sum("generation_mwh").alias("generation_mwh"))
)
state_total = Window.partitionBy("period_date", "state")
mix_state = by_cat.withColumn(
    "share_of_state", F.col("generation_mwh") / F.sum("generation_mwh").over(state_total)
)

(
    mix_state.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(gold_state)
)
print(f"Wrote {mix_state.count()} rows to {gold_state}")

# COMMAND ----------

# National monthly transition trend: renewable share and clean share over time.
national = (
    silver.groupBy("period_date")
    .agg(
        F.sum("generation_mwh").alias("total_mwh"),
        F.sum(F.when(F.col("energy_category") == "renewable", F.col("generation_mwh")).otherwise(0)).alias("renewable_mwh"),
        F.sum(F.when(F.col("is_clean"), F.col("generation_mwh")).otherwise(0)).alias("clean_mwh"),
    )
    .withColumn("renewable_share", F.col("renewable_mwh") / F.col("total_mwh"))
    .withColumn("clean_share", F.col("clean_mwh") / F.col("total_mwh"))
    .orderBy("period_date")
)

(
    national.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(gold_national)
)
print(f"Wrote {national.count()} rows to {gold_national}")
display(national)
