from enum import Enum


class PeriodType(Enum):
    MONTHLY   = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL    = "annual"


class ParamType(Enum):
    START_DATE        = "start_date"
    END_DATE          = "end_date"
    WRITE_OFF_WINDOW  = "write_off_window"