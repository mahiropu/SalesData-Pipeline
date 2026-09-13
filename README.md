# Sales Data Pipeline

A batch data pipeline that ingests daily sales CSV files, validates them, quarantines
bad rows, and loads the clean data into a DuckDB warehouse with a partitioned Parquet
export on top.

Built as a portfolio project for a Data Engineering internship.

## What it does

Every day a new `orders_YYYY-MM-DD.csv` file lands in `data/incoming/`. The pipeline:

1. Finds files that have not been processed yet
2. Checks the file has all required columns
3. Validates every row and splits it into good rows and bad rows
4. Writes bad rows to `data/quarantine/` with a `reject_reason` column
5. Transforms good rows (revenue, year, month, country cleanup, dedupe)
6. Loads them into DuckDB, replacing any order that already exists
7. Moves the file to `data/archive/`
8. Exports the whole fact table to Parquet, partitioned by year and month

## Flow

```
data/incoming/*.csv
        |
        v
   column check ------> skipped if columns are missing
        |
        v
  row validation ------> data/quarantine/*.csv  (bad rows + reason)
        |
        v
    transform          (revenue, year/month, dedupe, source_file, loaded_at)
        |
        v
   sales.duckdb        (fact_orders + processed_files)
        |
        v
  data/warehouse/order_year=2026/order_month=9/data_0.parquet
```

## Skills it shows

- Incremental file ingestion with a `processed_files` watermark table, so re-running
  the pipeline never loads the same file twice
- Idempotent loads: existing `order_id`s are deleted before insert, so a corrected
  file can safely be replayed
- Data quality gate with a quarantine folder instead of silently dropping rows
- Dimensional-style fact table plus a partitioned Parquet layer (Hive-style paths)
- DuckDB as an analytical engine, SQL analytics kept in `sql/analytics_queries.sql`
- Logging to console and file, plus a per-file audit log in the database
- 13 pytest unit tests on the validation and transform rules

## Validation rules

A row is quarantined if any of these fail, and the reason is written next to it:

| Reason | Rule |
|---|---|
| `invalid_order_date` | `order_date` cannot be parsed as a date |
| `missing_order_id` | `order_id` is blank |
| `missing_sku` | `sku` is blank |
| `invalid_quantity` | `quantity` is missing, zero or negative |
| `invalid_unit_price` | `unit_price` is missing, zero or negative |

The sample data generator deliberately injects around 4% broken rows so the
quarantine path is visible when you run it.

## Warehouse tables

`fact_orders`

| Column | Type | Notes |
|---|---|---|
| `order_id` | VARCHAR | Primary key |
| `order_date` | DATE | |
| `order_year`, `order_month` | INTEGER | Used as Parquet partitions |
| `customer_id`, `country` | VARCHAR | |
| `sku`, `product_name`, `category` | VARCHAR | |
| `quantity` | INTEGER | Always greater than zero |
| `unit_price`, `revenue` | DECIMAL | `revenue = quantity * unit_price` |
| `source_file` | VARCHAR | Which CSV the row came from |
| `loaded_at` | TIMESTAMP | When the pipeline wrote it |

`processed_files` — one row per ingested file with rows read, loaded and rejected.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m src.generate_data    # create 14 days of sample CSV files
python -m src.pipeline         # ingest, validate, load, export parquet
python -m src.analytics        # print the SQL reports
python -m pytest -v            # run the tests
```

Makefile shortcuts: `make install`, `make seed`, `make run`, `make analytics`, `make test`, `make clean`.

## Example run

```
2026-09-13 15:57:08 | INFO    | pipeline  | Read 400 rows from orders_2026-09-12.csv
2026-09-13 15:57:08 | WARNING | pipeline  | Quarantined 18 bad rows from orders_2026-09-12.csv
2026-09-13 15:57:08 | INFO    | pipeline  | Loaded 382 rows from orders_2026-09-12.csv
2026-09-13 15:57:08 | INFO    | warehouse | Exported fact_orders to partitioned parquet in warehouse
2026-09-13 15:57:08 | INFO    | pipeline  | === Pipeline finished: 5380 loaded, 220 rejected ===
```

Running it again with no new files:

```
2026-09-13 15:57:17 | INFO | pipeline | No new files to process
```

Analytics output:

```
=== Query 1 ===
   category  orders  units_sold  total_revenue
Electronics    1787      5402.0      3912448.0
  Furniture    1766      5272.0      1304420.0
    Kitchen    1827      5557.0       154872.5
```

## Analytics queries

`sql/analytics_queries.sql` contains five reports: revenue by category, revenue and
average order value by country, daily revenue trend, top 5 products by units sold,
and top 10 customers by lifetime value.

## Project layout

```
sales-data-pipeline/
├── config.yaml
├── requirements.txt
├── Makefile
├── src/
│   ├── generate_data.py    creates sample CSV files
│   ├── quality.py          column and row validation
│   ├── transform.py        revenue, date parts, dedupe
│   ├── warehouse.py        duckdb schema, loads, parquet export
│   ├── pipeline.py         orchestrates the run
│   ├── analytics.py        runs the SQL reports
│   └── utils.py            config and logging
├── sql/analytics_queries.sql
├── tests/
│   ├── test_quality.py
│   └── test_transform.py
└── data/
    ├── incoming/           new files land here
    ├── archive/            processed files moved here
    ├── quarantine/         rejected rows
    └── warehouse/          partitioned parquet
```

## Tech stack

Python 3 · DuckDB · pandas · PyArrow · PyYAML · pytest
