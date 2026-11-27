# Module 11 - Introduction to ML, DL & OpenVINO

- **Duration:** 48 hrs / 6 Days
- **Faculty:** Anuja Sridhar (PE STG), Usha Rani (PE STG)
- **Schedule:** 21/10/2026 - 28/10/2026
- **Holidays:** 19/10/2026 (Additional), 20/10/2026 (Dusshera), 24/10 - 26/10/2026 (Weekend)
- **Status:** done

## Deliverables

| Deliverable | Location |
| --- | --- |
| NYC coffee-chain capstone notebook | [`capstone/capstone_coffee_viability.ipynb`](capstone/capstone_coffee_viability.ipynb) |
| Capstone brief | [`capstone/Capstone Project.pdf`](capstone/Capstone%20Project.pdf) |
| Retail data-cleaning pipeline | [`assignments/retail-data-pipeline/assignment1.py`](assignments/retail-data-pipeline/assignment1.py) |
| Profit vs. sales regression notebook | [`assignments/profit-regression/profit_sales_regression.ipynb`](assignments/profit-regression/profit_sales_regression.ipynb) |

## Repository Layout

```text
11-ML-DL-OPENVINO/
├── README.md
├── requirements.txt
├── assignments/
│   ├── retail-data-pipeline/
│   │   └── assignment1.py
│   └── profit-regression/
│       └── profit_sales_regression.ipynb
├── capstone/
│   ├── Capstone Project.pdf
│   └── capstone_coffee_viability.ipynb
├── data/
│   ├── raw/
│   │   ├── retail/          # provided Module 11 practice data
│   │   └── capstone/        # cached NYC Open Data inputs
│   └── processed/           # generated CSV and PNG outputs
├── docs/
│   └── references/          # provided/reference snippets and caveats
└── archive/                 # unrelated scratch files kept out of deliverables
```

## Data

`data/raw/retail/` contains the Module 11 retail practice dataset:

- `sales_transactions.csv` - sales transactions
- `customer_profiles.json` - customer profiles
- `products.xlsx` and `retail_store.db` - product and store data
- `ab_campaign_results.csv` and `competitor_reviews.html` - campaign and review data
- `product_images/` - 400 product images for vision exercises
- `shelf_feed.mp4` and `support_call.wav` - video and audio samples for inference exercises

`data/raw/capstone/` contains the cached NYC Neighborhood Financial Health and
NYC Parks properties downloads. Delete those cached files to re-download them
from NYC Open Data when running the capstone notebook.

Generated files in `data/processed/`:

- `master_retail.csv` and `customer_ml_features.csv` - retail pipeline outputs
- `capstone_district_scores.csv` and `capstone_dashboard.png` - capstone outputs
- `profit_regression_plot.png` - regression plot preview

## Run

From this module directory:

```powershell
python assignments/retail-data-pipeline/assignment1.py
```

Open either notebook in Jupyter or Colab. The notebooks locate their data
relative to the module root, while the regression notebook also accepts files
uploaded directly to `/content` in Colab. The local kernel is `capstone-venv`.

The NumPy/pandas data-handling practice lives in
[`10-STATISTICS-AND-DATA-HANDLING/01-DATA-HANDLING-PRACTICE/`](../10-STATISTICS-AND-DATA-HANDLING/01-DATA-HANDLING-PRACTICE),
which matches the syllabus topic.
