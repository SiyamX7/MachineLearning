import pandas as pd 

# df = pd.read_json("data.json").set_index("Name")
# print(df.to_string())

# print(df.loc["David Hammond"])
# print(df.iloc[14])
# selection by column
# print(df["Name"].to_string())

# print(df[df["CGPA"] > 3.50]["Name"])

# print(df[df["CGPA"] > 3.50][["Name","CGPA"]].to_string())

# print(df.iloc[0])

df = pd.read_json("data.json").set_index("Name")

# print(df.loc[5:13, ["Name", "CGPA"]])
# print(df.iloc[5:12][["Name", "CGPA"]])

# inputName = input("Enter the name of the student: ")

# madarchod = df[df["CGPA"] > 3.50]
# bainchod = df[(df["City"] == "Dhaka") | (df["City"] == "Rajshahi")]

khankis = df.query("City in ['Dhaka', 'Rajshahi']")
# print(madarchod)
# print(bainchod)
# print(khankis["CGPA"].mean())
print(khankis.describe())
# try:
#     print(df.loc[inputName])
# except KeyError:
#     print(f"{inputName} not found.")