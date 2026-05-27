# All JDBC setup lives here.
# Edit credentials and storage paths in this file only.

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# JDBC credentials pulled
jdbc_username = dbutils.secrets.get(scope="your-scope", key="jdbc-username")
jdbc_password = dbutils.secrets.get(scope="your-scope", key="jdbc-password")

JDBC_URL = "jdbc:sqlserver://your-host:1433;databaseName=your_db"

CONNECTION_PROPERTIES = {
    "driver":    "com.sqlserver.jdbc.SQLServerDriver",
    "user":      jdbc_username,
    "password":  jdbc_password,
    "fetchsize": "1000",
}


OUTPUT_PATHS = {
    "monthly":   "/delta/stickers_analysis/monthly",
    "quarterly": "/delta/stickers_analysis/quarterly",
    "annual":    "/delta/stickers_analysis/annual",
}

# Storage and misc
STORAGE_NAME = "your-storage"
TEMP_DIR     = "/tmp/stickers_analysis"
EMAIL        = "you@company.com"
OUTPUT_PATH  = "/delta/stickers_analysis"