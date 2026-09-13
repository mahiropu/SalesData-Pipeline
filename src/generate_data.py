import random
from datetime import date, timedelta

import pandas as pd

from src.utils import get_logger, load_config, resolve

logger = get_logger("generate")


def build_day(order_date, order_start, config):
    products = config["products"]
    countries = config["countries"]
    bad_rate = config["generator"]["bad_row_rate"]
    rows = []

    for i in range(config["generator"]["orders_per_day"]):
        product = random.choice(products)
        quantity = random.randint(1, 5)
        unit_price = product["unit_price"]

        row = {
            "order_id": f"ORD-{order_start + i:07d}",
            "order_date": order_date.isoformat(),
            "customer_id": f"CUST-{random.randint(1, 500):04d}",
            "country": random.choice(countries),
            "sku": product["sku"],
            "product_name": product["name"],
            "category": product["category"],
            "quantity": quantity,
            "unit_price": unit_price,
        }

        if random.random() < bad_rate:
            row = break_row(row)

        rows.append(row)

    return rows


def break_row(row):
    problem = random.choice(["no_quantity", "negative_price", "bad_date", "no_sku", "zero_quantity"])

    if problem == "no_quantity":
        row["quantity"] = None
    elif problem == "negative_price":
        row["unit_price"] = -row["unit_price"]
    elif problem == "bad_date":
        row["order_date"] = "not-a-date"
    elif problem == "no_sku":
        row["sku"] = ""
    elif problem == "zero_quantity":
        row["quantity"] = 0

    return row


def generate():
    config = load_config()
    random.seed(config["generator"]["seed"])

    incoming = resolve(config["paths"]["incoming_dir"])
    incoming.mkdir(parents=True, exist_ok=True)

    days = config["generator"]["days"]
    start_date = date.today() - timedelta(days=days)
    order_start = 1

    for offset in range(days):
        order_date = start_date + timedelta(days=offset)
        rows = build_day(order_date, order_start, config)
        order_start += len(rows)

        path = incoming / f"orders_{order_date.isoformat()}.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        logger.info("Wrote %s rows to %s", len(rows), path.name)

    logger.info("Generated %s daily files", days)


if __name__ == "__main__":
    generate()
