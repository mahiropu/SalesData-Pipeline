import pandas as pd

from src.quality import split_good_and_bad
from src.transform import FINAL_COLUMNS, transform


def make_clean_rows():
    df = pd.DataFrame([
        {
            "order_id": "ORD-0000001",
            "order_date": "2026-09-01",
            "customer_id": "CUST-0001",
            "country": "bd",
            "sku": "MUG-01",
            "product_name": "Coffee Mug",
            "category": "Kitchen",
            "quantity": 2,
            "unit_price": 12.5,
        },
        {
            "order_id": "ORD-0000002",
            "order_date": "2026-09-02",
            "customer_id": "CUST-0002",
            "country": "US",
            "sku": "MUG-01",
            "product_name": "Coffee Mug",
            "category": "Kitchen",
            "quantity": 3,
            "unit_price": 12.5,
        },
    ])
    good, _ = split_good_and_bad(df)
    return good


def test_revenue_is_quantity_times_price():
    df = transform(make_clean_rows(), "orders_2026-09-01.csv")

    assert df["revenue"].tolist() == [25.0, 37.5]


def test_country_is_uppercased():
    df = transform(make_clean_rows(), "orders_2026-09-01.csv")

    assert df["country"].tolist() == ["BD", "US"]


def test_year_and_month_are_added():
    df = transform(make_clean_rows(), "orders_2026-09-01.csv")

    assert df["order_year"].tolist() == [2026, 2026]
    assert df["order_month"].tolist() == [9, 9]


def test_source_file_is_tracked():
    df = transform(make_clean_rows(), "orders_2026-09-01.csv")

    assert df["source_file"].unique().tolist() == ["orders_2026-09-01.csv"]


def test_duplicate_order_ids_are_removed():
    rows = pd.concat([make_clean_rows(), make_clean_rows()], ignore_index=True)

    df = transform(rows, "orders_2026-09-01.csv")

    assert len(df) == 2


def test_column_order():
    df = transform(make_clean_rows(), "orders_2026-09-01.csv")

    assert list(df.columns) == FINAL_COLUMNS
