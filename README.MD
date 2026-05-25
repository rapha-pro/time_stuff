# Stickers Analytics Pipeline

## Background

This project replaces a monolithic Databricks notebook with 25+ embedded SQL queries. The original notebook had several problems: queries mixed with Python orchestration, implicit execution order, manual widget inputs for dates, duplicated SQL, no documentation of query dependencies, and no way to batch reports across multiple periods.

This rewrite keeps the SQL exactly as it was. The change is structural: queries live in their own file, dependencies are declared explicitly, dates are calculated programmatically, and one entry point runs everything.

## Hypothesis

The pipeline tests whether customers who are offered stickers on their lattes have a lower walk-off (write-off) rate than customers who are not offered stickers. The benefit is calculated as:

    benefit = (write_off_rate_control minus write_off_rate_treated) times total_os_amount_treated

This represents the write-off amount avoided among sticker recipients compared to what would have happened at the control group's rate.

## Design Principles

This pipeline is built for a team of two running monthly, quarterly, and annual reports. The design favors simplicity over abstraction. Specifically:

No classes are used where plain functions or module-level state work. The original draft had SparkQueryRunner and AnalyticsPipeline classes; both were removed because they wrapped one-line operations.

PeriodType is defined once in enums.py and imported everywhere. The original draft had it duplicated in three files.

Date calculations are one function, not a class with methods. The DateRange dataclass holds the result so callers cannot accidentally swap start and end.

Queries declare their dependencies in catalog.py. The pipeline computes execution order automatically by topological sort, so adding a new query in the middle of a chain does not require renumbering anything.

SQL strings live in queries/sql_queries.py with no Python logic mixed in. They are easy to copy into a SQL editor for debugging.

Validation runs once at startup. Errors in the catalog (missing references, circular dependencies, incompatible period ranges) fail loudly before any query runs.

## File Structure

    project/
        run.py                    Entry point. This is what gets scheduled.
        connections.py            Spark session, JDBC credentials, storage paths.
        reporting_config.py       Period definitions, date math, DateRange dataclass.
        enums.py                  PeriodType and ParamType.
        catalog.py                Query registry and dependency resolution.
        queries/
            sql_queries.py        Raw SQL strings only.
        README.md                 This file.

Total framework code is around 250 lines.

## What Each File Does

**run.py** is the only file you execute. It validates the catalog, loops over the periods configured in reporting_config.py, resolves the dependency order from the catalog, and runs every query for each period. Output is saved to the path defined in connections.py.

**connections.py** holds all environment-specific values: the Spark session, JDBC URL, credentials pulled from Databricks secrets, storage paths, and notification email. This is the file you edit when moving between environments.

**reporting_config.py** holds three things: the global settings (WRITE_OFF_WINDOW and the duration constants), the list of reporting periods to run, and the date math that produces the look-back window for each period. It also validates that the configured period range is compatible with the period type.

**enums.py** defines PeriodType (MONTHLY, QUARTERLY, ANNUAL) and ParamType (START_DATE, END_DATE, WRITE_OFF_WINDOW). Both are imported wherever needed.

**catalog.py** is the registry of all queries. Each entry declares its SQL source, parameter requirements, dependencies, and description. The module also provides validate_catalog and get_execution_phases for safety checks and ordering.

**queries/sql_queries.py** is a list of SQL string constants. No Python logic. SQL uses placeholders like {start_date}, {end_date}, and {write_off_window} which run.py substitutes at execution time.

## Period Range Validation

The pipeline validates that the configured date range is compatible with the requested period type before running anything. Examples:

If an annual report is requested with only an 8 month range, the pipeline fails with a clear error: annual reports need 12 months minimum.

If a quarterly report is requested with only a 2 month range, the pipeline fails: quarterly reports need 3 months minimum.

If a quarterly report is given a 5 month range, only the first 3 months are used per quarter and the loop steps forward by 3 months. Extra months are not silently dropped without notice.

Annual reports must start on the fiscal year start month (configured as November). A range starting on any other month for an annual report fails validation.

This validation happens at the top of run.py main, before any SQL executes.

## Adding a New Query

Three steps in two files.

1. Add the SQL string to queries/sql_queries.py:

       QUERY_MY_NEW_THING = """
           CREATE OR REPLACE TEMP VIEW my_new_thing AS
           SELECT ...
       """

2. Import it in catalog.py and add an entry:

       from queries.sql_queries import QUERY_MY_NEW_THING

       QUERIES_CATALOG = {
           ...
           "my_new_thing": {
               "sql":          QUERY_MY_NEW_THING,
               "params":       [ParamType.START_DATE, ParamType.END_DATE],
               "dependencies": ["customer_transactions"],
               "description":  "What this query produces",
           },
       }

3. Run the pipeline. validate_catalog catches missing imports, missing dependencies, and circular references before any SQL runs.

## Running Monthly Reports

Edit REPORTING_PERIODS in reporting_config.py:

    REPORTING_PERIODS = [
        (PeriodType.MONTHLY, date(2025, 11, 1), date(2026, 4, 30)),
    ]

Then run:

    python run.py

The pipeline iterates from November 2025 to April 2026, one month at a time, runs all queries for each month, and saves the output to OUTPUT_PATH from connections.py.

## Scheduling

This pipeline is designed to run on Databricks Workflows.

1. In Databricks, open Workflows from the left sidebar.
2. Create a Job. Point it at the notebook or Python file that calls main from run.py.
3. Set the schedule. For monthly reports, the first day of each month at 6am is typical.
4. Add the notification email under the alerts section so failures get reported.

To avoid editing reporting_config.py every month, the helper last_complete_month in reporting_config.py returns the first day of the most recently completed month. Use it like this in REPORTING_PERIODS for a scheduled monthly job:

    REPORTING_PERIODS = [
        (PeriodType.MONTHLY, last_complete_month(), last_complete_month()),
    ]

The scheduled job will then always report on the month that just ended.

For quarterly reports, schedule for the first day of February, May, August, and November. For annual reports, schedule for the first day of November (fiscal year start).

## What Was Considered and Not Used

**dbt** was considered. It solves dependency resolution, documentation, and testing natively. It is well suited to teams maintaining hundreds of models. For a focused 25 query pipeline with two maintainers, the setup and learning cost was judged higher than the benefit. The catalog pattern in this project covers the same ground at a small fraction of the framework size.

**Airflow** was considered for scheduling. Databricks Workflows provides the same scheduling, monitoring, and alerting with no extra setup, so Airflow was not adopted.

**SparkQueryRunner and AnalyticsPipeline classes** were drafted and removed. Both wrapped operations that are one line of code in run.py. They added indirection without adding capability.

**Numbered SQL files (01_, 02_, 03_)** were considered as a simpler alternative to the catalog. Rejected because the topological sort over declared dependencies is safer than maintaining the order manually across 25 interdependent queries.

## Maintenance

Files touched monthly: reporting_config.py only, to update REPORTING_PERIODS if not using last_complete_month.

Files touched when adding queries: queries/sql_queries.py and catalog.py.

Files touched when moving environments: connections.py only.

Everything else stays put.