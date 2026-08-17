"""
Contenido de la Teoría de los Modelos.
Refleja el pipeline actual de entrenamiento:
- Filtro de composición (suma 100%)
- Exclusión de target ≤ 0
- Filtro de outliers por residuo OOF
- Selección de mejor algoritmo por K-Fold
- Reentrenamiento final con todos los datos limpios
"""


def contenido_modelos():
    """
    Devuelve las secciones de teoría de modelos y un subtítulo.
    """
    secciones = [
        {
            "titulo": "1. Enfoque general: un modelo por propiedad",
            "parrafos": [
                "El sistema NO entrena un único modelo grande. Por cada "
                "propiedad objetivo del dataset (viscosidad, densidad, etc.) "
                "se entrena un modelo de regresión INDEPENDIENTE, usando "
                "siempre como variables de entrada (features) la composición "
                "química (las primeras 11 columnas *_pct del Excel) más la "
                "temperatura del proceso.",
                "Esto permite que cada propiedad use el algoritmo que mejor "
                "le queda, en vez de forzar un único modelo para todas.",
            ],
            "imagen": "diagrama_pipeline.svg",
            "imagen_alt": (
                "Pipeline: dataset, candidatos, validación cruzada, "
                "selección y reentrenamiento"
            ),
        },
        {
            "titulo": "2. Limpieza de datos antes del entrenamiento",
            "parrafos": [
                "Antes de entrenar, el sistema aplica una serie de filtros "
                "automáticos para garantizar la calidad de los datos:",
            ],
            "items": [
                "Filtro de composición: se EXCLUYEN las filas donde la suma "
                "de óxidos no da 100% (± 0.5 puntos porcentuales de "
                "tolerancia) o donde falta algún porcentaje de composición.",
                "Temperatura inconsistente: si la temperatura está vacía o no "
                "es numérica, NO se descarta la fila; se reemplaza por 0.",
                "Target inválido: se excluyen las filas donde la variable "
                "objetivo es ≤ 0 (físicamente imposible para la mayoría de "
                "las propiedades).",
                "Filtro de outliers por residuo: se detectan y excluyen filas "
                "cuyo valor real está anormalmente lejos de lo que un modelo "
                "preliminar predice (ver sección 5).",
            ],
        },
        {
            "titulo": "3. Algoritmos candidatos evaluados",
            "parrafos": [
                "Para cada propiedad, el sistema entrena y compara tres "
                "algoritmos de ensamble basados en árboles de decisión "
                "(todos de scikit-learn), y se queda con el que mejor R² "
                "obtenga por validación cruzada:",
            ],
            "items": [
                "RandomForestRegressor (400 árboles, min_samples_leaf=2, "
                "max_features='sqrt'): construye muchos árboles de decisión "
                "sobre submuestras aleatorias de los datos (bagging) y "
                "promedia sus predicciones. Reduce el sobreajuste típico de "
                "un árbol individual.",
                "ExtraTreesRegressor (mismos hiperparámetros base): similar a "
                "Random Forest, pero además de muestrear los datos, elige los "
                "puntos de corte de cada árbol de forma más aleatoria. Suele "
                "ser más rápido y a veces generaliza mejor con pocos datos.",
                "GradientBoostingRegressor (400 estimadores, max_depth=3, "
                "learning_rate=0.05, subsample=0.8): construye los árboles de "
                "forma SECUENCIAL, donde cada árbol nuevo corrige los errores "
                "(residuos) que dejó el conjunto anterior. Suele lograr mayor "
                "precisión, a costa de ser más sensible a los hiperparámetros.",
            ],
            "imagen": "diagrama_ensamble.svg",
            "imagen_alt": (
                "Comparación entre bagging (árboles en paralelo) y "
                "boosting (árboles en secuencia)"
            ),
            "referencias": [
                {
                    "texto": "scikit-learn: RandomForestRegressor",
                    "url": "https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html",
                },
                {
                    "texto": "scikit-learn: ExtraTreesRegressor",
                    "url": "https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesRegressor.html",
                },
                {
                    "texto": "scikit-learn: GradientBoostingRegressor",
                    "url": "https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html",
                },
                {
                    "texto": "scikit-learn: guía de métodos de ensamble",
                    "url": "https://scikit-learn.org/stable/modules/ensemble.html",
                },
            ],
        },
        {
            "titulo": "4. Selección automática: validación cruzada K-Fold",
            "parrafos": [
                "Para decidir qué algoritmo usar en cada propiedad, se aplica "
                "validación cruzada K-Fold (K=5 por defecto, o menos si hay "
                "pocos datos disponibles para esa propiedad).",
                "El dataset se divide en K partes ('folds'). En cada "
                "iteración, el modelo se entrena con K-1 partes y se evalúa "
                "sobre la parte restante (que NO vio durante el entrenamiento "
                "de esa iteración). Repitiendo esto K veces, se obtiene una "
                "predicción 'out-of-fold' (OOF) para cada fila del dataset, "
                "generada siempre por un modelo que no la vio.",
                "El R² se calcula sobre esas predicciones OOF, nunca sobre "
                "datos de entrenamiento directo. Esto da una estimación "
                "honesta de qué tan bien generaliza el modelo a datos nuevos.",
            ],
            "imagen": "diagrama_kfold.svg",
            "imagen_alt": "Esquema de validación cruzada K-Fold con K=5",
            "referencias": [
                {
                    "texto": "scikit-learn: KFold — documentación oficial",
                    "url": "https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.KFold.html",
                },
                {
                    "texto": "scikit-learn: guía de validación cruzada",
                    "url": "https://scikit-learn.org/stable/modules/cross_validation.html",
                },
            ],
        },
        {
            "titulo": "5. Filtro de outliers por residuo de predicción",
            "parrafos": [
                "Además de los filtros básicos, el sistema aplica un filtro "
                "avanzado de outliers que detecta filas inconsistentes "
                "usando predicciones out-of-fold:",
            ],
            "items": [
                "Se entrena un RandomForest preliminar rápido con validación "
                "cruzada.",
                "Se obtienen predicciones OOF (cada fila es predicha por un "
                "modelo que NO la vio).",
                "Se calculan los residuos absolutos: |predicción - valor real|.",
                "Se define un umbral robusto: mediana + K × 1.4826 × MAD "
                "(donde MAD es la desviación absoluta mediana y K=3).",
                "Las filas con residuo mayor al umbral se consideran outliers "
                "y se excluyen del entrenamiento final.",
            ],
            "parrafos_extra": [
                "Este enfoque es superior a un IQR simple porque tiene en "
                "cuenta la relación entre las features y el target, no asume "
                "que la mayoría de un grupo es correcta, y funciona para "
                "cualquier variable sin conocer la física del problema.",
                "El filtro solo se aplica si hay al menos 15 filas "
                "disponibles; con menos datos, la validación cruzada no es "
                "confiable.",
            ],
        },
        {
            "titulo": "6. Transformación logarítmica",
            "parrafos": [
                "Algunas propiedades (como la viscosidad) suelen tener una "
                "distribución muy sesgada: muchos valores chicos y unos pocos "
                "valores grandes, que pueden variar en varios órdenes de "
                "magnitud.",
                "Para esas columnas (las que contienen 'viscosidad' o "
                "'viscosity' en el nombre), el modelo se entrena sobre "
                "log(1+y) en vez de sobre y directamente (función log1p de "
                "NumPy). Al predecir, el resultado se revierte con la función "
                "inversa expm1. Esto ayuda a que el modelo no esté dominado "
                "por los valores extremos.",
            ],
            "referencias": [
                {
                    "texto": "NumPy: numpy.log1p",
                    "url": "https://numpy.org/doc/stable/reference/generated/numpy.log1p.html",
                },
                {
                    "texto": "NumPy: numpy.expm1",
                    "url": "https://numpy.org/doc/stable/reference/generated/numpy.expm1.html",
                },
            ],
        },
        {
            "titulo": "7. Métrica de evaluación: R²",
            "parrafos": [
                "R² (coeficiente de determinación) mide qué proporción de la "
                "variabilidad de los datos reales explica el modelo, comparado "
                "contra simplemente predecir siempre el promedio.",
                "Un R² de 1.0 significa predicción perfecta; un R² de 0 "
                "significa que el modelo no es mejor que predecir el promedio; "
                "un R² negativo significa que el modelo predice peor que ese "
                "promedio.",
                "En este sistema, R² se calcula con la función r2_score de "
                "scikit-learn, sobre las predicciones out-of-fold descriptas "
                "anteriormente.",
            ],
            "imagen": "diagrama_r2.svg",
            "imagen_alt": "Comparación visual entre un R² alto y un R² bajo",
            "referencias": [
                {
                    "texto": "scikit-learn: r2_score",
                    "url": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.r2_score.html",
                },
                {
                    "texto": "Wikipedia: coeficiente de determinación (R²)",
                    "url": "https://es.wikipedia.org/wiki/Coeficiente_de_determinaci%C3%B3n",
                },
            ],
        },
        {
            "titulo": "8. Reentrenamiento final",
            "parrafos": [
                "Una vez elegido el mejor algoritmo para una propiedad (según "
                "el R² de validación cruzada), ese algoritmo se vuelve a "
                "entrenar UNA VEZ MÁS, pero esta vez usando el 100% de los "
                "datos limpios disponibles para esa propiedad (después de "
                "todos los filtros). Ese es el modelo final que se guarda y "
                "se usa para las predicciones reales.",
            ],
        },
        {
            "titulo": "9. Gráfico de densidad vs. temperatura",
            "parrafos": [
                "El sistema puede generar un gráfico que muestra cómo varía "
                "la densidad predicha en función de la temperatura, "
                "manteniendo la composición fija. Sobre esos puntos se ajusta "
                "una regresión lineal por mínimos cuadrados:",
            ],
            "items": [
                "ρ = pendiente × T + intercepto",
                "El R² del ajuste indica qué tan lineal es la relación.",
                "Se superponen los datos reales del dataset que tienen "
                "exactamente la misma composición (± 0.5% de tolerancia por "
                "componente).",
            ],
        },
        {
            "titulo": "10. Limitaciones a tener en cuenta",
            "items": [
                "Si una propiedad tiene menos de 10 filas válidas después de "
                "todos los filtros, no se entrena ningún modelo para ella.",
                "Los modelos basados en árboles NO extrapolan bien fuera del "
                "rango de composiciones y temperaturas que vieron en el "
                "dataset de entrenamiento: predicciones sobre mezclas muy "
                "distintas a las conocidas son menos confiables.",
                "La calidad de la predicción depende directamente de la "
                "calidad y consistencia del dataset. Usá el panel de "
                "Diagnóstico para detectar problemas.",
                "El filtro de outliers excluye filas automáticamente. Si "
                "sabés que una fila es correcta pero fue excluida, revisá que "
                "sus features sean consistentes.",
            ],
        },
    ]

    return secciones, (
        "Documentación técnica de los algoritmos de Machine Learning utilizados"
    )