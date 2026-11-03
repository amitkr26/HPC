import pandas as pd

# 1. Define the exact URLs
url_tips = 'https://raw.githubusercontent.com/mwaskom/seaborn-data/master/tips.csv'
# 2. Download and save them into three distinct variables
tips_df = pd.read_csv(url_tips)

# 3. Print the first 5 rows of each (using .head() empty defaults to 5)
#print("--- Tips Dataset ---")
#print(tips_df.head())

# Fixed: Completed the string literal and changed generic 'df' to 'tips_df'
#tips_df.to_json('export.json', orient='records')
#new_df = pd.read_json('export.json')

# Fixed the variable names to correctly reference titanic_df and fixed .head()
#tips_info = tips_df[['total_bill', 'tip', 'day']]
#print(tips_info.head())

# Fixed: Corrected 'Dinner' column check to filter the 'time' column and updated printed column names
dinner_time = tips_df[(tips_df['tip']>5.00)&(tips_df['time']=='Dinner')]
print(dinner_time[['total_bill', 'tip', 'time']].head())