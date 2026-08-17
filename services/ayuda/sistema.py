"""
Contenido de la Documentación Técnica del Sistema.
Refleja la arquitectura actual modularizada:
- Blueprints separados con rutas modulares
- Services organizados en paquetes
- JS modularizado (00-namespace a 11-init)
- CSS organizado por capas
- Entrenamiento en background con polling
- Perfil de usuario con avatar
"""


def contenido_sistema():
    """
    Devuelve las secciones de documentación técnica y un subtítulo.
    """
    secciones = [
        {
            "titulo": "1. Arquitectura general",
            "parrafos": [
                "La aplicación está construida en Flask, organizada en "
                "blueprints independientes, cada uno con sus rutas "
                "modularizadas en archivos separados:",
            ],
            "items": [
                "home — landing pública (blueprints/home/).",
                "auth — cuentas, login, logout y OAuth "
                "(blueprints/auth/: routes_forms.py + routes_oauth.py).",
                "mezclas — la app de predicción (blueprints/mezclas/: "
                "routes_page, routes_training, routes_prediction, "
                "routes_dataset, routes_grafico).",
                "admin — panel de administración (blueprints/admin/: "
                "routes_general, routes_dataset, routes_users).",
                "ayuda — este mismo menú (blueprints/ayuda/).",
                "diagnostico — análisis de datos "
                "(blueprints/diagnostico/).",
                "perfil — gestión de cuenta de usuario "
                "(blueprints/perfil/: routes_profile, routes_password, "
                "routes_avatar).",
            ],
            "parrafos_extra": [
                "La capa de lógica de negocio vive en services/, organizada "
                "en paquetes funcionales. utils/ contiene los helpers "
                "transversales: validadores, decoradores, autenticación y "
                "rutas de archivos por usuario.",
            ],
        },
        {
            "titulo": "2. Modularización de servicios",
            "parrafos": [
                "Los servicios están organizados en paquetes, cada uno con "
                "responsabilidad única:",
            ],
            "items": [
                "services/dataset/ — cache, lectura, esquema, validación, "
                "filtros, dataset maestro, filas de usuario y guardado de "
                "predicciones.",
                "services/modeling/ — estado de modelos, persistencia, "
                "información de entrenamiento, última predicción, "
                "entrenamiento en background, predicción, estado general y "
                "gráfico de densidad.",
                "services/diagnostics/ — variables diagnosticables, "
                "métricas y outliers, construcción de motivos y análisis "
                "principal.",
                "services/pdf/ — estilos, documentos, predicción, filas de "
                "dataset y gráfico de densidad.",
                "services/perfil/ — contraseña, datos personales y avatar.",
                "services/ayuda/ — contenido de los documentos de ayuda.",
            ],
            "parrafos_extra": [
                "Los archivos originales (excel_service.py, "
                "mezcla_service.py, diagnostico_service.py, pdf_service.py) "
                "se mantienen como fachadas de compatibilidad que re-exportan "
                "todo desde los paquetes, para no romper imports existentes.",
            ],
        },
        {
            "titulo": "3. Frontend: JavaScript modular",
            "parrafos": [
                "La lógica de la página principal de mezclas está dividida "
                "en 12 módulos secuenciales en static/js/mezclas/:",
            ],
            "items": [
                "00-namespace.js — objeto global IAM y constantes de colores.",
                "01-format.js — helpers de formateo y normalización.",
                "02-ui.js — mensajes, toasts, modal de confirmación.",
                "03-state.js — estado de la mezcla y cálculos de total.",
                "04-temperatura.js — lectura y validación de temperatura.",
                "05-visibilidad.js — control de visibilidad de botones.",
                "06-tablas.js — render de tablas R² y predicción.",
                "07-mezcla-ui.js — chips, progreso y gráfico de tarta.",
                "08-composicion.js — agregar/eliminar elementos.",
                "09-entrenamiento.js — polling de estado del entrenamiento.",
                "10-prediccion.js — predecir, exportar, guardar.",
                "11-init.js — inicialización y compatibilidad global.",
            ],
            "parrafos_extra": [
                "Además existen scripts independientes: flujo.js (wizard de "
                "3 pasos), configuracion_entrenamiento.js (modal de "
                "variables), grafico_tarta.js (tarta 3D SVG), "
                "grafico_densidad.js (Chart.js), dataset_tabla.js, "
                "diagnostico.js, admin.js y perfil.js.",
            ],
        },
        {
            "titulo": "4. Frontend: CSS por capas",
            "parrafos": [
                "Los estilos están organizados en capas temáticas dentro de "
                "static/css/:",
            ],
            "items": [
                "base/theme.css — variables globales y tipografía.",
                "layout/navbar.css — navbar y badges.",
                "components/ui.css — paneles, botones, chips, progreso, "
                "toasts.",
                "components/tables.css — tablas, R², dataset.",
                "features/flujo.css — wizard de 3 pasos.",
                "features/configuracion_entrenamiento.css — modal de "
                "variables.",
                "features/grafico_tarta.css — tarta 3D.",
                "features/grafico_densidad.css — gráfico densidad.",
                "features/diagnostico.css — panel de diagnóstico.",
                "pages/ayuda.css — documentos y redes sociales.",
                "utilities/responsive.css — ajustes mobile.",
            ],
        },
        {
            "titulo": "5. Cuentas, sesiones y contraseñas",
            "parrafos": [
                "Las cuentas se guardan en data/usuarios.json "
                "(utils/auth.py). Las contraseñas NUNCA se guardan en texto "
                "plano: se hashean con werkzeug.security (scrypt con salt) "
                "y se verifican con check_password_hash.",
                "La sesión de cada usuario se guarda en una cookie firmada "
                "criptográficamente con la SECRET_KEY de la app. La cookie "
                "contiene solamente el nombre de usuario; el servidor firma "
                "el contenido para que no se pueda falsificar.",
                "La cookie tiene los flags HttpOnly, SameSite=Lax y Secure "
                "(configurable por variable de entorno "
                "SESSION_COOKIE_SECURE).",
            ],
        },
        {
            "titulo": "6. Roles y control de acceso",
            "parrafos": [
                "Cada usuario tiene un flag es_admin en su registro. Los "
                "decoradores login_required / login_required_json "
                "(utils/auth.py) exigen sesión iniciada; admin_required / "
                "admin_required_json exigen además es_admin=True.",
                "El rol se revalida en CADA request leyendo el JSON de "
                "usuarios, no queda cacheado en la cookie: si un admin le "
                "quita el rol a alguien, esa persona pierde el acceso en su "
                "siguiente request.",
            ],
        },
        {
            "titulo": "7. Aislamiento de datos por usuario",
            "parrafos": [
                "Cada usuario tiene su propia carpeta en "
                "data/users/<username>/, con estos archivos:",
            ],
            "items": [
                "dataset.xlsx — su copia personal del dataset (creada la "
                "primera vez copiando el maestro).",
                "modelo.pkl — su modelo entrenado (serializado con joblib).",
                "info_modelo.json — metadatos del último entrenamiento "
                "(tabla R², tiempo, fecha, filas entrenadas/excluidas).",
                "ultima_prediccion.json — última mezcla + resultado "
                "(para restaurar al reingresar).",
                "avatar.<ext> — foto de perfil (opcional).",
            ],
            "parrafos_extra": [
                "En memoria del proceso, los diccionarios _modelos y "
                "_datasets cachean estos datos por nombre de usuario, para "
                "no leer del disco en cada request. Se usan firmas de "
                "archivo (mtime + tamaño) para detectar cambios externos.",
            ],
        },
        {
            "titulo": "8. Entrenamiento en background con polling",
            "parrafos": [
                "Al apretar 'Modelar', el frontend envía un POST a "
                "/mezclas/entrenar con la lista de variables seleccionadas. "
                "El servidor inicia un hilo (threading.Thread) que entrena "
                "variable por variable.",
                "El frontend hace polling cada 1.2 segundos a "
                "/mezclas/entrenar/estado para obtener el progreso: "
                "variable actual, total, tiempo transcurrido, y si terminó "
                "(listo=True) o hubo error.",
                "Cada usuario tiene su propio threading.Lock: evita que la "
                "MISMA persona dispare dos entrenamientos en paralelo "
                "(doble click, dos pestañas), sin bloquear a otros usuarios.",
            ],
            "codigo": (
                "# Flujo de entrenamiento (simplificado)\n"
                "POST /mezclas/entrenar  →  inicia hilo\n"
                "GET  /mezclas/entrenar/estado  →  polling cada 1.2s\n"
                "     respuesta: {corriendo, progreso, total,\n"
                "                 columna, tiempo, listo, tabla_r2}"
            ),
        },
        {
            "titulo": "9. Dataset maestro y detección de inconsistencias",
            "parrafos": [
                "El archivo definido en Config.ARCHIVO_DATASET es el dataset "
                "'maestro': la plantilla que se copia a cada usuario nuevo. "
                "El administrador lo edita desde /admin/dataset.",
                "Una fila se marca como inconsistente si le falta algún valor "
                "en las columnas de composición o en la temperatura, o si la "
                "suma de las columnas de composición no da aproximadamente "
                "100% (tolerancia de ±0.5 puntos porcentuales).",
                "Desde el panel de Admin se puede subir un nuevo dataset "
                "maestro (services/dataset_upload_service.py). Esto crea "
                "backups automáticos, reemplaza el maestro activo, "
                "sobreescribe el dataset personal del admin y borra el "
                "modelo entrenado.",
            ],
            "codigo": (
                "# services/dataset/validation.py (simplificado)\n"
                "def analizar_fila(fila, columnas_pct, col_temp):\n"
                "    faltantes = [c for c in obligatorias\n"
                "                 if pd.isna(fila[c])]\n"
                "    suma = sum(fila[c] for c in presentes)\n"
                "    inconsistente = bool(faltantes) or\n"
                "                    abs(suma - 100) > 0.5"
            ),
        },
        {
            "titulo": "10. Detección dinámica de columnas",
            "parrafos": [
                "El sistema detecta automáticamente la estructura del "
                "dataset sin depender de nombres hardcodeados:",
            ],
            "items": [
                "Composición: columnas terminadas en '_pct' dentro de las "
                "primeras 11 posiciones (A-K). Esto evita confundir con "
                "variables objetivo que también terminan en '_pct' (como "
                "Fraccion_Cristalina_pct).",
                "Temperatura: se busca por nombre con una lista de "
                "preferencia y un regex que rechaza falsos positivos como "
                "'Temperatura_Liquidus_K'.",
                "Variables entrenables: todas las columnas numéricas desde "
                "la posición 12 en adelante que no sean features.",
                "La cantidad de columnas de composición es configurable con "
                "la variable de entorno CANTIDAD_COLUMNAS_COMPOSICION.",
            ],
        },
        {
            "titulo": "11. Login social (OAuth) con Authlib",
            "parrafos": [
                "services/oauth_service.py registra los proveedores Google "
                "y X usando Authlib SOLO si sus credenciales (Client "
                "ID/Secret) están definidas como variables de entorno. Si "
                "faltan, el proveedor queda deshabilitado (el botón no se "
                "muestra) sin romper la aplicación.",
                "Al volver del proveedor externo (callback), se busca si ya "
                "existe un usuario vinculado a ese proveedor_id; si no "
                "existe, se crea una cuenta nueva derivando un nombre de "
                "usuario disponible a partir del email o username de la red "
                "social.",
            ],
        },
        {
            "titulo": "12. Perfil de usuario y avatar",
            "parrafos": [
                "El módulo de perfil (blueprints/perfil/ + "
                "services/perfil/) permite al usuario:",
            ],
            "items": [
                "Ver y actualizar sus datos personales (nombre, email).",
                "Cambiar su contraseña (solo cuentas locales, no sociales).",
                "Subir, ver y eliminar su foto de perfil (avatar).",
            ],
            "parrafos_extra": [
                "El avatar se guarda en data/users/<username>/avatar.<ext> "
                "con validación de extensión (.png, .jpg, .jpeg, .webp) y "
                "tamaño máximo de 2 MB. Se muestra en el navbar y en la "
                "página de perfil.",
            ],
        },
        {
            "titulo": "13. Generación de PDF con ReportLab",
            "parrafos": [
                "Los PDF se generan con ReportLab (biblioteca pura Python, "
                "sin dependencias nativas), organizados en services/pdf/:",
            ],
            "items": [
                "styles.py — estilos base y de tablas reutilizables.",
                "document.py — documentos de ayuda (tutorial, modelos, "
                "sistema).",
                "prediction.py — predicción de una mezcla.",
                "dataset_row.py — una fila del dataset.",
                "density_chart.py — gráfico de densidad vs. temperatura "
                "(dibujado con primitivas de ReportLab).",
            ],
            "parrafos_extra": [
                "Los documentos de ayuda se definen como datos estructurados "
                "en services/ayuda/ (listas de secciones). La misma "
                "estructura se usa para el HTML en pantalla y para el PDF, "
                "evitando mantener el contenido dos veces.",
            ],
        },
        {
            "titulo": "14. Panel de diagnóstico",
            "parrafos": [
                "El módulo de diagnóstico (blueprints/diagnostico/ + "
                "services/diagnostics/) analiza una variable objetivo y "
                "detecta:",
            ],
            "items": [
                "Filas con composición fuera de 100%.",
                "Objetivos atípicos (IQR + Z-score robusto con MAD).",
                "Temperaturas atípicas (IQR).",
                "Features faltantes.",
                "Componentes fuera de rango 0-100%.",
                "Filas duplicadas exactas.",
                "Target ≤ 0 (excluido del entrenamiento).",
                "Temperatura inconsistente (reemplazada por 0).",
            ],
            "parrafos_extra": [
                "El diagnóstico es de solo lectura: no modifica ningún dato. "
                "Muestra hasta 200 filas sospechosas con sus motivos.",
            ],
        },
        {
            "titulo": "15. Testing",
            "parrafos": [
                "El proyecto usa pytest con fixtures que aíslan "
                "completamente los datos de test (directorio temporal, "
                "usuarios.json temporal, dataset maestro sintético).",
                "Los tests cubren: validadores, constantes, detección de "
                "columnas, rutas de auth/home/admin/mezclas/perfil, "
                "gráfico de densidad, y funciones de perfil.",
            ],
            "codigo": (
                "# Ejecutar tests\n"
                "pytest tests/ -v --tb=short\n\n"
                "# Con cobertura\n"
                "pytest tests/ -v --cov=. --cov-report=term-missing"
            ),
        },
        {
            "titulo": "16. Despliegue (Render)",
            "parrafos": [
                "La app está configurada para desplegarse en Render con "
                "Gunicorn (1 worker, 4 threads, timeout 300s). El archivo "
                "render.yaml define:",
            ],
            "items": [
                "Disco persistente de 1 GB montado en /opt/data para "
                "usuarios, modelos y datasets.",
                "Health check en /healthz.",
                "Variables de entorno para SECRET_KEY, SESSION_COOKIE_SECURE, "
                "DATA_DIR y credenciales OAuth.",
                "Python 3.12 como runtime.",
            ],
        },
    ]

    return secciones, (
        "Documentación técnica interna — Solo para administradores"
    )