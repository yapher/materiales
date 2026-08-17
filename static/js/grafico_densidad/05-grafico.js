(function () {
"use strict";

const GD = window.GraficoDensidad;
if (!GD) {
    return;
}

/*
Render del gráfico Chart.js.
Arma los datasets según los filtros activos (02-filtros.js):
- Densidad predicha (verde): SIEMPRE visible.
- Regresión lineal (violeta) + cuadrados rojos:
  solo con gdFiltroRegresion activado.
- Datos reales del dataset (triángulos amarillos):
  solo con gdFiltroReales activado.
*/

function construirTooltipFilaReal(item) {
    const fila = item.raw.fila;
    if (!fila) {
        return [`Real: ${GD.formatearNumero(item.raw.y, 2)} kg/m³`];
    }
    const lineas = [];
    lineas.push(`── Fila #${item.raw.indice_dataset + 1} del dataset ──`);
    for (const [col, val] of Object.entries(fila)) {
        if (val !== null && val !== undefined && val !== "") {
            const valStr = typeof val === "number"
                ? GD.formatearNumero(val, 4)
                : String(val);
            lineas.push(`${col}: ${valStr}`);
        }
    }
    return lineas;
}

GD.renderChart = function (data) {
    const wrapper = GD.$("gdWrapper");
    if (!wrapper) {
        return;
    }
    if (typeof Chart === "undefined") {
        GD.mostrarError("Chart.js no está cargado. Refrescá la página.");
        return;
    }

    const filtros = GD.state.filtros;
    const hayReales = (
        filtros.reales &&
        (data.puntos_reales || []).length > 0
    );
    const hayRegIntervalos = (
        filtros.regresion &&
        (data.puntos_regresion_intervalos || []).length > 0
    );
    const hayRegLinea = (
        filtros.regresion &&
        data.regresion &&
        data.regresion.linea
    );

    wrapper.innerHTML = `
        <div class="grafico-densidad-header">
            <div>
                <h5 class="grafico-densidad-titulo">
                    <i class="bi bi-graph-up-arrow"></i>
                    Densidad vs. Temperatura
                </h5>
                <p class="grafico-densidad-subtitulo">
                    ${data.etiqueta} en función de la temperatura
                    (${data.parametros.temp_min} K → ${data.parametros.temp_max} K,
                    cada ${data.parametros.intervalo} K)
                </p>
            </div>
            <div id="gdEcuacion" class="grafico-ecuacion" style="display:none;"></div>
        </div>
        <div class="grafico-densidad-canvas-container">
            <canvas id="gdCanvas"></canvas>
        </div>
    `;

    const canvas = GD.$("gdCanvas");
    const ctx = canvas.getContext("2d");

    if (GD.state.chartInstance) {
        GD.state.chartInstance.destroy();
        GD.state.chartInstance = null;
    }

    const puntosLinea = data.puntos.map((p) => ({
        x: p.temperatura,
        y: p.densidad,
    }));

    const gradiente = ctx.createLinearGradient(0, 0, 0, 360);
    gradiente.addColorStop(0, "rgba(136, 201, 153, 0.45)");
    gradiente.addColorStop(0.5, "rgba(136, 201, 153, 0.18)");
    gradiente.addColorStop(1, "rgba(136, 201, 153, 0.02)");

    const datasets = [];

    // ------------------------------------------------------
    // DATOS REALES DEL DATASET (triángulos amarillos)
    // Solo si el filtro gdFiltroReales está activo.
    // ------------------------------------------------------
    if (hayReales) {
        datasets.push({
            label: "Datos reales (dataset)",
            data: data.puntos_reales.map((p) => ({
                x: p.temperatura,
                y: p.densidad,
                fila: p.fila,
                indice_dataset: p.indice_dataset,
            })),
            backgroundColor: "rgba(242, 216, 121, 0.9)",
            borderColor: "#f2d879",
            borderWidth: 1.5,
            pointRadius: 7,
            pointHoverRadius: 10,
            pointHoverBackgroundColor: "#f2d879",
            pointHoverBorderColor: "#14101f",
            pointHoverBorderWidth: 2,
            pointStyle: "triangle",
            showLine: false,
        });
    }

    // ------------------------------------------------------
    // PUNTOS CUADRADOS ROJOS SOBRE LA REGRESIÓN
    // Solo si el filtro gdFiltroRegresion está activo.
    // ------------------------------------------------------
    if (hayRegIntervalos) {
        datasets.push({
            label: "Regresión en intervalos",
            data: data.puntos_regresion_intervalos.map((p) => ({
                x: p.temperatura,
                y: p.densidad,
            })),
            backgroundColor: "rgba(224, 127, 127, 0.9)",
            borderColor: "#e07f7f",
            borderWidth: 1.5,
            pointRadius: 6,
            pointHoverRadius: 9,
            pointHoverBackgroundColor: "#e07f7f",
            pointHoverBorderColor: "#ffffff",
            pointHoverBorderWidth: 2,
            pointStyle: "rect",
            showLine: false,
        });
    }

    // ------------------------------------------------------
    // DENSIDAD PREDICHA (línea verde) — SIEMPRE visible
    // ------------------------------------------------------
    datasets.push({
        label: "Densidad predicha",
        data: puntosLinea,
        borderColor: "#88c999",
        backgroundColor: gradiente,
        borderWidth: 2.5,
        pointBackgroundColor: "#6bcf80",
        pointBorderColor: "#14101f",
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 7,
        pointHoverBackgroundColor: "#88c999",
        pointHoverBorderColor: "#ffffff",
        pointHoverBorderWidth: 2,
        fill: true,
        tension: 0.25,
    });

    // ------------------------------------------------------
    // REGRESIÓN LINEAL (línea violeta punteada)
    // Solo si el filtro gdFiltroRegresion está activo.
    // ------------------------------------------------------
    if (hayRegLinea) {
        datasets.push({
            label: "Regresión lineal",
            data: data.regresion.linea.map(
                (p) => ({ x: p.x, y: p.y })
            ),
            borderColor: "#c9a3f2",
            borderWidth: 2.5,
            borderDash: [6, 4],
            pointRadius: 0,
            pointHoverRadius: 0,
            fill: false,
        });
    }

    GD.state.chartInstance = new Chart(ctx, {
        type: "line",
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "nearest",
                intersect: true,
            },
            animation: {
                duration: 900,
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
                    borderColor: "rgba(136, 201, 153, 0.45)",
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: true,
                    titleFont: { size: 13, weight: "600" },
                    bodyFont: { size: 11 },
                    maxWidth: 350,
                    callbacks: {
                        title: function (items) {
                            if (!items.length) return "";
                            const dataset = items[0].dataset;
                            const temp = GD.formatearNumero(
                                items[0].raw.x,
                                0
                            );
                            if (dataset.label === "Datos reales (dataset)") {
                                return `▲ Dato real — T: ${temp} K`;
                            }
                            if (dataset.label === "Regresión en intervalos") {
                                return `■ Regresión — T: ${temp} K`;
                            }
                            return `Temperatura: ${temp} K`;
                        },
                        label: function (item) {
                            const dataset = item.dataset;
                            if (dataset.label === "Datos reales (dataset)") {
                                return construirTooltipFilaReal(item);
                            }
                            if (dataset.label === "Regresión en intervalos") {
                                return [
                                    `Densidad (regresión): ${GD.formatearNumero(item.raw.y, 2)} ${data.unidad_y}`,
                                    `Temperatura: ${GD.formatearNumero(item.raw.x, 0)} ${data.unidad_x}`,
                                ];
                            }
                            if (dataset.label === "Regresión lineal") {
                                return `ŷ = ${GD.formatearNumero(item.raw.y, 2)} ${data.unidad_y}`;
                            }
                            return `${dataset.label}: ${GD.formatearNumero(item.raw.y, 2)} ${data.unidad_y}`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    type: "linear",
                    title: {
                        display: true,
                        text: `Temperatura (${data.unidad_x})`,
                        color: "#9c93b8",
                        font: { size: 12, weight: "600" },
                        padding: { top: 8 },
                    },
                    ticks: {
                        color: "#9c93b8",
                        font: { size: 11 },
                        maxRotation: 0,
                        callback: function (value) {
                            return GD.formatearNumero(value, 0);
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
                        text: `${data.etiqueta} (${data.unidad_y})`,
                        color: "#9c93b8",
                        font: { size: 12, weight: "600" },
                        padding: { bottom: 8 },
                    },
                    ticks: {
                        color: "#9c93b8",
                        font: { size: 11 },
                        callback: function (value) {
                            return GD.formatearNumero(value, 0);
                        },
                    },
                    grid: {
                        color: "rgba(156, 147, 184, 0.08)",
                        drawBorder: false,
                    },
                    border: {
                        display: false,
                    },
                    beginAtZero: false,
                },
            },
        },
    });

    GD.renderStats(data);
    GD.renderEcuacion(data);
};
})();