# In connections.py, alongside the existing config

DELTA_BASE_PATH = "/delta/stickers_analysis"   # base for all delta tables


# In a new utils.py file (or appended to run.py if you prefer fewer files)

from pyspark.sql import DataFrame
from connections import spark, DELTA_BASE_PATH


def write_delta_table(df: DataFrame, name: str) -> None:
    """Overwrite a delta table at DELTA_BASE_PATH/name with schema evolution allowed."""
    (df.write
        .option("mergeSchema", "true")
        .format("delta")
        .mode("overwrite")
        .save(f"{DELTA_BASE_PATH}/{name}"))


def load_delta_table(name: str) -> DataFrame:
    """Read a delta table from DELTA_BASE_PATH/name."""
    return spark.read.format("delta").load(f"{DELTA_BASE_PATH}/{name}")



def append_delta_table(df: DataFrame, name: str) -> None:
    """Append rows to a delta table at DELTA_BASE_PATH/name with schema evolution allowed."""
    (df.write
        .option("mergeSchema", "true")
        .format("delta")
        .mode("append")
        .save(f"{DELTA_BASE_PATH}/{name}"))