"""
============================================================
Industrial Spare Parts Pricing & CM2 Profitability Analytics
EDA Workflow: Loading -> Cleaning -> Feature Engineering -> Stats
============================================================
"""

import pandas as pd
import os
import numpy as np

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 140)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# ============================================================
# 1. DATA LOADING
# ============================================================
fact_sales = pd.read_csv(f"{DATA_DIR}/fact_sales.csv", parse_dates=["Transaction_Date"])
fact_pricing = pd.read_csv(f"{DATA_DIR}/fact_pricing.csv", parse_dates=["Change_Date"])
dim_material = pd.read_csv(f"{DATA_DIR}/dim_material.csv", parse_dates=["Introduced_Date"])
dim_customer = pd.read_csv(f"{DATA_DIR}/dim_customer.csv", parse_dates=["Customer_Since"])
dim_sales_org = pd.read_csv(f"{DATA_DIR}/dim_sales_organization.csv")
dim_pricing_condition = pd.read_csv(f"{DATA_DIR}/dim_pricing_condition.csv")
dim_category_target = pd.read_csv(f"{DATA_DIR}/dim_category_target.csv")

print("=" * 60)
print("1. DATA LOADING")
print("=" * 60)
print(f"Fact_Sales shape:   {fact_sales.shape}")
print(f"Fact_Pricing shape: {fact_pricing.shape}")
print(f"Dim_Material shape: {dim_material.shape}")
print(f"Dim_Customer shape: {dim_customer.shape}")

# ============================================================
# 2. DATA INSPECTION
# ============================================================
print("\n" + "=" * 60)
print("2. DATA INSPECTION")
print("=" * 60)
print("\nFact_Sales dtypes:")
print(fact_sales.dtypes)
print("\nFact_Sales describe() [numeric columns]:")
print(fact_sales.describe().T)

# ============================================================
# 3. MERGE INTO A SINGLE ANALYTICAL DATAFRAME
# ============================================================
# Business reason: analysts almost always work off a single "flattened"
# analytical table (star schema joined together) rather than juggling
# multiple frames for every question. We keep the underlying tables
# separate (as in SQL) but build one merged frame for Python/EDA work.
df = (
    fact_sales
    .merge(dim_material, on="Material_ID", how="left", suffixes=("", "_mat"))
    .merge(dim_customer, on="Customer_ID", how="left", suffixes=("", "_cust"))
    .merge(dim_sales_org, on="Sales_Org_ID", how="left")
    .merge(dim_pricing_condition, on="Pricing_Condition_ID", how="left")
)

print(f"\nMerged analytical dataframe shape: {df.shape}")

# ============================================================
# 4. MISSING VALUES
# ============================================================
print("\n" + "=" * 60)
print("4. MISSING VALUES")
print("=" * 60)
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
missing_report = pd.DataFrame({"Missing_Count": missing, "Missing_Pct": missing_pct})
missing_report = missing_report[missing_report["Missing_Count"] > 0].sort_values("Missing_Count", ascending=False)
print(missing_report if len(missing_report) > 0 else "No missing values found in merged dataframe.")

# Business rule (from Part 6 Excel logic, applied consistently here):
# - Missing Standard_Cost/Selling_Price -> cannot compute CM2 -> DROP (flag & exclude), never impute a financial figure
# - Missing categorical attributes (e.g., Customer_Segment) -> impute as "Unclassified", never drop the row
critical_cols = ["Standard_Cost", "Selling_Price", "Quantity"]
rows_before = len(df)
df = df.dropna(subset=critical_cols)
rows_after = len(df)
print(f"\nRows dropped due to missing critical financial fields: {rows_before - rows_after}")

for col in ["Customer_Segment", "Material_Category"]:
    if df[col].isnull().any():
        df[col] = df[col].fillna("Unclassified")

# ============================================================
# 5. DUPLICATE DETECTION
# ============================================================
print("\n" + "=" * 60)
print("5. DUPLICATE DETECTION")
print("=" * 60)
dup_ids = df["Transaction_ID"].duplicated().sum()
print(f"Duplicate Transaction_IDs: {dup_ids}")

dup_full_rows = df.duplicated(
    subset=["Material_ID", "Customer_ID", "Transaction_Date", "Quantity", "Selling_Price"]
).sum()
print(f"Potential duplicate business rows (same material/customer/date/qty/price): {dup_full_rows}")

if dup_ids > 0:
    df = df.drop_duplicates(subset=["Transaction_ID"], keep="first")
    print("Duplicate Transaction_IDs removed, keeping first occurrence.")

# ============================================================
# 6. DATA TYPE CORRECTION
# ============================================================
print("\n" + "=" * 60)
print("6. DATA TYPE CORRECTION")
print("=" * 60)
# Ensure categorical columns are stored efficiently as 'category' dtype
# (reduces memory, speeds up groupby operations on large datasets)
cat_cols = [
    "Material_Category", "Material_Subcategory", "Customer_Segment",
    "Region", "Sales_Org_Name", "Condition_Type", "Quote_Status",
    "Negative_CM2_Flag", "Low_Margin_Flag", "Price_Revision_Required_Flag"
]
for col in cat_cols:
    if col in df.columns:
        df[col] = df[col].astype("category")

print("Converted categorical columns to 'category' dtype:")
print([c for c in cat_cols if c in df.columns])

# ============================================================
# 7. OUTLIER ANALYSIS (IQR method)
# ============================================================
print("\n" + "=" * 60)
print("7. OUTLIER ANALYSIS")
print("=" * 60)

def iqr_outlier_bounds(series):
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr

for col in ["Selling_Price", "Discount_Percentage", "CM2_Percentage"]:
    lower, upper = iqr_outlier_bounds(df[col])
    outlier_count = ((df[col] < lower) | (df[col] > upper)).sum()
    print(f"{col}: bounds=({lower:.2f}, {upper:.2f}) -> {outlier_count} outlier rows "
          f"({outlier_count/len(df)*100:.1f}%)")

# Business decision: we FLAG outliers but do NOT automatically remove them.
# In pricing data, an "outlier" discount or CM2% is often the most
# important row in the whole dataset (e.g. a large negative-CM2 deal) --
# removing it would hide the exact problem we're trying to find.
df["Is_Price_Outlier"] = (
    (df["Selling_Price"] < iqr_outlier_bounds(df["Selling_Price"])[0]) |
    (df["Selling_Price"] > iqr_outlier_bounds(df["Selling_Price"])[1])
)

# ============================================================
# 8. FEATURE ENGINEERING
# ============================================================
print("\n" + "=" * 60)
print("8. FEATURE ENGINEERING")
print("=" * 60)

# Time-based features
df["Txn_Year"] = df["Transaction_Date"].dt.year
df["Txn_Month"] = df["Transaction_Date"].dt.month
df["Txn_Month_Name"] = df["Transaction_Date"].dt.strftime("%b")
df["Txn_Quarter"] = "Q" + df["Transaction_Date"].dt.quarter.astype(str)
df["Txn_YearMonth"] = df["Transaction_Date"].dt.to_period("M").astype(str)

# Discount bands (matches SQL Query 10 banding logic, kept consistent)
df["Discount_Band"] = pd.cut(
    df["Discount_Percentage"],
    bins=[-0.01, 10, 20, 30, 40, 100],
    labels=["0-10%", "10-20%", "20-30%", "30-40%", "40%+"]
)

# CM2 performance vs target (gap, not just a flag)
df["CM2_Gap_vs_Target"] = df["CM2_Percentage"] - df["Target_CM2_Percentage"]

# Revenue tier per transaction (useful for weighting in charts)
df["Revenue_Tier"] = pd.qcut(df["Revenue"], q=4, labels=["Low", "Medium", "High", "Very High"])

# Material tenure at time of sale (days since introduced) -- newer parts
# may have less-mature pricing
df["Material_Age_Days"] = (df["Transaction_Date"] - df["Introduced_Date"]).dt.days

print("New engineered columns added:")
print(["Txn_Year", "Txn_Month", "Txn_Month_Name", "Txn_Quarter", "Txn_YearMonth",
       "Discount_Band", "CM2_Gap_vs_Target", "Revenue_Tier", "Material_Age_Days",
       "Is_Price_Outlier"])

# ============================================================
# 9. DESCRIPTIVE STATISTICS
# ============================================================
print("\n" + "=" * 60)
print("9. DESCRIPTIVE STATISTICS")
print("=" * 60)

print("\n--- Overall Business Summary ---")
total_revenue = df["Revenue"].sum()
total_cost = df["Cost"].sum()
total_cm2 = df["CM2"].sum()
overall_cm2_pct = total_cm2 / total_revenue * 100

print(f"Total Revenue:        Rs {total_revenue:,.0f}")
print(f"Total Cost:           Rs {total_cost:,.0f}")
print(f"Total CM2:            Rs {total_cm2:,.0f}")
print(f"Overall CM2%:         {overall_cm2_pct:.2f}%")
print(f"Total Transactions:   {len(df):,}")
print(f"Avg Selling Price:    Rs {df['Selling_Price'].mean():,.2f}")
print(f"Avg Discount %:       {df['Discount_Percentage'].mean():.2f}%")
print(f"Negative CM2 %:       {(df['Negative_CM2_Flag']=='Yes').mean()*100:.2f}%")
print(f"Below Target CM2 %:   {(df['Low_Margin_Flag']=='Yes').mean()*100:.2f}%")

print("\n--- Revenue & CM2 by Material Category ---")
cat_summary = df.groupby("Material_Category", observed=True).agg(
    Total_Revenue=("Revenue", "sum"),
    Total_CM2=("CM2", "sum"),
    Txn_Count=("Transaction_ID", "count")
)
cat_summary["CM2_Pct"] = (cat_summary["Total_CM2"] / cat_summary["Total_Revenue"] * 100).round(2)
print(cat_summary.sort_values("Total_Revenue", ascending=False))

print("\n--- Discount Band vs Avg CM2% ---")
band_summary = df.groupby("Discount_Band", observed=True).agg(
    Avg_CM2_Pct=("CM2_Percentage", "mean"),
    Txn_Count=("Transaction_ID", "count"),
    Negative_CM2_Count=("Negative_CM2_Flag", lambda x: (x == "Yes").sum())
).round(2)
print(band_summary)

# ============================================================
# 10. SAVE CLEANED + ENGINEERED DATASET FOR REUSE
# ============================================================
df.to_csv(f"{DATA_DIR}/fact_sales_cleaned_enriched.csv", index=False)
print(f"\nCleaned & enriched dataset saved: {DATA_DIR}/fact_sales_cleaned_enriched.csv")
print(f"Final shape: {df.shape}")
