import pandas as pd

from src.utils import utc_now

FINAL_COLUMNS = [
    "order_id",
    "order_date",
    "order_year",
    "order_month",
    "customer_id",
    "country",
    "sku",
    "product_name",
    "category",
    "quantity",
    "unit_price",
    "revenue",
    "source_file",
    "loaded_at",
]


def transform(df, source_file):
    df = df.copy()

    df["order_date"] = df["order_date_parsed"].dt.strftime("%Y-%m-%d")
    df["order_year"] = df["order_date_parsed"].dt.year
    df["order_month"] = df["order_date_parsed"].dt.month
    df["quantity"] = df["quantity"].astype(int)
    df["unit_price"] = df["unit_price"].round(2)
    df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)
    df["country"] = df["country"].str.upper().str.strip()
    df["source_file"] = source_file
    df["loaded_at"] = utc_now()

    df = df.drop_duplicates(subset=["order_id"], keep="last")

    return df[FINAL_COLUMNS].reset_index(drop=True)
