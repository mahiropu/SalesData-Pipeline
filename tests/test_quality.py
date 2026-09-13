import pandas as pd

from src.quality import check_columns, split_good_and_bad


def make_rows():
    return pd.DataFrame([
        {
            "order_id": "ORD-0000001",
            "order_date": "2026-09-01",
            "customer_id": "CUST-0001",
            "country": "BD",
            "sku": "MUG-01",
            "product_name": "Coffee Mug",
            "category": "Kitchen",
            "quantity": 2,
            "unit_price": 12.5,
        }
    ])


def with_change(column, value):
    df = make_rows()
    df.loc[0, column] = value
    return df


def test_check_columns_finds_nothing_when_file_is_valid():
    assert check_columns(make_rows()) == []


def test_check_columns_reports_missing_column():
    df = make_rows().drop(columns=["sku"])

    assert check_columns(df) == ["sku"]


def test_good_row_passes():
    good, bad = split_good_and_bad(make_rows())

    assert len(good) == 1
    assert len(bad) == 0


def test_bad_date_is_rejected():
    good, bad = split_good_and_bad(with_change("order_date", "not-a-date"))

    assert len(good) == 0
    assert bad["reject_reason"].tolist() == ["invalid_order_date"]


def test_missing_sku_is_rejected():
    good, bad = split_good_and_bad(with_change("sku", ""))

    assert bad["reject_reason"].tolist() == ["missing_sku"]


def test_zero_quantity_is_rejected():
    good, bad = split_good_and_bad(with_change("quantity", 0))

    assert bad["reject_reason"].tolist() == ["invalid_quantity"]


def test_negative_price_is_rejected():
    good, bad = split_good_and_bad(with_change("unit_price", -12.5))

    assert bad["reject_reason"].tolist() == ["invalid_unit_price"]
