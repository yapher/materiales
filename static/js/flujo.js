(function () {
    const state = {
        datasetListo: false,
        datasetCargando: false,
        datasetError: null,
        entrenamientoCorriendo: false,
    };

    function el(id) {
        return document.getElementById(id);
    }

    function flujoDisponible() {
        return !!el("flujoPasos");
    }

    function actualizarPaneles(modeloListo) {
        const panelComposicion = el("panelComposicion");
        const resultadosModelo = el("resultadosModelo");

        if (panelComposicion) {
            panelComposicion.style.display = modeloListo ? "" : "none";
        }

        if (resultadosModelo) {
            resultadosModelo.style.display = modeloListo ? "" : "none";
        }
    }

    function actualizar() {
        if (!flujoDisponible()) return;

        const pasoDataset = el("pasoDataset");
        const pasoEntrenamiento = el("pasoEntrenamiento");
        const pasoPrediccion = el("pasoPrediccion");

        const descripcionDataset = el("descripcionDataset");
        const descripcionEntrenamiento = el("descripcionEntrenamiento");
        const descripcionPrediccion = el("descripcionPrediccion");

        const conectorDatasetEntrenamiento = el("conectorDatasetEntrenamiento");
        const conectorEntrenamientoPrediccion = el("conectorEntrenamientoPrediccion");

        const modeloListo = window.MezclasApp && typeof window.MezclasApp.getModeloListo === "function"
            ? window.MezclasApp.getModeloListo()
            : false;

        const prediccionCalculada = window.MezclasApp && typeof window.MezclasApp.hayPrediccion === "function"
            ? window.MezclasApp.hayPrediccion()
            : false;

        // Paso 1
        if (pasoDataset) {
            pasoDataset.classList.remove("paso-activo", "paso-completo", "paso-error");

            if (state.datasetError) {
                pasoDataset.classList.add("paso-error");
                if (descripcionDataset) descripcionDataset.textContent = state.datasetError;
            } else if (state.datasetListo) {
                pasoDataset.classList.add("paso-completo");
                if (descripcionDataset) descripcionDataset.textContent = "Dataset cargado correctamente.";
            } else if (state.datasetCargando) {
                pasoDataset.classList.add("paso-activo");
                if (descripcionDataset) descripcionDataset.textContent = "Cargando dataset automáticamente...";
            } else {
                pasoDataset.classList.add("paso-activo");
                if (descripcionDataset) descripcionDataset.textContent = "Esperando la carga del dataset...";
            }
        }

        if (conectorDatasetEntrenamiento) {
            conectorDatasetEntrenamiento.classList.toggle(
                "conector-completo",
                state.datasetListo || modeloListo
            );
        }

        // Paso 2
        if (pasoEntrenamiento) {
            pasoEntrenamiento.classList.remove("paso-activo", "paso-completo", "paso-error");

            if (modeloListo) {
                pasoEntrenamiento.classList.add("paso-completo");
                if (descripcionEntrenamiento) {
                    descripcionEntrenamiento.textContent = "Modelo entrenado. La predicción está habilitada.";
                }
            } else if (state.entrenamientoCorriendo) {
                pasoEntrenamiento.classList.add("paso-activo");
                if (descripcionEntrenamiento) {
                    descripcionEntrenamiento.textContent = "Entrenando modelo...";
                }
            } else if (state.datasetListo) {
                pasoEntrenamiento.classList.add("paso-activo");
                if (descripcionEntrenamiento) {
                    descripcionEntrenamiento.textContent = "Dataset listo. Apretá Modelar.";
                }
            } else {
                if (descripcionEntrenamiento) {
                    descripcionEntrenamiento.textContent = "Primero se debe cargar el dataset.";
                }
            }
        }

        if (conectorEntrenamientoPrediccion) {
            conectorEntrenamientoPrediccion.classList.toggle(
                "conector-completo",
                modeloListo
            );
        }

        // Paso 3
        if (pasoPrediccion) {
            pasoPrediccion.classList.remove("paso-activo", "paso-completo", "paso-error");

            if (modeloListo && prediccionCalculada) {
                pasoPrediccion.classList.add("paso-completo");
                if (descripcionPrediccion) {
                    descripcionPrediccion.textContent = "Predicción calculada.";
                }
            } else if (modeloListo) {
                pasoPrediccion.classList.add("paso-activo");
                if (descripcionPrediccion) {
                    descripcionPrediccion.textContent = "Armá la mezcla y presioná Predecir.";
                }
            } else {
                if (descripcionPrediccion) {
                    descripcionPrediccion.textContent = "Se habilita cuando el modelo está entrenado.";
                }
            }
        }

        actualizarPaneles(modeloListo);
    }

    function cargarDataset() {
        if (!flujoDisponible()) return;

        state.datasetCargando = true;
        state.datasetError = null;
        state.datasetListo = false;

        if (window.setOcupado) window.setOcupado(true);
        if (window.setMensaje) window.setMensaje("Cargando dataset automáticamente...");

        actualizar();

        fetch("/mezclas/cargar_dataset", { method: "POST" })
            .then(r => r.json())
            .then(data => {
                if (data.error) throw new Error(data.error);

                state.datasetListo = true;
                state.datasetCargando = false;
                state.datasetError = null;

                if (window.setMensaje) {
                    window.setMensaje(`Dataset listo (${data.filas} filas)`);
                }

                document.dispatchEvent(new CustomEvent("flujo:dataset-actualizado"));

                actualizar();

                if (window.setOcupado) window.setOcupado(false);
            })
            .catch(err => {
                state.datasetListo = false;
                state.datasetCargando = false;
                state.datasetError = err.message;

                if (window.setMensaje) window.setMensaje(err.message);

                actualizar();

                if (window.setOcupado) window.setOcupado(false);
            });
    }

    window.FlujoModelo = {
        actualizar,
        cargarDataset,
        isDatasetListo() {
            return state.datasetListo;
        },
        isEntrenamientoCorriendo() {
            return state.entrenamientoCorriendo;
        },
        setDatasetListo(valor) {
            state.datasetListo = !!valor;

            if (valor) {
                state.datasetError = null;
                state.datasetCargando = false;
            }

            actualizar();
        },
        setEntrenamientoCorriendo(valor) {
            state.entrenamientoCorriendo = !!valor;
            actualizar();
        }
    };

    document.addEventListener("mezclas:estado-actualizado", actualizar);

    function init() {
        if (!flujoDisponible()) return;

        cargarDataset();
        actualizar();

        if (window.setOcupado) {
            window.setOcupado(false);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();