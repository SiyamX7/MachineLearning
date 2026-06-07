import pandas as pd

data = [10,20,30]

series = pd.Series(data, index=['a', 'b', 'c'])

print(series)

print(series.loc['a'])