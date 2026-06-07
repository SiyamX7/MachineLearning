import pandas as pd

# pd.set_option("display.max_rows", None)
# pd.set_option("display.max_columns", None)
# pd.set_option("display.max_colwidth", None)


# df = pd.read_csv("pandas_practice_dataset.csv")

dp = pd.read_json("data.json")
# print(df)
# print(list(df.columns))
# print(df.head())
# print(df.tail())

print(dp.to_string())
print("gua da marse")