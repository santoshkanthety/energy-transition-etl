# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Setup
# MAGIC One-time setup: create the catalog/schema and verify the EIA secret is reachable.
# MAGIC Run this once interactively before deploying the job. Not part of the job DAG.

# COMMAND ----------

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "energy_transition_dev")
dbutils.widgets.text("secret_scope", "energy_transition")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
secret_scope = dbutils.widgets.get("secret_scope")

# COMMAND ----------

spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
print(f"Ready: {catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Secret check
# MAGIC The EIA API key lives in the `energy_transition` secret scope under key `eia_api_key`.
# MAGIC Create it from the CLI (key is never stored in the repo):
# MAGIC ```bash
# MAGIC databricks secrets create-scope energy_transition
# MAGIC databricks secrets put-secret energy_transition eia_api_key
# MAGIC ```

# COMMAND ----------

try:
    key = dbutils.secrets.get(scope=secret_scope, key="eia_api_key")
    print(f"EIA key found in scope '{secret_scope}' (length {len(key)}).")
except Exception as e:
    print(f"Secret not reachable: {e}")
    print("Create it with the CLI commands above before running the job.")
