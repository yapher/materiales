"""
Contenido de los 3 documentos del menú de Ayuda. Se define acá, en
Python, como estructura de datos simple (lista de secciones), para que
la MISMA información se pueda mostrar en HTML (templates/ayuda/documento.html)
y exportar a PDF (services/pdf_service.py) sin duplicar el texto.
"""


def contenido_tutorial():
    secciones = [
        {
            "titulo": "1. Crear una cuenta e iniciar sesión",
            "parrafos": [
                "Para usar la aplicación necesitás una cuenta. Podés registrarte con "
                "usuario y contraseña desde 'Registrarse', o iniciar sesión con Google "
                "o X si el administrador los tiene habilitados.",
                "Cada cuenta tiene su propio dataset y su propio modelo entrenado: lo "
                "que hace un usuario no afecta a los demás.",
            ],
        },
        {
            "titulo": "2. Entrenar tu modelo",
            "parrafos": [
                "En la sección 'Predicción' encontrás el botón 'Entrenar Modelo'. Al "
                "apretarlo, el sistema toma automáticamente tu copia del dataset y "
                "entrena, una por una, un modelo de Machine Learning para cada "
                "propiedad del material (viscosidad, densidad, etc.).",
                "El progreso se muestra en vivo, variable por variable, con el tiempo "
                "transcurrido. Al terminar, vas a ver una tabla con el R² (una medida "
                "de qué tan bien predice cada modelo) para cada propiedad.",
            ],
            "items": [
                "R² cercano a 1 (verde): el modelo predice muy bien esa propiedad.",
                "R² medio (amarillo): predicción aceptable, con más margen de error.",
                "R² bajo (naranja/rojo): esa propiedad es difícil de predecir con los "
                "datos actuales; conviene tomar esa predicción con cautela.",
            ],
        },
        {
            "titulo": "3. Armar una mezcla y predecir",
            "parrafos": [
                "Elegí cada elemento de la composición (CaO, SiO2, Al2O3, etc.) y su "
                "porcentaje. La barra de progreso te muestra cuánto llevás sumado: "
                "tiene que llegar exactamente a 100% para poder predecir.",
                "Ingresá también la temperatura del proceso en grados Celsius, y "
                "apretá 'Predecir'. El sistema va a mostrar el valor estimado de cada "
                "propiedad para esa mezcla y esa temperatura.",
            ],
        },
        {
            "titulo": "4. Recomendaciones de uso",
            "items": [
                "Si cambiás la mezcla, la predicción anterior se invalida automáticamente "
                "y hay que volver a predecir.",
                "No hace falta reentrenar cada vez que predecís: el modelo entrenado "
                "queda guardado entre sesiones (mientras no lo borres desde Admin).",
                "Si algo falla, el mensaje de error suele indicar la causa (por ejemplo, "
                "\"Entrená el modelo primero\" si todavía no entrenaste ninguno).",
            ],
        },
    ]
    return secciones, "Guía para usar la aplicación paso a paso"


def contenido_modelos():
    secciones = [
        {
            "titulo": "1. Enfoque general: un modelo por propiedad",
            "parrafos": [
                "El sistema NO entrena un único modelo grande. Por cada propiedad "
                "objetivo del dataset (viscosidad, densidad, etc.) se entrena un "
                "modelo de regresión INDEPENDIENTE, usando siempre como variables de "
                "entrada (features) la composición química (los *_pct) más la "
                "temperatura del proceso (Temperatura_C).",
                "Esto permite que cada propiedad use el algoritmo que mejor le queda, "
                "en vez de forzar un único modelo para todas.",
            ],
            "imagen": "diagrama_pipeline.svg",
            "imagen_alt": "Pipeline: dataset, candidatos, validación cruzada, selección y reentrenamiento",
        },
        {
            "titulo": "2. Algoritmos candidatos evaluados",
            "parrafos": [
                "Para cada propiedad, el sistema entrena y compara tres algoritmos de "
                "ensamble basados en árboles de decisión (todos de scikit-learn), y se "
                "queda con el que mejor R² obtiene por validación cruzada:",
            ],
            "items": [
                "RandomForestRegressor (400 árboles, min_samples_leaf=2, "
                "max_features='sqrt'): construye muchos árboles de decisión sobre "
                "submuestras aleatorias de los datos (bagging) y promedia sus "
                "predicciones. Reduce el sobreajuste típico de un árbol individual.",
                "ExtraTreesRegressor (mismos hiperparámetros base): similar a Random "
                "Forest, pero además de muestrear los datos, elige los puntos de corte "
                "de cada árbol de forma más aleatoria. Suele ser más rápido y a veces "
                "generaliza mejor con pocos datos.",
                "GradientBoostingRegressor (400 estimadores, max_depth=3, "
                "learning_rate=0.05, subsample=0.8): construye los árboles de forma "
                "SECUENCIAL, donde cada árbol nuevo corrige los errores (residuos) que "
                "dejó el conjunto de árboles anterior. Suele lograr mayor precisión, a "
                "costa de ser más sensible a los hiperparámetros.",
            ],
            "imagen": "diagrama_ensamble.svg",
            "imagen_alt": "Comparación entre bagging (árboles en paralelo) y boosting (árboles en secuencia)",
            "referencias": [
                {"texto": "scikit-learn: RandomForestRegressor (documentación oficial)", "url": "https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html"},
                {"texto": "scikit-learn: ExtraTreesRegressor (documentación oficial)", "url": "https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesRegressor.html"},
                {"texto": "scikit-learn: GradientBoostingRegressor (documentación oficial)", "url": "https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html"},
                {"texto": "scikit-learn: guía de métodos de ensamble (bagging vs. boosting)", "url": "https://scikit-learn.org/stable/modules/ensemble.html"},
            ],
        },
        {
            "titulo": "3. Selección automática de modelo: validación cruzada K-Fold",
            "parrafos": [
                "Para decidir qué algoritmo usar en cada propiedad, se aplica "
                "validación cruzada K-Fold (K=5 por defecto, o menos si hay pocos "
                "datos disponibles para esa propiedad).",
                "El dataset se divide en K partes ('folds'). En cada iteración, el "
                "modelo se entrena con K-1 partes y se evalúa sobre la parte restante "
                "(que NO vio durante el entrenamiento de esa iteración). Repitiendo "
                "esto K veces, se obtiene una predicción 'out-of-fold' (OOF) para cada "
                "fila del dataset, generada siempre por un modelo que no la vio.",
                "El R² se calcula sobre esas predicciones OOF, nunca sobre datos de "
                "entrenamiento directo. Esto da una estimación honesta de qué tan bien "
                "generaliza el modelo a datos nuevos, evitando el sobreajuste que se "
                "obtendría si se midiera el R² sobre los mismos datos de entrenamiento.",
            ],
            "imagen": "diagrama_kfold.svg",
            "imagen_alt": "Esquema de validación cruzada K-Fold con K=5",
            "referencias": [
                {"texto": "scikit-learn: KFold — documentación oficial", "url": "https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.KFold.html"},
                {"texto": "scikit-learn: guía de validación cruzada", "url": "https://scikit-learn.org/stable/modules/cross_validation.html"},
            ],
        },
        {
            "titulo": "4. Transformación logarítmica para variables sesgadas",
            "parrafos": [
                "Algunas propiedades (como la viscosidad) suelen tener una "
                "distribución muy sesgada: muchos valores chicos y unos pocos valores "
                "grandes, que pueden variar en varios órdenes de magnitud.",
                "Para esas columnas (definidas en COLUMNAS_LOG dentro de "
                "services/ml_service.py), el modelo se entrena sobre log(1+y) en vez "
                "de sobre y directamente (función log1p de NumPy). Al predecir, el "
                "resultado se revierte con la función inversa expm1. Esto ayuda a que "
                "el modelo no esté dominado por los valores extremos.",
            ],
            "referencias": [
                {"texto": "NumPy: numpy.log1p — documentación oficial", "url": "https://numpy.org/doc/stable/reference/generated/numpy.log1p.html"},
                {"texto": "NumPy: numpy.expm1 — documentación oficial", "url": "https://numpy.org/doc/stable/reference/generated/numpy.expm1.html"},
            ],
        },
        {
            "titulo": "5. Métrica de evaluación: R² (coeficiente de determinación)",
            "parrafos": [
                "R² mide qué proporción de la variabilidad de los datos reales "
                "explica el modelo, comparado contra simplemente predecir siempre el "
                "promedio. Un R² de 1.0 significa predicción perfecta; un R² de 0 "
                "significa que el modelo no es mejor que predecir el promedio; un R² "
                "negativo significa que el modelo predice peor que ese promedio.",
                "En este sistema, R² se calcula con la función r2_score de "
                "scikit-learn, sobre las predicciones out-of-fold descriptas arriba.",
            ],
            "imagen": "diagrama_r2.svg",
            "imagen_alt": "Comparación visual entre un R² alto y un R² bajo",
            "referencias": [
                {"texto": "scikit-learn: r2_score — documentación oficial", "url": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.r2_score.html"},
                {"texto": "Wikipedia: coeficiente de determinación (R²)", "url": "https://es.wikipedia.org/wiki/Coeficiente_de_determinaci%C3%B3n"},
            ],
        },
        {
            "titulo": "6. Reentrenamiento final",
            "parrafos": [
                "Una vez elegido el mejor algoritmo para una propiedad (según el R² de "
                "validación cruzada), ese algoritmo se vuelve a entrenar UNA VEZ MÁS, "
                "pero esta vez usando el 100% de los datos disponibles para esa "
                "propiedad (no solo K-1 folds). Ese es el modelo final que se guarda "
                "y se usa para las predicciones reales.",
            ],
        },
        {
            "titulo": "7. Limitaciones a tener en cuenta",
            "items": [
                "Si una propiedad tiene menos de 10 filas con datos completos, no se "
                "entrena ningún modelo para ella (se descarta).",
                "Los modelos basados en árboles NO extrapolan bien fuera del rango de "
                "composiciones y temperaturas que vieron en el dataset de "
                "entrenamiento: predicciones sobre mezclas muy distintas a las "
                "conocidas son menos confiables.",
                "La calidad de la predicción depende directamente de la calidad y "
                "consistencia del dataset (ver el panel de Admin para la detección de "
                "filas inconsistentes).",
            ],
        },
    ]
    return secciones, "Documentación técnica de los algoritmos de Machine Learning utilizados"


def contenido_sistema():
    secciones = [
        {
            "titulo": "1. Arquitectura general",
            "parrafos": [
                "La aplicación está construida en Flask, organizada en blueprints "
                "(módulos de rutas independientes): home (landing pública), auth "
                "(cuentas/login), mezclas (la app de predicción en sí), admin "
                "(panel de administración) y ayuda (este mismo menú).",
                "La capa de lógica de negocio vive en services/ (excel_service, "
                "mezcla_service, ml_service, oauth_service, pdf_service), separada de "
                "las rutas HTTP. utils/ contiene los helpers transversales: "
                "validadores, manejo de errores, autenticación y rutas de archivos "
                "por usuario.",
            ],
        },
        {
            "titulo": "2. Cuentas, sesiones y contraseñas",
            "parrafos": [
                "Las cuentas se guardan en data/usuarios.json (utils/auth.py). Las "
                "contraseñas NUNCA se guardan en texto plano: se hashean con "
                "werkzeug.security.generate_password_hash (PBKDF2 con salt) y se "
                "verifican con check_password_hash, que nunca revierte el hash, solo "
                "compara.",
                "La sesión de cada usuario se guarda en una cookie firmada "
                "criptográficamente con la SECRET_KEY de la app (flask.session). La "
                "cookie contiene solamente el nombre de usuario; el servidor firma el "
                "contenido para que no se pueda falsificar sin conocer la clave.",
                "La cookie tiene los flags HttpOnly (no accesible desde JavaScript), "
                "SameSite=Lax (mitiga CSRF básico) y Secure quedará activo cuando el "
                "sitio corra sobre HTTPS (variable de entorno SESSION_COOKIE_SECURE).",
            ],
        },
        {
            "titulo": "3. Roles y control de acceso",
            "parrafos": [
                "Cada usuario tiene un flag es_admin en su registro. Los decoradores "
                "login_required / login_required_json (utils/auth.py) exigen sesión "
                "iniciada; admin_required / admin_required_json exigen además "
                "es_admin=True. El rol se revalida en CADA request leyendo el JSON de "
                "usuarios, no queda 'cacheado' en la cookie: si un admin le quita el "
                "rol a alguien, esa persona pierde el acceso en su siguiente request, "
                "aunque su sesión siga abierta.",
            ],
        },
        {
            "titulo": "4. Aislamiento de datos por usuario",
            "parrafos": [
                "Cada usuario tiene su propia carpeta en data/users/<username>/, con "
                "tres archivos: dataset.xlsx (su copia personal del dataset, creada "
                "la primera vez que la necesita, copiando el dataset maestro), "
                "modelo.pkl (su modelo entrenado, serializado con joblib) e "
                "info_modelo.json (metadatos del último entrenamiento: tabla de R², "
                "tiempo y fecha).",
                "En memoria del proceso, los diccionarios _modelos y _datasets "
                "(mezcla_service.py y excel_service.py) cachean estos datos por "
                "nombre de usuario, para no leer del disco en cada request.",
            ],
        },
        {
            "titulo": "5. Entrenamiento en vivo con Server-Sent Events (SSE)",
            "parrafos": [
                "El botón 'Entrenar Modelo' abre una conexión EventSource hacia "
                "/mezclas/entrenar_stream. El servidor entrena columna por columna y "
                "va emitiendo eventos 'data: {...}\\n\\n' con el progreso, en vez de "
                "bloquear la respuesta hasta terminar todo el entrenamiento.",
                "Un detalle importante de implementación: si la sesión del usuario "
                "es nueva, el user_id se resuelve ANTES de armar la Response (no "
                "dentro del generador), porque los headers HTTP —incluida la cookie "
                "nueva— se envían antes de que el generador empiece a producir datos. "
                "Resolverlo tarde haría que la cookie de sesión nunca llegue al "
                "navegador.",
                "Cada usuario tiene su propio threading.Lock para el entrenamiento: "
                "evita que la MISMA persona dispare dos entrenamientos en paralelo "
                "(doble click, dos pestañas), sin bloquear a otros usuarios entre sí.",
            ],
        },
        {
            "titulo": "6. Dataset maestro y detección de inconsistencias",
            "parrafos": [
                "El archivo definido en Config.ARCHIVO_DATASET es el dataset "
                "'maestro': la plantilla que se copia a cada usuario nuevo. El "
                "administrador lo edita desde /admin/dataset (services/excel_service.py, "
                "funciones *_maestro).",
                "Una fila se marca como inconsistente si le falta algún valor en las "
                "columnas de composición o en Temperatura_C, o si la suma de las "
                "columnas de composición (*_pct) no da aproximadamente 100% (tolerancia "
                "de ±0.5 puntos porcentuales).",
                "Importante: editar el dataset maestro NO modifica retroactivamente "
                "las copias que los usuarios ya descargaron a su sesión. Para que un "
                "usuario reciba los cambios, tiene que recargar su dataset.",
            ],
            "codigo": (
                "# services/excel_service.py (simplificado)\n"
                "def _analizar_fila(fila, columnas_pct):\n"
                "    faltantes = [c for c in columnas_obligatorias if pd.isna(fila[c])]\n"
                "    suma = sum(fila[c] for c in columnas_pct if not pd.isna(fila[c]))\n"
                "    inconsistente = bool(faltantes) or abs(suma - 100) > 0.5"
            ),
        },
        {
            "titulo": "7. Login social (OAuth) con Authlib",
            "parrafos": [
                "services/oauth_service.py registra los proveedores Google y X "
                "usando Authlib SOLO si sus credenciales (Client ID/Secret) están "
                "definidas como variables de entorno. Si faltan, el proveedor queda "
                "deshabilitado (el botón no se muestra) sin romper la aplicación.",
                "Al volver del proveedor externo (callback), se busca si ya existe "
                "un usuario vinculado a ese proveedor_id; si no existe, se crea una "
                "cuenta nueva derivando un nombre de usuario disponible a partir del "
                "email o username de la red social.",
            ],
        },
        {
            "titulo": "8. Generación de PDF",
            "parrafos": [
                "Los documentos de este menú de Ayuda se definen como datos "
                "estructurados en services/ayuda_content.py (listas de secciones con "
                "título, párrafos, ítems y bloques de código). La misma estructura "
                "se usa para el HTML en pantalla y para el PDF, evitando mantener el "
                "contenido dos veces.",
                "El PDF se genera con ReportLab (biblioteca pura Python, sin "
                "dependencias nativas), armando el documento como una secuencia de "
                "Flowables (Paragraph, ListFlowable, Preformatted) sobre un "
                "SimpleDocTemplate en tamaño A4.",
            ],
        },
    ]
    return secciones, "Documentación técnica interna — Solo para administradores"
