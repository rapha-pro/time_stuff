# Single entry point. Run this to generate all reports.

from datetime import date
from dateutil.relativedelta import relativedelta

from connections        import spark, OUTPUT_PATH, jdbc
from enums              import PeriodType, ParamType, QueryType
from reporting_config   import (
    REPORTING_PERIODS,
    WRITE_OFF_WINDOW,
    MONTHLY_DURATION,
    QUARTERLY_DURATION,
    ANNUAL_DURATION,
    FISCAL_YEAR_START_MONTH,
    get_look_back_dates,
    validate_period_range,
    months_between,
    DateRange,
)
from catalog            import (
    QUERIES_CATALOG,
    get_execution_phases,
    validate_catalog,
    print_execution_plan,
)


def build_params(query_name: str, dates: DateRange) -> dict:
    """Map catalog ParamType declarations to actual values for this run."""
    needed = QUERIES_CATALOG[query_name]["params"]
    values = {
        ParamType.START_DATE:       dates.start,
        ParamType.END_DATE:         dates.end,
        ParamType.WRITE_OFF_WINDOW: WRITE_OFF_WINDOW,
    }
    return {p.value: values[p] for p in needed}


def run_jdbc_query(query_name: str, sql: str) -> None:
    """Load data from external database into a temp view."""
    df = (
        spark.read
        .jdbc(url=JDBC_URL, table=sql, properties=CONNECTION_PROPERTIES)
        .cache()
    )
    df.createOrReplaceTempView(query_name)


def run_spark_sql(sql: str) -> None:
    """Run SQL against existing temp views."""
    spark.sql(sql)


def run_query(query_name: str, query_config: dict, params: dict) -> None:
    """Dispatch to the right execution method based on query type."""
    sql = query_config["sql"].format(**params)

    if query_config["type"] == QueryType.JDBC:
        run_jdbc_query(query_name, sql)
    elif query_config["type"] == QueryType.SPARK_SQL:
        run_spark_sql(sql)
    else:
        raise ValueError(f"Unknown query type: {query_config['type']}")


def run_all_queries(dates: DateRange) -> None:
    """Run every query in the catalog in dependency order."""
    phases = get_execution_phases()

    for phase_num in sorted(phases.keys()):
        print(f"  Phase {phase_num}:")
        for query_name in phases[phase_num]:
            config = QUERIES_CATALOG[query_name]
            params = build_params(query_name, dates)
            print(f"    running {query_name} ({config['type'].value})")
            run_query(query_name, config, params)


def iter_period_starts(period_type: PeriodType, range_start: date, range_end: date):
    """Yield the first day of each period that fits entirely within the range."""
    duration_months = {
        PeriodType.MONTHLY:   MONTHLY_DURATION,
        PeriodType.QUARTERLY: QUARTERLY_DURATION,
        PeriodType.ANNUAL:    ANNUAL_DURATION,
    }[period_type]

    # Annual: start at the first fiscal year boundary on or after range_start
    if period_type == PeriodType.ANNUAL:
        if range_start.month <= FISCAL_YEAR_START_MONTH:
            current = date(range_start.year, FISCAL_YEAR_START_MONTH, 1)
        else:
            current = date(range_start.year + 1, FISCAL_YEAR_START_MONTH, 1)
    else:
        current = range_start.replace(day=1)

    # Yield only if the full period fits inside the range
    while True:
        period_end = current + relativedelta(months=duration_months) - relativedelta(days=1)
        if period_end > range_end:
            break
        yield current
        current += relativedelta(months=duration_months)

    # Warn if there are leftover months that did not fit a full period
    if current <= range_end:
        skipped = months_between(current, range_end)
        print(
            f"  Note: {skipped} month(s) at end of range skipped "
            f"(not enough for a full {period_type.value} period)"
        )


def save_results(period_type: PeriodType, period_start: date) -> None:
    """Save the final output table for this period."""
    out = f"{OUTPUT_PATH}/{period_type.value}/{period_start}"
    print(f"    saving to {out}")
    spark.table("customer_segments").write.format("delta").mode("overwrite").save(out)


def main() -> None:
    if not validate_catalog():
        raise RuntimeError("Fix catalog errors before running.")

    print_execution_plan()

    for period_type, range_start, range_end in REPORTING_PERIODS:
        validate_period_range(period_type, range_start, range_end)
        print(f"\n{period_type.value.upper()} reports from {range_start} to {range_end}")

        for period_start in iter_period_starts(period_type, range_start, range_end):
            dates = get_look_back_dates(period_start, period_type)
            print(f"\n  Period start: {period_start}   look back: {dates.start} to {dates.end}")
            run_all_queries(dates)
            save_results(period_type, period_start)

    print("\nAll reports complete.")


if __name__ == "__main__":
    main()