import pandas as pd

df = pd.read_excel("output/facturas_procesadas.xlsx")
print("Shape:", df.shape)
print(df.head())
