import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

mtcars_url = 'https://gist.githubusercontent.com/ZeccaLehn/4e06d2575eb9589dbe8c365d61cb056c/raw/mtcars.csv'
df_mtcars = pd.read_csv(mtcars_url, index_col=0)
#print(df_mtcars.head())

url_tips = 'https://raw.githubusercontent.com/mwaskom/seaborn-data/master/tips.csv'
tips_df = pd.read_csv(url_tips)

url_iris = 'https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv'
iris_df = pd.read_csv(url_iris)

url_titanic = 'https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv'
titanic_df = pd.read_csv(url_titanic)

# Fixed: Changed df_cars to df_mtcars to reference the correct variable name
cars_sorted = df_mtcars.sort_values('hp')
plt.plot(cars_sorted['hp'], cars_sorted['mpg'], color='red', linestyle='--', marker='o')
#plt.xlabel('Horsepower (hp)')
#plt.ylabel('Miles per Gallon (mpg)')
#plt.title('hp vs mpg')
plt.show()