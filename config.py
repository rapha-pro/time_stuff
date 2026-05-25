# All date math and period settings.

from dataclasses import dataclass
from datetime import date
from dateutil.relativedelta import relativedelta

from enums import PeriodType


# Settings
WRITE_OFF_WINDOW   = 13
MONTHLY_DURATION   = 1
QUARTERLY_DURATION = 3
ANNUAL_DURATION    = 12

FISCAL_YEAR_START_MONTH = 11


# What to report on
REPORTING_PERIODS = [
    (PeriodType.MONTHLY,    date(2025, 11, 1), date(2026,  4, 30)),
    (PeriodType.QUARTERLY,  date(2025, 11, 1), date(2026,  4, 30)),
    (PeriodType.ANNUAL,     date(2024, 11, 1), date(2025, 10, 31)),
]


@dataclass
class DateRange:
    start: date
    end:   date


def last_complete_month() -> date:
    """First day of the most recently completed month. Use this for scheduled runs."""
    return (date.today().replace(day=1) - relativedelta(months=1))


def first_of_current_month() -> date:
    """First day of the current month."""
    return date.today().replace(day=1)


def months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


def _contains_fiscal_year(range_start: date, range_end: date) -> bool:
    if range_start.month <= FISCAL_YEAR_START_MONTH:
        first_fy_start = date(range_start.year, FISCAL_YEAR_START_MONTH, 1)
    else:
        first_fy_start = date(range_start.year + 1, FISCAL_YEAR_START_MONTH, 1)

    fy_end = first_fy_start + relativedelta(months=ANNUAL_DURATION) - relativedelta(days=1)
    return first_fy_start >= range_start and fy_end <= range_end


def validate_period_not_in_future(period_type: PeriodType, range_start: date, range_end: date) -> None:
    """A period is valid only if it has fully ended (period_end < first of current month)."""
    latest_valid_end = first_of_current_month() - relativedelta(days=1)

    if range_end > latest_valid_end:
        raise ValueError(
            f"Range end {range_end} is in the current month or future. "
            f"Reports can only run on completed periods. "
            f"Latest valid range end is {latest_valid_end} (end of last completed month)."
        )


def validate_period_range(period_type: PeriodType, range_start: date, range_end: date) -> None:
    """Run all validations on a configured period range."""
    validate_period_not_in_future(period_type, range_start, range_end)

    months = months_between(range_start, range_end)
    required = {
        PeriodType.MONTHLY:   MONTHLY_DURATION,
        PeriodType.QUARTERLY: QUARTERLY_DURATION,
        PeriodType.ANNUAL:    ANNUAL_DURATION,
    }[period_type]

    if months < required:
        raise ValueError(
            f"{period_type.value} reports need at least {required} months of range, "
            f"but {range_start} to {range_end} is only {months} months. "
            f"Either extend the range or switch to a shorter period type."
        )

    if period_type == PeriodType.ANNUAL:
        if not _contains_fiscal_year(range_start, range_end):
            raise ValueError(
                f"Annual report range {range_start} to {range_end} does not contain "
                f"a complete fiscal year (November through October)."
            )


def get_look_back_dates(period_start: date, period_type: PeriodType) -> DateRange:
    duration_months = {
        PeriodType.MONTHLY:   MONTHLY_DURATION,
        PeriodType.QUARTERLY: QUARTERLY_DURATION,
        PeriodType.ANNUAL:    ANNUAL_DURATION,
    }[period_type]

    start = (period_start - relativedelta(months=WRITE_OFF_WINDOW)).replace(day=1)
    end   = start + relativedelta(months=duration_months) - relativedelta(days=1)

    return DateRange(start=start, end=end)