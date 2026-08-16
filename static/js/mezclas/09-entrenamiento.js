(function () {
    "use strict";

    const IAM = window.IAM;

    if (!IAM) {
        return;
    }

    /*
    Entrenamiento:
    - polling de estado
    - barra de progreso
    - actualización de estado del modelo
    */

    IAM.actualizarBarraProgreso = function (actual, total) {
        const barra = document.getElementById("barraProgreso");

        if (!barra) {
            return;
        }

        const pct = total > 0
            ? Math.round((actual / total) * 100)
            : 0;

        barra.style.width = `${pct}%`;
        barra.textContent = `${pct}%`;
    };

    IAM.iniciarPollEntrenamiento = function () {
        if (IAM.state.pollEntrenamiento) {
            return;
        }

        IAM.consultarEstadoEntrenamiento();

        IAM.state.pollEntrenamiento = setInterval(
            IAM.consultarEstadoEntrenamiento,
            1200
        );
    };

    IAM.consultarEstadoEntrenamiento = function () {
        fetch("/mezclas/entrenar/estado")
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (!data) {
                    return;
                }

                const badge = document.getElementById("badgeEntrenando");
                const progresoDiv = document.getElementById("progresoEntrenamiento");

                if (window.FlujoModelo) {
                    window.FlujoModelo.setEntrenamientoCorriendo(!!data.corriendo);
                }

                if (data.corriendo) {
                    if (badge) {
                        badge.style.display = "inline-flex";
                    }

                    if (progresoDiv) {
                        progresoDiv.style.display = "block";
                    }

                    if (data.total) {
                        IAM.actualizarBarraProgreso(data.progreso, data.total);

                        IAM.setMensaje(
                            `Entrenando ${data.progreso} / ${data.total} variables... ` +
                            `(${data.columna || "..."}) — ${data.tiempo}s`
                        );
                    } else {
                        IAM.setMensaje("Entrenando...");
                    }

                    if (window.FlujoModelo) {
                        window.FlujoModelo.actualizar();
                    }

                    return;
                }

                if (badge) {
                    badge.style.display = "none";
                }

                if (IAM.state.pollEntrenamiento) {
                    clearInterval(IAM.state.pollEntrenamiento);
                    IAM.state.pollEntrenamiento = null;
                }

                IAM.setOcupado(false);

                if (data.error) {
                    IAM.mostrarToast("Error de entrenamiento", data.error, true);
                    IAM.setMensaje(data.error);

                    if (window.FlujoModelo) {
                        window.FlujoModelo.actualizar();
                    }

                    return;
                }

                if (data.listo) {
                    if (progresoDiv) {
                        progresoDiv.style.display = "block";
                    }

                    IAM.actualizarBarraProgreso(
                        data.progreso || data.total || 1,
                        data.total || 1
                    );

                    const yaVisto = localStorage.getItem("entrenamiento_visto") === data.fecha;

                    IAM.state.modeloListo = true;

                    IAM.actualizarVisibilidadPredecir();
                    IAM.setOcupado(false);

                    if (Array.isArray(data.tabla_r2)) {
                        IAM.state.datosR2 = data.tabla_r2;
                        IAM.renderTablaR2();
                    }

                    if (!yaVisto) {
                        IAM.mostrarToast(
                            "Modelo entrenado",
                            `Entrenamiento completado en ${data.tiempo}s.`
                        );

                        localStorage.setItem("entrenamiento_visto", data.fecha);
                    }

                    IAM.setMensaje(`Modelo entrenado en ${data.tiempo}s`);
                }

                if (window.FlujoModelo) {
                    window.FlujoModelo.actualizar();
                }
            })
            .catch(() => {});
    };
})();