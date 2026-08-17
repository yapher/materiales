(function () {
    "use strict";

    // ==========================================================
    // ESTADO INTERNO
    // ==========================================================
    let chartInstance = null;
    let modalElement = null;
    let modalInstance = null;
    let ultimaConsulta = null;

    // ==========================================================
    // HELPERS
    // ==========================================================
    function $(id) {
        return document.getElementById(id);
    }

    function setLoaderVisible(visible) {
        const loader = $("regLoader");
        if (loader) {
            loader.style.display = visible ? "flex" : "none";
        }
    }

    function mostrarError(mensaje) {
        const wrapper = $("regWrapper");
        if (!wrapper) return;
        wrapper.innerHTML = `
            <div class="regresion-error">
                <i class="bi bi-exclamation-triangle-fill"></i>
                <p class="regresion-error-text mb-0">${mensaje}</p>
            </div>
        `;
    }

    function mostrarVacio(mensaje) {
        const wrapper = $("regWrapper");
        if (!wrapper) return;
        wrapper.innerHTML = `
            <div class="regresion-empty">
                <i class="bi bi-graph-up"></i>
                <p class="mb-0">${mensaje || "Seleccioná una variable y presioná \"Generar gráfico\"."}</p>
            </div>
        `;
    }

    function formatearNumero(valor, decimales = 2) {
        if (valor === null || valor === undefined || isNaN(valor)) return "—";
        return Number(valor).toLocaleString("es-AR", {
            minimumFractionDigits: 0,
            maximumFractionDigits: decimales,
        });
    }

    function claseR2(r2) {
        if (r2 === null || r2 === undefined) return "malo";
        if (r2 >= 0.8) return "bueno";
        if (r2 >= 0.5) return "medio";
        return "malo";
    }

    function textoInterpretacion(stats, data) {
        const r2 = stats.r2;
        if (r2 === null || r2 === undefined) {
            return "No se pudo calcular la regresión.";
        }

        const clase = claseR2(r2);
        let texto = "";

        if (clase === "bueno") {
            texto = `<strong>Excelente linealidad (R² = ${formatearNumero(r2, 3)}):</strong> `;
            texto += "los puntos se alinean casi perfectamente sobre la diagonal ideal.";
        } else if (clase === "medio") {
            texto = `<strong>Linealidad aceptable (R² = ${formatearNumero(r2, 3)}):</strong> `;
            texto += "hay una tendencia clara pero con dispersión considerable.";
        } else {
            texto = `<strong>Linealidad débil (R² = ${formatearNumero(r2, 3)}):</strong> `;
            texto += "los puntos muestran mucha dispersión respecto a la línea ideal.";
        }

        if (stats.r2_predictivo !== null && stats.r2_predictivo !== undefined) {
            texto += ` R² predictivo: ${formatearNumero(stats.r2_predictivo, 3)}.`;
        }

        if (stats.pendiente !== null && Math.abs(stats.pendiente - 1) > 0.1) {
            texto += ` La pendiente (${formatearNumero(stats.pendiente, 2)}) se aleja de 1, `;
            texto += "lo que indica un sesgo sistemático en las predicciones.";
        }

        if (data && data.outliers && data.outliers.cantidad > 0) {
            texto += ` Se detectaron <strong>${data.outliers.cantidad} puntos atípicos</strong> `;
            texto += "(en rojo) con residuos anormalmente altos.";
        }

        return texto;
    }

    // ==========================================================
    // RENDER DE ESTADÍSTICAS
    // ==========================================================
    function renderStats(data) {
        const cont = $("regStats");
        const interpretacion = $("regInterpretacion");
        const ecuacion = $("regEcuacion");
        if (!cont) return;

        const stats = data.stats;
        const clase = claseR2(stats.r2);

        cont.style.display = "";
        cont.innerHTML = `
            <div class="regresion-stat-card">
                <div class="regresion-stat-label">R² linealidad</div>
                <div class="regresion-stat-valor stat-r2">${formatearNumero(stats.r2, 4)}</div>
            </div>
            <div class="regresion-stat-card">
                <div class="regresion-stat-label">R² predictivo</div>
                <div class="regresion-stat-valor stat-r2">${formatearNumero(stats.r2_predictivo, 4)}</div>
            </div>
            <div class="regresion-stat-card">
                <div class="regresion-stat-label">Pendiente</div>
                <div class="regresion-stat-valor stat-pendiente">${formatearNumero(stats.pendiente, 3)}</div>
            </div>
            <div class="regresion-stat-card">
                <div class="regresion-stat-label">Intercepto</div>
                <div class="regresion-stat-valor">${formatearNumero(stats.intercepto, 2)}</div>
            </div>
            <div class="regresion-stat-card">
                <div class="regresion-stat-label">RMSE</div>
                <div class="regresion-stat-valor stat-rmse">${formatearNumero(stats.rmse, 2)}</div>
            </div>
            <div class="regresion-stat-card">
                <div class="regresion-stat-label">MAE</div>
                <div class="regresion-stat-valor stat-mae">${formatearNumero(stats.mae, 2)}</div>
            </div>
            <div class="regresion-stat-card">
                <div class="regresion-stat-label">MAPE</div>
                <div class="regresion-stat-valor">${stats.mape !== null ? formatearNumero(stats.mape, 1) + "%" : "—"}</div>
            </div>
            <div class="regresion-stat-card">
                <div class="regresion-stat-label">Outliers</div>
                <div class="regresion-stat-valor stat-outliers">${data.outliers.cantidad}</div>
            </div>
            <div class="regresion-stat-card">
                <div class="regresion-stat-label">Puntos</div>
                <div class="regresion-stat-valor">${stats.cantidad}</div>
            </div>
        `;

        if (interpretacion) {
            interpretacion.className = `regresion-interpretacion r2-${clase}`;
            interpretacion.innerHTML = `<i class="bi bi-info-circle me-2"></i>${textoInterpretacion(stats, data)}`;
            interpretacion.style.display = "";
        }

        if (ecuacion) {
            if (stats.pendiente !== null && stats.intercepto !== null) {
                const signo = stats.intercepto >= 0 ? "+" : "−";
                const b = Math.abs(stats.intercepto);
                ecuacion.innerHTML = `
                    <span class="regresion-ecuacion-label">Ecuación:</span>
                    <span>ŷ = ${formatearNumero(stats.pendiente, 3)} · x ${signo} ${formatearNumero(b, 2)}</span>
                `;
                ecuacion.style.display = "";
            } else {
                ecuacion.style.display = "none";
            }
        }
    }

    // ==========================================================
    // RENDER DEL GRÁFICO (Chart.js)
    // ==========================================================
    function renderChart(data) {
        const wrapper = $("regWrapper");
        if (!wrapper) return;

        if (typeof Chart === "undefined") {
            mostrarError("Chart.js no está cargado. Refrescá la página.");
            return;
        }

        wrapper.innerHTML = `
            <div class="regresion-header">
                <div>
                    <h5 class="regresion-titulo">
                        <i class="bi bi-graph-up"></i>
                        Regresión lineal: ${data.etiqueta}
                    </h5>
                    <p class="regresion-subtitulo">
                        Valores reales del dataset vs. predicciones del modelo
                        (${data.algoritmo}, ${data.filas_entrenadas} filas entrenadas)
                    </p>
                </div>
                <div id="regEcuacion" class="regresion-ecuacion" style="display:none;"></div>
            </div>
            <div class="regresion-canvas-container">
                <canvas id="regCanvas"></canvas>
            </div>
            <div id="regInterpretacion" class="regresion-interpretacion" style="display:none;"></div>
        `;

        const canvas = $("regCanvas");
        const ctx = canvas.getContext("2d");

        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }

        // Separar puntos normales y outliers
        const puntosNormales = data.puntos.filter((p) => !p.es_outlier);
        const puntosOutliers = data.puntos.filter((p) => p.es_outlier);

        chartInstance = new Chart(ctx, {
            type: "scatter",
            data: {
                datasets: [
                    // Puntos normales
                    {
                        label: "Predicciones",
                        data: puntosNormales.map((p) => ({ x: p.real, y: p.predicho })),
                        backgroundColor: "rgba(136, 201, 153, 0.75)",
                        borderColor: "#88c999",
                        borderWidth: 1.5,
                        pointRadius: 5,
                        pointHoverRadius: 8,
                        pointHoverBackgroundColor: "#6bcf80",
                        pointHoverBorderColor: "#ffffff",
                        pointHoverBorderWidth: 2,
                    },
                    // Outliers
                    {
                        label: "Outliers",
                        data: puntosOutliers.map((p) => ({ x: p.real, y: p.predicho })),
                        backgroundColor: "rgba(224, 127, 127, 0.85)",
                        borderColor: "#e07f7f",
                        borderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 9,
                        pointHoverBackgroundColor: "#e07f7f",
                        pointHoverBorderColor: "#ffffff",
                        pointHoverBorderWidth: 2,
                        pointStyle: "triangle",
                    },
                    // Línea ideal (y = x)
                    {
                        label: "Línea ideal (y = x)",
                        type: "line",
                        data: data.linea_ideal.map((p) => ({ x: p.x, y: p.y })),
                        borderColor: "rgba(156, 147, 184, 0.6)",
                        borderWidth: 2,
                        borderDash: [8, 4],
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        fill: false,
                    },
                    // Línea de regresión
                    {
                        label: "Ajuste lineal",
                        type: "line",
                        data: data.linea_regresion.map((p) => ({ x: p.x, y: p.y })),
                        borderColor: "#c9a3f2",
                        borderWidth: 2.5,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        fill: false,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: "nearest",
                    intersect: true,
                },
                animation: {
                    duration: 800,
                    easing: "easeOutQuart",
                },
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            color: "#9c93b8",
                            font: { size: 11 },
                            padding: 15,
                            usePointStyle: true,
                        },
                    },
                    tooltip: {
                        backgroundColor: "rgba(30, 23, 48, 0.96)",
                        titleColor: "#f1eefc",
                        bodyColor: "#f1eefc",
                        borderColor: "rgba(201, 163, 242, 0.45)",
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: true,
                        titleFont: { size: 12, weight: "600" },
                        bodyFont: { size: 11 },
                        callbacks: {
                            title: function (items) {
                                if (!items.length) return "";
                                const dataset = items[0].dataset;
                                if (dataset.label === "Línea ideal (y = x)") return "Línea ideal";
                                if (dataset.label === "Ajuste lineal") return "Ajuste lineal";
                                return "Punto del dataset";
                            },
                            label: function (item) {
                                const dataset = item.dataset;
                                if (dataset.label === "Línea ideal (y = x)") {
                                    return `y = x = ${formatearNumero(item.raw.x, 2)}`;
                                }
                                if (dataset.label === "Ajuste lineal") {
                                    return `ŷ = ${formatearNumero(item.raw.y, 2)}`;
                                }
                                const residuo = Math.abs(item.raw.x - item.raw.y);
                                const esOutlier = dataset.label === "Outliers";
                                const etiqueta = esOutlier ? "⚠ OUTLIER" : "";
                                return [
                                    `Real: ${formatearNumero(item.raw.x, 2)}`,
                                    `Predicho: ${formatearNumero(item.raw.y, 2)}`,
                                    `Residuo: ${formatearNumero(residuo, 2)} ${etiqueta}`,
                                ];
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: `Valor real — ${data.etiqueta}`,
                            color: "#9c93b8",
                            font: { size: 12, weight: "600" },
                            padding: { top: 8 },
                        },
                        ticks: {
                            color: "#9c93b8",
                            font: { size: 11 },
                            callback: function (value) {
                                return formatearNumero(value, 0);
                            },
                        },
                        grid: {
                            color: "rgba(156, 147, 184, 0.08)",
                            drawBorder: false,
                        },
                        border: {
                            display: false,
                        },
                    },
                    y: {
                        title: {
                            display: true,
                            text: `Valor predicho — ${data.etiqueta}`,
                            color: "#9c93b8",
                            font: { size: 12, weight: "600" },
                            padding: { bottom: 8 },
                        },
                        ticks: {
                            color: "#9c93b8",
                            font: { size: 11 },
                            callback: function (value) {
                                return formatearNumero(value, 0);
                            },
                        },
                        grid: {
                            color: "rgba(156, 147, 184, 0.08)",
                            drawBorder: false,
                        },
                        border: {
                            display: false,
                        },
                    },
                },
            },
        });

        renderStats(data);
    }

    // ==========================================================
    // CARGAR VARIABLES DISPONIBLES
    // ==========================================================
    async function cargarVariables() {
        const select = $("regVariable");
        if (!select) return;

        try {
            const respuesta = await fetch("/mezclas/grafico_regresion/variables");
            const data = await respuesta.json().catch(() => ({}));
            if (!respuesta.ok || data.error) {
                throw new Error(data.error || "No se pudo cargar la lista.");
            }

            if (!data.variables || data.variables.length === 0) {
                mostrarVacio("No hay variables entrenadas en el modelo. Entrená el modelo primero.");
                select.innerHTML = '<option value="">— sin variables —</option>';
                select.disabled = true;
                return false;
            }

            select.innerHTML = data.variables
                .map(
                    (v) =>
                        `<option value="${v.valor}" title="${v.descripcion}">${v.etiqueta} (${v.valor})</option>`
                )
                .join("");
            select.disabled = false;
            return true;
        } catch (error) {
            mostrarError(error.message);
            return false;
        }
    }

    // ==========================================================
    // LLAMADA AL BACKEND
    // ==========================================================
    async function generarGrafico() {
        const select = $("regVariable");
        if (!select) return;

        const columna = select.value;
        if (!columna) {
            mostrarError("Seleccioná una variable para graficar.");
            return;
        }

        setLoaderVisible(true);
        const btnGenerar = $("regBtnGenerar");
        if (btnGenerar) btnGenerar.disabled = true;

        try {
            const respuesta = await fetch("/mezclas/grafico_regresion", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ columna }),
            });
            const data = await respuesta.json().catch(() => ({}));
            if (!respuesta.ok || data.error) {
                throw new Error(data.error || `Error ${respuesta.status}`);
            }
            ultimaConsulta = data;
            renderChart(data);
            if (window.mostrarToast) {
                window.mostrarToast(
                    "Regresión calculada",
                    `${data.stats.cantidad} puntos analizados, R² = ${formatearNumero(data.stats.r2, 3)}.`,
                    false
                );
            }
        } catch (error) {
            mostrarError(error.message);
            if (window.mostrarToast) {
                window.mostrarToast("Error", error.message, true);
            }
        } finally {
            setLoaderVisible(false);
            if (btnGenerar) btnGenerar.disabled = false;
        }
    }

    // ==========================================================
    // DESCARGAR PNG
    // ==========================================================
    function descargarPNG() {
        if (!chartInstance) return;
        const url = chartInstance.toBase64Image("image/png", 1.0);
        const a = document.createElement("a");
        a.href = url;
        a.download = `regresion_${ultimaConsulta ? ultimaConsulta.columna : "lineal"}_${Date.now()}.png`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        if (window.mostrarToast) {
            window.mostrarToast("Imagen descargada", "Gráfico guardado como PNG.");
        }
    }

    // ==========================================================
    // INICIALIZACIÓN
    // ==========================================================
    function inicializarModal() {
        modalElement = $("modalGraficoRegresion");
        if (!modalElement) return;

        if (typeof bootstrap !== "undefined") {
            modalInstance = bootstrap.Modal.getOrCreateInstance(modalElement);
        }

        const btnGenerar = $("regBtnGenerar");
        if (btnGenerar) {
            btnGenerar.addEventListener("click", generarGrafico);
        }

        const btnDescargar = $("regBtnDescargar");
        if (btnDescargar) {
            btnDescargar.addEventListener("click", descargarPNG);
        }

        const select = $("regVariable");
        if (select) {
            select.addEventListener("change", generarGrafico);
        }

        modalElement.addEventListener("hidden.bs.modal", () => {
            if (chartInstance) {
                chartInstance.destroy();
                chartInstance = null;
            }
        });

        modalElement.addEventListener("shown.bs.modal", async () => {
            mostrarVacio();
            const hayVariables = await cargarVariables();
            if (hayVariables) {
                generarGrafico();
            }
        });
    }

    // ==========================================================
    // EXPONER API GLOBAL
    // ==========================================================
    window.GraficoRegresion = {
        abrir() {
            if (!modalInstance && modalElement && typeof bootstrap !== "undefined") {
                modalInstance = bootstrap.Modal.getOrCreateInstance(modalElement);
            }
            if (modalInstance) modalInstance.show();
        },
        generar: generarGrafico,
    };

    function init() {
        inicializarModal();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();