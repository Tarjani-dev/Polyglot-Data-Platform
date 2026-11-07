# Databricks notebook source
# DBTITLE 1,Cell 1
#The client_id and tenant_id values in the Databricks notebooks are hardcoded — a learning-project shortcut. In production, these would be pulled from `dbutils.widgets`, environment variables, or a secret scope, the same way the client secret already is via `dbutils.secrets.get`. Left as-is here since the environment is retired.

# --- STEP 1: Azure AD service principal credentials ---
# NOTE: client_id and tenant_id below are hardcoded as a learning-project shortcut.
# In production these would come from dbutils.widgets, environment variables, or a
# secret scope, the same way the client secret already is via dbutils.secrets.get.
# Left as-is here since the environment is retired.

client_id = "d03acda5-f58c-449b-8153-8bda233754ff" #PASTE_YOUR_CLIENT_ID_HERE
tenant_id = "493896fc-33b0-40aa-9232-31d29aa9e404" #PASTE_YOUR_TENANT_ID_HERE
storage_account_name = "stprojectvdevsi" #PASTE_YOUR_STORAGE_ACCOUNT_NAME_HERE # (e.g., stprojectvdevsi)


# --- STEP 2: Configure Spark to authenticate to ADLS Gen2 via OAuth ---
configs = {
  "fs.azure.account.auth.type": "OAuth",
  "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
  "fs.azure.account.oauth2.client.id": client_id,
  "fs.azure.account.oauth2.client.secret": dbutils.secrets.get(scope="polyglot-scope", key="databricks-client-secret"),
  "fs.azure.account.oauth2.client.endpoint": f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
}

storage_account_fqdn = f"{storage_account_name}.dfs.core.windows.net"
for key, value in configs.items():
    spark.conf.set(f"{key}.{storage_account_fqdn}", value)


# --- STEP 3: Verify connectivity by listing files in the 'raw' container ---
try:
    raw_path = f"abfss://raw@{storage_account_fqdn}/"
    files = dbutils.fs.ls(raw_path)
    print("SUCCESS: Direct access to the 'raw' container is working.")
    for file_info in files[:5]:
        print(file_info.path)
except Exception as e:
    print("FAILED: Direct access did not work. Check your error below:")
    print(e)