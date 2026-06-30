import pandas as pd

ARCHIVO = "assets/data/Plantilla_Base_Polvos_Coladores_con_ML_Dataset (version 1).xlsx"
HOJA = "ML_Dataset"


def cargar_dataset():
    df = pd.read_excel(ARCHIVO, sheet_name=HOJA)

    # ANTES: df = df.dropna()  -> esto borraba una FILA ENTERA si
    # cualquier columna tenia un NaN, aunque esa columna no se usara
    # para predecir Temperatura_C / Viscosidad_Pa_s / etc.
    # Eso puede estar recortando datos validos justo en las variables
    # mas dificiles de predecir.
    #
    # Aca solo se eliminan filas 100% vacias (basura de Excel).
    # El manejo de NaN especifico de cada variable se hace en
    # ml_service.py, columna por columna, para aprovechar el maximo
    # de datos disponibles para cada modelo.
    df = df.dropna(how="all")

    return df
