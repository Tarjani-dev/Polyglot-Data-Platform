# Databricks notebook source
# DBTITLE 1,Cell 1
# Cell 1: Call the Authentication Notebook

%run ./01_Mount_DataLake

storage_account = "stprojectvdevsi"
print("✅ Ready to process Medallion Layers!")

# COMMAND ----------

# DBTITLE 1,Shared setup
# COMMAND ----------
import re

from pyspark.sql.functions import col, current_timestamp, lit

storage_account_fqdn = f"{storage_account}.dfs.core.windows.net"

# NOTE: client_id and tenant_id below are hardcoded as a learning-project shortcut.
# In production these would come from dbutils.widgets, environment variables, or a
# secret scope, the same way the client secret already is via dbutils.secrets.get.
# Left as-is here since the environment is retired.

configs = {
    "fs.azure.account.auth.type": "OAuth",
    "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
    "fs.azure.account.oauth2.client.id": "d03acda5-f58c-449b-8153-8bda233754ff",
    "fs.azure.account.oauth2.client.secret": dbutils.secrets.get(scope="polyglot-scope", key="databricks-client-secret"),
    "fs.azure.account.oauth2.client.endpoint": "https://login.microsoftonline.com/493896fc-33b0-40aa-9232-31d29aa9e404/oauth2/token",
}
for key, value in configs.items():
    spark.conf.set(f"{key}.{storage_account_fqdn}", value)

raw_path = f"abfss://raw@{storage_account}.dfs.core.windows.net/source=local/"
bronze_path = f"abfss://bronze@{storage_account}.dfs.core.windows.net/delta/employees/"

# COMMAND ----------
# MAGIC %md
# MAGIC ## Bronze Layer: Raw CSV Ingestion (Employees)

# DBTITLE 1,Cell 2
# 2. Read all CSV files dynamically from the raw folder
df_raw = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv(f"{raw_path}*.csv")

df_raw = df_raw.toDF(*[re.sub(r"[ ,;{}()\n\t=]+", "_", c).strip("_") for c in df_raw.columns])

# 3. Add Lineage Metadata (The Audit Trail)
df_bronze = df_raw \
    .withColumn("_ingestion_time", current_timestamp()) \
    .withColumn("_source_file", col("_metadata.file_path")) \
    .withColumn("_status", lit("NEW"))

# 4. Write to Bronze as an Immutable Delta Table
df_bronze.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(bronze_path)

print("✅ Bronze Layer processed successfully!")
display(df_bronze)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Bronze Layer: Raw JSON Ingestion (API Responses)
# COMMAND ----------

# ==========================================
# PART 2: PROCESS THE JSON FILES
# ==========================================

# 1. Define separate path for JSON Bronze table
bronze_json_path = f"abfss://bronze@{storage_account}.dfs.core.windows.net/delta/api_responses/"

# 2. Read all JSON files dynamically
# Note: option("multiline", "true") is critical for JSON files formatted across multiple lines!
df_raw_json = spark.read \
    .option("multiline", "true") \
    .json(f"{raw_path}*.json")

# 3. Normalize column names (replace special characters/whitespace with underscores)
df_raw_json = df_raw_json.toDF(*[re.sub(r"[ ,;{}()\n\t=]+", "_", c).strip("_") for c in df_raw_json.columns])

# 4. Add Lineage Metadata
df_bronze_json = df_raw_json \
    .withColumn("_ingestion_time", current_timestamp()) \
    .withColumn("_source_file", col("_metadata.file_path")) \
    .withColumn("_status", lit("NEW"))

# 5. Write to Bronze as a separate Immutable Delta Table
df_bronze_json.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(bronze_json_path)

print("✅ JSON Bronze Layer processed successfully!")
display(df_bronze_json)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Silver Layer: Cleansing & Deduplication
# COMMAND ----------

#silver
from pyspark.sql.functions import col

# 1. Define Paths for both Data Streams
bronze_emp_path = f"abfss://bronze@{storage_account}.dfs.core.windows.net/delta/employees/"
bronze_json_path = f"abfss://bronze@{storage_account}.dfs.core.windows.net/delta/api_responses/"

silver_emp_path = f"abfss://silver@{storage_account}.dfs.core.windows.net/delta/employees/"
silver_json_path = f"abfss://silver@{storage_account}.dfs.core.windows.net/delta/api_responses/"

# ==========================================
# PART 1: CLEAN EMPLOYEES (CSV)
# ==========================================
df_bronze_emp = spark.read.format("delta").load(bronze_emp_path)

df_silver_emp = df_bronze_emp \
    .dropDuplicates() \
    .filter(col("_status") != "ERROR")

df_silver_emp.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(silver_emp_path)

print("✅ Employee Silver Layer cleaned and saved!")

# ==========================================
# PART 2: CLEAN API RESPONSES (JSON)
# ==========================================
df_bronze_json = spark.read.format("delta").load(bronze_json_path)

df_silver_json = df_bronze_json \
    .dropDuplicates() \
    .filter(col("_status") != "ERROR")

df_silver_json.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(silver_json_path)

print("✅ API Responses Silver Layer cleaned and saved!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer: Daily Platform Audit

# COMMAND ----------

# Cell 4: The Gold Layer (Business Aggregations)
from pyspark.sql.functions import count, to_date, lit

gold_audit_path = f"abfss://gold@{storage_account}.dfs.core.windows.net/delta/daily_platform_audit/"

# 1. Read from both Silver Tables
df_read_emp = spark.read.format("delta").load(silver_emp_path)
df_read_json = spark.read.format("delta").load(silver_json_path)

# 2. Aggregate Employee Data
df_gold_emp = df_read_emp \
    .withColumn("ingest_date", to_date(col("_ingestion_time"))) \
    .groupBy("ingest_date") \
    .agg(count("*").alias("records_processed")) \
    .withColumn("data_type", lit("Employees (CSV)"))

# 3. Aggregate API Response Data
df_gold_json = df_read_json \
    .withColumn("ingest_date", to_date(col("_ingestion_time"))) \
    .groupBy("ingest_date") \
    .agg(count("*").alias("records_processed")) \
    .withColumn("data_type", lit("API Responses (JSON)"))

# 4. Combine them into one unified Executive Table
df_gold_unified = df_gold_emp.unionByName(df_gold_json)

# 5. Write to Gold
df_gold_unified.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(gold_audit_path)

print("✅ Gold Layer aggregation generated successfully!")
display(df_gold_unified)

# COMMAND ----------

# Quick validation query reading directly from your Gold layer
gold_audit_path = f"abfss://gold@{storage_account}.dfs.core.windows.net/delta/daily_platform_audit/"
display(spark.read.format("delta").load(gold_audit_path))

