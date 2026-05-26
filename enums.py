from enum import Enum


class PeriodType(Enum):
    MONTHLY   = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL    = "annual"


class ParamType(Enum):
    START_DATE        = "start_date"
    END_DATE          = "end_date"
    WRITE_OFF_WINDOW  = "write_off_window"


class QueryType(Enum):
    JDBC      = "jdbc"       # subquery sent to external database
    SPARK_SQL = "spark_sql"  # operates on existing temp views