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
