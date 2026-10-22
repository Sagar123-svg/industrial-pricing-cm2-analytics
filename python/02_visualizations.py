"""
============================================================
Industrial Spare Parts Pricing & CM2 Profitability Analytics
Visualizations: Revenue/CM2 trends, category breakdowns,
discount analysis, customer/material rankings
============================================================
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 110
plt.rcParams["axes.titlesize"] = 13
plt.rcParams["axes.titleweight"] = "bold"

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
CHART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts/python_eda")
os.makedirs(CHART_DIR, exist_ok=True)

df = pd.read_csv(f"{DATA_DIR}/fact_sales_cleaned_enriched.csv", parse_dates=["Transaction_Date"])

def rupee_formatter(x, pos):
    if x >= 1e7:
        return f"{x/1e7:.1f}Cr"
    elif x >= 1e5:
        return f"{x/1e5:.1f}L"
    elif x >= 1e3:
        return f"{x/1e3:.0f}K"
    return f"{x:.0f}"

RUPEE_FMT = mticker.FuncFormatter(rupee_formatter)

# ============================================================
# CHART 1: Monthly Revenue Trend
# ============================================================
monthly = df.groupby("Txn_YearMonth").agg(Revenue=("Revenue", "sum"), CM2=("CM2", "sum")).reset_index()
monthly = monthly.sort_values("Txn_YearMonth")

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(monthly["Txn_YearMonth"], monthly["Revenue"], marker="o", color="#2563eb", linewidth=2)
ax.set_title("Monthly Revenue Trend")
ax.set_ylabel("Revenue (INR)")
ax.set_xlabel("Month")
ax.yaxis.set_major_formatter(RUPEE_FMT)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/01_monthly_revenue_trend.png")
plt.close()

# ============================================================
# CHART 2: Monthly CM2 Trend (value + %)
# ============================================================
monthly["CM2_Pct"] = monthly["CM2"] / monthly["Revenue"] * 100

fig, ax1 = plt.subplots(figsize=(11, 5))
ax1.bar(monthly["Txn_YearMonth"], monthly["CM2"], color="#16a34a", alpha=0.7, label="CM2 (Rs)")
ax1.set_ylabel("CM2 (INR)")
ax1.yaxis.set_major_formatter(RUPEE_FMT)
ax2 = ax1.twinx()
ax2.plot(monthly["Txn_YearMonth"], monthly["CM2_Pct"], color="#dc2626", marker="o", linewidth=2, label="CM2 %")
ax2.set_ylabel("CM2 %")
ax1.set_title("Monthly CM2 Trend (Value & Margin %)")
plt.xticks(rotation=45, ha="right")
fig.legend(loc="upper left", bbox_to_anchor=(0.08, 0.9))
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/02_monthly_cm2_trend.png")
plt.close()

# ============================================================
# CHART 3: Revenue by Material Category
# ============================================================
cat_rev = df.groupby("Material_Category", observed=True)["Revenue"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(x=cat_rev.values, y=cat_rev.index, hue=cat_rev.index, palette="Blues_r", ax=ax, legend=False)
ax.set_title("Revenue by Material Category")
ax.set_xlabel("Total Revenue (INR)")
ax.xaxis.set_major_formatter(RUPEE_FMT)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/03_revenue_by_category.png")
plt.close()

# ============================================================
# CHART 4: CM2 % by Material Category (vs Target)
# ============================================================
cat_summary = df.groupby("Material_Category", observed=True).agg(
    CM2=("CM2", "sum"), Revenue=("Revenue", "sum"), Target=("Target_CM2_Percentage", "mean")
)
cat_summary["CM2_Pct"] = cat_summary["CM2"] / cat_summary["Revenue"] * 100
cat_summary = cat_summary.sort_values("CM2_Pct", ascending=False)

fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(cat_summary))
ax.bar(x - 0.2, cat_summary["CM2_Pct"], width=0.4, label="Actual CM2 %", color="#2563eb")
ax.bar(x + 0.2, cat_summary["Target"], width=0.4, label="Target CM2 %", color="#94a3b8")
ax.set_xticks(x)
ax.set_xticklabels(cat_summary.index, rotation=20, ha="right")
ax.set_title("CM2 % by Category vs Target")
ax.set_ylabel("CM2 %")
ax.legend()
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/04_cm2pct_by_category_vs_target.png")
plt.close()

# ============================================================
# CHART 5: Discount % Distribution
# ============================================================
fig, ax = plt.subplots(figsize=(9, 5))
sns.histplot(df["Discount_Percentage"], bins=30, kde=True, color="#f59e0b", ax=ax)
ax.axvline(df["Discount_Percentage"].mean(), color="red", linestyle="--", label=f"Mean: {df['Discount_Percentage'].mean():.1f}%")
ax.set_title("Discount % Distribution")
ax.set_xlabel("Discount %")
ax.legend()
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/05_discount_distribution.png")
plt.close()

# ============================================================
# CHART 6: CM2 % Distribution (with negative-CM2 zone highlighted)
# ============================================================
fig, ax = plt.subplots(figsize=(9, 5))
sns.histplot(df["CM2_Percentage"], bins=40, color="#16a34a", ax=ax)
ax.axvline(0, color="red", linestyle="--", linewidth=2, label="CM2 = 0 (breakeven)")
ax.axvspan(df["CM2_Percentage"].min(), 0, color="red", alpha=0.08)
ax.set_title("CM2 % Distribution (Red zone = Loss-making transactions)")
ax.set_xlabel("CM2 %")
ax.legend()
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/06_cm2pct_distribution.png")
plt.close()

# ============================================================
# CHART 7: Standard Cost vs Selling Price (scatter)
# ============================================================
fig, ax = plt.subplots(figsize=(8, 7))
sample = df.sample(min(2000, len(df)), random_state=42)  # sample for readability
colors = sample["Negative_CM2_Flag"].map({"Yes": "#dc2626", "No": "#2563eb"})
ax.scatter(sample["Standard_Cost"], sample["Selling_Price"], c=colors, alpha=0.5, s=18)
max_val = max(sample["Standard_Cost"].max(), sample["Selling_Price"].max())
ax.plot([0, max_val], [0, max_val], color="gray", linestyle="--", label="Selling Price = Cost")
ax.set_title("Standard Cost vs Selling Price\n(Red = Negative CM2 transactions)")
ax.set_xlabel("Standard Cost (INR)")
ax.set_ylabel("Selling Price (INR)")
ax.legend()
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/07_cost_vs_price_scatter.png")
plt.close()

# ============================================================
# CHART 8: Discount % vs CM2 % (scatter + trend)
# ============================================================
fig, ax = plt.subplots(figsize=(9, 6))
sample2 = df.sample(min(2500, len(df)), random_state=42)
sns.regplot(
    data=sample2, x="Discount_Percentage", y="CM2_Percentage",
    scatter_kws={"alpha": 0.35, "s": 15, "color": "#7c3aed"},
    line_kws={"color": "red"}, ax=ax
)
ax.axhline(0, color="black", linestyle=":", linewidth=1)
ax.set_title("Discount % vs CM2 % (with trend line)")
ax.set_xlabel("Discount %")
ax.set_ylabel("CM2 %")
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/08_discount_vs_cm2_scatter.png")
plt.close()

# ============================================================
# CHART 9: Top 10 Customers by Revenue
# ============================================================
top_cust = df.groupby("Customer_Name", observed=True)["Revenue"].sum().sort_values(ascending=False).head(10)

fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(x=top_cust.values, y=top_cust.index, hue=top_cust.index, palette="Greens_r", ax=ax, legend=False)
ax.set_title("Top 10 Customers by Revenue")
ax.set_xlabel("Total Revenue (INR)")
ax.xaxis.set_major_formatter(RUPEE_FMT)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/09_top10_customers_revenue.png")
plt.close()

# ============================================================
# CHART 10: Top 10 Materials by Revenue
# ============================================================
top_mat = df.groupby("Material_Description", observed=True)["Revenue"].sum().sort_values(ascending=False).head(10)

fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(x=top_mat.values, y=top_mat.index, hue=top_mat.index, palette="Purples_r", ax=ax, legend=False)
ax.set_title("Top 10 Materials by Revenue")
ax.set_xlabel("Total Revenue (INR)")
ax.xaxis.set_major_formatter(RUPEE_FMT)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/10_top10_materials_revenue.png")
plt.close()

# ============================================================
# CHART 11: Negative CM2 Materials (worst offenders)
# ============================================================
neg = df[df["Negative_CM2_Flag"] == "Yes"]
neg_by_mat = neg.groupby("Material_Description", observed=True).agg(
    Total_Negative_CM2=("CM2", "sum"), Txn_Count=("Transaction_ID", "count")
).sort_values("Total_Negative_CM2").head(10)

fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(x=neg_by_mat["Total_Negative_CM2"], y=neg_by_mat.index, hue=neg_by_mat.index,
            palette="Reds_r", ax=ax, legend=False)
ax.set_title("Top 10 Materials by Total Negative CM2 (Rs)")
ax.set_xlabel("Total Negative CM2 (INR)")
ax.xaxis.set_major_formatter(RUPEE_FMT)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/11_negative_cm2_materials.png")
plt.close()

print("All 11 charts saved to:", CHART_DIR)
for f in sorted(os.listdir(CHART_DIR)):
    print(" -", f)
