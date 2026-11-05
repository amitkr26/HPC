import pandas as pd

# 1. Define the exact URLs
url_iris = 'https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv'

# 2. Download and save them into three distinct variables
iris_df = pd.read_csv(url_iris)

# 3. Print the first 5 rows of each (using .head() empty defaults to 5)
#print("\n--- Iris Dataset ---")
# print(iris_df.head())

# Fixed: Completed the string literal and changed generic 'df' to 'tips_df'
# tips_df.to_json('export.json', orient='records')
# new_df = pd.read_json('export.json')

# only print sepal_length and species columns and save to new dataframe called iris_subset, print first 3 rows
# iris_subset = iris_df[['sepal_length', 'species']]
# print(iris_subset.head(3))

# Fixed: Changed tips_df to iris_df to query sepal_length and species correctly
# wealthy_iris = iris_df[(iris_df['sepal_length']>6.0)]
# print(wealthy_iris[['sepal_length', 'species']].head())

#iris_count = iris_df['species']
#print(iris_count.value_counts())

bins = [0, 5.0, 6.5, 10.0]
labels = ['Short', 'Medium', 'Long']
# Pass the labels list into the function and target the numeric 'sepal_length' column
iris_df['Length_Group'] = pd.cut(iris_df['sepal_length'], bins=bins, labels=labels)
print(iris_df[['sepal_length', 'Length_Group', 'species']].head(6))