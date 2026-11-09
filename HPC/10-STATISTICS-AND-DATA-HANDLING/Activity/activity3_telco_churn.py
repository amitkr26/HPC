"""
Activity 3: Telco Customer Churn Data Visualization Mastery Lab
Dataset: Telco Customer Churn (telco_churn.csv)
Group 1 Members:
  - Raidas Kunal (Role: Single Variables and Categories - Foundations)
  - Amit Kumar (Role: Relationships and Correlations)
  - Mehul Lahot (Role: Advanced Storytelling and Export)
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set overall seaborn aesthetic
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({'font.sans-serif': 'DejaVu Sans', 'font.size': 10})

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "telco_churn.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "activity3_telco_churn")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load Dataset
print("[Activity 3] Loading Telco Customer Churn dataset...")
df = pd.read_csv(DATA_PATH)

# Handle TotalCharges numeric conversion (as explicitly noted in the lab PDF)
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
# Impute negligible missing values with median for downstream numerical stability
df['TotalCharges'] = df['TotalCharges'].fillna(df['TotalCharges'].median())

print(f"Dataset Shape: {df.shape}")
print(df.head())

# ==============================================================================
# GROUP 1: Single Variables and Categories (Foundations)
# Lead: Raidas Kunal
# ==============================================================================
print("\n--- Running Group 1: Foundations (Lead: Raidas Kunal) ---")

# Part 1: Distribution Analysis
# Continuous column: tenure (as specified in PDF)
plt.figure(figsize=(9, 5))
sns.histplot(df['tenure'], kde=True, color='teal', bins=36, alpha=0.6)
plt.title("Distribution of Customer Tenure (Months) with KDE Curve", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Customer Tenure (Months with Telco)", fontsize=12)
plt.ylabel("Number of Customers", fontsize=12)
hist_path = os.path.join(OUTPUT_DIR, "part1_distribution_histogram.png")
plt.savefig(hist_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {hist_path}")

# Part 2: Categorical Comparisons
# 1 & 2: Countplot of Contract
plt.figure(figsize=(9, 5))
contract_order = ["Month-to-month", "One year", "Two year"]
ax = sns.countplot(data=df, x='Contract', order=contract_order, hue='Contract', palette='Blues_r', legend=False)
plt.title("Customer Distribution by Subscription Contract Type", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Contract Terms", fontsize=12)
plt.ylabel("Total Subscribers", fontsize=12)
plt.xticks(rotation=15, fontsize=11)
for p in ax.patches:
    h = p.get_height()
    if h > 0:
        ax.annotate(f"{int(h)} ({h/len(df)*100:.1f}%)", 
                    (p.get_x() + p.get_width() / 2., h),
                    ha='center', va='bottom', fontsize=10, xytext=(0, 4), 
                    textcoords='offset points', fontweight='bold')
countplot_path = os.path.join(OUTPUT_DIR, "part2_contract_countplot.png")
plt.savefig(countplot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {countplot_path}")

# 4: Boxplot showing continuous column across categorical
# Continuous: MonthlyCharges, Categorical: Contract
plt.figure(figsize=(10, 6))
sns.boxplot(data=df, x='Contract', y='MonthlyCharges', order=contract_order, hue='Contract', palette='Set3', legend=False)
plt.title("Monthly Charges Distribution & Outliers across Contract Plans", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Contract Plan", fontsize=12)
plt.ylabel("Monthly Charges (USD)", fontsize=12)
boxplot_path = os.path.join(OUTPUT_DIR, "part2_contract_charges_boxplot.png")
plt.savefig(boxplot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {boxplot_path}")

# ==============================================================================
# GROUP 2: Relationships and Correlations
# Lead: Amit Kumar
# ==============================================================================
print("\n--- Running Group 2: Relationships and Correlations (Lead: Amit Kumar) ---")

# Part 1: Relational Scatterplot
# MonthlyCharges vs TotalCharges with hue='Churn', alpha=0.6
plt.figure(figsize=(10, 6))
churn_palette = {'No': '#2ecc71', 'Yes': '#e74c3c'}
sns.scatterplot(data=df, x='MonthlyCharges', y='TotalCharges', hue='Churn', alpha=0.6, palette=churn_palette, s=40)
plt.title("Monthly Charges vs. Total Charges Correlated by Churn Outcome", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Monthly Charges ($)", fontsize=12)
plt.ylabel("Total Lifetime Charges ($)", fontsize=12)
plt.legend(title="Customer Churn", loc='upper left')
scatter_path = os.path.join(OUTPUT_DIR, "part3_charges_scatter.png")
plt.savefig(scatter_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {scatter_path}")

# Part 2: The Heatmap
# Isolate numeric columns & calculate correlation
numeric_cols = df[['tenure', 'MonthlyCharges', 'TotalCharges', 'SeniorCitizen']]
corr_matrix = numeric_cols.corr()
plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='coolwarm', cbar=True, square=True, linewidths=0.5)
plt.title("Correlation Matrix of Numerical Customer Metrics", fontsize=14, fontweight='bold', pad=12)
heatmap_path = os.path.join(OUTPUT_DIR, "part4_churn_correlation_heatmap.png")
plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {heatmap_path}")

# ==============================================================================
# GROUP 3: Advanced Storytelling and Export
# Lead: Mehul Lahot
# ==============================================================================
print("\n--- Running Group 3: Storytelling and Export (Lead: Mehul Lahot) ---")

# Part 1: Subplot Grid Layout
# 1 row, 2 columns (14x6 inches)
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Subplot 1 (Left): Recreate Scatterplot from Part 3
sns.scatterplot(data=df, x='MonthlyCharges', y='TotalCharges', hue='Churn', alpha=0.6, palette=churn_palette, s=35, ax=axes[0])
axes[0].set_title("(A) Monthly vs. Total Charges by Churn Status", fontsize=12, fontweight='bold')
axes[0].set_xlabel("Monthly Charges ($)", fontsize=11)
axes[0].set_ylabel("Total Charges ($)", fontsize=11)
axes[0].legend(title="Churn", loc='upper left')

# Subplot 2 (Right): Barplot showing average MonthlyCharges grouped by Contract
avg_charges_by_contract = df.groupby('Contract')['MonthlyCharges'].mean().reset_index()
sns.barplot(data=avg_charges_by_contract, x='Contract', y='MonthlyCharges', order=contract_order, hue='Contract', palette='viridis', ax=axes[1], legend=False)
axes[1].set_title("(B) Average Monthly Billing by Contract Type", fontsize=12, fontweight='bold')
axes[1].set_xlabel("Contract Type", fontsize=11)
axes[1].set_ylabel("Average Monthly Charges ($)", fontsize=11)
for p in axes[1].patches:
    h = p.get_height()
    if h > 0:
        axes[1].annotate(f"${h:.2f}", 
                         (p.get_x() + p.get_width() / 2., h / 2),
                         ha='center', va='center', fontsize=11, color='white', fontweight='bold')

plt.tight_layout()
subplot_path = os.path.join(OUTPUT_DIR, "part5_subplot_grid.png")
plt.savefig(subplot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {subplot_path}")

# Part 2 & Part 3: Annotations, Polish and High-Res Final Export
# Programmatically find absolute maximum MonthlyCharges
max_mc_idx = df['MonthlyCharges'].idxmax()
max_mc_customer = df.loc[max_mc_idx]
print(f"Absolute Maximum Monthly Charge Customer: ID {max_mc_customer['customerID']} at ${max_mc_customer['MonthlyCharges']}")

fig, ax = plt.subplots(figsize=(10, 6.5))
sns.scatterplot(data=df, x='tenure', y='MonthlyCharges', hue='Churn', alpha=0.65, s=50, palette=churn_palette, ax=ax)
ax.set_title("Customer Tenure vs. Monthly Charges with Peak Billed Outlier", fontsize=14, fontweight='bold', pad=14)
ax.set_xlabel("Tenure (Months with Company)", fontsize=12)
ax.set_ylabel("Monthly Charges (USD)", fontsize=12)
ax.legend(title="Customer Churn", loc='lower right')

# Annotation of Record High
ax.annotate(
    f"Record High Monthly Charge!\nCustomer: {max_mc_customer['customerID']}\nRate: ${max_mc_customer['MonthlyCharges']:.2f}/mo (Tenure: {max_mc_customer['tenure']} mo)",
    xy=(max_mc_customer['tenure'], max_mc_customer['MonthlyCharges']),
    xytext=(max_mc_customer['tenure'] - 30, max_mc_customer['MonthlyCharges'] - 12),
    arrowprops=dict(facecolor='darkred', edgecolor='black', arrowstyle='->', lw=2),
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffe6cc', alpha=0.9, edgecolor='darkred', lw=1.5),
    fontsize=10,
    fontweight='bold'
)

final_path = os.path.join(OUTPUT_DIR, "final_visualization.png")
plt.savefig(final_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved Final Visual: {final_path} (300 DPI)")
print("[Activity 3] Successfully Completed!")

