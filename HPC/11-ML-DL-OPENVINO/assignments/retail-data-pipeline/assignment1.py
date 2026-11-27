from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
RAW = BASE_DIR / "data" / "raw" / "retail"
PROC_DIR = BASE_DIR / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

MASTER_PATH = PROC_DIR / "master_retail.csv"
ML_PATH = PROC_DIR / "customer_ml_features.csv"
SNAPSHOT_DATE = pd.Timestamp("2025-12-31")


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    return df


tx_df = clean_columns(pd.read_csv(RAW / "sales_transactions.csv"))
prod_df = clean_columns(
    pd.read_excel(RAW / "products.xlsx", sheet_name="Products", engine="openpyxl")
)
cust_df = clean_columns(pd.read_json(RAW / "customer_profiles.json"))

print("=== SALES TRANSACTION AUDIT ===")
print(f"Rows: {len(tx_df):,}")
print(f"Columns: {tx_df.columns.tolist()}")
tx_df.info()
print(f"\nExact duplicate rows: {tx_df.duplicated().sum():,}")
print("\nMissing values per column:")
print(tx_df.isna().sum().to_string())
print("\nUnique region values:")
print(sorted(tx_df["region"].dropna().astype(str).unique().tolist()))
print("\nSummary statistics:")
print(tx_df.describe(include="all").to_string())

tx_clean = tx_df.drop_duplicates().copy()
tx_clean["region"] = tx_clean["region"].astype("string").str.strip().str.title()
tx_clean["discount_pct"] = tx_clean["discount_pct"].fillna(0.0)
cust_df["region"] = cust_df["region"].astype("string").str.strip().str.title()

q1 = tx_clean["units_sold"].quantile(0.25)
q3 = tx_clean["units_sold"].quantile(0.75)
iqr_upper = q3 + 1.5 * (q3 - q1)
print("\n=== UNITS OUTLIER CHECK ===")
print(f"Q1={q1}, Q3={q3}, IQR upper fence={iqr_upper}")
print(f"Rows with units_sold <= 0: {(tx_clean['units_sold'] <= 0).sum():,}")
print(f"Rows with units_sold >= 45: {(tx_clean['units_sold'] >= 45).sum():,}")
print(f"Rows with units_sold > 15: {(tx_clean['units_sold'] > 15).sum():,}")
print(
    f"Rows above the IQR upper fence: "
    f"{(tx_clean['units_sold'] > iqr_upper).sum():,}"
)

invalid_units = (tx_clean["units_sold"] <= 0) | (tx_clean["units_sold"] > 15)
print(f"Removing invalid/outlier rows: {invalid_units.sum():,}")
tx_clean = tx_clean.loc[~invalid_units].copy()

master_df = (
    tx_clean.merge(prod_df, on="product_id", how="left")
    .merge(cust_df, on="customer_id", how="left", suffixes=("", "_cust"))
)
master_df["region"] = master_df["region"].fillna(master_df["region_cust"])
master_df = master_df.drop(columns=["region_cust"])

master_df["transaction_date"] = pd.to_datetime(
    master_df["transaction_date"], errors="raise"
)
master_df["sales_amount"] = (
    master_df["units_sold"]
    * master_df["unit_price"]
    * (1.0 - master_df["discount_pct"] / 100.0)
).round(2)
master_df["profit"] = (
    master_df["sales_amount"] - master_df["units_sold"] * master_df["cost_price"]
).round(2)
master_df["order_year"] = master_df["transaction_date"].dt.year
master_df["order_month"] = master_df["transaction_date"].dt.to_period("M").astype(str)
master_df["day_of_week"] = master_df["transaction_date"].dt.day_name()

if master_df.isna().any().any():
    raise ValueError("Unexpected nulls remain in master_df")

expected_sales = (
    master_df["units_sold"]
    * master_df["unit_price"]
    * (1.0 - master_df["discount_pct"] / 100.0)
).round(2)
print(
    "\nMax sales_amount formula error: "
    f"{(master_df['sales_amount'] - expected_sales).abs().max():.12f}"
)
print(f"Master rows after cleaning: {len(master_df):,}")
print(f"Master columns: {master_df.columns.tolist()}")

master_df.to_csv(MASTER_PATH, index=False)
print(f"\n[SUCCESS] Exported {MASTER_PATH}")
print(f"master_df.shape = {master_df.shape}")
print(master_df.head(10).to_string(index=False))

master_df = pd.read_csv(MASTER_PATH, parse_dates=["transaction_date"])
order_level = (
    master_df.groupby(["customer_id", "order_id"], as_index=False)
    .agg(
        order_date=("transaction_date", "max"),
        order_spend=("sales_amount", "sum"),
        order_units=("units_sold", "sum"),
        order_profit=("profit", "sum"),
    )
)

preferred_category = (
    master_df.groupby(["customer_id", "category"])["sales_amount"]
    .sum()
    .reset_index()
    .sort_values(["customer_id", "sales_amount"], ascending=[True, False])
    .drop_duplicates("customer_id")[["customer_id", "category"]]
    .rename(columns={"category": "preferred_category"})
    .reset_index(drop=True)
)

customer_orders = (
    order_level.groupby("customer_id", as_index=False)
    .agg(
        order_count=("order_id", "nunique"),
        total_spend=("order_spend", "sum"),
        avg_order_value=("order_spend", "mean"),
        total_units=("order_units", "sum"),
        avg_units_per_order=("order_units", "mean"),
        total_profit=("order_profit", "sum"),
        last_order_date=("order_date", "max"),
    )
)
customer_orders["recency_days"] = (
    SNAPSHOT_DATE - customer_orders["last_order_date"]
).dt.days
customer_orders = customer_orders.drop(columns=["last_order_date"])

average_discount = (
    master_df.groupby("customer_id", as_index=False)["discount_pct"]
    .mean()
    .rename(columns={"discount_pct": "avg_discount"})
)

customer_profile = cust_df[
    [
        "customer_id",
        "age",
        "region",
        "tenure_months",
        "loyalty_tier",
        "support_tickets",
        "churned",
    ]
].drop_duplicates("customer_id")

ml_df = customer_profile.merge(customer_orders, on="customer_id", how="left")
ml_df = ml_df.merge(average_discount, on="customer_id", how="left")
ml_df = ml_df.merge(preferred_category, on="customer_id", how="left")

zero_fill_cols = [
    "order_count",
    "total_spend",
    "avg_order_value",
    "total_units",
    "avg_units_per_order",
    "total_profit",
    "avg_discount",
]
ml_df[zero_fill_cols] = ml_df[zero_fill_cols].fillna(0)
ml_df["order_count"] = ml_df["order_count"].astype(int)
ml_df["total_units"] = ml_df["total_units"].astype(int)
ml_df["recency_days"] = ml_df["recency_days"].astype("Int64")

ml_df["profit_margin_pct"] = np.where(
    ml_df["total_spend"] > 0,
    (ml_df["total_profit"] / ml_df["total_spend"]) * 100.0,
    0.0,
).round(2)
ml_df["tickets_per_year"] = np.where(
    ml_df["tenure_months"] > 0,
    ml_df["support_tickets"] / (ml_df["tenure_months"] / 12.0),
    0.0,
).round(3)
ml_df["orders_per_month"] = np.where(
    ml_df["tenure_months"] > 0,
    ml_df["order_count"] / ml_df["tenure_months"],
    0.0,
).round(3)

ml_df.to_csv(ML_PATH, index=False)

print("\n=== CUSTOMER ML FEATURES ===")
print(f"Snapshot date: {SNAPSHOT_DATE.date()}")
print(f"Rows: {len(ml_df):,}")
print(f"Unique customers: {ml_df['customer_id'].nunique():,}")
print(f"No-purchase customers: {(ml_df['order_count'] == 0).sum():,}")
print(f"ml_df.shape = {ml_df.shape}")
print("\nMissing values per column:")
print(ml_df.isna().sum().to_string())
print("\nVerification totals:")
print(f"Orders: {ml_df['order_count'].sum():,}")
print(f"Spend: {ml_df['total_spend'].sum():,.2f}")
print(f"Units: {ml_df['total_units'].sum():,}")
print(f"Profit: {ml_df['total_profit'].sum():,.2f}")
print(f"\n[SUCCESS] Exported {ML_PATH}")
print(ml_df.head(10).to_string(index=False))
