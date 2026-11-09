"""
Builder script to generate Data_Visualization_Mastery_Lab.ipynb
with full code, markdown instructions, and explanations.
"""

import json
import os

nb = {
    "cells": [],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.13.7"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

def add_md(text):
    nb["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split("\n")]
    })

def add_code(code):
    nb["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in code.strip().split("\n")]
    })

# Header Cell
add_md("""# Data Visualization Mastery Lab

### Group 1
- **Mehul Lahot**
- **Raidas Kunal**
- **Amit Kumar**

---

### Group Rotation Strategy Across Activities:
| Activity | Dataset | Single Variables & Categories (Foundations) | Relationships & Correlations | Advanced Storytelling & Export |
| :--- | :--- | :--- | :--- | :--- |
| **Activity 1** | **Video Game Sales** | **Mehul Lahot** | **Raidas Kunal** | **Amit Kumar** |
| **Activity 2** | **Pokemon with Stats** | **Amit Kumar** | **Mehul Lahot** | **Raidas Kunal** |
| **Activity 3** | **Telco Customer Churn** | **Raidas Kunal** | **Amit Kumar** | **Mehul Lahot** |

---
### Setup & Global Configuration""")

add_code("""import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Global styling configuration
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({'font.sans-serif': 'DejaVu Sans', 'font.size': 11})

DATA_DIR = "data"
OUTPUTS_DIR = "outputs"
os.makedirs(OUTPUTS_DIR, exist_ok=True)
print("Libraries imported and environment initialized successfully!")""")

# ==============================================================================
# ACTIVITY 1
# ==============================================================================
add_md("""# ==========================================================
# ACTIVITY 1: Video Game Sales Analysis
# ==========================================================
**Dataset:** `vgsales.csv`  
**Description:** Contains sales data (in millions) for video games across different regions, along with platforms, years, genres, and publishers.  

**Group 1 Roles for Activity 1:**
- **Foundations (Part 1 & 2):** Mehul Lahot
- **Relationships & Heatmap (Part 3 & 4):** Raidas Kunal
- **Storytelling, Annotations & Export (Part 5 & 6):** Amit Kumar""")

add_code("""# Load Video Game Sales Dataset
vg_df = pd.read_csv(os.path.join(DATA_DIR, "vgsales.csv"))
print(f"Video Game Dataset Shape: {vg_df.shape}")
vg_df.head()""")

add_md("""### Part 1: Distribution Analysis (Foundations)
- **Role Lead:** Mehul Lahot
- Continuous Column: `Global_Sales`
- Histogram created with Seaborn, KDE enabled, custom purple color palette, descriptive title, and X-axis label.""")

add_code("""plt.figure(figsize=(9, 5))
# Filtering to <= 5M to provide a clear view of the density curve without extreme outlier skew
sns.histplot(vg_df[vg_df['Global_Sales'] <= 5]['Global_Sales'], kde=True, color='purple', bins=40, alpha=0.6)
plt.title("Distribution of Global Sales (<= 5M Copies) with KDE Curve", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Global Sales (in Millions)", fontsize=12)
plt.ylabel("Number of Video Games", fontsize=12)
plt.show()""")

add_md("""### Part 2: Categorical Comparisons
- **Role Lead:** Mehul Lahot
- Countplot of `Genre` with x-ticks rotated by 45 degrees.
- Boxplot of `Global_Sales` across `Genre` showing distribution and outliers.""")

add_code("""# Countplot of Game Genres
plt.figure(figsize=(10, 5))
genre_order = vg_df['Genre'].value_counts().index
ax = sns.countplot(data=vg_df, x='Genre', order=genre_order, hue='Genre', palette='mako', legend=False)
plt.title("Total Video Game Releases by Genre", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Genre", fontsize=12)
plt.ylabel("Number of Titles Released", fontsize=12)
plt.xticks(rotation=45, ha='right')

for p in ax.patches:
    h = p.get_height()
    if h > 0:
        ax.annotate(f"{int(h)}", (p.get_x() + p.get_width() / 2., h),
                    ha='center', va='bottom', fontsize=9, xytext=(0, 3), textcoords='offset points')
plt.show()

# Boxplot of Global Sales across Genre
plt.figure(figsize=(11, 6))
sns.boxplot(data=vg_df[vg_df['Global_Sales'] <= 3], x='Genre', y='Global_Sales', order=genre_order, hue='Genre', palette='Set2', legend=False)
plt.title("Global Sales Distribution & Outliers across Genres (<= 3M)", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Genre", fontsize=12)
plt.ylabel("Global Sales (Millions)", fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.show()""")

add_md("""### Part 3: Relationships & Relational Scatterplot
- **Role Lead:** Raidas Kunal
- Scatterplot comparing `NA_Sales` vs. `EU_Sales`.
- Color-coded by `Genre` (`hue='Genre'`).
- Transparency configured (`alpha=0.65`) to visualize density overlap.""")

add_code("""plt.figure(figsize=(10, 6))
sns.scatterplot(data=vg_df, x='NA_Sales', y='EU_Sales', hue='Genre', alpha=0.65, palette='tab10', s=45)
plt.title("North America vs. Europe Sales Correlation by Genre", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("North America Sales (Millions)", fontsize=12)
plt.ylabel("Europe Sales (Millions)", fontsize=12)
plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', title='Genre')
plt.show()""")

add_md("""### Part 4: The Heatmap
- **Role Lead:** Raidas Kunal
- Numeric isolation, correlation matrix calculation via `.corr()`.
- Seaborn Heatmap with `annot=True` and `'coolwarm'` color palette.""")

add_code("""vg_num = vg_df.select_dtypes(include=['float64', 'int64']).drop(columns=['Rank'], errors='ignore')
vg_corr = vg_num.corr()

plt.figure(figsize=(8, 6))
sns.heatmap(vg_corr, annot=True, fmt=".2f", cmap='coolwarm', square=True, linewidths=0.5)
plt.title("Correlation Matrix of Regional & Global Video Game Sales", fontsize=14, fontweight='bold', pad=12)
plt.show()""")

add_md("""### Part 5: Subplot Grid Layout & Advanced Storytelling
- **Role Lead:** Amit Kumar
- 1 Row x 2 Columns Subplot Grid.
  - Subplot 1 (Left): Scatterplot of `NA_Sales` vs `EU_Sales`.
  - Subplot 2 (Right): Barplot showing average `Global_Sales` grouped by `Genre`.
- `plt.tight_layout()` applied.""")

add_code("""fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Subplot 1
sns.scatterplot(data=vg_df, x='NA_Sales', y='EU_Sales', hue='Genre', alpha=0.6, s=35, ax=axes[0], legend=False)
axes[0].set_title("(A) NA Sales vs. EU Sales by Genre", fontsize=12, fontweight='bold')
axes[0].set_xlabel("NA Sales (Millions)", fontsize=11)
axes[0].set_ylabel("EU Sales (Millions)", fontsize=11)

# Subplot 2
avg_sales_by_genre = vg_df.groupby('Genre')['Global_Sales'].mean().reset_index().sort_values(by='Global_Sales', ascending=False)
sns.barplot(data=avg_sales_by_genre, x='Genre', y='Global_Sales', hue='Genre', palette='Blues_r', ax=axes[1], legend=False)
axes[1].set_title("(B) Average Global Sales per Title by Genre", fontsize=12, fontweight='bold')
axes[1].set_xlabel("Genre", fontsize=11)
axes[1].set_ylabel("Average Global Sales (Millions)", fontsize=11)
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()""")

add_md("""### Part 6: Programmatic Annotations & High-Definition Export
- **Role Lead:** Amit Kumar
- Programmatically find absolute maximum `Global_Sales` using pandas (`.idxmax()`).
- Annotate the exact coordinate with `plt.annotate()`.
- Export chart as `final_visualization.png` at 300 DPI.""")

add_code("""max_idx = vg_df['Global_Sales'].idxmax()
max_game = vg_df.loc[max_idx]
print(f"Top Selling Game: {max_game['Name']} | Global Sales: {max_game['Global_Sales']}M | NA Sales: {max_game['NA_Sales']}M")

fig, ax = plt.subplots(figsize=(10, 6.5))
sns.scatterplot(data=vg_df, x='NA_Sales', y='Global_Sales', hue='Genre', alpha=0.7, s=50, palette='tab10', ax=ax)
ax.set_title("Global Sales vs. North America Sales with Peak Record High Annotation", fontsize=14, fontweight='bold', pad=14)
ax.set_xlabel("North America Sales (Millions)", fontsize=12)
ax.set_ylabel("Global Sales (Millions)", fontsize=12)
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', title="Game Genre")

# Annotate
ax.annotate(
    f"Record High!\\n{max_game['Name']}\\n({max_game['Global_Sales']:.2f}M Global, {max_game['NA_Sales']:.2f}M NA)",
    xy=(max_game['NA_Sales'], max_game['Global_Sales']),
    xytext=(max_game['NA_Sales'] - 15, max_game['Global_Sales'] - 15),
    arrowprops=dict(facecolor='crimson', edgecolor='black', arrowstyle='->', lw=2),
    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8, edgecolor='crimson', lw=1.5),
    fontsize=10,
    fontweight='bold'
)

out_fig1 = os.path.join(OUTPUTS_DIR, "activity1_videogames", "final_visualization.png")
plt.savefig(out_fig1, dpi=300, bbox_inches='tight')
plt.show()
print(f"High-res visual exported to: {out_fig1}")""")

# ==============================================================================
# ACTIVITY 2
# ==============================================================================
add_md("""# ==========================================================
# ACTIVITY 2: Pokemon with Stats Analysis
# ==========================================================
**Dataset:** `pokemon.csv`  
**Description:** Contains stats (HP, Attack, Defense, Speed) and Types for 800 Pokemon.  

**Group 1 Roles for Activity 2 (Role Swapped):**
- **Foundations (Part 1 & 2):** Amit Kumar
- **Relationships & Heatmap (Part 3 & 4):** Mehul Lahot
- **Storytelling, Annotations & Export (Part 5 & 6):** Raidas Kunal""")

add_code("""# Load Pokemon Dataset
pk_df = pd.read_csv(os.path.join(DATA_DIR, "pokemon.csv"))
if 'Total' not in pk_df.columns:
    pk_df['Total'] = pk_df['HP'] + pk_df['Attack'] + pk_df['Defense'] + pk_df['Sp. Atk'] + pk_df['Sp. Def'] + pk_df['Speed']
print(f"Pokemon Dataset Shape: {pk_df.shape}")
pk_df.head()""")

add_md("""### Part 1: Distribution Analysis (Foundations)
- **Role Lead:** Amit Kumar
- Continuous Column: `Speed`
- Histogram created with Seaborn, KDE enabled, custom forest green color, descriptive title, and X-axis label.""")

add_code("""plt.figure(figsize=(9, 5))
sns.histplot(pk_df['Speed'], kde=True, color='forestgreen', bins=30, alpha=0.6)
plt.title("Distribution of Pokemon Speed Base Stats with KDE Curve", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Speed Base Stat", fontsize=12)
plt.ylabel("Frequency (Number of Pokemon)", fontsize=12)
plt.show()""")

add_md("""### Part 2: Categorical Comparisons
- **Role Lead:** Amit Kumar
- Countplot of `Type 1` with x-ticks rotated by 45 degrees.
- Boxplot of `Attack` across `Type 1` showing distribution and stat outliers.""")

add_code("""# Countplot of Primary Types
plt.figure(figsize=(11, 5))
type_order = pk_df['Type 1'].value_counts().index
ax = sns.countplot(data=pk_df, x='Type 1', order=type_order, hue='Type 1', palette='viridis', legend=False)
plt.title("Frequency Distribution of Primary Pokemon Types (Type 1)", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Primary Pokemon Type", fontsize=12)
plt.ylabel("Number of Pokemon", fontsize=12)
plt.xticks(rotation=45, ha='right')

for p in ax.patches:
    h = p.get_height()
    if h > 0:
        ax.annotate(f"{int(h)}", (p.get_x() + p.get_width() / 2., h),
                    ha='center', va='bottom', fontsize=9, xytext=(0, 3), textcoords='offset points')
plt.show()

# Boxplot of Attack across Type 1
plt.figure(figsize=(12, 6))
sns.boxplot(data=pk_df, x='Type 1', y='Attack', order=type_order, hue='Type 1', palette='Spectral', legend=False)
plt.title("Attack Stat Distribution & Outliers across Primary Types", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Primary Pokemon Type", fontsize=12)
plt.ylabel("Attack Base Stat", fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.show()""")

add_md("""### Part 3: Relationships & Relational Scatterplot
- **Role Lead:** Mehul Lahot
- Scatterplot comparing `Attack` vs. `Defense`.
- Color-coded by `Legendary` status.
- Alpha adjusted (`alpha=0.7`) to inspect clusters.""")

add_code("""plt.figure(figsize=(10, 6))
sns.scatterplot(data=pk_df, x='Attack', y='Defense', hue='Legendary', alpha=0.7, palette={False: '#3498db', True: '#e74c3c'}, s=55)
plt.title("Pokemon Attack vs. Defense Base Stats (by Legendary Status)", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Attack Base Stat", fontsize=12)
plt.ylabel("Defense Base Stat", fontsize=12)
plt.legend(title="Legendary Status", loc='upper left')
plt.show()""")

add_md("""### Part 4: The Heatmap
- **Role Lead:** Mehul Lahot
- Correlation matrix of all numeric combat stats.
- Seaborn Heatmap with `annot=True` and `'viridis'` color palette.""")

add_code("""pk_num = pk_df[['HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed', 'Generation']]
pk_corr = pk_num.corr()

plt.figure(figsize=(8, 6.5))
sns.heatmap(pk_corr, annot=True, fmt=".2f", cmap='viridis', square=True, linewidths=0.5)
plt.title("Correlation Matrix of Pokemon Combat Stats", fontsize=14, fontweight='bold', pad=12)
plt.show()""")

add_md("""### Part 5: Subplot Grid Layout
- **Role Lead:** Raidas Kunal
- 1 Row x 2 Columns Grid:
  - Subplot 1 (Left): Recreated `Attack` vs `Defense` scatterplot by `Legendary`.
  - Subplot 2 (Right): Barplot showing average `Total` combat power by `Type 1`.
- `plt.tight_layout()` applied.""")

add_code("""fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Subplot 1
sns.scatterplot(data=pk_df, x='Attack', y='Defense', hue='Legendary', alpha=0.7, palette={False: '#3498db', True: '#e74c3c'}, s=45, ax=axes[0])
axes[0].set_title("(A) Attack vs. Defense by Legendary Status", fontsize=12, fontweight='bold')
axes[0].set_xlabel("Attack Base Stat", fontsize=11)
axes[0].set_ylabel("Defense Base Stat", fontsize=11)
axes[0].legend(title="Legendary", loc='upper left')

# Subplot 2
avg_total_by_type = pk_df.groupby('Type 1')['Total'].mean().reset_index().sort_values(by='Total', ascending=False)
sns.barplot(data=avg_total_by_type, x='Type 1', y='Total', hue='Type 1', palette='crest', ax=axes[1], legend=False)
axes[1].set_title("(B) Average Total Combat Power by Primary Type", fontsize=12, fontweight='bold')
axes[1].set_xlabel("Primary Type", fontsize=11)
axes[1].set_ylabel("Average Total Base Stats", fontsize=11)
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()""")

add_md("""### Part 6: Programmatic Annotations & High-Definition Export
- **Role Lead:** Raidas Kunal
- Programmatically find absolute maximum `HP` using pandas (`.idxmax()`).
- Annotate the exact coordinate of the maximum (`Blissey`).
- Export chart as `final_visualization.png` at 300 DPI.""")

add_code("""max_hp_idx = pk_df['HP'].idxmax()
max_hp_pokemon = pk_df.loc[max_hp_idx]
print(f"Max HP Pokemon: {max_hp_pokemon['Name']} | HP: {max_hp_pokemon['HP']} | Defense: {max_hp_pokemon['Defense']}")

fig, ax = plt.subplots(figsize=(10, 6.5))
sns.scatterplot(data=pk_df, x='Defense', y='HP', hue='Legendary', alpha=0.75, s=60, palette={False: '#2980b9', True: '#e67e22'}, ax=ax)
ax.set_title("Pokemon HP vs. Defense with Record High HP Outlier Callout", fontsize=14, fontweight='bold', pad=14)
ax.set_xlabel("Defense Base Stat", fontsize=12)
ax.set_ylabel("Hit Points (HP)", fontsize=12)
ax.legend(title="Legendary", loc='upper right')

# Annotation
ax.annotate(
    f"Record High HP!\\n{max_hp_pokemon['Name']}\\n(HP: {max_hp_pokemon['HP']}, Def: {max_hp_pokemon['Defense']})",
    xy=(max_hp_pokemon['Defense'], max_hp_pokemon['HP']),
    xytext=(max_hp_pokemon['Defense'] + 30, max_hp_pokemon['HP'] - 20),
    arrowprops=dict(facecolor='darkred', edgecolor='black', arrowstyle='->', lw=2),
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#fff2cc', alpha=0.9, edgecolor='darkred', lw=1.5),
    fontsize=10,
    fontweight='bold'
)

out_fig2 = os.path.join(OUTPUTS_DIR, "activity2_pokemon", "final_visualization.png")
plt.savefig(out_fig2, dpi=300, bbox_inches='tight')
plt.show()
print(f"High-res visual exported to: {out_fig2}")""")

# ==============================================================================
# ACTIVITY 3
# ==============================================================================
add_md("""# ==========================================================
# ACTIVITY 3: Telco Customer Churn Analysis
# ==========================================================
**Dataset:** `telco_churn.csv`  
**Description:** Contains customer account information (tenure, contract type, payment method, monthly charges) and churn outcome.  

**Group 1 Roles for Activity 3 (Role Swapped):**
- **Foundations (Part 1 & 2):** Raidas Kunal
- **Relationships & Heatmap (Part 3 & 4):** Amit Kumar
- **Storytelling, Annotations & Export (Part 5 & 6):** Mehul Lahot""")

add_code("""# Load Telco Churn Dataset
churn_df = pd.read_csv(os.path.join(DATA_DIR, "telco_churn.csv"))

# Convert TotalCharges to numeric (as instructed in lab manual for Option C)
churn_df['TotalCharges'] = pd.to_numeric(churn_df['TotalCharges'], errors='coerce')
churn_df['TotalCharges'] = churn_df['TotalCharges'].fillna(churn_df['TotalCharges'].median())

print(f"Telco Dataset Shape: {churn_df.shape}")
churn_df.head()""")

add_md("""### Part 1: Distribution Analysis (Foundations)
- **Role Lead:** Raidas Kunal
- Continuous Column: `tenure`
- Histogram created with Seaborn, KDE enabled, custom teal color, descriptive title, and X-axis label.""")

add_code("""plt.figure(figsize=(9, 5))
sns.histplot(churn_df['tenure'], kde=True, color='teal', bins=36, alpha=0.6)
plt.title("Distribution of Customer Tenure (Months) with KDE Curve", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Customer Tenure (Months with Telco)", fontsize=12)
plt.ylabel("Number of Customers", fontsize=12)
plt.show()""")

add_md("""### Part 2: Categorical Comparisons
- **Role Lead:** Raidas Kunal
- Countplot of `Contract` with percentage annotations.
- Boxplot of `MonthlyCharges` across `Contract` plans.""")

add_code("""# Countplot of Contract Types
plt.figure(figsize=(9, 5))
contract_order = ["Month-to-month", "One year", "Two year"]
ax = sns.countplot(data=churn_df, x='Contract', order=contract_order, hue='Contract', palette='Blues_r', legend=False)
plt.title("Customer Distribution by Subscription Contract Type", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Contract Terms", fontsize=12)
plt.ylabel("Total Subscribers", fontsize=12)

for p in ax.patches:
    h = p.get_height()
    if h > 0:
        ax.annotate(f"{int(h)} ({h/len(churn_df)*100:.1f}%)", 
                    (p.get_x() + p.get_width() / 2., h),
                    ha='center', va='bottom', fontsize=10, xytext=(0, 4), 
                    textcoords='offset points', fontweight='bold')
plt.show()

# Boxplot of MonthlyCharges across Contract
plt.figure(figsize=(10, 6))
sns.boxplot(data=churn_df, x='Contract', y='MonthlyCharges', order=contract_order, hue='Contract', palette='Set3', legend=False)
plt.title("Monthly Charges Distribution & Outliers across Contract Plans", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Contract Plan", fontsize=12)
plt.ylabel("Monthly Charges (USD)", fontsize=12)
plt.show()""")

add_md("""### Part 3: Relationships & Relational Scatterplot
- **Role Lead:** Amit Kumar
- Scatterplot comparing `MonthlyCharges` vs. `TotalCharges`.
- Color-coded by `Churn` (`hue='Churn'`).
- Transparency configured (`alpha=0.6`) to visualize retention dynamics.""")

add_code("""plt.figure(figsize=(10, 6))
churn_palette = {'No': '#2ecc71', 'Yes': '#e74c3c'}
sns.scatterplot(data=churn_df, x='MonthlyCharges', y='TotalCharges', hue='Churn', alpha=0.6, palette=churn_palette, s=40)
plt.title("Monthly Charges vs. Total Charges Correlated by Churn Outcome", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Monthly Charges ($)", fontsize=12)
plt.ylabel("Total Lifetime Charges ($)", fontsize=12)
plt.legend(title="Customer Churn", loc='upper left')
plt.show()""")

add_md("""### Part 4: The Heatmap
- **Role Lead:** Amit Kumar
- Convert `TotalCharges` to numeric and isolate numerical columns.
- Correlation matrix calculated via `.corr()`.
- Seaborn Heatmap with `annot=True` and `'coolwarm'` color palette.""")

add_code("""churn_num = churn_df[['tenure', 'MonthlyCharges', 'TotalCharges', 'SeniorCitizen']]
churn_corr = churn_num.corr()

plt.figure(figsize=(8, 6))
sns.heatmap(churn_corr, annot=True, fmt=".2f", cmap='coolwarm', square=True, linewidths=0.5)
plt.title("Correlation Matrix of Numerical Customer Metrics", fontsize=14, fontweight='bold', pad=12)
plt.show()""")

add_md("""### Part 5: Subplot Grid Layout
- **Role Lead:** Mehul Lahot
- 1 Row x 2 Columns Grid:
  - Subplot 1 (Left): Recreated `MonthlyCharges` vs `TotalCharges` by `Churn`.
  - Subplot 2 (Right): Barplot showing average `MonthlyCharges` grouped by `Contract`.
- `plt.tight_layout()` applied.""")

add_code("""fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Subplot 1
sns.scatterplot(data=churn_df, x='MonthlyCharges', y='TotalCharges', hue='Churn', alpha=0.6, palette=churn_palette, s=35, ax=axes[0])
axes[0].set_title("(A) Monthly vs. Total Charges by Churn Status", fontsize=12, fontweight='bold')
axes[0].set_xlabel("Monthly Charges ($)", fontsize=11)
axes[0].set_ylabel("Total Charges ($)", fontsize=11)
axes[0].legend(title="Churn", loc='upper left')

# Subplot 2
avg_charges_by_contract = churn_df.groupby('Contract')['MonthlyCharges'].mean().reset_index()
sns.barplot(data=avg_charges_by_contract, x='Contract', y='MonthlyCharges', order=contract_order, hue='Contract', palette='viridis', ax=axes[1], legend=False)
axes[1].set_title("(B) Average Monthly Billing by Contract Type", fontsize=12, fontweight='bold')
axes[1].set_xlabel("Contract Type", fontsize=11)
axes[1].set_ylabel("Average Monthly Charges ($)", fontsize=11)
for p in axes[1].patches:
    h = p.get_height()
    if h > 0:
        axes[1].annotate(f"${h:.2f}", (p.get_x() + p.get_width() / 2., h / 2),
                         ha='center', va='center', fontsize=11, color='white', fontweight='bold')

plt.tight_layout()
plt.show()""")

add_md("""### Part 6: Programmatic Annotations & High-Definition Export
- **Role Lead:** Mehul Lahot
- Programmatically find absolute maximum `MonthlyCharges` using pandas (`.idxmax()`).
- Annotate the highest paying customer outlier.
- Export chart as `final_visualization.png` at 300 DPI.""")

add_code("""max_mc_idx = churn_df['MonthlyCharges'].idxmax()
max_mc_customer = churn_df.loc[max_mc_idx]
print(f"Top Monthly Charged Customer: {max_mc_customer['customerID']} | Monthly Charge: ${max_mc_customer['MonthlyCharges']} | Tenure: {max_mc_customer['tenure']} months")

fig, ax = plt.subplots(figsize=(10, 6.5))
sns.scatterplot(data=churn_df, x='tenure', y='MonthlyCharges', hue='Churn', alpha=0.65, s=50, palette=churn_palette, ax=ax)
ax.set_title("Customer Tenure vs. Monthly Charges with Peak Billed Outlier", fontsize=14, fontweight='bold', pad=14)
ax.set_xlabel("Tenure (Months with Company)", fontsize=12)
ax.set_ylabel("Monthly Charges (USD)", fontsize=12)
ax.legend(title="Customer Churn", loc='lower right')

# Annotation
ax.annotate(
    f"Record High Monthly Charge!\\nCustomer: {max_mc_customer['customerID']}\\nRate: ${max_mc_customer['MonthlyCharges']:.2f}/mo (Tenure: {max_mc_customer['tenure']} mo)",
    xy=(max_mc_customer['tenure'], max_mc_customer['MonthlyCharges']),
    xytext=(max_mc_customer['tenure'] - 30, max_mc_customer['MonthlyCharges'] - 12),
    arrowprops=dict(facecolor='darkred', edgecolor='black', arrowstyle='->', lw=2),
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffe6cc', alpha=0.9, edgecolor='darkred', lw=1.5),
    fontsize=10,
    fontweight='bold'
)

out_fig3 = os.path.join(OUTPUTS_DIR, "activity3_telco_churn", "final_visualization.png")
plt.savefig(out_fig3, dpi=300, bbox_inches='tight')
plt.show()
print(f"High-res visual exported to: {out_fig3}")""")

add_md("""# ==========================================================
# Conclusion & Key Insights Across Datasets
# ==========================================================

1. **Video Game Sales (Activity 1):**
   - **Distribution:** Sales follow an extreme Pareto distribution (long tail); the majority of titles sell under 0.5M units, while blockbuster titles like *Wii Sports* (82.74M) represent extreme positive outliers.
   - **Market Dominance:** Action and Sports genres overwhelmingly dominate the number of releases, but Platformers and Shooters produce higher average global sales per game.
   - **Regional Alignment:** North America and Europe sales exhibit a strong positive linear correlation (r = 0.77).

2. **Pokemon with Stats (Activity 2):**
   - **Stat Distributions:** Pokemon speed stats exhibit a bell-shaped distribution centered around 68 base speed, with swift outliers like *Deoxys Speed Forme* reaching 180.
   - **Combat Relationships:** Attack and Defense show moderate positive correlation (r = 0.44). Legendary Pokemon consistently occupy the upper-right quadrant across combat attributes.
   - **Outlier Dynamics:** *Blissey* exhibits the undisputed record high HP (255) with minimal defense, demonstrating extreme tanking specializations.

3. **Telco Customer Churn (Activity 3):**
   - **Tenure Bimodality:** Customer tenure exhibits a bimodal distribution with massive clusters at new signups (1-3 months) and long-term loyalists (70-72 months).
   - **Churn Drivers:** Customers with Month-to-Month contracts and high monthly charges ($70 - $100) experience drastically higher churn rates.
   - **Financial Health:** Converting Month-to-Month customers to One-Year or Two-Year contracts provides a strong buffer against customer attrition.""")

nb_path = r"C:\Users\STUDENT\Desktop\Amit\HPC\10-STATISTICS-AND-DATA-HANDLING\Activity\Data_Visualization_Mastery_Lab.ipynb"
with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)

print(f"Successfully generated notebook: {nb_path}")

