import pandas as pd

df_prices = pd.DataFrame({'Price': [10.50, 20.00, 15.75]})
def calculate_tax(amount):
    return amount*1.10
df_prices['Price_With_Tax'] = df_prices['Price'].apply(calculate_tax)
print(df_prices)