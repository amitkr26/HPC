import pandas as pd

# 1. Define the exact URLs
url_titanic = 'https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv'

# 2. Download and save them into three distinct variables
titanic_df = pd.read_csv(url_titanic)

# 3. Print the first 5 rows of each (using .head() empty defaults to 5)
# print("\n--- Titanic Dataset ---")
# print(titanic_df.head())

# Fixed the variable names to correctly reference titanic_df and fixed .head()
# ages = titanic_df['Age']
# passenger_info = titanic_df[['Name', 'Age', 'Survived']]
# print(passenger_info.head())

# Fixed: Changed df_titanic to titanic_df
wealthy_survivors = titanic_df[(titanic_df['Fare']>50)&(titanic_df['Survived']==1)]
print(wealthy_survivors[['Name', 'Fare', 'Survived']].head())