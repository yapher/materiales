/* ==========================================================
   flujo.js
   Lógica visual del camino:
   1. Dataset
   2. Entrenamiento
   3. Predicción

   Este archivo solo maneja el estado visual del flujo.
   No entrena, no predice y no toca endpoints de modelo.
   ========================================================== */

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
        return !!el('flujoPasos');
    }

    function actualizar() {
        if (!flujoDisponible()) return;

        const pasoDataset = el('pasoDataset');
        const pasoEntrenamiento = el('pasoEntrenamiento');
        const pasoPrediccion = el('pasoPrediccion');

        const descripcionDataset = el('descripcionDataset');
        const descripcionEntrenamiento = el('descripcionEntrenamiento');
        const descripcionPrediccion = el('descripcionPrediccion');

        const conectorDatasetEntrenamiento = el('conectorDatasetEntrenamiento');
        const conectorEntrenamientoPrediccion = el('conectorEntrenamientoPrediccion');

        // Estado global que viene de mezclas.js
        const modeloListo = window.MezclasApp && typeof window.MezclasApp.getModeloListo === 'function'
            ? window.MezclasApp.getModeloListo()
            : false;

        const prediccionCalculada = window.MezclasApp && typeof window.MezclasApp.hayPrediccion === 'function'
            ? window.MezclasApp.hayPrediccion()
            : false;

        // -------------------------
        // Paso 1: Dataset
        // -------------------------
        if (pasoDataset) {
            pasoDataset.classList.remove('paso-activo', 'paso-completo', 'paso-error');

            if (state.datasetError) {
                pasoDataset.classList.add('paso-error');
                if (descripcionDataset) {
                    descripcionDataset.textContent = state.datasetError;
                }
            } else if (state.datasetListo) {
                pasoDataset.classList.add('paso-completo');
                if (descripcionDataset) {
                    descripcionDataset.textContent = 'Dataset cargado correctamente.';
                }
            } else if (state.datasetCargando) {
                pasoDataset.classList.add('paso-activo');
                if (descripcionDataset) {
                    descripcionDataset.textContent = 'Cargando dataset automáticamente...';
                }
            } else {
                pasoDataset.classList.add('paso-activo');
                if (descripcionDataset) {
                    descripcionDataset.textContent = 'Esperando la carga del dataset...';
                }
            }
        }

        if (conectorDatasetEntrenamiento) {
            conectorDatasetEntrenamiento.classList.toggle(
                'conector-completo',
                state.datasetListo || modeloListo
            );
        }

        // -------------------------
        // Paso 2: Entrenamiento
        // -------------------------
        if (pasoEntrenamiento) {
            pasoEntrenamiento.classList.remove('paso-activo', 'paso-completo', 'paso-error');

            if (modeloListo) {
                pasoEntrenamiento.classList.add('paso-completo');
                if (descripcionEntrenamiento) {
                    descripcionEntrenamiento.textContent = 'Modelo entrenado. La predicción está habilitada.';
                }
            } else if (state.entrenamientoCorriendo) {
                pasoEntrenamiento.classList.add('paso-activo');
                if (descripcionEntrenamiento) {
                    descripcionEntrenamiento.textContent = 'Entrenando modelo...';
                }
            } else if (state.datasetListo) {
                pasoEntrenamiento.classList.add('paso-activo');
                if (descripcionEntrenamiento) {
                    descripcionEntrenamiento.textContent = 'Dataset listo. Apretá Entrenar Modelo.';
                }
            } else {
                if (descripcionEntrenamiento) {
                    descripcionEntrenamiento.textContent = 'Primero se debe cargar el dataset.';
                }
            }
        }

        if (conectorEntrenamientoPrediccion) {
            conectorEntrenamientoPrediccion.classList.toggle(
                'conector-completo',
                modeloListo
            );
        }

        // -------------------------
        // Paso 3: Predicción
        // -------------------------
        if (pasoPrediccion) {
            pasoPrediccion.classList.remove('paso-activo', 'paso-completo', 'paso-error');

            if (modeloListo && prediccionCalculada) {
                pasoPrediccion.classList.add('paso-completo');
                if (descripcionPrediccion) {
                    descripcionPrediccion.textContent = 'Predicción calculada.';
                }
            } else if (modeloListo) {
                pasoPrediccion.classList.add('paso-activo');
                if (descripcionPrediccion) {
                    descripcionPrediccion.textContent = 'Armá la mezcla y presioná Predecir.';
                }
            } else {
                if (descripcionPrediccion) {
                    descripcionPrediccion.textContent = 'Se habilita cuando el modelo está entrenado.';
                }
            }
        }

        actualizarPaneles(modeloListo);
    }

    function actualizarPaneles(modeloListo) {
        const panelComposicion = el('panelComposicion');
        const resultadosModelo = el('resultadosModelo');

        if (panelComposicion) {
            panelComposicion.style.display = modeloListo ? '' : 'none';
        }

        if (resultadosModelo) {
            resultadosModelo.style.display = modeloListo ? '' : 'none';
        }
    }

    function cargarDataset() {
        if (!flujoDisponible()) return;

        state.datasetCargando = true;
        state.datasetError = null;
        state.datasetListo = false;

        actualizar();

        fetch('/mezclas/cargar_dataset', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data.error) throw new Error(data.error);

                state.datasetListo = true;
                state.datasetCargando = false;
                state.datasetError = null;

                document.dispatchEvent(new CustomEvent('flujo:dataset-actualizado', {
                    detail: data
                }));

                actualizar();
            })
            .catch(err => {
                state.datasetListo = false;
                state.datasetCargando = false;
                state.datasetError = err.message;

                actualizar();
            });
    }

    function init() {
        if (!flujoDisponible()) return;

        cargarDataset();
        actualizar();
    }

    // API pública para mezclas.js
    window.FlujoModelo = {
        init,
        actualizar,
        cargarDataset,
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
        },
        isDatasetListo() {
            return state.datasetListo;
        },
        isEntrenamientoCorriendo() {
            return state.entrenamientoCorriendo;
        }
    };

    // Inicialización inmediata porque el script se carga al final del body.
    init();
})();