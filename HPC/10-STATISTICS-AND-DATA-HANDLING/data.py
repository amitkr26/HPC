import kagglehub

# Download latest version
path = kagglehub.dataset_download("dgomonov/new-york-city-airbnb-open-data")

print("Path to dataset files:", path)

import pandas as pd
import numpy as np
import os

pd.set_option("display.width", 95)         # keep printed tables inside the page
pd.set_option("display.max_columns", None)

# Fixed: Joined the local path variable with the actual CSV filename instead of a URL string
csv_path = os.path.join(path, "AB_NYC_2019.csv")
df = pd.read_csv(csv_path)        # Option A: NYC Airbnb Open Data
original_shape = df.shape
print("===== PART 1: Import =====")
print("File loaded into a DataFrame with shape:", original_shape)

print("\n===== PART 3: Structural Cleaning =====")
df = df.drop(columns=["id", "host_name"])
df = df.rename(columns={"neighbourhood_group": "borough"})
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
print("Columns now:", list(df.columns))

print("\n===== PART 4: Handling Missing Data =====")
df["name"] = df["name"].fillna("Unknown")
df["reviews_per_month"] = df["reviews_per_month"].fillna(0)
print("Nulls left in last_review (kept on purpose):", df["last_review"].isnull().sum())

print("\nMissing values per column (after filling):")
print(df.isnull().sum())

print("\n===== PART 5: Type Conversion =====")
memory_before = df.memory_usage(deep=True).sum()

df["last_review"] = pd.to_datetime(df["last_review"])
df["room_type"] = df["room_type"].astype("category")
df["borough"] = df["borough"].astype("category")

memory_after = df.memory_usage(deep=True).sum()
print(df.dtypes)
print(f"\nMemory used: {memory_before / 1024:.1f} KB -> {memory_after / 1024:.1f} KB")

print("\n===== PART 6: Outliers and Duplicates =====")
print("Duplicate rows found:", df.duplicated().sum())
df = df.drop_duplicates(keep="first")

print("Rows with price = 0:", (df["price"] == 0).sum())
df = df[df["price"] != 0]

cutoff = df["price"].quantile(0.99)
print("99th percentile of price:", cutoff)
df = df[df["price"] < cutoff]

print("\nShape before cleaning:", original_shape)
print("Shape after cleaning :", df.shape)
print("Rows removed         :", original_shape[0] - df.shape[0])

print("\n===== PART 7: Feature Engineering =====")
df["price_tier"] = pd.cut(
    df["price"],
    bins=[0, 100, 250, np.inf],
    labels=["Budget", "Mid-Range", "Luxury"],
)
print(df["price_tier"].value_counts())

print("\n===== PART 8: Final Export =====")
df.to_csv("cleaned_dataset_v1.csv", index=False)

check = pd.read_csv("cleaned_dataset_v1.csv")
print("Saved cleaned_dataset_v1.csv with shape", check.shape)
print("Columns in file:", list(check.columns))