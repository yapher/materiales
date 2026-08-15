"""
Constantes compartidas entre mezcla_service.py y excel_service.py.
"""

ELEMENTOS = [
    "CaO", "SiO2", "Al2O3", "MgO",
    "Na2O", "K2O", "Li2O", "CaF2",
    "Fe2O3", "MnO", "TiO2",
]

COLUMNAS = [f"{e}_pct" for e in ELEMENTOS]
COLUMNAS_MODELO = COLUMNAS + ["Temperatura_C"]


VARIABLE_ENTRENABLE_POR_DEFECTO = "Densidad_kg_m3"

VARIABLES_ENTRENABLES = [
    {
        "valor": "Densidad_kg_m3",
        "etiqueta": "Densidad (kg/m³)",
        "descripcion": "Densidad aparente o volumétrica del polvo colador.",
        "por_defecto": True,
    },
    {
        "valor": "Viscosidad_Pa_s",
        "etiqueta": "Viscosidad (Pa·s)",
        "descripcion": "Viscosidad del material a la temperatura de proceso.",
        "por_defecto": False,
    },
    {
        "valor": "Conductividad_Termica_W_mK",
        "etiqueta": "Conductividad térmica (W/mK)",
        "descripcion": "Capacidad del material de conducir calor.",
        "por_defecto": False,
    },
    {
        "valor": "Inicio_Cristalizacion_C",
        "etiqueta": "Inicio de cristalización (°C)",
        "descripcion": "Temperatura donde comienza la cristalización.",
        "por_defecto": False,
    },
    {
        "valor": "Fraccion_Cristalina_pct",
        "etiqueta": "Fracción cristalina (%)",
        "descripcion": "Porcentaje de fase cristalina.",
        "por_defecto": False,
    },
    {
        "valor": "Presencia_Cuspidina",
        "etiqueta": "Presencia de cuspidina",
        "descripcion": "Indicador de presencia de cuspidina.",
        "por_defecto": False,
    },
    {
        "valor": "C_libre_pct",
        "etiqueta": "Carbono libre (%)",
        "descripcion": "Porcentaje de carbono libre.",
        "por_defecto": False,
    },
    {
        "valor": "Alcalinos_tot",
        "etiqueta": "Alcalinos totales",
        "descripcion": "Contenido total de óxidos alcalinos.",
        "por_defecto": False,
    },
    {
        "valor": "Oxidos_Basicos_tot",
        "etiqueta": "Óxidos básicos totales",
        "descripcion": "Suma de óxidos básicos.",
        "por_defecto": False,
    },
    {
        "valor": "Oxidos_Acidos_tot",
        "etiqueta": "Óxidos ácidos totales",
        "descripcion": "Suma de óxidos ácidos.",
        "por_defecto": False,
    },
    {
        "valor": "Fluoruros_totales",
        "etiqueta": "Fluoruros totales",
        "descripcion": "Contenido total de fluoruros.",
        "por_defecto": False,
    },
    {
        "valor": "Basicidad_CaO_SiO2",
        "etiqueta": "Basicidad CaO/SiO₂",
        "descripcion": "Relación básica CaO / SiO₂.",
        "por_defecto": False,
    },
    {
        "valor": "Tiempo_Mantenimiento_min",
        "etiqueta": "Tiempo de mantenimiento (min)",
        "descripcion": "Tiempo de mantenimiento térmico.",
        "por_defecto": False,
    },
    {
        "valor": "Velocidad_Calentamiento_C_min",
        "etiqueta": "Velocidad de calentamiento (°C/min)",
        "descripcion": "Velocidad de calentamiento del ensayo.",
        "por_defecto": False,
    },
]