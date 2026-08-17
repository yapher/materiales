"""
Contenido del Tutorial de Uso.
Refleja el estado actual de la aplicación:
- Flujo de 3 pasos (Dataset → Entrenamiento → Predicción)
- Configuración de variables a modelar
- Gráfico de tarta 3D
- Gráfico de densidad vs. temperatura
- Panel de diagnóstico
- Mi Dataset
- Perfil de usuario
"""


def contenido_tutorial():
    """
    Devuelve las secciones del tutorial de uso y un subtítulo.
    """
    secciones = [
        {
            "titulo": "1. Crear una cuenta e iniciar sesión",
            "parrafos": [
                "Para usar la aplicación necesitás una cuenta. Podés registrarte "
                "con usuario y contraseña desde 'Registrarse', o iniciar sesión "
                "con Google o X si el administrador los tiene habilitados.",
                "Cada cuenta tiene su propio dataset y su propio modelo entrenado: "
                "lo que hace un usuario no afecta a los demás.",
                "Desde el menú de tu usuario (arriba a la derecha) podés acceder "
                "a tu perfil para cambiar la contraseña, actualizar tus datos o "
                "subir una foto de perfil.",
            ],
        },
        {
            "titulo": "2. El flujo de trabajo: 3 pasos",
            "parrafos": [
                "La página principal de Predicción muestra un camino de 3 pasos "
                "que te guía en el proceso:",
            ],
            "items": [
                "Paso 1 — Dataset: tu copia personal del dataset se carga "
                "automáticamente al entrar. Podés verla y editarla desde "
                "'Ver mi dataset'.",
                "Paso 2 — Entrenamiento: elegí qué variables querés modelar "
                "(botón de engranaje rojo) y apretá 'Modelar'. El sistema "
                "entrena en segundo plano y muestra el progreso en vivo.",
                "Paso 3 — Predicción: una vez entrenado el modelo, armá tu "
                "mezcla y obtené las predicciones.",
            ],
        },
        {
            "titulo": "3. Configurar las variables a modelar",
            "parrafos": [
                "Antes de entrenar, apretá el botón rojo redondo con el ícono "
                "de engranaje junto al botón 'Modelar'. Se abre un modal donde "
                "podés seleccionar qué propiedades del material querés que el "
                "sistema aprenda a predecir (densidad, viscosidad, etc.).",
                "Las variables disponibles se detectan automáticamente desde "
                "tu dataset. Podés seleccionar una o varias. La selección se "
                "guarda en tu navegador para la próxima vez.",
            ],
            "items": [
                "'Usar variable por defecto': selecciona solo la variable "
                "principal (generalmente Densidad).",
                "'Limpiar selección': desmarca todo para empezar de cero.",
            ],
        },
        {
            "titulo": "4. Entrenar tu modelo",
            "parrafos": [
                "Al apretar 'Modelar', el sistema toma tu copia del dataset y "
                "entrena, una por una, un modelo de Machine Learning para cada "
                "variable seleccionada. El entrenamiento corre en segundo plano: "
                "podés seguir usando la app mientras tanto.",
                "El progreso se muestra en una barra con el número de variable "
                "actual, el total y el tiempo transcurrido. Al terminar, aparece "
                "una tabla con el R² de cada variable entrenada.",
            ],
            "items": [
                "R² cercano a 1 (verde): el modelo predice muy bien esa propiedad.",
                "R² medio (amarillo): predicción aceptable, con más margen de error.",
                "R² bajo (naranja/rojo): esa propiedad es difícil de predecir con "
                "los datos actuales; tomá esa predicción con cautela.",
            ],
        },
        {
            "titulo": "5. Armar una mezcla y predecir",
            "parrafos": [
                "Elegí cada elemento de la composición (CaO, SiO₂, Al₂O₃, etc.) "
                "y su porcentaje. El sistema te sugiere automáticamente el "
                "porcentaje restante para llegar a 100%.",
                "La barra de progreso y el gráfico de tarta 3D te muestran en "
                "tiempo real cuánto llevás sumado. Tiene que llegar exactamente "
                "a 100% para poder predecir.",
                "Ingresá la temperatura del proceso en Kelvin y apretá "
                "'Predecir'. El sistema muestra el valor estimado de cada "
                "propiedad entrenada para esa mezcla y temperatura.",
            ],
        },
        {
            "titulo": "6. Gráfico de tarta 3D",
            "parrafos": [
                "Junto al formulario de composición se muestra un gráfico de "
                "tarta tridimensional que representa visualmente la distribución "
                "de los componentes de tu mezcla.",
                "Cada porción tiene un color distinto por elemento. Si pasás el "
                "mouse por encima, se eleva y muestra un tooltip con el "
                "porcentaje exacto. Cuando la mezcla está incompleta, se muestra "
                "una porción gris 'Restante'.",
            ],
        },
        {
            "titulo": "7. Gráfico de densidad vs. temperatura",
            "parrafos": [
                "Después de realizar una predicción, aparece un botón verde "
                "redondo con un ícono de gráfico en el panel de composición. "
                "Al apretarlo se abre un modal con el gráfico de densidad "
                "predicha en función de la temperatura.",
                "Podés configurar el rango de temperatura (mínima, máxima e "
                "intervalo). El gráfico muestra:",
            ],
            "items": [
                "Línea verde: densidad predicha por el modelo a cada temperatura.",
                "Línea violeta punteada: regresión lineal ajustada (ρ = m·T + b).",
                "Cuadrados rojos: valores de la regresión en cada intervalo.",
                "Triángulos amarillos: datos reales del dataset con la misma "
                "composición (hover para ver la fila completa).",
            ],
            "parrafos_extra": [
                "Podés descargar el gráfico como imagen PNG o exportarlo a PDF "
                "con toda la información.",
            ],
        },
        {
            "titulo": "8. Guardar y exportar predicciones",
            "parrafos": [
                "Después de predecir, tenés dos opciones:",
            ],
            "items": [
                "'Exportar a PDF': genera un documento con la composición, "
                "temperatura y todas las propiedades predichas.",
                "'Guardar en el dataset': agrega la predicción como una fila "
                "nueva en tu dataset personal. Después podés reentrenar el "
                "modelo para que la tenga en cuenta.",
            ],
        },
        {
            "titulo": "9. Mi Dataset",
            "parrafos": [
                "Desde 'Ver mi dataset' en el Paso 1 del flujo, accedés a tu "
                "copia personal del dataset. Ahí podés:",
            ],
            "items": [
                "Ver todas las filas con sus valores.",
                "Editar cualquier celda (botón de lápiz).",
                "Eliminar filas (botón de basura).",
                "Exportar una fila individual a PDF.",
                "Las filas inconsistentes se marcan con un ícono de advertencia; "
                "apretalo para ver el motivo.",
            ],
        },
        {
            "titulo": "10. Panel de diagnóstico",
            "parrafos": [
                "Desde el menú 'Diagnóstico' podés analizar cualquier variable "
                "de tu dataset para detectar problemas antes de entrenar:",
            ],
            "items": [
                "Filas donde la composición no suma 100%.",
                "Valores objetivo atípicos (outliers).",
                "Temperaturas inconsistentes o atípicas.",
                "Features faltantes.",
                "Filas duplicadas exactas.",
                "Componentes fuera de rango 0-100%.",
            ],
            "parrafos_extra": [
                "El diagnóstico NO modifica ningún dato: solo muestra un "
                "informe para que decidas qué filas corregir o eliminar.",
            ],
        },
        {
            "titulo": "11. Recomendaciones de uso",
            "items": [
                "Si cambiás la mezcla (agregás o quitás un elemento), la "
                "predicción anterior se invalida automáticamente y hay que "
                "volver a predecir.",
                "No hace falta reentrenar cada vez que predecís: el modelo "
                "entrenado queda guardado entre sesiones.",
                "Si guardás predicciones en tu dataset, reentrená para que el "
                "modelo las incorpore.",
                "Usá el panel de diagnóstico antes de entrenar si el R² te da "
                "bajo: puede haber filas inconsistentes afectando la calidad.",
                "Si algo falla, el mensaje de error suele indicar la causa "
                "(por ejemplo, 'Primero entrená el modelo' si todavía no "
                "entrenaste ninguno).",
            ],
        },
    ]

    return secciones, "Guía para usar la aplicación paso a paso"