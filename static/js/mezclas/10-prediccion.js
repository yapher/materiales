(function () {
    "use strict";

    const IAM = window.IAM;

    if (!IAM) {
        return;
    }

    /*
    Predicción:
    - predecir
    - exportar PDF
    - guardar en dataset
    - estado del servidor
    - restaurar última predicción
    */

    IAM.predecir = function () {
        const temperatura = IAM.obtenerTemperatura();

        if (!temperatura.cargada) {
            return IAM.setMensaje("Ingresá la temperatura del proceso en K");
        }

        const total = IAM.calcularTotalMezcla();

        if (Math.abs(total - 100) > 0.001) {
            return IAM.setMensaje(
                `La mezcla debe sumar 100% (actual: ${IAM.formatearPorcentaje(total)}%)`
            );
        }

        IAM.setOcupado(true);
        IAM.setMensaje("Calculando predicción...");

        fetch("/mezclas/predecir", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                mix: IAM.state.mix,
                temperatura: temperatura.valor
            })
        })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }

                IAM.state.datosPrediccion = data.tabla_prediccion;

                IAM.state.ultimaMezcla = {
                    mix: JSON.parse(JSON.stringify(IAM.state.mix)),
                    temperatura: temperatura.valor
                };

                IAM.renderTablaPrediccion();
                IAM.setMensaje("Predicción calculada");
            })
            .catch(err => IAM.setMensaje(err.message))
            .finally(() => IAM.setOcupado(false));
    };

    IAM.exportarPrediccionPDF = async function () {
        if (!IAM.state.ultimaMezcla) {
            return;
        }

        IAM.setMensaje("Generando PDF...");

        try {
            const r = await fetch("/mezclas/predecir/pdf", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(IAM.state.ultimaMezcla)
            });

            if (!r.ok) {
                throw new Error("No se pudo generar el PDF");
            }

            const blob = await r.blob();
            const url = URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = "prediccion_mezcla.pdf";

            document.body.appendChild(a);
            a.click();
            a.remove();

            URL.revokeObjectURL(url);

            IAM.setMensaje("PDF descargado");
        } catch (err) {
            IAM.setMensaje(err.message);
        }
    };

    IAM.guardarPrediccionDataset = async function () {
        if (!IAM.state.ultimaMezcla) {
            return;
        }

        const confirmado = await IAM.confirmarModerno(
            "¿Agregar esta predicción como una fila nueva a tu dataset?",
            "Guardar predicción"
        );

        if (!confirmado) {
            return;
        }

        IAM.setMensaje("Guardando en el dataset...");

        fetch("/mezclas/guardar_prediccion", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(IAM.state.ultimaMezcla)
        })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }

                IAM.mostrarToast("Guardado", data.mensaje);
                IAM.setMensaje(data.mensaje);
            })
            .catch(err => IAM.setMensaje(err.message));
    };

    IAM.comprobarEstadoServidor = function () {
        fetch("/mezclas/estado")
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (!data) {
                    return;
                }

                if (data.dataset_cargado && window.FlujoModelo) {
                    window.FlujoModelo.setDatasetListo(true);
                }

                if (
                    data.modelo_info &&
                    Array.isArray(data.modelo_info.tabla_r2)
                ) {
                    IAM.state.datosR2 = data.modelo_info.tabla_r2;
                    IAM.renderTablaR2();
                }

                if (data.modelo_en_memoria || data.modelo_persistido) {
                    IAM.state.modeloListo = true;

                    IAM.actualizarVisibilidadPredecir();
                    IAM.setOcupado(false);
                }

                IAM.notificarWorkflow();
            })
            .catch(() => {});
    };

    IAM.restaurarUltimaPrediccion = function () {
        if (!document.getElementById("tablaPrediccion")) {
            return;
        }

        fetch("/mezclas/ultima_prediccion")
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (!data || !data.tabla_prediccion || !data.mix) {
                    return;
                }

                IAM.state.mix = data.mix;
                IAM.state.datosPrediccion = data.tabla_prediccion;

                IAM.state.ultimaMezcla = {
                    mix: data.mix,
                    temperatura: data.temperatura
                };

                const inputTemp = document.getElementById("temperatura");

                if (
                    inputTemp &&
                    data.temperatura !== undefined &&
                    data.temperatura !== null
                ) {
                    inputTemp.value = data.temperatura;
                }

                IAM.actualizarMix();
                IAM.renderTablaPrediccion();
            })
            .catch(() => {});
    };
})();