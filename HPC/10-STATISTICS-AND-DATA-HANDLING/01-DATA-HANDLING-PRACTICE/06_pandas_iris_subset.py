import pandas as pd

# 1. Define the exact URLs
url_iris = 'https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv'

# 2. Download and save them into three distinct variables
iris_df = pd.read_csv(url_iris)

# 3. Print the first 5 rows of each (using .head() empty defaults to 5)
print("\n--- Iris Dataset ---")
print(iris_df.head())

# Fixed: Completed the string literal and changed generic 'df' to 'tips_df'
# tips_df.to_json('export.json', orient='records')
# new_df = pd.read_json('export.json')

# only print sepal_length and species columns and save to new dataframe called iris_subset, print first 3 rows
iris_info = iris_df[['species', 'sepal_length']]
print(iris_info.head(3))