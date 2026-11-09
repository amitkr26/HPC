"""
Activity 2: Pokemon with Stats Data Visualization Mastery Lab
Dataset: Pokemon with Stats (pokemon.csv)
Group 1 Members:
  - Amit Kumar (Role: Single Variables and Categories - Foundations)
  - Mehul Lahot (Role: Relationships and Correlations)
  - Raidas Kunal (Role: Advanced Storytelling and Export)
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
DATA_PATH = os.path.join(BASE_DIR, "data", "pokemon.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "activity2_pokemon")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load Dataset
print("[Activity 2] Loading Pokemon with Stats dataset...")
df = pd.read_csv(DATA_PATH)
# Ensure Total stat is calculated if not present
if 'Total' not in df.columns:
    df['Total'] = df['HP'] + df['Attack'] + df['Defense'] + df['Sp. Atk'] + df['Sp. Def'] + df['Speed']

print(f"Dataset Shape: {df.shape}")
print(df.head())

# ==============================================================================
# GROUP 1: Single Variables and Categories (Foundations)
# Lead: Amit Kumar
# ==============================================================================
print("\n--- Running Group 1: Foundations (Lead: Amit Kumar) ---")

# Part 1: Distribution Analysis
# Continuous column: Speed (as specified in PDF)
plt.figure(figsize=(9, 5))
sns.histplot(df['Speed'], kde=True, color='forestgreen', bins=30, alpha=0.6)
plt.title("Distribution of Pokemon Speed Stats with KDE Trendline", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Speed Base Stat", fontsize=12)
plt.ylabel("Frequency (Number of Pokemon)", fontsize=12)
hist_path = os.path.join(OUTPUT_DIR, "part1_distribution_histogram.png")
plt.savefig(hist_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {hist_path}")

# Part 2: Categorical Comparisons
# 1 & 2: Countplot of Type 1
plt.figure(figsize=(11, 5))
type_order = df['Type 1'].value_counts().index
ax = sns.countplot(data=df, x='Type 1', order=type_order, hue='Type 1', palette='viridis', legend=False)
plt.title("Frequency Distribution of Primary Pokemon Types (Type 1)", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Primary Pokemon Type", fontsize=12)
plt.ylabel("Number of Pokemon", fontsize=12)
plt.xticks(rotation=45, ha='right', fontsize=10)
for p in ax.patches:
    h = p.get_height()
    if h > 0:
        ax.annotate(f"{int(h)}", 
                    (p.get_x() + p.get_width() / 2., h),
                    ha='center', va='bottom', fontsize=9, xytext=(0, 3), 
                    textcoords='offset points')
countplot_path = os.path.join(OUTPUT_DIR, "part2_type1_countplot.png")
plt.savefig(countplot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {countplot_path}")

# 4: Boxplot showing continuous column across categorical
# Continuous: Attack, Categorical: Type 1
plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x='Type 1', y='Attack', order=type_order, hue='Type 1', palette='Spectral', legend=False)
plt.title("Attack Stat Distribution & Outliers across Primary Types", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Primary Pokemon Type", fontsize=12)
plt.ylabel("Attack Base Stat", fontsize=12)
plt.xticks(rotation=45, ha='right', fontsize=10)
boxplot_path = os.path.join(OUTPUT_DIR, "part2_type_attack_boxplot.png")
plt.savefig(boxplot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {boxplot_path}")

# ==============================================================================
# GROUP 2: Relationships and Correlations
# Lead: Mehul Lahot
# ==============================================================================
print("\n--- Running Group 2: Relationships and Correlations (Lead: Mehul Lahot) ---")

# Part 1: Relational Scatterplot
# Attack vs Defense with hue='Legendary', alpha=0.7
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='Attack', y='Defense', hue='Legendary', alpha=0.7, palette={False: '#3498db', True: '#e74c3c'}, s=55)
plt.title("Pokemon Attack vs. Defense Base Stats (by Legendary Status)", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Attack Base Stat", fontsize=12)
plt.ylabel("Defense Base Stat", fontsize=12)
plt.legend(title="Legendary Status", loc='upper left')
scatter_path = os.path.join(OUTPUT_DIR, "part3_attack_vs_defense_scatter.png")
plt.savefig(scatter_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {scatter_path}")

# Part 2: The Heatmap
# Isolate numeric columns & calculate correlation
numeric_cols = df[['HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed', 'Generation']]
corr_matrix = numeric_cols.corr()
plt.figure(figsize=(8, 6.5))
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='viridis', cbar=True, square=True, linewidths=0.5)
plt.title("Correlation Matrix of Pokemon Combat Stats", fontsize=14, fontweight='bold', pad=12)
heatmap_path = os.path.join(OUTPUT_DIR, "part4_stats_correlation_heatmap.png")
plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {heatmap_path}")

# ==============================================================================
# GROUP 3: Advanced Storytelling and Export
# Lead: Raidas Kunal
# ==============================================================================
print("\n--- Running Group 3: Storytelling and Export (Lead: Raidas Kunal) ---")

# Part 1: Subplot Grid Layout
# 1 row, 2 columns (14x6 inches)
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Subplot 1 (Left): Recreate Scatterplot from Part 3
sns.scatterplot(data=df, x='Attack', y='Defense', hue='Legendary', alpha=0.7, palette={False: '#3498db', True: '#e74c3c'}, s=45, ax=axes[0])
axes[0].set_title("(A) Attack vs. Defense by Legendary Status", fontsize=12, fontweight='bold')
axes[0].set_xlabel("Attack Base Stat", fontsize=11)
axes[0].set_ylabel("Defense Base Stat", fontsize=11)
axes[0].legend(title="Legendary", loc='upper left')

# Subplot 2 (Right): Barplot showing average Total Stat by Type 1
avg_total_by_type = df.groupby('Type 1')['Total'].mean().reset_index().sort_values(by='Total', ascending=False)
sns.barplot(data=avg_total_by_type, x='Type 1', y='Total', hue='Type 1', palette='crest', ax=axes[1], legend=False)
axes[1].set_title("(B) Average Total Combat Power by Primary Type", fontsize=12, fontweight='bold')
axes[1].set_xlabel("Primary Type", fontsize=11)
axes[1].set_ylabel("Average Total Base Stats", fontsize=11)
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
subplot_path = os.path.join(OUTPUT_DIR, "part5_subplot_grid.png")
plt.savefig(subplot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {subplot_path}")

# Part 2 & Part 3: Annotations, Polish and High-Res Final Export
# Programmatically find absolute maximum HP
max_hp_idx = df['HP'].idxmax()
max_hp_pokemon = df.loc[max_hp_idx]
print(f"Absolute Maximum HP Pokemon: {max_hp_pokemon['Name']} with {max_hp_pokemon['HP']} HP")

fig, ax = plt.subplots(figsize=(10, 6.5))
sns.scatterplot(data=df, x='Defense', y='HP', hue='Legendary', alpha=0.75, s=60, palette={False: '#2980b9', True: '#e67e22'}, ax=ax)
ax.set_title("Pokemon HP vs. Defense with Record High HP Outlier Callout", fontsize=14, fontweight='bold', pad=14)
ax.set_xlabel("Defense Base Stat", fontsize=12)
ax.set_ylabel("Hit Points (HP)", fontsize=12)
ax.legend(title="Legendary", loc='upper right')

# Annotation of Record High
ax.annotate(
    f"Record High HP!\n{max_hp_pokemon['Name']}\n(HP: {max_hp_pokemon['HP']}, Def: {max_hp_pokemon['Defense']})",
    xy=(max_hp_pokemon['Defense'], max_hp_pokemon['HP']),
    xytext=(max_hp_pokemon['Defense'] + 30, max_hp_pokemon['HP'] - 20),
    arrowprops=dict(facecolor='darkred', edgecolor='black', arrowstyle='->', lw=2),
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#fff2cc', alpha=0.9, edgecolor='darkred', lw=1.5),
    fontsize=10,
    fontweight='bold'
)

final_path = os.path.join(OUTPUT_DIR, "final_visualization.png")
plt.savefig(final_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved Final Visual: {final_path} (300 DPI)")
print("[Activity 2] Successfully Completed!")

