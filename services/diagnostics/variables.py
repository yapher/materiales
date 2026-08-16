"""
Listado de variables disponibles para diagnóstico.
"""

from ..excel_service import (
    cargar_dataset,
    obtener_target_columns,
)

from ..constants import (
    normalizar_nombre_columna,
    etiqueta_amigable,
)


def obtener_variables_diagnostico():
    """
    Devuelve la lista de variables objetivo que se pueden
    analizar en el panel de diagnóstico.

    También devuelve una variable por defecto para seleccionar
    automáticamente cuando el usuario abre la página.
    """
    df = cargar_dataset()
    targets = obtener_target_columns(df)

    default_target = None

    if targets:
        preferidas = [
            "Densidad_kg_m3",
            "densidad_kg_m3",
            "Densidad",
            "densidad",
        ]

        for candidata in preferidas:
            clave = normalizar_nombre_columna(candidata)

            match = next(
                (
                    t for t in targets
                    if normalizar_nombre_columna(t) == clave
                ),
                None
            )

            if match:
                default_target = match
                break

        if default_target is None:
            default_target = targets[0]

    variables = []

    for target in targets:
        variables.append({
            "valor": target,
            "etiqueta": etiqueta_amigable(target),
        })

    return variables, default_target