import shutil
import sys

import pandas as pd

from src import warehouse
from src.quality import REQUIRED_COLUMNS, check_columns, split_good_and_bad
from src.transform import transform
from src.utils import get_logger, load_config, resolve

logger = get_logger("pipeline")


def find_new_files(config, connection):
    incoming = resolve(config["paths"]["incoming_dir"])
    done = warehouse.already_processed(connection)

    new_files = []
    for path in sorted(incoming.glob("*.csv")):
        if path.name in done:
            logger.info("Skipping %s, already processed", path.name)
        else:
            new_files.append(path)

    return new_files


def quarantine(bad, config, file_name):
    if bad.empty:
        return

    target_dir = resolve(config["paths"]["quarantine_dir"])
    target_dir.mkdir(parents=True, exist_ok=True)
    bad.to_csv(target_dir / file_name, index=False)
    logger.warning("Quarantined %s bad rows from %s", len(bad), file_name)


def archive(path, config):
    target_dir = resolve(config["paths"]["archive_dir"])
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(target_dir / path.name))


def process_file(path, config, connection):
    df = pd.read_csv(path)
    logger.info("Read %s rows from %s", len(df), path.name)

    missing = check_columns(df)
    if missing:
        logger.error("Skipping %s, missing columns: %s", path.name, missing)
        return 0, 0

    good, bad = split_good_and_bad(df)
    quarantine(bad, config, path.name)

    rows_loaded = 0
    if not good.empty:
        clean = transform(good, path.name)
        rows_loaded = warehouse.load_orders(connection, clean)
        logger.info("Loaded %s rows from %s", rows_loaded, path.name)

    warehouse.mark_processed(connection, path.name, len(df), rows_loaded, len(bad))
    archive(path, config)

    return rows_loaded, len(bad)


def run():
    config = load_config()
    connection = warehouse.connect(config)
    warehouse.init_schema(connection)

    logger.info("=== Pipeline started ===")

    files = find_new_files(config, connection)
    if not files:
        logger.info("No new files to process")
        connection.close()
        return 0

    total_loaded = 0
    total_rejected = 0

    try:
        for path in files:
            loaded, rejected = process_file(path, config, connection)
            total_loaded += loaded
            total_rejected += rejected

        warehouse.export_parquet(connection, config)
        logger.info("=== Pipeline finished: %s loaded, %s rejected ===", total_loaded, total_rejected)
        return 0

    except Exception:
        logger.exception("Pipeline failed")
        return 1

    finally:
        connection.close()


if __name__ == "__main__":
    sys.exit(run())
