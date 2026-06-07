import pandas as pd

data = {
    "name" : ["siyam", "samin", "dog", "cat", "dhon", "bal", "chat"],
    "age" : [25,15,7,4,24,22,44]
}

df = pd.DataFrame(data)

# print(df.head())
# print(df.tail())
# print(df.shape)
# print(df.info())
# print(df.columns)
# print(df.describe())

# print(df["age"])
# print(df[["age", "name"]])

# print(df.iloc[0])
print(df.loc[0])

print(df[df["age"] > 20])

# add new column
df["salary"] = [1000, 2000, 3000, 400, 68, 654, 765]

print(df)