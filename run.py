# Single entry point. Run this to generate all reports.

from datetime import date
from dateutil.relativedelta import relativedelta
from pyspark.sql.utils import AnalysisException

from connections        import spark, OUTPUT_PATH, CONNECTIONS
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





dbutils.widgets.dropdown(
    name="period_type",
    defaultValue="monthly",
    choices=["monthly", "quarterly", "annual"],
    label="Period Type",
)



def get_period_type_from_job() -> PeriodType:
    period_type_str = dbutils.widgets.get("period_type")
    return PeriodType(period_type_str)



# Map each period type to its delta table name
DELTA_TABLE_NAMES = {
    PeriodType.MONTHLY:   "monthly_report",
    PeriodType.QUARTERLY: "quarterly_report",
    PeriodType.ANNUAL:    "annual_report",
}


def build_params(query_name: str, dates: DateRange) -> dict:
    """Map catalog ParamType declarations to actual values for this run."""
    needed = QUERIES_CATALOG[query_name]["params"]
    values = {
        ParamType.START_DATE:       dates.start,
        ParamType.END_DATE:         dates.end,
        ParamType.WRITE_OFF_WINDOW: WRITE_OFF_WINDOW,
    }
    return {p.value: values[p] for p in needed}


def run_jdbc_query(query_name: str, sql: str, connection_name: str) -> None:
    """Load data from external database into a temp view named query_name."""
    conn = CONNECTIONS[connection_name]
    df = (
        spark.read
        .jdbc(url=conn["url"], table=sql, properties=conn["properties"])
        .cache()
    )
    df.createOrReplaceTempView(query_name)


def run_spark_sql(sql: str) -> None:
    spark.sql(sql)


def run_query(query_name: str, query_config: dict, params: dict) -> None:
    sql = query_config["sql"].format(**params)

    if query_config["type"] == QueryType.JDBC:
        connection_name = query_config.get("connection", DEFAULT_CONNECTION)
        run_jdbc_query(query_name, sql, connection_name)
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



def save_results(
    period_type: PeriodType,
    period: DateRange,
    final_view: str = "customer_segments",
) -> None:
    table_name = DELTA_TABLE_NAMES[period_type]

    # Build the new rows
    result_df = (
        spark.table(final_view)
        .withColumn("period_start", lit(period.start))
        .withColumn("period_end",   lit(period.end))
    )

    # If the table exists, drop any prior rows for this exact period before appending
    try:
        existing = load_delta_table(table_name)
        kept = existing.filter(
            (existing.period_start != lit(period.start)) |
            (existing.period_end   != lit(period.end))
        )
        # Overwrite with the kept rows plus the new rows
        combined = kept.unionByName(result_df, allowMissingColumns=True)
        write_delta_table(combined, table_name)
    except AnalysisException:
        # Table doesn't exist yet — first run, just write
        write_delta_table(result_df, table_name)

    print(f"  Saved {result_df.count()} rows for {period.start} to {period.end} to {table_name}")


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