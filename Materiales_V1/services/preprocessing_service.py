def preparar_dataset(df):
    df = df.copy()
    df = df.dropna()

    return df
