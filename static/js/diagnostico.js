(function () {
    "use strict";

    function escaparHtml(valor) {
        return String(valor)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function setMensaje(texto, esError = false) {
        const box = document.getElementById("mensajeDiagnostico");
        const span = document.getElementById("mensajeDiagnosticoTexto");

        if (!box || !span) {
            return;
        }

        span.textContent = texto;

        box.style.borderColor = esError ? "#e07f7f" : "";
        box.style.color = esError ? "#e0a97f" : "";
        box.style.display = texto ? "block" : "none";
    }

    function formatearNumero(valor) {
        if (valor === null || valor === undefined) {
            return "—";
        }

        return String(valor);
    }

    function renderCards(data) {
        const contenedor = document.getElementById("diagCards");

        if (!contenedor) {
            return;
        }

        const resumen = data.resumen || {};

        const cards = [
            {
                icono: "bi-list-ol",
                titulo: "Total de filas",
                valor: formatearNumero(data.total_filas),
            },
            {
                icono: "bi-check2-circle",
                titulo: "Filas entrenables",
                valor: `${formatearNumero(data.filas_entrenables)} (${formatearNumero(data.porcentaje_entrenable)}%)`,
            },
            {
                icono: "bi-exclamation-triangle",
                titulo: "Objetivos atípicos",
                valor: formatearNumero(resumen.objetivos_atipicos),
            },
            {
                icono: "bi-pie-chart",
                titulo: "Composición fuera de 100%",
                valor: formatearNumero(resumen.suma_composicion_fuera),
            },
            {
                icono: "bi-question-circle",
                titulo: "Entradas faltantes",
                valor: formatearNumero(resumen.features_faltantes),
            },
            {
                icono: "bi-thermometer-half",
                titulo: "Temperaturas atípicas",
                valor: formatearNumero(resumen.temperaturas_atipicas),
            },
            {
                icono: "bi-copy",
                titulo: "Duplicadas exactas",
                valor: formatearNumero(resumen.duplicadas_exactas),
            },
            {
                icono: "bi-file-earmark-excel",
                titulo: "Variable analizada",
                valor: escaparHtml(data.etiqueta_variable || data.variable),
            },
        ];

        contenedor.innerHTML = cards.map(card => {
            return `
                <div class="panel diag-card">
                    <div class="diag-card-icono">
                        <i class="bi ${card.icono}"></i>
                    </div>

                    <div class="diag-card-texto">
                        <div class="diag-card-titulo">${card.titulo}</div>
                        <div class="diag-card-valor">${card.valor}</div>
                    </div>
                </div>
            `;
        }).join("");
    }

    function renderEstadisticas(data) {
        const contenedor = document.getElementById("diagEstadisticas");

        if (!contenedor) {
            return;
        }

        const stats = data.estadisticas_target || {};

        contenedor.innerHTML = `
            <div class="row g-3">
                <div class="col-md-3">
                    <div class="diag-stat">
                        <span class="diag-stat-label">Cantidad</span>
                        <span class="diag-stat-value">${formatearNumero(stats.cantidad)}</span>
                    </div>
                </div>

                <div class="col-md-3">
                    <div class="diag-stat">
                        <span class="diag-stat-label">Faltantes</span>
                        <span class="diag-stat-value">${formatearNumero(stats.faltantes)}</span>
                    </div>
                </div>

                <div class="col-md-3">
                    <div class="diag-stat">
                        <span class="diag-stat-label">Mínimo</span>
                        <span class="diag-stat-value">${formatearNumero(stats.min)}</span>
                    </div>
                </div>

                <div class="col-md-3">
                    <div class="diag-stat">
                        <span class="diag-stat-label">Máximo</span>
                        <span class="diag-stat-value">${formatearNumero(stats.max)}</span>
                    </div>
                </div>

                <div class="col-md-3">
                    <div class="diag-stat">
                        <span class="diag-stat-label">Media</span>
                        <span class="diag-stat-value">${formatearNumero(stats.media)}</span>
                    </div>
                </div>

                <div class="col-md-3">
                    <div class="diag-stat">
                        <span class="diag-stat-label">Mediana</span>
                        <span class="diag-stat-value">${formatearNumero(stats.mediana)}</span>
                    </div>
                </div>

                <div class="col-md-3">
                    <div class="diag-stat">
                        <span class="diag-stat-label">Desvío</span>
                        <span class="diag-stat-value">${formatearNumero(stats.desvio)}</span>
                    </div>
                </div>

                <div class="col-md-3">
                    <div class="diag-stat">
                        <span class="diag-stat-label">IQR</span>
                        <span class="diag-stat-value">${formatearNumero(stats.iqr)}</span>
                    </div>
                </div>
            </div>

            <p class="text-muted small mt-3 mb-0">
                <i class="bi bi-info-circle"></i>
                Las filas entrenables son las que tienen la variable objetivo completa
                y todas las columnas de entrada completas.
            </p>
        `;
    }

    function renderSospechosas(data) {
        const tbody = document.getElementById("diagTablaSospechosas");
        const vacio = document.getElementById("diagSinSospechosas");
        const contador = document.getElementById("diagContadorSospechosas");

        if (!tbody) {
            return;
        }

        const filas = data.sospechosas || [];

        if (contador) {
            contador.textContent = `${data.resumen?.filas_sospechosas ?? 0} detectadas`;
        }

        if (!filas.length) {
            tbody.innerHTML = "";

            if (vacio) {
                vacio.style.display = "block";
            }

            return;
        }

        if (vacio) {
            vacio.style.display = "none";
        }

        tbody.innerHTML = filas.map(fila => {
            const razones = (fila.razones || []).map(razon => {
                return `<span class="diag-motivo">${escaparHtml(razon)}</span>`;
            }).join(" ");

            return `
                <tr>
                    <td>${formatearNumero(fila.fila)}</td>
                    <td>${formatearNumero(fila.variable)}</td>
                    <td>${formatearNumero(fila.temperatura)}</td>
                    <td>${formatearNumero(fila.suma_pct)}</td>
                    <td>${razones}</td>
                </tr>
            `;
        }).join("");

        if (data.resumen?.filas_sospechosas > data.sospechosas_mostradas) {
            tbody.innerHTML += `
                <tr>
                    <td colspan="5" class="text-muted text-center">
                        Se muestran las primeras ${data.sospechosas_mostradas} filas sospechosas.
                    </td>
                </tr>
            `;
        }
    }

    function analizar() {
        const select = document.getElementById("diagnosticoVariable");
        const boton = document.getElementById("btnAnalizarDiagnostico");
        const resultados = document.getElementById("resultadosDiagnostico");

        if (!select || !boton) {
            return;
        }

        const variable = select.value;

        if (!variable) {
            setMensaje("Seleccioná una variable para analizar.", true);
            return;
        }

        boton.disabled = true;
        setMensaje("Analizando dataset...");

        fetch(`/diagnostico/analizar?variable=${encodeURIComponent(variable)}`)
            .then(async respuesta => {
                const data = await respuesta.json().catch(() => ({}));

                if (!respuesta.ok || data.error) {
                    throw new Error(
                        data.error || `Error ${respuesta.status}`
                    );
                }

                return data;
            })
            .then(data => {
                renderCards(data);
                renderEstadisticas(data);
                renderSospechosas(data);

                if (resultados) {
                    resultados.style.display = "block";
                }

                setMensaje(data.mensaje_lectura || "Análisis completado.");
            })
            .catch(error => {
                if (resultados) {
                    resultados.style.display = "none";
                }

                setMensaje(error.message, true);
            })
            .finally(() => {
                boton.disabled = false;
            });
    }

    function init() {
        const boton = document.getElementById("btnAnalizarDiagnostico");

        if (boton) {
            boton.addEventListener("click", analizar);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();