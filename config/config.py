"""
Configuration for the analytics pipeline.
Central place to manage all settings and report definitions.
"""

from datetime import date
from enum import Enum

# Period type (already in your notebook)
class PeriodType(Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


# Database connection config
JDBC_URL = "jdbc:mysql://your-db-host:3306/database"
CONNECTION_PROPERTIES = {
    "driver": "com.mysql.jdbc.Driver",
    "user": "your_username",
    "password": "your_password"
}

# DateRangeCalculator defaults
DATE_CALCULATOR_CONFIG = {
    "look_back_months": 13,
    "monthly_duration": 1,
    "quarterly_duration": 3,
    "annual_duration": 12
}

# What periods do you want to report on?
REPORTING_PERIODS = [
    # Monthly reports: Nov 2025 through Apr 2026
    (PeriodType.MONTHLY, date(2025, 11, 1), date(2026, 4, 30)),
    
    # Quarterly reports: Nov 2025 through Apr 2026
    (PeriodType.QUARTERLY, date(2025, 11, 1), date(2026, 4, 30)),
    
    # Annual reports: Full year 2025
    (PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31)),
]

# Output path for saving reports
REPORT_OUTPUT_PATH = "/delta/stickers_analysis"
REPORT_OUTPUT_FORMAT = "delta"  # or "csv"