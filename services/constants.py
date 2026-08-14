"""
Constantes compartidas entre mezcla_service.py y excel_service.py.
Separadas en su propio modulo para que excel_service (que ahora
tambien valida filas del dataset maestro) no tenga que importar de
mezcla_service y crear una dependencia circular.
"""

ELEMENTOS = [
    "CaO", "SiO2", "Al2O3", "MgO",
    "Na2O", "K2O", "Li2O", "CaF2",
    "Fe2O3", "MnO", "TiO2",
]

COLUMNAS = [f"{e}_pct" for e in ELEMENTOS]
COLUMNAS_MODELO = COLUMNAS + ["Temperatura_C"]
