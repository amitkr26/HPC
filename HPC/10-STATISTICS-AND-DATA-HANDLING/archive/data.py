# Part 1: Dataset Selection and Import[cite: 8]
import pandas as pd

# Load the downloaded CSV file into a pandas DataFrame[cite: 8]
# (Make sure 'AB_NYC_2019.csv' is in the same folder as your script)
df = pd.read_csv('AB_NYC_2019.csv')

# Part 2: Data Profiling & Initial Inspection[cite: 8, 9]
print("--- First 10 and Last 5 Rows ---")
print(df.head(10)) # Display the first 10 rows[cite: 9]
print(df.tail(5))  # Display the last 5 rows[cite: 9]

print("\n--- Original Shape ---")
print(df.shape)    # Print the shape to see starting rows and columns[cite: 9]

print("\n--- DataFrame Summary ---")
print(df.info())   # Inspect data types and non-null counts[cite: 9]

print("\n--- Descriptive Statistics ---")
print(df.describe()) # Check min/max values for suspicious numbers like a $0 price[cite: 9]

print("\n--- Total Missing Values ---")
print(df.isna().sum()) # Calculate exact total of missing (null) values per column[cite: 9]

# Part 3: Structural Cleaning[cite: 9]
# Drop unnecessary columns to save memory and anonymize data[cite: 9]
df = df.drop(columns=['id', 'host_name']) 

# Rename neighbourhood_group to borough[cite: 9]
df = df.rename(columns={'neighbourhood_group': 'borough'})

# Standardize column names (lowercase and replace spaces with underscores)[cite: 9]
df.columns = df.columns.str.lower().str.replace(' ', '_')

# Part 4: Handling Missing Data[cite: 9, 10]
# Fill missing categorical listing names with "Unknown"[cite: 9]
df['name'] = df['name'].fillna("Unknown")

# Fill missing numerical reviews per month with 0[cite: 9]
df['reviews_per_month'] = df['reviews_per_month'].fillna(0)

# (Date Missing Data: 'last_review' nulls are intentionally left alone)[cite: 10]

print("\n--- Missing Values After Patching ---")
print(df.isna().sum()) # Prove 'name' and 'reviews_per_month' have zero missing values[cite: 10]

# Part 5: Data Formatting and Type Conversion[cite: 10]
# Convert 'last_review' from standard text/object to proper datetime[cite: 10]
df['last_review'] = pd.to_datetime(df['last_review'])

# Convert 'room_type' and 'borough' to 'category' data types to save memory[cite: 10]
df['room_type'] = df['room_type'].astype('category')
df['borough'] = df['borough'].astype('category')

print("\n--- Data Types After Conversion ---")
print(df.dtypes) # Verify the changes to datetime and category[cite: 10]

# Part 6: Outliers and Duplicates[cite: 10]
# Drop completely identical rows, keeping only the first occurrence[cite: 10]
df = df.drop_duplicates()

# Remove rows where the price is exactly 0[cite: 10]
df = df[df['price'] > 0]

# Calculate the 99th percentile and filter out extreme upper outliers[cite: 10]
q99_price = df['price'].quantile(0.99)
df = df[df['price'] < q99_price]

print("\n--- Shape After Outlier/Duplicate Removal ---")
print(df.shape) # Compare to original shape to see rows removed[cite: 10]

# Part 7: Feature Engineering[cite: 11]
# Categorize price into Budget ($1-$100), Mid-Range ($101-$250), and Luxury ($251+)[cite: 11]
bins = [0, 100, 250, float('inf')]
labels = ['Budget', 'Mid-Range', 'Luxury']
df['price_tier'] = pd.cut(df['price'], bins=bins, labels=labels)

print("\n--- Price Tier Value Counts ---")
print(df['price_tier'].value_counts()) # Check your work[cite: 11]

# Part 8: Final Export[cite: 11]
# Export fully cleaned DataFrame without the index column[cite: 11]
df.to_csv('cleaned_dataset_v1.csv', index=False)