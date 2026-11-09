"""
Script to generate the comprehensive Word Report:
Amit_Kumar_Data_Visualization_Mastery_Lab.docx
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
DOCX_PATH = os.path.join(BASE_DIR, "Amit_Kumar_Data_Visualization_Mastery_Lab.docx")

doc = docx.Document()

# Page Margins: 0.8 in
sections = doc.sections
for section in sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

# Helper function to style table headers
def style_table_header(row, col_colors):
    for idx, cell in enumerate(row.cells):
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{col_colors}"/>')
        cell._tc.get_or_add_tcPr().append(shading)
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(10)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_callout(doc, text, title="Insight"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F0F4F8"/>')
    cell._tc.get_or_add_tcPr().append(shading)
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    r1 = p.add_run(f"📌 {title}: ")
    r1.bold = True
    r1.font.color.rgb = RGBColor(24, 76, 120)
    r1.font.size = Pt(10)
    r2 = p.add_run(text)
    r2.font.size = Pt(9.5)
    r2.font.color.rgb = RGBColor(40, 40, 40)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_code_snippet(doc, code_str):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8F9FA"/>')
    cell._tc.get_or_add_tcPr().append(shading)
    set_cell_margins(cell, top=100, bottom=100, left=160, right=160)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(code_str.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(33, 37, 41)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# ==============================================================================
# TITLE & COVER DETAILS
# ==============================================================================
title_p = doc.add_paragraph()
title_p.paragraph_format.space_before = Pt(10)
title_p.paragraph_format.space_after = Pt(4)
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
t_run = title_p.add_run("Data Visualization Mastery Lab")
t_run.font.size = Pt(24)
t_run.font.bold = True
t_run.font.color.rgb = RGBColor(20, 50, 90)

sub_p = doc.add_paragraph()
sub_p.paragraph_format.space_after = Pt(14)
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
s_run = sub_p.add_run("Comprehensive Exploratory Data Analysis & Visualization Across 3 Benchmark Datasets")
s_run.font.size = Pt(12)
s_run.font.italic = True
s_run.font.color.rgb = RGBColor(90, 100, 110)

# Student Details Box
meta_table = doc.add_table(rows=4, cols=2)
meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
meta_data = [
    ("Course & Module:", "Advanced Certificate Course - HPC (AI) | Module 10: Statistics & Data Handling"),
    ("Primary Author:", "Amit Kumar"),
    ("Group Affiliation:", "Group 1 (Mehul Lahot, Raidas Kunal, Amit Kumar)"),
    ("Execution Environment:", "Python 3.13 | Pandas, Seaborn, Matplotlib, NumPy")
]
for row_idx, (k, v) in enumerate(meta_data):
    row = meta_table.rows[row_idx]
    k_cell, v_cell = row.cells[0], row.cells[1]
    k_cell.text = k
    v_cell.text = v
    k_cell.paragraphs[0].runs[0].font.bold = True
    k_cell.paragraphs[0].runs[0].font.size = Pt(10)
    v_cell.paragraphs[0].runs[0].font.size = Pt(10)
    k_cell.width = Inches(2.2)
    v_cell.width = Inches(4.6)
    set_cell_margins(k_cell, top=60, bottom=60, left=100, right=100)
    set_cell_margins(v_cell, top=60, bottom=60, left=100, right=100)
    for c in (k_cell, v_cell):
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F4F6F9"/>')
        c._tc.get_or_add_tcPr().append(shading)

doc.add_paragraph().paragraph_format.space_after = Pt(10)

# Role Rotation Matrix
h1 = doc.add_heading("Group 1 Role Rotation Matrix", level=1)
h1.runs[0].font.color.rgb = RGBColor(20, 50, 90)

desc_p = doc.add_paragraph(
    "In accordance with the laboratory guidelines ('Every Group will work on all three datasets; "
    "each member of the group will change his/her role for each activity'), the team distributed and "
    "rotated leadership roles across the three distinct functional competencies:"
)
desc_p.runs[0].font.size = Pt(10.5)

rot_table = doc.add_table(rows=4, cols=4)
rot_table.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ["Activity & Dataset", "Foundations (Distr & Count)", "Relationships & Correlation", "Storytelling & Export"]
for c_idx, h_text in enumerate(headers):
    rot_table.rows[0].cells[c_idx].text = h_text
style_table_header(rot_table.rows[0], "1F497D")

matrix_rows = [
    ("Activity 1: Video Game Sales", "Mehul Lahot", "Raidas Kunal", "Amit Kumar (Lead)"),
    ("Activity 2: Pokemon with Stats", "Amit Kumar (Lead)", "Mehul Lahot", "Raidas Kunal"),
    ("Activity 3: Telco Customer Churn", "Raidas Kunal", "Amit Kumar (Lead)", "Mehul Lahot")
]

for r_idx, r_vals in enumerate(matrix_rows, start=1):
    row = rot_table.rows[r_idx]
    for c_idx, val in enumerate(r_vals):
        cell = row.cells[c_idx]
        cell.text = val
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
        set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
        p.runs[0].font.size = Pt(9.5)
        if "Amit Kumar" in val:
            p.runs[0].font.bold = True
            p.runs[0].font.color.rgb = RGBColor(180, 50, 20)

doc.add_paragraph().paragraph_format.space_after = Pt(14)

# ==============================================================================
# SECTION: ACTIVITY 1 - VIDEO GAME SALES
# ==============================================================================
h_act1 = doc.add_heading("Activity 1: Video Game Sales Analysis", level=1)
h_act1.runs[0].font.color.rgb = RGBColor(20, 50, 90)

p1 = doc.add_paragraph(
    "Dataset: vgsales.csv (16,598 records, 11 columns)\n"
    "Focus: Regional vs. global sales, genre distribution, platform performance, and extreme sales outliers."
)
p1.runs[0].font.size = Pt(10)

# Part 1
h2 = doc.add_heading("Part 1: Distribution Analysis (Global_Sales) — Lead: Mehul Lahot", level=2)
h2.runs[0].font.color.rgb = RGBColor(40, 80, 130)
doc.add_paragraph(
    "Objective: Analyze the single variable distribution of continuous sales metrics using a Seaborn Histogram "
    "overlaid with a Kernel Density Estimate (KDE) curve in a custom purple palette."
)
add_code_snippet(doc, """plt.figure(figsize=(9, 5))
sns.histplot(vg_df[vg_df['Global_Sales'] <= 5]['Global_Sales'], kde=True, color='purple', bins=40, alpha=0.6)
plt.title("Distribution of Global Sales (<= 5M Copies) with KDE Curve", fontsize=14, fontweight='bold')
plt.xlabel("Global Sales (in Millions)"); plt.ylabel("Number of Video Games")
plt.savefig("part1_distribution_histogram.png", dpi=300, bbox_inches='tight')""")

fig1_p = os.path.join(OUTPUTS_DIR, "activity1_videogames", "part1_distribution_histogram.png")
if os.path.exists(fig1_p):
    doc.add_picture(fig1_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_callout(doc, "Global sales exhibit a severe positive (right-skewed) Pareto distribution. Over 75% of games achieve under 0.5M copies, while blockbuster titles form an extreme long-tail extension up to 82.74M.", "Distribution Insight")

# Part 2
h2 = doc.add_heading("Part 2: Categorical Comparisons (Genre) — Lead: Mehul Lahot", level=2)
h2.runs[0].font.color.rgb = RGBColor(40, 80, 130)
doc.add_paragraph(
    "Objective: Determine dominating categories via a Countplot with 45-degree rotated x-ticks, and examine "
    "spread and outliers using a Boxplot of Global Sales across game genres."
)
add_code_snippet(doc, """# Countplot with rotated ticks
sns.countplot(data=vg_df, x='Genre', order=genre_order, palette='mako')
plt.xticks(rotation=45, ha='right')

# Boxplot of continuous Global_Sales across categorical Genre
sns.boxplot(data=vg_df[vg_df['Global_Sales'] <= 3], x='Genre', y='Global_Sales', order=genre_order, palette='Set2')
plt.xticks(rotation=45, ha='right')""")

c1_p = os.path.join(OUTPUTS_DIR, "activity1_videogames", "part2_genre_countplot.png")
b1_p = os.path.join(OUTPUTS_DIR, "activity1_videogames", "part2_genre_sales_boxplot.png")
if os.path.exists(c1_p):
    doc.add_picture(c1_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
if os.path.exists(b1_p):
    doc.add_picture(b1_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_callout(doc, "Action (3,316 titles) and Sports (2,346 titles) represent the highest volume of game releases. However, the boxplot indicates that Platform and Shooter titles maintain significantly higher median sales and greater upper-quartile spreads.", "Categorical Comparison Insight")

# Part 3 & 4
h2 = doc.add_heading("Part 3 & 4: Relational Scatterplot & Correlation Heatmap — Lead: Raidas Kunal", level=2)
h2.runs[0].font.color.rgb = RGBColor(40, 80, 130)
doc.add_paragraph(
    "Objective: Explore inter-column relationships using a scatterplot with hue and alpha transparency, and compute "
    "the mathematical Pearson correlation matrix rendered through an annotated Seaborn heatmap."
)
add_code_snippet(doc, """# Scatterplot with hue and alpha
sns.scatterplot(data=vg_df, x='NA_Sales', y='EU_Sales', hue='Genre', alpha=0.65, palette='tab10', s=45)

# Correlation Heatmap
sns.heatmap(vg_df[['NA_Sales', 'EU_Sales', 'JP_Sales', 'Other_Sales', 'Global_Sales']].corr(),
            annot=True, fmt='.2f', cmap='coolwarm', square=True)""")

s1_p = os.path.join(OUTPUTS_DIR, "activity1_videogames", "part3_na_vs_eu_sales_scatter.png")
h1_p = os.path.join(OUTPUTS_DIR, "activity1_videogames", "part4_sales_correlation_heatmap.png")
if os.path.exists(s1_p):
    doc.add_picture(s1_p, width=Inches(5.6))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
if os.path.exists(h1_p):
    doc.add_picture(h1_p, width=Inches(5.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_callout(doc, "North American and European sales have a strong positive correlation (r = 0.77). Global sales are overwhelmingly driven by NA sales (r = 0.94) and EU sales (r = 0.90), whereas Japanese sales exhibit a unique regional taste profile (r = 0.62).", "Correlation Finding")

# Part 5 & 6
h2 = doc.add_heading("Part 5, 6 & 7: Subplot Grid, Programmatic Annotation & 300 DPI Export — Lead: Amit Kumar", level=2)
h2.runs[0].font.color.rgb = RGBColor(40, 80, 130)
doc.add_paragraph(
    "Objective: Build an executive multi-panel dashboard combining scatterplot and grouped average barplot in a 1x2 grid, "
    "programmatically detect the all-time peak selling title via pandas, place a targeted callout annotation, and export in 300 DPI."
)
add_code_snippet(doc, """# Programmatic coordinate detection of maximum Global_Sales
max_idx = vg_df['Global_Sales'].idxmax()
max_game = vg_df.loc[max_idx]

# Subplot Grid
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
sns.scatterplot(..., ax=axes[0])
sns.barplot(..., ax=axes[1])
plt.tight_layout()

# Annotation
ax.annotate(f"Record High!\\n{max_game['Name']}\\n({max_game['Global_Sales']:.2f}M Copies)",
            xy=(max_game['NA_Sales'], max_game['Global_Sales']),
            xytext=(max_game['NA_Sales'] - 15, max_game['Global_Sales'] - 15),
            arrowprops=dict(facecolor='crimson', arrowstyle='->', lw=2),
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8))
plt.savefig("final_visualization.png", dpi=300, bbox_inches='tight')""")

sub1_p = os.path.join(OUTPUTS_DIR, "activity1_videogames", "part5_subplot_grid.png")
fin1_p = os.path.join(OUTPUTS_DIR, "activity1_videogames", "final_visualization.png")
if os.path.exists(sub1_p):
    doc.add_picture(sub1_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
if os.path.exists(fin1_p):
    doc.add_picture(fin1_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_callout(doc, "Wii Sports stands as the undisputed record holder with 82.74M global sales (41.49M NA, 29.02M EU). Platform games achieve the highest average global sales per released game (0.94M), surpassing Action titles which average 0.53M.", "Storytelling Highlight")

# ==============================================================================
# SECTION: ACTIVITY 2 - POKEMON WITH STATS
# ==============================================================================
doc.add_page_break()
h_act2 = doc.add_heading("Activity 2: Pokemon with Stats Analysis", level=1)
h_act2.runs[0].font.color.rgb = RGBColor(20, 50, 90)

p2 = doc.add_paragraph(
    "Dataset: pokemon.csv (800 records, 13 columns)\n"
    "Focus: Combat base stats (HP, Attack, Defense, Speed), Type classifications, and Legendary tier disparities."
)
p2.runs[0].font.size = Pt(10)

# Part 1
h2 = doc.add_heading("Part 1: Distribution Analysis (Speed Base Stat) — Lead: Amit Kumar", level=2)
h2.runs[0].font.color.rgb = RGBColor(40, 80, 130)
doc.add_paragraph(
    "Objective: Assess speed stat distributions across all 800 Pokemon using a Seaborn Histogram with KDE trendline "
    "configured in a forest green aesthetic."
)
add_code_snippet(doc, """plt.figure(figsize=(9, 5))
sns.histplot(pk_df['Speed'], kde=True, color='forestgreen', bins=30, alpha=0.6)
plt.title("Distribution of Pokemon Speed Base Stats with KDE Curve", fontsize=14, fontweight='bold')
plt.xlabel("Speed Base Stat"); plt.ylabel("Frequency (Number of Pokemon)")
plt.savefig("part1_distribution_histogram.png", dpi=300, bbox_inches='tight')""")

fig2_p = os.path.join(OUTPUTS_DIR, "activity2_pokemon", "part1_distribution_histogram.png")
if os.path.exists(fig2_p):
    doc.add_picture(fig2_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_callout(doc, "Pokemon speed stats follow an approximately normal distribution centered at mean = 68.28 (std = 29.06). The interquartile range spans 45 to 90, with Deoxys Speed Forme topping the scale at 180 base speed.", "Speed Distribution Finding")

# Part 2
h2 = doc.add_heading("Part 2: Categorical Comparisons (Type 1 & Attack) — Lead: Amit Kumar", level=2)
h2.runs[0].font.color.rgb = RGBColor(40, 80, 130)
doc.add_paragraph(
    "Objective: Evaluate primary type prevalence via Countplot with rotated labels and benchmark physical Attack "
    "potency across types via Boxplots."
)
add_code_snippet(doc, """# Countplot of Primary Types (Type 1)
sns.countplot(data=pk_df, x='Type 1', order=type_order, palette='viridis')
plt.xticks(rotation=45, ha='right')

# Boxplot of Attack stat across Type 1
sns.boxplot(data=pk_df, x='Type 1', y='Attack', order=type_order, palette='Spectral')
plt.xticks(rotation=45, ha='right')""")

c2_p = os.path.join(OUTPUTS_DIR, "activity2_pokemon", "part2_type1_countplot.png")
b2_p = os.path.join(OUTPUTS_DIR, "activity2_pokemon", "part2_type_attack_boxplot.png")
if os.path.exists(c2_p):
    doc.add_picture(c2_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
if os.path.exists(b2_p):
    doc.add_picture(b2_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_callout(doc, "Water (112) and Normal (98) are the most frequent primary types, whereas Flying (4) and Fairy (17) are rare. Dragon and Fighting types demonstrate the highest median Attack stats (>100), exhibiting significant positive outlier megas.", "Type Combat Profile")

# Part 3 & 4
h2 = doc.add_heading("Part 3 & 4: Relational Scatterplot & Correlation Heatmap — Lead: Mehul Lahot", level=2)
h2.runs[0].font.color.rgb = RGBColor(40, 80, 130)
doc.add_paragraph(
    "Objective: Quantify the trade-off between physical offense (Attack) and defense (Defense) segmented by Legendary "
    "status, and construct the complete multi-stat correlation matrix using a viridis heatmap."
)
add_code_snippet(doc, """# Attack vs Defense by Legendary status
sns.scatterplot(data=pk_df, x='Attack', y='Defense', hue='Legendary', alpha=0.7,
                palette={False: '#3498db', True: '#e74c3c'}, s=55)

# Full Combat Stat Correlation Heatmap
sns.heatmap(pk_df[['HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed', 'Generation']].corr(),
            annot=True, fmt='.2f', cmap='viridis', square=True)""")

s2_p = os.path.join(OUTPUTS_DIR, "activity2_pokemon", "part3_attack_vs_defense_scatter.png")
h2_p = os.path.join(OUTPUTS_DIR, "activity2_pokemon", "part4_stats_correlation_heatmap.png")
if os.path.exists(s2_p):
    doc.add_picture(s2_p, width=Inches(5.6))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
if os.path.exists(h2_p):
    doc.add_picture(h2_p, width=Inches(5.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_callout(doc, "Attack and Defense display a moderate positive correlation (r = 0.44). Legendary Pokemon are distinctly separated from regular Pokemon, congregating in the top-right high-offense high-defense quadrant. Special Attack and Special Defense correlate strongly (r = 0.51).", "Stat Synergy Analysis")

# Part 5 & 6
h2 = doc.add_heading("Part 5, 6 & 7: Subplot Grid, Programmatic Annotation & 300 DPI Export — Lead: Raidas Kunal", level=2)
h2.runs[0].font.color.rgb = RGBColor(40, 80, 130)
doc.add_paragraph(
    "Objective: Present a multi-panel dashboard comparing Attack/Defense scatter with Total Base Stats by Type, and "
    "programmatically annotate the extreme HP outlier (Blissey) at 300 DPI."
)
add_code_snippet(doc, """# Programmatic detection of maximum HP
max_hp_idx = pk_df['HP'].idxmax()
max_hp_pokemon = pk_df.loc[max_hp_idx]

# Subplot Grid
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
# [Scatterplot Left, Average Total Stat Barplot Right]

# Annotation Callout
ax.annotate(f"Record High HP!\\n{max_hp_pokemon['Name']}\\n(HP: {max_hp_pokemon['HP']}, Def: {max_hp_pokemon['Defense']})",
            xy=(max_hp_pokemon['Defense'], max_hp_pokemon['HP']),
            xytext=(max_hp_pokemon['Defense'] + 30, max_hp_pokemon['HP'] - 20),
            arrowprops=dict(facecolor='darkred', arrowstyle='->', lw=2),
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#fff2cc', edgecolor='darkred'))
plt.savefig("final_visualization.png", dpi=300, bbox_inches='tight')""")

sub2_p = os.path.join(OUTPUTS_DIR, "activity2_pokemon", "part5_subplot_grid.png")
fin2_p = os.path.join(OUTPUTS_DIR, "activity2_pokemon", "final_visualization.png")
if os.path.exists(sub2_p):
    doc.add_picture(sub2_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
if os.path.exists(fin2_p):
    doc.add_picture(fin2_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_callout(doc, "Blissey sets the absolute record high HP stat at 255 (with a modest defense of 10). Dragon types lead all categories with the highest average Total Base Stat (~550), followed by Steel and Flying types.", "Pokemon Outlier Insight")

# ==============================================================================
# SECTION: ACTIVITY 3 - TELCO CUSTOMER CHURN
# ==============================================================================
doc.add_page_break()
h_act3 = doc.add_heading("Activity 3: Telco Customer Churn Analysis", level=1)
h_act3.runs[0].font.color.rgb = RGBColor(20, 50, 90)

p3 = doc.add_paragraph(
    "Dataset: telco_churn.csv (7,043 customer accounts, 21 columns)\n"
    "Focus: Customer tenure distributions, contract type impact, monthly charges vs. lifetime billing, and churn drivers."
)
p3.runs[0].font.size = Pt(10)

# Part 1
h2 = doc.add_heading("Part 1: Distribution Analysis (Customer Tenure) — Lead: Raidas Kunal", level=2)
h2.runs[0].font.color.rgb = RGBColor(40, 80, 130)
doc.add_paragraph(
    "Objective: Analyze customer lifecycle duration using a Seaborn Histogram with KDE curve in a rich teal color."
)
add_code_snippet(doc, """plt.figure(figsize=(9, 5))
sns.histplot(churn_df['tenure'], kde=True, color='teal', bins=36, alpha=0.6)
plt.title("Distribution of Customer Tenure (Months) with KDE Curve", fontsize=14, fontweight='bold')
plt.xlabel("Customer Tenure (Months with Telco)"); plt.ylabel("Number of Customers")
plt.savefig("part1_distribution_histogram.png", dpi=300, bbox_inches='tight')""")

fig3_p = os.path.join(OUTPUTS_DIR, "activity3_telco_churn", "part1_distribution_histogram.png")
if os.path.exists(fig3_p):
    doc.add_picture(fig3_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_callout(doc, "Customer tenure exhibits a pronounced bimodal distribution: huge spikes occur at months 1-3 (newly acquired subscribers at high churn risk) and months 70-72 (highly sticky, loyal multi-year subscribers).", "Tenure Bimodality Insight")

# Part 2
h2 = doc.add_heading("Part 2: Categorical Comparisons (Contract & Charges) — Lead: Raidas Kunal", level=2)
h2.runs[0].font.color.rgb = RGBColor(40, 80, 130)
doc.add_paragraph(
    "Objective: Quantify subscriber distribution across contract commitments and examine monthly fee spreads across "
    "plans using Boxplots."
)
add_code_snippet(doc, """# Countplot of Contract Types
sns.countplot(data=churn_df, x='Contract', order=contract_order, palette='Blues_r')

# Boxplot of MonthlyCharges across Contract
sns.boxplot(data=churn_df, x='Contract', y='MonthlyCharges', order=contract_order, palette='Set3')""")

c3_p = os.path.join(OUTPUTS_DIR, "activity3_telco_churn", "part2_contract_countplot.png")
b3_p = os.path.join(OUTPUTS_DIR, "activity3_telco_churn", "part2_contract_charges_boxplot.png")
if os.path.exists(c3_p):
    doc.add_picture(c3_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
if os.path.exists(b3_p):
    doc.add_picture(b3_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_callout(doc, "Over 55.0% of subscribers (3,875 customers) are on flexible Month-to-Month contracts. Two-Year plans exhibit the widest interquartile range of monthly fees ($25 to $90), capturing both barebones phone-only users and premium fiber-optic bundle users.", "Contract Breakdown")

# Part 3 & 4
h2 = doc.add_heading("Part 3 & 4: Relational Scatterplot & Correlation Heatmap — Lead: Amit Kumar", level=2)
h2.runs[0].font.color.rgb = RGBColor(40, 80, 130)
doc.add_paragraph(
    "Objective: Map the interplay between Monthly Charges and Total Charges color-coded by Churn status, and compute "
    "the numerical correlation matrix after parsing TotalCharges to float."
)
add_code_snippet(doc, """# Parsing TotalCharges as instructed in Lab manual for Option C
churn_df['TotalCharges'] = pd.to_numeric(churn_df['TotalCharges'], errors='coerce')
churn_df['TotalCharges'].fillna(churn_df['TotalCharges'].median(), inplace=True)

# Scatterplot Monthly vs Total Charges by Churn
sns.scatterplot(data=churn_df, x='MonthlyCharges', y='TotalCharges', hue='Churn',
                alpha=0.6, palette={'No': '#2ecc71', 'Yes': '#e74c3c'}, s=40)

# Heatmap of numerical metrics
sns.heatmap(churn_df[['tenure', 'MonthlyCharges', 'TotalCharges', 'SeniorCitizen']].corr(),
            annot=True, fmt='.2f', cmap='coolwarm', square=True)""")

s3_p = os.path.join(OUTPUTS_DIR, "activity3_telco_churn", "part3_charges_scatter.png")
h3_p = os.path.join(OUTPUTS_DIR, "activity3_telco_churn", "part4_churn_correlation_heatmap.png")
if os.path.exists(s3_p):
    doc.add_picture(s3_p, width=Inches(5.6))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
if os.path.exists(h3_p):
    doc.add_picture(h3_p, width=Inches(5.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_callout(doc, "Total Charges strongly correlate with tenure (r = 0.83) and monthly billing (r = 0.65). Churned customers (red) are disproportionately concentrated in the lower-right sector: high monthly fees ($70-$110) combined with short tenure (<15 months).", "Churn Vulnerability Cluster")

# Part 5 & 6
h2 = doc.add_heading("Part 5, 6 & 7: Subplot Grid, Programmatic Annotation & 300 DPI Export — Lead: Mehul Lahot", level=2)
h2.runs[0].font.color.rgb = RGBColor(40, 80, 130)
doc.add_paragraph(
    "Objective: Create an executive retention cockpit contrasting scatter dynamics with contract billing averages, "
    "identify the absolute maximum monthly charge subscriber, and save at publication quality."
)
add_code_snippet(doc, """# Programmatic search for peak monthly billed customer
max_mc_idx = churn_df['MonthlyCharges'].idxmax()
max_mc_customer = churn_df.loc[max_mc_idx]

# Subplot Grid
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
# [Scatterplot Left, Average Billing by Contract Right]

# Annotation Callout
ax.annotate(f"Record High Monthly Charge!\\nCustomer: {max_mc_customer['customerID']}\\nRate: ${max_mc_customer['MonthlyCharges']:.2f}/mo",
            xy=(max_mc_customer['tenure'], max_mc_customer['MonthlyCharges']),
            xytext=(max_mc_customer['tenure'] - 30, max_mc_customer['MonthlyCharges'] - 12),
            arrowprops=dict(facecolor='darkred', arrowstyle='->', lw=2),
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffe6cc', edgecolor='darkred'))
plt.savefig("final_visualization.png", dpi=300, bbox_inches='tight')""")

sub3_p = os.path.join(OUTPUTS_DIR, "activity3_telco_churn", "part5_subplot_grid.png")
fin3_p = os.path.join(OUTPUTS_DIR, "activity3_telco_churn", "final_visualization.png")
if os.path.exists(sub3_p):
    doc.add_picture(sub3_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
if os.path.exists(fin3_p):
    doc.add_picture(fin3_p, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_callout(doc, "Customer 7569-NMZYQ holds the record highest monthly billing rate at $118.75/month on a Two-Year contract (retained). Average monthly charges increase from Month-to-Month ($66.40) to Two-Year plans ($60.77 average with bundled discounts).", "Executive Churn Summary")

# Save document
doc.save(DOCX_PATH)
print(f"Successfully generated final Word report: {DOCX_PATH}")

