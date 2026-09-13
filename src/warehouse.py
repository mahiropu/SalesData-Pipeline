import duckdb

from src.utils import get_logger, resolve

logger = get_logger("warehouse")

SCHEMA = """
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id VARCHAR PRIMARY KEY,
    order_date DATE NOT NULL,
    order_year INTEGER NOT NULL,
    order_month INTEGER NOT NULL,
    customer_id VARCHAR NOT NULL,
    country VARCHAR NOT NULL,
    sku VARCHAR NOT NULL,
    product_name VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    revenue DECIMAL(12, 2) NOT NULL,
    source_file VARCHAR NOT NULL,
    loaded_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS processed_files (
    file_name VARCHAR PRIMARY KEY,
    processed_at TIMESTAMP NOT NULL,
    rows_read INTEGER NOT NULL,
    rows_loaded INTEGER NOT NULL,
    rows_rejected INTEGER NOT NULL
);
"""


def connect(config):
    return duckdb.connect(str(resolve(config["paths"]["database"])))


def init_schema(connection):
    connection.execute(SCHEMA)
    logger.info("Schema ready")


def already_processed(connection):
    rows = connection.execute("SELECT file_name FROM processed_files").fetchall()
    return {row[0] for row in rows}


def load_orders(connection, df):
    connection.register("staging", df)

    connection.execute("DELETE FROM fact_orders WHERE order_id IN (SELECT order_id FROM staging)")
    connection.execute("INSERT INTO fact_orders SELECT * FROM staging")
    connection.unregister("staging")

    return len(df)


def mark_processed(connection, file_name, rows_read, rows_loaded, rows_rejected):
    connection.execute("DELETE FROM processed_files WHERE file_name = ?", [file_name])
    connection.execute(
        "INSERT INTO processed_files VALUES (?, now(), ?, ?, ?)",
        [file_name, rows_read, rows_loaded, rows_rejected],
    )


def export_parquet(connection, config):
    target = resolve(config["paths"]["warehouse_dir"])
    target.mkdir(parents=True, exist_ok=True)

    connection.execute(
        f"""
        COPY (SELECT * FROM fact_orders)
        TO '{target}'
        (FORMAT PARQUET, PARTITION_BY (order_year, order_month), OVERWRITE_OR_IGNORE 1)
        """
    )
    logger.info("Exported fact_orders to partitioned parquet in %s", target.name)
