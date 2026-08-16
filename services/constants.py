"""
Constantes y helpers de nombres.
IMPORTANTE:
Las variables entrenables YA NO se definen acá.
Ahora se descubren dinámicamente desde el Excel en services/excel_service.py.

Este archivo mantiene:
- sufijo de columnas de composición
- cantidad de columnas iniciales que corresponden a composición (A-K)
- detección de columna de temperatura
- etiquetas conocidas para mostrar bonito
- compatibilidad hacia atrás con imports viejos
"""

import os
import re

# ==========================================================
# Composición
# ==========================================================
SUFIJO_COMPOSICION = "_pct"

# ==========================================================
# Cantidad de columnas iniciales del Excel que corresponden
# a la composición de la mezcla.
#
# Según el dataset actual:
# - Columnas A a K => elementos de composición.
# - Columna L en adelante => variables a modelar.
#
# A-K son 11 columnas.
#
# Si en el futuro cambiara la estructura del dataset, se puede
# ajustar con la variable de entorno CANTIDAD_COLUMNAS_COMPOSICION.
# ==========================================================
CANTIDAD_COLUMNAS_COMPOSICION = int(
    os.environ.get("CANTIDAD_COLUMNAS_COMPOSICION", "11")
)


def es_posicion_composicion(indice):
    """
    Devuelve True si el índice de la columna pertenece al bloque
    inicial de composición.

    Ejemplo:
    - Columna A => índice 0
    - Columna K => índice 10
    - Columna L => índice 11

    Para composición A-K, el límite es 11.
    """
    return 0 <= indice < CANTIDAD_COLUMNAS_COMPOSICION


# ==========================================================
# Temperatura
# ==========================================================
PREFERENCIA_TEMPERATURA = [
    "Temperatura_K",
    "Temperatura_k",
    "Temperatura_C",
    "Temperatura",
    "Temperature_K",
    "Temperature_C",
    "Temperature",
    "Temp_K",
    "Temp_C",
    "Temp",
]

# Solo se considera columna de temperatura si es exactamente algo como:
# Temperatura, Temperatura_K, Temperatura_C, Temperature_K, Temp, etc.
# Evita confundir con variables objetivo tipo "Temperatura_Liquidus_K".
_PATRON_TEMPERATURA = re.compile(r"^temp(eratura|erature)?(_(k|c))?$")


# ==========================================================
# Etiquetas conocidas (solo para mostrar más lindo)
# ==========================================================
MAPA_ETIQUETAS = {
    "Densidad_kg_m3": "Densidad (kg/m³)",
    "Viscosidad_Pa_s": "Viscosidad (Pa·s)",
    "Conductividad_Termica_W_mK": "Conductividad térmica (W/mK)",
    "Inicio_Cristalizacion_C": "Inicio de cristalización (°C)",
    "Fraccion_Cristalina_pct": "Fracción cristalina (%)",
    "Presencia_Cuspidina": "Presencia de cuspidina",
    "C_libre_pct": "Carbono libre (%)",
    "Alcalinos_tot": "Alcalinos totales",
    "Oxidos_Basicos_tot": "Óxidos básicos totales",
    "Oxidos_Acidos_tot": "Óxidos ácidos totales",
    "Fluoruros_totales": "Fluoruros totales",
    "Basicidad_CaO_SiO2": "Basicidad CaO/SiO₂",
    "Tiempo_Mantenimiento_min": "Tiempo de mantenimiento (min)",
    "Velocidad_Calentamiento_C_min": "Velocidad de calentamiento (°C/min)",
}

MAPA_DESCRIPCIONES = {
    "Densidad_kg_m3": "Densidad aparente o volumétrica del polvo colador.",
    "Viscosidad_Pa_s": "Viscosidad del material a la temperatura de proceso.",
    "Conductividad_Termica_W_mK": "Capacidad del material de conducir calor.",
    "Inicio_Cristalizacion_C": "Temperatura donde comienza la cristalización.",
    "Fraccion_Cristalina_pct": "Porcentaje de fase cristalina.",
    "Presencia_Cuspidina": "Indicador de presencia de cuspidina.",
    "C_libre_pct": "Porcentaje de carbono libre.",
    "Alcalinos_tot": "Contenido total de óxidos alcalinos.",
    "Oxidos_Basicos_tot": "Suma de óxidos básicos.",
    "Oxidos_Acidos_tot": "Suma de óxidos ácidos.",
    "Fluoruros_totales": "Contenido total de fluoruros.",
    "Basicidad_CaO_SiO2": "Relación básica CaO / SiO₂.",
    "Tiempo_Mantenimiento_min": "Tiempo de mantenimiento térmico.",
    "Velocidad_Calentamiento_C_min": "Velocidad de calentamiento del ensayo.",
}


# ==========================================================
# Helpers
# ==========================================================
def normalizar_nombre_columna(columna):
    """
    Normaliza el nombre de una columna para comparaciones:
    - minúsculas
    - sin espacios
    - guiones bajos
    """
    return str(columna).strip().lower().replace(" ", "_")


def es_columna_temperatura(columna):
    """
    Devuelve True si la columna parece ser la temperatura de proceso.
    """
    norm = normalizar_nombre_columna(columna)
    return bool(_PATRON_TEMPERATURA.match(norm))


def etiqueta_amigable(columna):
    """
    Devuelve una etiqueta para mostrar en la UI.
    Si la columna está en el mapa conocido, usa esa etiqueta.
    Si no, convierte 'Nombre_Columna' en 'Nombre Columna'.
    """
    columna = str(columna)
    if columna in MAPA_ETIQUETAS:
        return MAPA_ETIQUETAS[columna]

    norm = normalizar_nombre_columna(columna)
    for clave, valor in MAPA_ETIQUETAS.items():
        if normalizar_nombre_columna(clave) == norm:
            return valor

    return columna.replace("_", " ").strip()


def descripcion_variable(columna):
    """
    Devuelve una descripción para la UI.
    """
    columna = str(columna)
    if columna in MAPA_DESCRIPCIONES:
        return MAPA_DESCRIPCIONES[columna]

    norm = normalizar_nombre_columna(columna)
    for clave, valor in MAPA_DESCRIPCIONES.items():
        if normalizar_nombre_columna(clave) == norm:
            return valor

    return f"Variable '{columna}' detectada automáticamente del dataset."


def etiqueta_temperatura(columna):
    """
    Devuelve el label para el input de temperatura.
    """
    if not columna:
        return "Temperatura"

    norm = normalizar_nombre_columna(columna)

    if norm.endswith("_k"):
        return "Temperatura (K)"

    if norm.endswith("_c"):
        return "Temperatura (°C)"

    return etiqueta_amigable(columna)


# ==========================================================
# Compatibilidad hacia atrás
#
# Antes el sistema importaba estas constantes fijas.
# Se dejan vacías para no romper imports viejos, pero ya no
# son la fuente de verdad.
# ==========================================================
ELEMENTOS = []
COLUMNAS = []
COLUMNAS_MODELO = []
VARIABLE_ENTRENABLE_POR_DEFECTO = None
VARIABLES_ENTRENABLES = []