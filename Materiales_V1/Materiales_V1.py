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
