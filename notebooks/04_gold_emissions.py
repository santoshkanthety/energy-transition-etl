# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Gold — emissions & carbon intensity
# MAGIC Combines the new **CO2 emissions** feed (`bronze_eia_emissions`) with the generation
# MAGIC trend to produce the cleanest single proof of the transition: **carbon intensity**
# MAGIC (lbs CO2 per MWh) falling as renewables rise.
# MAGIC - `gold_emissions_trend` — annual electric-power CO2 (national + per-state), YoY change.
# MAGIC - `gold_carbon_intensity` — national lbs CO2 / MWh per year, joined to renewable share.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "energy_transition_dev")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

bronze_emissions = f"{catalog}.{schema}.bronze_eia_emissions"
gold_trend = f"{catalog}.{schema}.gold_transition_trend"
gold_emissions = f"{catalog}.{schema}.gold_emissions_trend"
gold_intensity = f"{catalog}.{schema}.gold_carbon_intensity"

LB_PER_METRIC_TON = 2204.62
MILLION = 1_000_000.0

# COMMAND ----------

# Clean the emissions feed: annual electric-power CO2 in million metric tons.
emissions = (
    spark.table(bronze_emissions)
    .select(
        F.col("period").cast("int").alias("yr"),
        F.col("stateId").alias("state"),
        F.col("stateDescription").alias("state_name"),
        F.col("value").cast("double").alias("co2_mmt"),  # million metric tons
    )
    .filter(F.col("co2_mmt").isNotNull())
    .dropDuplicates(["yr", "state"])
)

# YoY change per state.
w = Window.partitionBy("state").orderBy("yr")
emissions_trend = (
    emissions
    .withColumn("co2_mmt_prev", F.lag("co2_mmt").over(w))
    .withColumn("co2_yoy_pct", F.try_divide(F.col("co2_mmt") - F.col("co2_mmt_prev"), F.col("co2_mmt_prev")) * 100)
)
(
    emissions_trend.write.format("delta")
    .mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(gold_emissions)
)
print(f"Wrote {emissions_trend.count()} rows to {gold_emissions}")

# COMMAND ----------

# National annual generation total (MWh) from the existing gold trend.
gen_annual = (
    spark.table(gold_trend)
    .groupBy(F.year("period_date").alias("yr"))
    .agg(
        F.sum("total_mwh").alias("total_mwh"),
        F.avg("renewable_share").alias("renewable_share"),
        F.avg("clean_share").alias("clean_share"),
    )
)

# Carbon intensity = national electric-power CO2 / annual generation, in lbs / MWh.
national_co2 = emissions.filter(F.col("state") == "US").select("yr", "co2_mmt")
intensity = (
    gen_annual.join(national_co2, "yr", "inner")
    .withColumn(
        "lbs_co2_per_mwh",
        F.try_divide(F.col("co2_mmt") * MILLION * LB_PER_METRIC_TON, F.col("total_mwh")),
    )
    .orderBy("yr")
)
(
    intensity.write.format("delta")
    .mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(gold_intensity)
)
print(f"Wrote {intensity.count()} rows to {gold_intensity}")
display(intensity.select("yr", "renewable_share", "lbs_co2_per_mwh"))
