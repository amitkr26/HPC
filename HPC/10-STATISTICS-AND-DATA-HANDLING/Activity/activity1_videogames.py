"""
Activity 1: Video Game Sales Data Visualization Mastery Lab
Dataset: Video Game Sales (vgsales.csv)
Group 1 Members:
  - Mehul Lahot (Role: Single Variables and Categories - Foundations)
  - Raidas Kunal (Role: Relationships and Correlations)
  - Amit Kumar (Role: Advanced Storytelling and Export)
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
DATA_PATH = os.path.join(BASE_DIR, "data", "vgsales.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "activity1_videogames")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load Dataset
print("[Activity 1] Loading Video Game Sales dataset...")
df = pd.read_csv(DATA_PATH)
print(f"Dataset Shape: {df.shape}")
print(df.head())

# ==============================================================================
# GROUP 1: Single Variables and Categories (Foundations)
# Lead: Mehul Lahot
# ==============================================================================
print("\n--- Running Group 1: Foundations ---")

# Part 1: Distribution Analysis
# Continuous column: Global_Sales
plt.figure(figsize=(9, 5))
# To clearly observe distribution given extreme long-tail outliers (Wii Sports = 82M),
# we visualize sales up to 5M with KDE, plus an inset / note
sns.histplot(df[df['Global_Sales'] <= 5]['Global_Sales'], kde=True, color='purple', bins=40, alpha=0.6)
plt.title("Distribution of Global Sales (<= 5M Copies) with KDE Trendline", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Global Sales (in Millions)", fontsize=12)
plt.ylabel("Number of Video Games", fontsize=12)
hist_path = os.path.join(OUTPUT_DIR, "part1_distribution_histogram.png")
plt.savefig(hist_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {hist_path}")

# Part 2: Categorical Comparisons
# 1 & 2: Countplot of Genre
plt.figure(figsize=(10, 5))
genre_order = df['Genre'].value_counts().index
ax = sns.countplot(data=df, x='Genre', order=genre_order, palette='mako')
plt.title("Number of Video Games Released per Genre", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Game Genre", fontsize=12)
plt.ylabel("Total Releases", fontsize=12)
plt.xticks(rotation=45, ha='right', fontsize=10)
# Add value labels on bars
for p in ax.patches:
    ax.annotate(f"{int(p.get_height())}", 
                (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='bottom', fontsize=9, xytext=(0, 3), 
                textcoords='offset points')
countplot_path = os.path.join(OUTPUT_DIR, "part2_genre_countplot.png")
plt.savefig(countplot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {countplot_path}")

# 4: Boxplot showing continuous column across categorical
# Continuous: Global_Sales (<= 3M for outlier visibility across boxes), Categorical: Genre
plt.figure(figsize=(11, 6))
sns.boxplot(data=df[df['Global_Sales'] <= 3], x='Genre', y='Global_Sales', order=genre_order, palette='Set2')
plt.title("Global Sales Distribution & Outliers across Genres (<= 3M)", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Genre", fontsize=12)
plt.ylabel("Global Sales (Millions)", fontsize=12)
plt.xticks(rotation=45, ha='right', fontsize=10)
boxplot_path = os.path.join(OUTPUT_DIR, "part2_genre_sales_boxplot.png")
plt.savefig(boxplot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {boxplot_path}")

# ==============================================================================
# GROUP 2: Relationships and Correlations
# Lead: Raidas Kunal
# ==============================================================================
print("\n--- Running Group 2: Relationships and Correlations ---")

# Part 1: Relational Scatterplot
# NA_Sales vs EU_Sales with hue='Genre', alpha=0.65
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='NA_Sales', y='EU_Sales', hue='Genre', alpha=0.65, palette='tab10', s=45)
plt.title("North America vs. Europe Sales Correlation by Genre", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("North America Sales (Millions)", fontsize=12)
plt.ylabel("Europe Sales (Millions)", fontsize=12)
plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, title='Genre')
scatter_path = os.path.join(OUTPUT_DIR, "part3_na_vs_eu_sales_scatter.png")
plt.savefig(scatter_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {scatter_path}")

# Part 2: The Heatmap
# Isolate numeric columns & calculate correlation
numeric_cols = df.select_dtypes(include=['float64', 'int64']).drop(columns=['Rank'], errors='ignore')
corr_matrix = numeric_cols.corr()
plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='coolwarm', cbar=True, square=True, linewidths=0.5)
plt.title("Correlation Matrix of Regional & Global Video Game Sales", fontsize=14, fontweight='bold', pad=12)
heatmap_path = os.path.join(OUTPUT_DIR, "part4_sales_correlation_heatmap.png")
plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {heatmap_path}")

# ==============================================================================
# GROUP 3: Advanced Storytelling and Export
# Lead: Amit Kumar
# ==============================================================================
print("\n--- Running Group 3: Storytelling and Export ---")

# Part 1: Subplot Grid Layout
# 1 row, 2 columns (14x6 inches)
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Subplot 1 (Left): Recreate Scatterplot from Part 3
sns.scatterplot(data=df, x='NA_Sales', y='EU_Sales', hue='Genre', alpha=0.6, s=35, ax=axes[0], legend=False)
axes[0].set_title("(A) NA Sales vs. EU Sales by Genre", fontsize=12, fontweight='bold')
axes[0].set_xlabel("NA Sales (Millions)", fontsize=11)
axes[0].set_ylabel("EU Sales (Millions)", fontsize=11)

# Subplot 2 (Right): Barplot showing average Global Sales grouped by Genre
avg_sales_by_genre = df.groupby('Genre')['Global_Sales'].mean().reset_index().sort_values(by='Global_Sales', ascending=False)
sns.barplot(data=avg_sales_by_genre, x='Genre', y='Global_Sales', palette='Blues_r', ax=axes[1])
axes[1].set_title("(B) Average Global Sales per Title by Genre", fontsize=12, fontweight='bold')
axes[1].set_xlabel("Genre", fontsize=11)
axes[1].set_ylabel("Average Global Sales (Millions)", fontsize=11)
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
subplot_path = os.path.join(OUTPUT_DIR, "part5_subplot_grid.png")
plt.savefig(subplot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {subplot_path}")

# Part 2 & Part 3: Annotations, Polish and High-Res Final Export
# Programmatically find absolute maximum Global Sales
max_idx = df['Global_Sales'].idxmax()
max_game = df.loc[max_idx]
print(f"Absolute Maximum Game: {max_game['Name']} with {max_game['Global_Sales']}M sales")

fig, ax = plt.subplots(figsize=(10, 6.5))
sns.scatterplot(data=df, x='NA_Sales', y='Global_Sales', hue='Genre', alpha=0.7, s=50, palette='tab10', ax=ax)
ax.set_title("Global Sales vs. North America Sales with Peak Record High Annotation", fontsize=14, fontweight='bold', pad=14)
ax.set_xlabel("North America Sales (Millions)", fontsize=12)
ax.set_ylabel("Global Sales (Millions)", fontsize=12)
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', title="Game Genre")

# Annotation of Record High
ax.annotate(
    f"Record High!\n{max_game['Name']}\n({max_game['Global_Sales']:.2f}M Global, {max_game['NA_Sales']:.2f}M NA)",
    xy=(max_game['NA_Sales'], max_game['Global_Sales']),
    xytext=(max_game['NA_Sales'] - 15, max_game['Global_Sales'] - 15),
    arrowprops=dict(facecolor='crimson', edgecolor='black', arrowstyle='->', lw=2),
    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8, edgecolor='crimson', lw=1.5),
    fontsize=10,
    fontweight='bold'
)

final_path = os.path.join(OUTPUT_DIR, "final_visualization.png")
plt.savefig(final_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved Final Visual: {final_path} (300 DPI)")
print("[Activity 1] Successfully Completed!")

