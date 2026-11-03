import pandas as pd

# 1. Define the exact URLs
url_tips = 'https://raw.githubusercontent.com/mwaskom/seaborn-data/master/tips.csv'
url_titanic = 'https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv'
url_iris = 'https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv'

# 2. Download and save them into three distinct variables
tips_df = pd.read_csv(url_tips)
titanic_df = pd.read_csv(url_titanic)
iris_df = pd.read_csv(url_iris)

# 3. Print the first 5 rows of each (using .head() empty defaults to 5)
print("--- Tips Dataset ---")
print(tips_df.head())

print("\n--- Titanic Dataset ---")
print(titanic_df.head())

print("\n--- Iris Dataset ---")
print(iris_df.head())

# Fixed: Completed the string literal and changed generic 'df' to 'tips_df'
tips_df.to_json('export.json', orient='records')
new_df = pd.read_json('export.json')

# Fixed the variable names to correctly reference titanic_df and fixed .head()
ages = titanic_df['Age']
passenger_info = titanic_df[['Name', 'Age', 'Survived']]
print(passenger_info.head())