# Data Visualization Mastery Lab

**Course Module:** Module 10: Statistics and Data Handling  
**Primary Author:** Amit Kumar  
**Group Affiliation:** Group 1  
**Group Members:**
- Mehul Lahot
- Raidas Kunal
- Amit Kumar

---

## 👥 Group 1 Role Rotation Matrix Across Activities

In strict compliance with the lab instructions (*"Every Group will work on all three datasets. Each member of group will change his/her role for each activity"*), leadership roles were systematically rotated across all 3 activities:

| Activity | Dataset | Role 1: Foundations (Distribution & Countplot) | Role 2: Relationships & Correlations (Scatter & Heatmap) | Role 3: Advanced Storytelling & Export (Subplots, Callout & 300 DPI) |
| :--- | :--- | :--- | :--- | :--- |
| **Activity 1** | **Video Game Sales** (`vgsales.csv`) | **Mehul Lahot** | **Raidas Kunal** | **Amit Kumar (Lead)** |
| **Activity 2** | **Pokemon with Stats** (`pokemon.csv`) | **Amit Kumar (Lead)** | **Mehul Lahot** | **Raidas Kunal** |
| **Activity 3** | **Telco Customer Churn** (`telco_churn.csv`) | **Raidas Kunal** | **Amit Kumar (Lead)** | **Mehul Lahot** |

---

## 📁 Repository Structure

```
Activity/
│
├── data/                                      # Benchmark Datasets (Exact Kaggle Schemas)
│   ├── vgsales.csv                            # Video Game Sales (16,598 rows x 11 cols)
│   ├── pokemon.csv                            # Pokemon with Stats (800 rows x 13 cols)
│   └── telco_churn.csv                        # Telco Customer Churn (7,043 rows x 21 cols)
│
├── outputs/                                   # High-Definition Visualizations (300 DPI)
│   ├── activity1_videogames/
│   │   ├── part1_distribution_histogram.png   # Global_Sales distribution with KDE curve (purple)
│   │   ├── part2_genre_countplot.png          # Releases by Genre with 45° rotated labels
│   │   ├── part2_genre_sales_boxplot.png      # Global Sales spread and outliers across genres
│   │   ├── part3_na_vs_eu_sales_scatter.png   # NA vs EU Sales scatterplot with genre hue (alpha=0.65)
│   │   ├── part4_sales_correlation_heatmap.png# Pearson correlation matrix (coolwarm palette)
│   │   ├── part5_subplot_grid.png             # 1x2 Subplot Dashboard (Scatter + Avg Barplot)
│   │   └── final_visualization.png            # Programmatic peak outlier callout (Wii Sports 82.74M)
│   │
│   ├── activity2_pokemon/
│   │   ├── part1_distribution_histogram.png   # Speed distribution with KDE curve (forest green)
│   │   ├── part2_type1_countplot.png          # Primary Types (Type 1) countplot
│   │   ├── part2_type_attack_boxplot.png      # Attack stat spread and outliers across primary types
│   │   ├── part3_attack_vs_defense_scatter.png# Attack vs Defense by Legendary status (alpha=0.7)
│   │   ├── part4_stats_correlation_heatmap.png# Combat stats correlation matrix (viridis palette)
│   │   ├── part5_subplot_grid.png             # 1x2 Subplot Dashboard (Scatter + Avg Total Barplot)
│   │   └── final_visualization.png            # Programmatic peak HP outlier callout (Blissey 255 HP)
│   │
│   └── activity3_telco_churn/
│       ├── part1_distribution_histogram.png   # Customer tenure distribution with KDE curve (teal)
│       ├── part2_contract_countplot.png       # Contract types with subscriber share percentage
│       ├── part2_contract_charges_boxplot.png # MonthlyCharges spread and outliers across contracts
│       ├── part3_charges_scatter.png          # Monthly vs Total Charges by Churn (alpha=0.6)
│       ├── part4_churn_correlation_heatmap.png# Numerical metrics correlation matrix (coolwarm)
│       ├── part5_subplot_grid.png             # 1x2 Subplot Dashboard (Scatter + Avg Monthly Barplot)
│       └── final_visualization.png            # Programmatic peak billing callout ($118.75/mo)
│
├── activity1_videogames.py                    # Complete standalone executable for Activity 1
├── activity2_pokemon.py                       # Complete standalone executable for Activity 2
├── activity3_telco_churn.py                   # Complete standalone executable for Activity 3
├── run_all_activities.py                      # Master automated runner for all 3 activities
├── Data_Visualization_Mastery_Lab.ipynb       # Interactive Jupyter Notebook with all cells
└── Amit_Kumar_Data_Visualization_Mastery_Lab.docx # Professional 10.6MB report with all charts embedded
```

---

## 🚀 Execution Instructions

Run all activities sequentially using the master script:
```bash
python run_all_activities.py
```

Or run any activity individually:
```bash
python activity1_videogames.py
python activity2_pokemon.py
python activity3_telco_churn.py
```

To regenerate the Jupyter Notebook or the final Word report:
```bash
python generate_notebook.py
python generate_docx_report.py
```

---

## 📊 Summary of Analytical Findings

### 1. Activity 1: Video Game Sales
- **Right-Skewed Distribution:** Over 75% of games sell under 0.47M copies. Blockbuster titles form an extreme long-tail extension up to 82.74M.
- **Genre Volume vs. Profitability:** Action (3,316) and Sports (2,346) produce the highest volume of titles, but Platformers achieve the highest average sales per title (0.94M).
- **Regional Synergy:** NA and EU sales have a strong positive correlation ($r = 0.77$). NA sales are the primary driver of global revenue ($r = 0.94$).
- **Peak Outlier:** *Wii Sports* holds the all-time record high with **82.74M copies** (41.49M NA, 29.02M EU).

### 2. Activity 2: Pokemon with Stats
- **Normal Stat Distribution:** Speed stats follow a Gaussian distribution centered at $\mu = 68.28$ ($\sigma = 29.06$), with *Deoxys Speed Forme* reaching the record speed of 180.
- **Physical vs. Special Balance:** Attack and Defense exhibit moderate positive correlation ($r = 0.44$). Legendary Pokemon strictly dominate the upper-right combat quadrant.
- **Record Outlier:** *Blissey* achieves the undisputed record high HP of **255** (with a minimal Defense of 10), representing an extreme specialized tank archetype.

### 3. Activity 3: Telco Customer Churn
- **Bimodal Tenure:** Extreme clusters exist at months 1–3 (high risk early dropouts) and months 70–72 (long-term brand loyalists).
- **Churn Determinants:** 55% of customers are on Month-to-Month contracts. Customers with short tenure paying high monthly rates ($70–$110) represent the highest churn density.
- **Peak Outlier:** Customer `7569-NMZYQ` pays the record highest monthly billing rate at **$118.75/month** on a Two-Year contract.

