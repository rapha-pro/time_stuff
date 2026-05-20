from enum import Enum
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Tuple


class PeriodType(Enum):
    """
    Purpose:
        Enumeration of valid reporting period types to prevent typos,
        ensure type safety, and make code more maintainable.
    
    Attributes:
        - MONTHLY: Monthly reporting periods (1 month effect window)
        - QUARTERLY: Quarterly reporting periods (3 month effect window)
        - ANNUAL: Annual/Fiscal year reporting periods (12 month effect window)
    """
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class DateRangeCalculator:
    """
    Purpose:
        Calculate date ranges for reporting periods and their corresponding
        look-back periods. Encapsulates all date logic in one place for easy
        understanding, testing, and modification. All period types use a
        configurable look-back duration from the period start, then return
        the effect window (duration of the effect measurement period).
    
    Attributes:
        - look_back_months: int, months to look back from period start (default 13)
        - monthly_duration: int, duration of monthly reporting period in months (default 1)
        - quarterly_duration: int, duration of quarterly reporting period in months (default 3)
        - annual_duration: int, duration of annual reporting period in months (default 12)
    """
    
    def __init__(
        self,
        look_back_months: int = 13,
        monthly_duration: int = 1,
        quarterly_duration: int = 3,
        annual_duration: int = 12
    ):
        """
        Purpose:
            Initialize the DateRangeCalculator with configurable durations.
            These settings control how far back to look and how long each
            period type lasts.
        
        Args:
            - look_back_months: int, number of months to look back from period start
                               to find the effect measurement window (default 13)
            - monthly_duration: int, length of a monthly period in months (default 1)
            - quarterly_duration: int, length of a quarterly period in months (default 3)
            - annual_duration: int, length of an annual period in months (default 12)
        
        Return:
            None
        
        Example:
            calculator = DateRangeCalculator(
                look_back_months=13,
                monthly_duration=1,
                quarterly_duration=3,
                annual_duration=12
            )
        """
        self.look_back_months = look_back_months
        self.monthly_duration = monthly_duration
        self.quarterly_duration = quarterly_duration
        self.annual_duration = annual_duration
    
    def get_monthly_dates(self, period_start: date) -> Tuple[date, date]:
        """
        Purpose:
            Calculate the look-back date range for a monthly reporting period.
            Looks back 13 months from period start, then returns the exact
            1-month window where effect is measured (the month before period start).
        
        Args:
            - period_start: datetime.date marking the first day of the month to report on
        
        Return:
            Tuple of (look_back_start, look_back_end) representing the 1-month
            window of data to analyze (effect window)
        
        Example:
            Input: period_start = date(2026, 1, 1) (January 2026 report)
            Output: (date(2024, 12, 1), date(2024, 12, 31))
            Explanation: Look back 13 months from Jan 2026 = Dec 2024.
                        Return December 2024 (1-month duration) as effect window.
                        Customers who saw stickers in Dec 2024 return in Jan 2026.
        """
        # Look back 13 months from period start
        look_back_start = period_start - relativedelta(months=self.look_back_months)
        look_back_start = look_back_start.replace(day=1)
        
        # Return the effect window (duration = monthly_duration = 1 month)
        look_back_end = look_back_start + relativedelta(months=self.monthly_duration) - relativedelta(days=1)
        
        return look_back_start, look_back_end
    
    def get_quarterly_dates(self, period_start: date) -> Tuple[date, date]:
        """
        Purpose:
            Calculate the look-back date range for a quarterly reporting period.
            Looks back 13 months from period start, then returns the 3-month
            window where effect is measured (the quarter before period start).
        
        Args:
            - period_start: datetime.date marking the first day of the quarter (1st of month)
        
        Return:
            Tuple of (look_back_start, look_back_end) representing the 3-month
            window of data to analyze (effect window)
        
        Example:
            Input: period_start = date(2026, 5, 1) (Q3 May-July 2026)
            Output: (date(2025, 4, 1), date(2025, 6, 30))
            Explanation: Look back 13 months from May 2026 = April 2025.
                        Return April 1 - June 30, 2025 (3-month duration) as effect window.
                        Customers who saw stickers in Q2 2025 (Apr-Jun) return in Q3 2026 (May-Jul).
        """
        # Look back 13 months from period start
        look_back_start = period_start - relativedelta(months=self.look_back_months)
        look_back_start = look_back_start.replace(day=1)
        
        # Return the effect window (duration = quarterly_duration = 3 months)
        look_back_end = look_back_start + relativedelta(months=self.quarterly_duration) - relativedelta(days=1)
        
        return look_back_start, look_back_end
    
    def get_annual_dates(self, period_start: date) -> Tuple[date, date]:
        """
        Purpose:
            Calculate the look-back date range for an annual/fiscal year reporting period.
            Looks back 13 months from fiscal year start, then returns the 12-month
            window where effect is measured (the full year before fiscal year begins).
        
        Args:
            - period_start: datetime.date marking the first day of the fiscal year
        
        Return:
            Tuple of (look_back_start, look_back_end) representing the 12-month
            window of data to analyze (effect window - full baseline year)
        
        Example:
            Input: period_start = date(2024, 11, 1) (FY Nov 2024 - Oct 2025)
            Output: (date(2023, 10, 1), date(2024, 9, 30))
            Explanation: Look back 13 months from Nov 2024 = Oct 2023.
                        Return Oct 2023 - Sep 2024 (12-month duration) as effect window.
                        Customers' behavior throughout the year before FY 2024-2025.
        """
        # Look back 13 months from period start
        look_back_start = period_start - relativedelta(months=self.look_back_months)
        look_back_start = look_back_start.replace(day=1)
        
        # Return the effect window (duration = annual_duration = 12 months)
        look_back_end = look_back_start + relativedelta(months=self.annual_duration) - relativedelta(days=1)
        
        return look_back_start, look_back_end
    
    def get_look_back_dates(
        self,
        period_start: date,
        period_type: PeriodType
    ) -> Tuple[date, date]:
        """
        Purpose:
            Main entry point to get look-back dates for any period type.
            Routes to the appropriate method based on period_type.
            Provides a consistent interface for callers.
        
        Args:
            - period_start: datetime.date marking the first day of the reporting period
            - period_type: PeriodType enum indicating MONTHLY, QUARTERLY, or ANNUAL
        
        Return:
            Tuple of (look_back_start, look_back_end) representing the data collection
            window (effect window) for measuring the reporting period's performance.
        
        Raises:
            ValueError: if period_type is not a valid PeriodType enum value
        
        Example:
            calculator = DateRangeCalculator()
            
            # Monthly
            start, end = calculator.get_look_back_dates(date(2026, 1, 1), PeriodType.MONTHLY)
            # Returns: (date(2024, 12, 1), date(2024, 12, 31))
            
            # Quarterly
            start, end = calculator.get_look_back_dates(date(2026, 5, 1), PeriodType.QUARTERLY)
            # Returns: (date(2025, 4, 1), date(2025, 6, 30))
            
            # Annual
            start, end = calculator.get_look_back_dates(date(2024, 11, 1), PeriodType.ANNUAL)
            # Returns: (date(2023, 10, 1), date(2024, 9, 30))
        """
        if period_type == PeriodType.MONTHLY:
            return self.get_monthly_dates(period_start)
        
        elif period_type == PeriodType.QUARTERLY:
            return self.get_quarterly_dates(period_start)
        
        elif period_type == PeriodType.ANNUAL:
            return self.get_annual_dates(period_start)
        
        else:
            raise ValueError(f"Unknown period type: {period_type}")


# ===== USAGE EXAMPLE =====
"""
calculator = DateRangeCalculator(
    look_back_months=13,
    monthly_duration=1,
    quarterly_duration=3,
    annual_duration=12
)

# Monthly: January 2026 report
start, end = calculator.get_look_back_dates(date(2026, 1, 1), PeriodType.MONTHLY)
print(f"Monthly: {start} to {end}")
# Output: Monthly: 2024-12-01 to 2024-12-31

# Quarterly: Q3 2026 report (May-July)
start, end = calculator.get_look_back_dates(date(2026, 5, 1), PeriodType.QUARTERLY)
print(f"Quarterly: {start} to {end}")
# Output: Quarterly: 2025-04-01 to 2025-06-30

# Annual: FY 2024-2025 (Nov 2024 - Oct 2025)
start, end = calculator.get_look_back_dates(date(2024, 11, 1), PeriodType.ANNUAL)
print(f"Annual: {start} to {end}")
# Output: Annual: 2023-10-01 to 2024-09-30
"""