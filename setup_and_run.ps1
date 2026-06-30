$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot

function Write-Step($msg) {
    Write-Host ""
    Write-Host "=== $msg ===" -ForegroundColor Cyan
}

# =========================================================
# 1) DETECTAR PYTHON (sin instalar nada, asumimos que ya esta)
# =========================================================
Write-Step "Verificando Python"

$pyCmd = $null
foreach ($candidate in @("python", "py")) {
    try {
        $verOutput = & $candidate --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $verOutput -match "Python 3\.(1[0-9]|[2-9][0-9])") {
            $pyCmd = $candidate
            Write-Host "Encontrado: $verOutput (comando: $candidate)"
            break
        }
    } catch {}
}

if (-not $pyCmd) {
    Write-Host "No se encontro Python en el PATH." -ForegroundColor Red
    Write-Host "Verificalo abriendo una terminal y escribiendo: python --version" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

# =========================================================
# 2) INSTALAR DEPENDENCIAS (a nivel de usuario, SIN venv,
#    SIN admin: van a %APPDATA%\Python\...)
# =========================================================
Write-Step "Verificando dependencias"

$reflexCheck = & $pyCmd -m pip show reflex 2>$null
if (-not $reflexCheck) {
    Write-Step "Instalando dependencias (puede tardar varios minutos)"
    & $pyCmd -m pip install --user --upgrade pip
    & $pyCmd -m pip install --user reflex==0.7.8
    & $pyCmd -m pip install --user pandas==2.2.3
    & $pyCmd -m pip install --user scikit-learn==1.7.1
    & $pyCmd -m pip install --user openpyxl
} else {
    Write-Host "Dependencias ya instaladas, se omite este paso."
}

if (-not (Test-Path ".\requirements.txt")) {
@'
reflex==0.7.8
pandas==2.2.3
scikit-learn==1.7.1
openpyxl
'@ | Set-Content -Path ".\requirements.txt" -Encoding UTF8
}

# =========================================================
# 3) INICIALIZAR PROYECTO REFLEX (si no existe)
#    OJO: forzamos --name Materiales_V1 para que el nombre de
#    la app NO dependa de como se llame la carpeta raiz
#    (sino reflex busca "<carpeta>.py" en vez de "Materiales_V1.py")
# =========================================================
if (-not (Test-Path ".\rxconfig.py")) {
    Write-Step "Inicializando proyecto Reflex"
    & $pyCmd -m reflex init --name Materiales_V1 --template blank --loglevel warning
}

# Auto-correccion: si rxconfig.py ya existe con un app_name distinto
# de "Materiales_V1" (por ejemplo de una corrida anterior donde la
# carpeta raiz tenia otro nombre), lo corregimos aca.
if (Test-Path ".\rxconfig.py") {
    $rxContent = Get-Content ".\rxconfig.py" -Raw
    if ($rxContent -match 'app_name\s*=\s*"([^"]+)"') {
        $appNameActual = $Matches[1]
        if ($appNameActual -ne "Materiales_V1") {
            Write-Step "Corrigiendo rxconfig.py ($appNameActual -> Materiales_V1)"
            $rxContent = $rxContent -replace 'app_name\s*=\s*"[^"]+"', 'app_name="Materiales_V1"'
            Set-Content -Path ".\rxconfig.py" -Value $rxContent -Encoding UTF8

            $stray = ".\$appNameActual"
            if (Test-Path $stray) {
                Write-Host "Aviso: la carpeta '$appNameActual\' quedo de una inicializacion anterior y ya no se usa." -ForegroundColor Yellow
                Write-Host "El proyecto real esta en .\Materiales_V1\. Podes borrar '$appNameActual\' a mano." -ForegroundColor Yellow
            }
        }
    }
}

# =========================================================
# 4) CREAR ESTRUCTURA DE CARPETAS
# =========================================================
Write-Step "Verificando estructura de carpetas"

$pkg      = ".\Materiales_V1"
$services = "$pkg\services"

New-Item -ItemType Directory -Force -Path $services       | Out-Null
New-Item -ItemType Directory -Force -Path ".\assets\data" | Out-Null

if (-not (Test-Path "$pkg\__init__.py"))      { New-Item -ItemType File -Path "$pkg\__init__.py"      | Out-Null }
if (-not (Test-Path "$services\__init__.py")) { New-Item -ItemType File -Path "$services\__init__.py" | Out-Null }

# =========================================================
# 5) ESCRIBIR ARCHIVOS DEL PROYECTO (solo si no existen,
#    para no pisar cambios que hayas hecho despues)
# =========================================================
Write-Step "Verificando archivos del proyecto"

# -----------------------------------------------------------------
# FIX: "reflex init --template blank" ya crea Materiales_V1.py con
# el contenido por defecto del template ("Welcome to Reflex!").
# Eso hacia que el "if (-not (Test-Path ...))" de abajo fuera FALSE
# desde la primera corrida (el archivo ya existia), y entonces
# nuestro codigo real (con ELEMENTOS, State, botones, etc.) nunca
# se llegaba a escribir. Resultado: la app siempre mostraba la
# pagina default de Reflex, en TODAS las corridas futuras tambien
# (porque una vez creado, el archivo "ya existe" para siempre).
#
# Solucion: si el archivo existe pero NO contiene nuestro marcador
# unico ("ELEMENTOS", que solo aparece en nuestra version), es el
# template default -> lo borramos para que el bloque de abajo lo
# recree con el codigo real.
# -----------------------------------------------------------------
if (Test-Path "$pkg\Materiales_V1.py") {
    $contenidoActual = Get-Content "$pkg\Materiales_V1.py" -Raw
    if ($contenidoActual -notmatch "ELEMENTOS") {
        Write-Host "Detectado template por defecto de Reflex, se reemplaza por la app real" -ForegroundColor Yellow
        Remove-Item "$pkg\Materiales_V1.py" -Force
    }
}

if (-not (Test-Path "$pkg\Materiales_V1.py")) {
Write-Host "Creando Materiales_V1.py"
@'
import reflex as rx
from .state import State


ELEMENTOS = [
    "CaO","SiO2","Al2O3","MgO",
    "Na2O","K2O","Li2O","CaF2",
    "Fe2O3","MnO","TiO2"
]


def index():

    return rx.container(

        rx.vstack(

            rx.heading("IA Mezclas Industriales", size="8"),

            rx.hstack(

                rx.select(
                    ELEMENTOS,
                    placeholder="Elemento",
                    value=State.elemento_sel,
                    on_change=State.set_elemento,
                ),

                rx.input(
                    placeholder="Porcentaje",
                    type="number",
                    value=State.porcentaje_sel,
                    on_change=State.set_porcentaje,
                ),

                rx.button(
                    "Agregar",
                    on_click=State.agregar_elemento
                ),
            ),

            # =========================
            # TEMPERATURA (NUEVO INPUT)
            # =========================
            rx.hstack(
                rx.text("Temperatura del proceso (C):"),
                rx.input(
                    placeholder="Ej: 1500",
                    type="number",
                    value=State.temperatura,
                    on_change=State.set_temperatura,
                    width="150px",
                ),
                align="center",
                spacing="2",
            ),

            rx.hstack(

                rx.button(
                    "Cargar Dataset",
                    on_click=State.cargar_excel,
                    disabled=~State.mezcla_completa | State.ocupado,
                    loading=State.cargando,
                ),

                rx.button(
                    "Entrenar Modelo",
                    on_click=State.entrenar,
                    disabled=~State.dataset_listo | State.ocupado,
                    loading=State.entrenando,
                ),

                rx.button(
                    "Predecir",
                    on_click=State.predecir,
                    disabled=~State.modelo_listo | State.ocupado,
                    loading=State.prediciendo,
                ),
            ),

            # =========================
            # INDICADOR DE PROGRESO GLOBAL
            # =========================
            rx.cond(
                State.ocupado,
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.text("Procesando, espera un momento..."),
                    spacing="2",
                ),
            ),

            rx.text(State.mensaje),

            # =========================
            # MIX
            # =========================
            rx.foreach(
                State.mix,
                lambda x: rx.card(
                    rx.hstack(
                        rx.badge(x["elemento"]),
                        rx.text(f"{x['pct']} %"),
                        rx.button(
                            "X",
                            on_click=lambda: State.eliminar_elemento(x["elemento"])
                        )
                    )
                )
            ),

            rx.text(f"Progreso: {State.porcentaje_total} %"),

            rx.divider(),

            # =========================
            # TABLA R2
            # =========================
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Variable"),
                        rx.table.column_header_cell("R2")
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        State.tabla_r2,
                        lambda row: rx.table.row(
                            rx.table.cell(row["columna"]),
                            rx.table.cell(row["r2"])
                        )
                    )
                ),
            ),

            rx.divider(),

            # =========================
            # TABLA PREDICCION
            # =========================
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Variable"),
                        rx.table.column_header_cell("Prediccion")
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        State.tabla_prediccion,
                        lambda row: rx.table.row(
                            rx.table.cell(row["columna"]),
                            rx.table.cell(row["prediccion"])
                        )
                    )
                ),
            ),

            spacing="4"
        ),

        padding="20px"
    )


app = rx.App()
app.add_page(index)
'@ | Set-Content -Path "$pkg\Materiales_V1.py" -Encoding UTF8
}

if (-not (Test-Path "$pkg\state.py")) {
Write-Host "Creando state.py"
@'
import time

import reflex as rx
import numpy as np

from .services.excel_service import cargar_dataset
from .services.ml_service import entrenar_una_columna


modelos_global = None
df_global = None


COLUMNAS = [
    "CaO_pct",
    "SiO2_pct",
    "Al2O3_pct",
    "MgO_pct",
    "Na2O_pct",
    "K2O_pct",
    "Li2O_pct",
    "CaF2_pct",
    "Fe2O3_pct",
    "MnO_pct",
    "TiO2_pct"
]

# Temperatura_C es una entrada conocida (la define el usuario), igual
# que la composicion. Se agrega como feature extra para TODOS los modelos.
COLUMNAS_MODELO = COLUMNAS + ["Temperatura_C"]


class State(rx.State):

    resumen: str = ""
    mensaje: str = ""

    mix: list[dict] = []

    elemento_sel: str = ""
    porcentaje_sel: str = ""

    temperatura: str = ""

    dataset_listo: bool = False
    modelo_listo: bool = False
    mezcla_completa: bool = False

    porcentaje_total: float = 0

    # flags de carga para mostrar spinners / botones "loading"
    cargando: bool = False
    entrenando: bool = False
    prediciendo: bool = False

    # contador de progreso y tiempo del entrenamiento
    progreso_entrenamiento: int = 0
    total_entrenamiento: int = 0
    tiempo_entrenamiento: float = 0.0

    # tablas para UI
    tabla_r2: list[dict] = []
    tabla_prediccion: list[dict] = []

    # =========================
    # VARS CALCULADAS
    # =========================
    @rx.var
    def ocupado(self) -> bool:
        return self.cargando or self.entrenando or self.prediciendo

    @rx.var
    def progreso_pct(self) -> int:
        if self.total_entrenamiento == 0:
            return 0
        return int(self.progreso_entrenamiento / self.total_entrenamiento * 100)

    # =========================
    # INPUT
    # =========================

    def set_elemento(self, value: str):
        self.elemento_sel = value

    def set_porcentaje(self, value: str):
        self.porcentaje_sel = value

    def set_temperatura(self, value: str):
        self.temperatura = value

    # =========================
    # UTILIDAD
    # =========================

    def total_porcentaje(self):
        return sum(e["pct"] for e in self.mix)

    def actualizar_estado(self):
        self.porcentaje_total = self.total_porcentaje()
        self.mezcla_completa = (self.porcentaje_total == 100)

    # =========================
    # AGREGAR
    # =========================

    def agregar_elemento(self):

        if not self.elemento_sel:
            self.mensaje = "Selecciona un elemento"
            return

        try:
            pct = float(self.porcentaje_sel)
        except:
            self.mensaje = "Porcentaje invalido"
            return

        total = self.total_porcentaje()

        if total >= 100:
            self.mensaje = "Mezcla completa"
            return

        if total + pct > 100:
            self.mensaje = "No puede superar 100%"
            return

        for e in self.mix:
            if e["elemento"] == self.elemento_sel:
                self.mensaje = "Elemento ya agregado"
                return

        self.mix.append({
            "elemento": self.elemento_sel,
            "pct": pct
        })

        self.actualizar_estado()

        self.elemento_sel = ""
        self.porcentaje_sel = ""

        self.mensaje = f"Total: {self.porcentaje_total}%"

    # =========================
    # ELIMINAR
    # =========================

    def eliminar_elemento(self, elemento: str):

        global df_global, modelos_global

        self.mix = [e for e in self.mix if e["elemento"] != elemento]
        self.actualizar_estado()

        # Se modifico la mezcla: cualquier dataset/modelo/tabla
        # calculada antes ya no corresponde a la mezcla actual.
        # Reseteamos todo como si el programa se hubiera ejecutado
        # de nuevo. (La temperatura NO se borra: es independiente de
        # que oxidos haya en la mezcla.)
        df_global = None
        modelos_global = None

        self.dataset_listo = False
        self.modelo_listo = False
        self.resumen = ""
        self.tabla_r2 = []
        self.tabla_prediccion = []
        self.progreso_entrenamiento = 0
        self.total_entrenamiento = 0
        self.tiempo_entrenamiento = 0.0
        self.mensaje = "Mezcla modificada: volve a cargar el dataset y entrenar"

    # =========================
    # DATASET
    # =========================

    def cargar_excel(self):

        global df_global

        self.cargando = True
        self.mensaje = "Cargando dataset..."
        yield  # fuerza a mostrar el spinner ANTES de la parte pesada

        df_global = cargar_dataset()

        self.resumen = f"Filas: {len(df_global)} | Columnas: {len(df_global.columns)}"
        self.dataset_listo = True
        self.cargando = False
        self.mensaje = f"Dataset cargado: {len(df_global)} filas"

    # =========================
    # ENTRENAR (TABLA R2) - con contador de progreso y tiempo
    # =========================

    def entrenar(self):

        global modelos_global, df_global

        if df_global is None:
            self.mensaje = "Carga dataset primero"
            return

        # Temperatura_C ya no se predice: es un input. Se excluye de
        # las columnas a predecir.
        columnas_y = [
            c for c in df_global.columns[11:26]
            if c != "Temperatura_C"
        ]

        total = len(columnas_y)

        self.entrenando = True
        self.progreso_entrenamiento = 0
        self.total_entrenamiento = total
        self.tiempo_entrenamiento = 0.0
        self.mensaje = f"Entrenando 0 / {total} variables..."
        yield  # muestra la barra de progreso en 0% antes de arrancar

        inicio = time.time()
        modelos = {}
        scores = {}

        for i, columna in enumerate(columnas_y, start=1):

            info, score = entrenar_una_columna(df_global, COLUMNAS_MODELO, columna)

            if info is not None:
                modelos[columna] = info
            scores[columna] = score

            # Actualiza contador y tiempo DESPUES de cada variable,
            # y el yield empuja ese estado al navegador en vivo.
            self.progreso_entrenamiento = i
            self.tiempo_entrenamiento = round(time.time() - inicio, 1)
            self.mensaje = (
                f"Entrenando {i} / {total} variables... "
                f"{self.tiempo_entrenamiento}s transcurridos"
            )
            yield

        modelos_global = modelos

        # TABLA R2 ORDENADA (se descartan columnas sin datos suficientes)
        self.tabla_r2 = [
            {"columna": k, "r2": v}
            for k, v in sorted(
                scores.items(),
                key=lambda x: x[1] if x[1] is not None else -1,
                reverse=True,
            )
            if v is not None
        ]

        self.tiempo_entrenamiento = round(time.time() - inicio, 1)
        self.modelo_listo = True
        self.entrenando = False
        self.mensaje = f"Modelo entrenado en {self.tiempo_entrenamiento}s"

    # =========================
    # VALIDAR
    # =========================

    def validar(self):

        if self.porcentaje_total != 100:
            self.mensaje = f"La mezcla debe sumar 100% (actual {self.porcentaje_total}%)"
            return False

        if not self.temperatura:
            self.mensaje = "Ingresa la temperatura del proceso"
            return False

        try:
            float(self.temperatura)
        except ValueError:
            self.mensaje = "Temperatura invalida"
            return False

        return True

    # =========================
    # PREDICCION (TABLA)
    # =========================

    def predecir(self):

        global modelos_global

        if modelos_global is None:
            self.mensaje = "Entrena el modelo primero"
            return

        if not self.validar():
            return

        self.prediciendo = True
        self.mensaje = "Calculando prediccion..."
        yield

        valores = {}

        for col in COLUMNAS:
            val = 0
            for e in self.mix:
                if e["elemento"] == col.replace("_pct", ""):
                    val = e["pct"]
            valores[col] = val

        valores["Temperatura_C"] = float(self.temperatura)

        tabla = []

        for nombre, info in modelos_global.items():

            modelo = info["modelo"]
            features = info["features"]
            usar_log = info["log"]

            vector = [valores.get(feat, 0) for feat in features]

            pred = modelo.predict([vector])[0]

            if usar_log:
                pred = float(np.expm1(pred))

            pred = round(float(pred), 4)

            tabla.append({
                "columna": nombre,
                "prediccion": pred
            })

        tabla.sort(key=lambda r: r["columna"])

        self.tabla_prediccion = tabla
        self.prediciendo = False
        self.mensaje = "Prediccion calculada"
'@ | Set-Content -Path "$pkg\state.py" -Encoding UTF8
}

if (-not (Test-Path "$services\excel_service.py")) {
Write-Host "Creando services\excel_service.py"
@'
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
'@ | Set-Content -Path "$services\excel_service.py" -Encoding UTF8
}

if (-not (Test-Path "$services\ml_service.py")) {
Write-Host "Creando services\ml_service.py"
@'
import numpy as np
from sklearn.base import clone
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    ExtraTreesRegressor,
)
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score


# Variables muy "sesgadas" (muchos valores chicos, pocos grandes),
# donde conviene entrenar en escala logaritmica. Es un truco estandar
# para viscosidad, que suele variar en varios ordenes de magnitud.
COLUMNAS_LOG = {"Viscosidad_Pa_s"}


def _modelos_candidatos():
    """Devuelve instancias NUEVAS de cada modelo candidato."""
    return {
        "RandomForest": RandomForestRegressor(
            n_estimators=400,
            max_depth=None,
            min_samples_leaf=2,
            max_features="sqrt",
            random_state=42,
        ),
        "ExtraTrees": ExtraTreesRegressor(
            n_estimators=400,
            min_samples_leaf=2,
            max_features="sqrt",
            random_state=42,
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=400,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        ),
    }


def _evaluar_oof(modelo_base, X, y, usar_log, cv):
    """
    Validacion cruzada "out-of-fold": en cada fold se entrena con una
    parte de los datos y se predice la parte que el modelo NO vio.
    El R2 se calcula sobre esas predicciones honestas, nunca sobre
    datos de entrenamiento (a diferencia de model.score(X, y)).
    """

    preds_oof = np.zeros(len(y))

    for train_idx, test_idx in cv.split(X):

        modelo = clone(modelo_base)

        y_train = y[train_idx]
        if usar_log:
            y_train = np.log1p(y_train)

        modelo.fit(X[train_idx], y_train)

        pred = modelo.predict(X[test_idx])
        if usar_log:
            pred = np.expm1(pred)

        preds_oof[test_idx] = pred

    return r2_score(y, preds_oof)


def entrenar_una_columna(df, columnas_x, columna, n_splits=5):
    """
    Entrena (con seleccion automatica de modelo + validacion cruzada)
    UNA SOLA columna objetivo.

    Se separo del loop principal (antes en entrenar_modelo)
    para que state.py pueda llamarla columna por columna y reportar
    progreso/tiempo transcurrido en vivo, en vez de bloquear todo de
    una sola vez sin feedback.

    Devuelve:
        info:  dict {"modelo", "features", "log", "algoritmo"} o None
               si no habia datos suficientes
        score: r2 (float) por validacion cruzada, o None
    """

    usar_log = columna in COLUMNAS_LOG

    subset = df[columnas_x + [columna]].dropna()

    if len(subset) < 10:
        return None, None

    X = subset[columnas_x].to_numpy()
    y = subset[columna].to_numpy()

    k = max(2, min(n_splits, len(subset) // 2))
    cv = KFold(n_splits=k, shuffle=True, random_state=42)

    mejor_nombre = None
    mejor_score = -np.inf

    for nombre, modelo_base in _modelos_candidatos().items():
        try:
            score = _evaluar_oof(modelo_base, X, y, usar_log, cv)
        except Exception:
            score = -np.inf

        if score > mejor_score:
            mejor_score = score
            mejor_nombre = nombre

    # Reentrenamos el mejor algoritmo con TODOS los datos disponibles
    # para esa columna (se usa despues en /predecir).
    modelo_final = _modelos_candidatos()[mejor_nombre]
    y_fit = np.log1p(y) if usar_log else y
    modelo_final.fit(X, y_fit)

    info = {
        "modelo": modelo_final,
        "features": columnas_x,
        "log": usar_log,
        "algoritmo": mejor_nombre,
    }

    return info, round(float(mejor_score), 4)


def entrenar_modelo(df, columnas_x, columnas_y, n_splits=5):
    """
    Entrena TODAS las columnas de una sola vez (sin progreso intermedio).
    Se mantiene como utilidad simple; state.py usa entrenar_una_columna
    directamente para poder mostrar el contador en vivo.
    """

    modelos = {}
    scores = {}

    for columna in columnas_y:
        info, score = entrenar_una_columna(df, columnas_x, columna, n_splits)
        if info is not None:
            modelos[columna] = info
        scores[columna] = score

    return modelos, scores
'@ | Set-Content -Path "$services\ml_service.py" -Encoding UTF8
}

if (-not (Test-Path "$services\preprocessing_service.py")) {
Write-Host "Creando services\preprocessing_service.py"
@'
def preparar_dataset(df):
    df = df.copy()
    df = df.dropna()

    return df
'@ | Set-Content -Path "$services\preprocessing_service.py" -Encoding UTF8
}

# =========================================================
# 6) VERIFICAR EXCEL
# =========================================================
$excelPath = ".\assets\data\Plantilla_Base_Polvos_Coladores_con_ML_Dataset (version 1).xlsx"
if (-not (Test-Path $excelPath)) {
    Write-Host ""
    Write-Host "ATENCION: no se encontro el archivo Excel en:" -ForegroundColor Yellow
    Write-Host "  $((Resolve-Path '.').Path)\assets\data\Plantilla_Base_Polvos_Coladores_con_ML_Dataset (version 1).xlsx" -ForegroundColor Yellow
    Write-Host "Copialo ahi antes de usar el boton 'Cargar Dataset' en la app." -ForegroundColor Yellow
}

# =========================================================
# 7) ABRIR NAVEGADOR Y CORRER LA APP
# =========================================================
Write-Step "Iniciando la aplicacion"
Write-Host "El navegador se va a abrir solo en unos segundos..."
Write-Host "Para detener la app, cerra esta ventana o presiona Ctrl+C."
Write-Host ""

Start-Job -ScriptBlock {
    function Wait-ForPort($port, $maxSeconds) {
        $elapsed = 0
        while ($elapsed -lt $maxSeconds) {
            try {
                $conn = Test-NetConnection -ComputerName "localhost" -Port $port -WarningAction SilentlyContinue
                if ($conn.TcpTestSucceeded) { return $true }
            } catch {}
            Start-Sleep -Seconds 2
            $elapsed += 2
        }
        return $false
    }

    # Backend (8000) y frontend (3000) tienen que estar los DOS
    # arriba antes de abrir el navegador, sino la pagina carga en
    # blanco porque el websocket al backend todavia no conecta.
    $backendReady  = Wait-ForPort -port 8000 -maxSeconds 180
    $frontendReady = Wait-ForPort -port 3000 -maxSeconds 180

    if ($backendReady -and $frontendReady) {
        Start-Sleep -Seconds 3   # margen extra para que termine de renderizar
        Start-Process "http://localhost:3000"
    }
} | Out-Null

& $pyCmd -m reflex run