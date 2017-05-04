import pandas as pd

df = pd.read_csv('out.csv')
df = df.fillna(df.mean())
df_norm = (df - df.mean()) / (df.max() - df.min())
df_norm.corr()['Client']
