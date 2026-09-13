import pandas as pd

REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "customer_id",
    "country",
    "sku",
    "product_name",
    "category",
    "quantity",
    "unit_price",
]


def check_columns(df):
    missing = []
    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            missing.append(column)
    return missing


def add_reject_reason(df):
    df = df.copy()

    df["order_date_parsed"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    reasons = []
    for row in df.itertuples(index=False):
        if pd.isna(row.order_date_parsed):
            reasons.append("invalid_order_date")
        elif not str(row.order_id).strip():
            reasons.append("missing_order_id")
        elif not str(row.sku).strip() or str(row.sku) == "nan":
            reasons.append("missing_sku")
        elif pd.isna(row.quantity) or row.quantity <= 0:
            reasons.append("invalid_quantity")
        elif pd.isna(row.unit_price) or row.unit_price <= 0:
            reasons.append("invalid_unit_price")
        else:
            reasons.append("")

    df["reject_reason"] = reasons
    return df


def split_good_and_bad(df):
    df = add_reject_reason(df)

    good = df[df["reject_reason"] == ""].copy()
    bad = df[df["reject_reason"] != ""].copy()

    good = good.drop(columns=["reject_reason"])
    bad = bad.drop(columns=["order_date_parsed"])

    return good, bad
