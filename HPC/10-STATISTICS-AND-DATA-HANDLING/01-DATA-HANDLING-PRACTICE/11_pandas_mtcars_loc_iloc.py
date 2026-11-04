import pandas as pd

# --- Part 2: mtcars Dataset ---
# Load the new dataset, using index_col=0 to make the car names the row labels
mtcars_url = 'https://gist.githubusercontent.com/ZeccaLehn/4e06d2575eb9589dbe8c365d61cb056c/raw/mtcars.csv'
df_mtcars = pd.read_csv(mtcars_url, index_col=0)
print(df_mtcars)

print("\n--- mtcars Dataset: .loc ---")
# Searching by exact text labels for both specific rows and specific columns
mtcars_loc = df_mtcars.loc[['Mazda RX4', 'Honda Civic', 'Fiat 128'], ['mpg', 'hp']]
print(mtcars_loc)

print("\n--- mtcars Dataset: .iloc ---")
# Searching by numerical index: last 3 rows (-3:), first 4 columns (:4)
mtcars_iloc = df_mtcars.iloc[-3:, :4]
print(mtcars_iloc)