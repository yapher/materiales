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

    function getFormularioValores() {
        const tempMin = parseFloat($("gdTempMin")?.value);
        const tempMax = parseFloat($("gdTempMax")?.value);
        const intervalo = parseFloat($("gdIntervalo")?.value);
        return { tempMin, tempMax, intervalo };
    }

    function setLoaderVisible(visible) {
        const loader = $("gdLoader");
        if (loader) {
            loader.style.display = visible ? "flex" : "none";
        }
    }

    function mostrarError(mensaje) {
        const wrapper = $("gdWrapper");
        if (!wrapper) return;
        wrapper.innerHTML = `
            <div class="grafico-densidad-error">
                <i class="bi bi-exclamation-triangle-fill"></i>
                <p class="grafico-error-text mb-0">${mensaje}</p>
            </div>
        `;
    }

    function mostrarVacio() {
        const wrapper = $("gdWrapper");
        if (!wrapper) return;
        wrapper.innerHTML = `
            <div class="grafico-densidad-empty">
                <i class="bi bi-graph-up"></i>
                <p class="mb-0">Ajustá los parámetros y presioná "Generar gráfico".</p>
            </div>
        `;
    }

    function getMezclaActual() {
        if (window.IAM && typeof window.IAM.getMix === "function") {
            return window.IAM.getMix();
        }
        return [];
    }

    function getColoresElemento() {
        if (window.IAM && window.IAM.COLORES_ELEMENTO) {
            return window.IAM.COLORES_ELEMENTO;
        }
        return {};
    }

    function formatearNumero(valor, decimales = 2) {
        if (valor === null || valor === undefined || isNaN(valor)) return "—";
        return Number(valor).toLocaleString("es-AR", {
            minimumFractionDigits: 0,
            maximumFractionDigits: decimales,
        });
    }

    // ==========================================================
    // RENDER DE LA COMPOSICIÓN DE LA MEZCLA
    // ==========================================================
    function renderComposicion() {
        const contChips = $("gdComposicionChips");
        const contenedor = $("gdComposicion");
        if (!contChips) return;

        const mix = getMezclaActual();
        if (!mix || mix.length === 0) {
            if (contenedor) {
                contenedor.style.display = "none";
            }
            return;
        }

        if (contenedor) {
            contenedor.style.display = "";
        }

        const colores = getColoresElemento();

        // Ordenar por porcentaje descendente
        const mixOrdenada = [...mix].sort((a, b) => (b.pct || 0) - (a.pct || 0));

        contChips.innerHTML = mixOrdenada.map(item => {
            const color = colores[item.elemento] || "#88c999";
            const pctStr = formatearNumero(item.pct, 2);
            return `
                <div class="grafico-composicion-chip">
                    <span
                        class="grafico-composicion-chip-color"
                        style="background:${color};"
                    ></span>
                    <span class="grafico-composicion-chip-elemento">
                        ${item.elemento}
                    </span>
                    <span class="grafico-composicion-chip-pct">
                        ${pctStr}%
                    </span>
                </div>
            `;
        }).join("");

        // Agregar total
        const total = mix.reduce((acc, e) => acc + (e.pct || 0), 0);
        contChips.innerHTML += `
            <div class="grafico-composicion-chip grafico-composicion-total">
                <span class="grafico-composicion-chip-elemento">Total</span>
                <span class="grafico-composicion-chip-pct">
                    ${formatearNumero(total, 2)}%
                </span>
            </div>
        `;
    }

    // ==========================================================
    // RENDER DE ESTADÍSTICAS
    // ==========================================================
    function renderStats(data) {
        const cont = $("gdStats");
        if (!cont) return;

        const stats = data.stats;
        const reg = data.regresion;
        const cantidadReales = (data.puntos_reales || []).length;
        const cantidadRegIntervalos = (data.puntos_regresion_intervalos || []).length;

        cont.style.display = "";
        let html = `
            <div class="grafico-stat-card">
                <div class="grafico-stat-label">Mínima</div>
                <div class="grafico-stat-valor stat-min">${formatearNumero(stats.min)} <small style="font-size:0.7em;">kg/m³</small></div>
            </div>
            <div class="grafico-stat-card">
                <div class="grafico-stat-label">Máxima</div>
                <div class="grafico-stat-valor stat-max">${formatearNumero(stats.max)} <small style="font-size:0.7em;">kg/m³</small></div>
            </div>
            <div class="grafico-stat-card">
                <div class="grafico-stat-label">Promedio</div>
                <div class="grafico-stat-valor stat-avg">${formatearNumero(stats.promedio)} <small style="font-size:0.7em;">kg/m³</small></div>
            </div>
            <div class="grafico-stat-card">
                <div class="grafico-stat-label">Puntos predichos</div>
                <div class="grafico-stat-valor">${stats.cantidad}</div>
            </div>
        `;

        if (reg) {
            html += `
                <div class="grafico-stat-card">
                    <div class="grafico-stat-label">R² del ajuste</div>
                    <div class="grafico-stat-valor stat-r2">${formatearNumero(reg.r2, 4)}</div>
                </div>
                <div class="grafico-stat-card">
                    <div class="grafico-stat-label">Pendiente</div>
                    <div class="grafico-stat-valor stat-pendiente">${formatearNumero(reg.pendiente, 4)}</div>
                </div>
            `;
        }

        html += `
            <div class="grafico-stat-card">
                <div class="grafico-stat-label">Puntos regresión</div>
                <div class="grafico-stat-valor stat-regresion">${cantidadRegIntervalos}</div>
            </div>
            <div class="grafico-stat-card">
                <div class="grafico-stat-label">Datos reales</div>
                <div class="grafico-stat-valor stat-real">${cantidadReales}</div>
            </div>
        `;

        cont.innerHTML = html;
    }

    // ==========================================================
    // RENDER DE LA ECUACIÓN DE REGRESIÓN
    // ==========================================================
    function renderEcuacion(data) {
        const ecuacion = $("gdEcuacion");
        if (!ecuacion) return;

        const reg = data.regresion;
        if (!reg || reg.pendiente === null || reg.pendiente === undefined) {
            ecuacion.style.display = "none";
            return;
        }

        const signo = reg.intercepto >= 0 ? "+" : "−";
        const b = Math.abs(reg.intercepto);
        ecuacion.innerHTML = `
            <span class="grafico-ecuacion-label">Ajuste lineal:</span>
            <span>ρ = ${formatearNumero(reg.pendiente, 4)} · T ${signo} ${formatearNumero(b, 2)}</span>
        `;
        ecuacion.style.display = "";
    }

    // ==========================================================
    // TOOLTIP PARA PUNTOS REALES (info completa de la fila)
    // ==========================================================
    function construirTooltipFilaReal(item) {
        const fila = item.raw.fila;
        if (!fila) {
            return [`Real: ${formatearNumero(item.raw.y, 2)} kg/m³`];
        }

        const lineas = [];
        lineas.push(`── Fila #${item.raw.indice_dataset + 1} del dataset ──`);

        for (const [col, val] of Object.entries(fila)) {
            if (val !== null && val !== undefined && val !== "") {
                const valStr = typeof val === "number"
                    ? formatearNumero(val, 4)
                    : String(val);
                lineas.push(`${col}: ${valStr}`);
            }
        }

        return lineas;
    }

    // ==========================================================
    // RENDER DEL GRÁFICO (Chart.js)
    // ==========================================================
    function renderChart(data) {
        const wrapper = $("gdWrapper");
        if (!wrapper) return;

        if (typeof Chart === "undefined") {
            mostrarError("Chart.js no está cargado. Refrescá la página.");
            return;
        }

        const hayReales = (data.puntos_reales || []).length > 0;
        const hayRegIntervalos = (data.puntos_regresion_intervalos || []).length > 0;

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

        const canvas = $("gdCanvas");
        const ctx = canvas.getContext("2d");

        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
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

        // DATOS REALES DEL DATASET (triángulos amarillos)
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

        // PUNTOS CUADRADOS ROJOS SOBRE LA REGRESIÓN
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

        // DENSIDAD PREDICHA (línea verde)
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

        // REGRESIÓN LINEAL (línea violeta punteada)
        if (data.regresion && data.regresion.linea) {
            datasets.push({
                label: "Regresión lineal",
                data: data.regresion.linea.map((p) => ({ x: p.x, y: p.y })),
                borderColor: "#c9a3f2",
                borderWidth: 2.5,
                borderDash: [6, 4],
                pointRadius: 0,
                pointHoverRadius: 0,
                fill: false,
            });
        }

        chartInstance = new Chart(ctx, {
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
                                const temp = formatearNumero(items[0].raw.x, 0);
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
                                        `Densidad (regresión): ${formatearNumero(item.raw.y, 2)} ${data.unidad_y}`,
                                        `Temperatura: ${formatearNumero(item.raw.x, 0)} ${data.unidad_x}`,
                                    ];
                                }

                                if (dataset.label === "Regresión lineal") {
                                    return `ŷ = ${formatearNumero(item.raw.y, 2)} ${data.unidad_y}`;
                                }

                                return `${dataset.label}: ${formatearNumero(item.raw.y, 2)} ${data.unidad_y}`;
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
                            text: `${data.etiqueta} (${data.unidad_y})`,
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
                        beginAtZero: false,
                    },
                },
            },
        });

        renderStats(data);
        renderEcuacion(data);
    }

    // ==========================================================
    // LLAMADA AL BACKEND
    // ==========================================================
    async function generarGrafico() {
        const mix = getMezclaActual();
        if (!mix || mix.length === 0) {
            mostrarError(
                "Agregá elementos a la mezcla antes de generar el gráfico."
            );
            return;
        }

        const total = mix.reduce((acc, e) => acc + (e.pct || 0), 0);
        if (Math.abs(total - 100) > 0.01) {
            mostrarError(
                `La mezcla debe sumar 100% (actual: ${total.toFixed(2)}%).`
            );
            return;
        }

        const { tempMin, tempMax, intervalo } = getFormularioValores();

        if (isNaN(tempMin) || isNaN(tempMax) || isNaN(intervalo)) {
            mostrarError("Completá los tres parámetros del rango.");
            return;
        }
        if (tempMax <= tempMin) {
            mostrarError("La temperatura máxima debe ser mayor que la mínima.");
            return;
        }
        if (intervalo <= 0) {
            mostrarError("El intervalo debe ser mayor que 0.");
            return;
        }

        setLoaderVisible(true);
        const btnGenerar = $("gdBtnGenerar");
        if (btnGenerar) btnGenerar.disabled = true;

        try {
            const respuesta = await fetch("/mezclas/grafico_densidad", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    mix,
                    temp_min: tempMin,
                    temp_max: tempMax,
                    intervalo,
                }),
            });
            const data = await respuesta.json().catch(() => ({}));
            if (!respuesta.ok || data.error) {
                throw new Error(
                    data.error || `Error ${respuesta.status}`
                );
            }
            ultimaConsulta = data;
            renderChart(data);

            const cantReales = (data.puntos_reales || []).length;
            const cantRegInt = (data.puntos_regresion_intervalos || []).length;
            if (window.mostrarToast) {
                window.mostrarToast(
                    "Gráfico generado",
                    `${data.stats.cantidad} puntos predichos, ` +
                    `${cantRegInt} puntos de regresión, ` +
                    `${cantReales} datos reales.` +
                    (data.regresion ? ` R² = ${formatearNumero(data.regresion.r2, 3)}.` : ""),
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
        a.download = `densidad_vs_temperatura_${Date.now()}.png`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        if (window.mostrarToast) {
            window.mostrarToast("Imagen descargada", "Gráfico guardado como PNG.");
        }
    }

    // ==========================================================
    // EXPORTAR A PDF
    // ==========================================================
    async function exportarPDF() {
        const mix = getMezclaActual();
        if (!mix || mix.length === 0) {
            if (window.mostrarToast) {
                window.mostrarToast(
                    "Error",
                    "Necesitás una mezcla válida para exportar.",
                    true
                );
            }
            return;
        }

        const total = mix.reduce((acc, e) => acc + (e.pct || 0), 0);
        if (Math.abs(total - 100) > 0.01) {
            if (window.mostrarToast) {
                window.mostrarToast(
                    "Error",
                    "La mezcla debe sumar 100% para exportar.",
                    true
                );
            }
            return;
        }

        const { tempMin, tempMax, intervalo } = getFormularioValores();

        if (isNaN(tempMin) || isNaN(tempMax) || isNaN(intervalo)) {
            if (window.mostrarToast) {
                window.mostrarToast(
                    "Error",
                    "Completá los parámetros del rango.",
                    true
                );
            }
            return;
        }

        const btnPDF = $("gdBtnPDF");
        if (btnPDF) btnPDF.disabled = true;

        if (window.mostrarToast) {
            window.mostrarToast("Generando PDF", "Creando documento PDF...", false);
        }

        try {
            const respuesta = await fetch("/mezclas/grafico_densidad/pdf", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    mix,
                    temp_min: tempMin,
                    temp_max: tempMax,
                    intervalo,
                }),
            });

            if (!respuesta.ok) {
                const data = await respuesta.json().catch(() => ({}));
                throw new Error(data.error || `Error ${respuesta.status}`);
            }

            const blob = await respuesta.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `densidad_vs_temperatura_${Date.now()}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);

            if (window.mostrarToast) {
                window.mostrarToast(
                    "PDF descargado",
                    "El documento PDF fue generado correctamente."
                );
            }
        } catch (error) {
            if (window.mostrarToast) {
                window.mostrarToast("Error al generar PDF", error.message, true);
            }
        } finally {
            if (btnPDF) btnPDF.disabled = false;
        }
    }

    // ==========================================================
    // INICIALIZACIÓN
    // ==========================================================
    function inicializarModal() {
        modalElement = $("modalGraficoDensidad");
        if (!modalElement) return;

        if (typeof bootstrap !== "undefined") {
            modalInstance = bootstrap.Modal.getOrCreateInstance(modalElement);
        }

        const btnGenerar = $("gdBtnGenerar");
        if (btnGenerar) {
            btnGenerar.addEventListener("click", generarGrafico);
        }

        const btnDescargar = $("gdBtnDescargar");
        if (btnDescargar) {
            btnDescargar.addEventListener("click", descargarPNG);
        }

        const btnPDF = $("gdBtnPDF");
        if (btnPDF) {
            btnPDF.addEventListener("click", exportarPDF);
        }

        ["gdTempMin", "gdTempMax", "gdIntervalo"].forEach((id) => {
            const input = $(id);
            if (input) {
                input.addEventListener("keydown", (e) => {
                    if (e.key === "Enter") {
                        e.preventDefault();
                        generarGrafico();
                    }
                });
            }
        });

        modalElement.addEventListener("hidden.bs.modal", () => {
            if (chartInstance) {
                chartInstance.destroy();
                chartInstance = null;
            }
        });

        // Al abrir el modal: mostrar composición y generar gráfico
        modalElement.addEventListener("shown.bs.modal", () => {
            mostrarVacio();
            renderComposicion();

            const mix = getMezclaActual();
            const total = mix.reduce((acc, e) => acc + (e.pct || 0), 0);
            if (mix.length > 0 && Math.abs(total - 100) < 0.01) {
                generarGrafico();
            }
        });
    }

    // ==========================================================
    // EXPONER API GLOBAL
    // ==========================================================
    window.GraficoDensidad = {
        abrir() {
            if (!modalInstance && modalElement && typeof bootstrap !== "undefined") {
                modalInstance = bootstrap.Modal.getOrCreateInstance(modalElement);
            }
            if (modalInstance) modalInstance.show();
        },
        generar: generarGrafico,
        exportarPDF: exportarPDF,
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