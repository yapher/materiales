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

    function formatearNumero(valor, decimales = 2) {
        if (valor === null || valor === undefined || isNaN(valor)) return "—";
        return Number(valor).toLocaleString("es-AR", {
            minimumFractionDigits: 0,
            maximumFractionDigits: decimales,
        });
    }

    // ==========================================================
    // RENDER DE ESTADÍSTICAS
    // ==========================================================
    function renderStats(stats) {
        const cont = $("gdStats");
        if (!cont) return;
        cont.style.display = "";
        cont.innerHTML = `
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
                <div class="grafico-stat-label">Puntos</div>
                <div class="grafico-stat-valor">${stats.cantidad}</div>
            </div>
        `;
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

        wrapper.innerHTML = `
            <div class="grafico-densidad-header">
                <div>
                    <h5 class="grafico-densidad-titulo">
                        <i class="bi bi-graph-up-arrow"></i>
                        Evolución de la densidad
                    </h5>
                    <p class="grafico-densidad-subtitulo">
                        ${data.etiqueta} en función de la temperatura
                        (${data.parametros.temp_min} K → ${data.parametros.temp_max} K,
                        cada ${data.parametros.intervalo} K)
                    </p>
                </div>
            </div>
            <div class="grafico-densidad-canvas-container">
                <canvas id="gdCanvas"></canvas>
            </div>
        `;

        const canvas = $("gdCanvas");
        const ctx = canvas.getContext("2d");

        // Destruir instancia previa
        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }

        const labels = data.puntos.map((p) => p.temperatura);
        const valores = data.puntos.map((p) => p.densidad);

        // Gradiente de relleno
        const gradiente = ctx.createLinearGradient(0, 0, 0, 360);
        gradiente.addColorStop(0, "rgba(136, 201, 153, 0.45)");
        gradiente.addColorStop(0.5, "rgba(136, 201, 153, 0.18)");
        gradiente.addColorStop(1, "rgba(136, 201, 153, 0.02)");

        chartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: data.etiqueta,
                        data: valores,
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
                        tension: 0.35,
                        cubicInterpolationMode: "monotone",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: "index",
                    intersect: false,
                },
                animation: {
                    duration: 900,
                    easing: "easeOutQuart",
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        backgroundColor: "rgba(30, 23, 48, 0.96)",
                        titleColor: "#f1eefc",
                        bodyColor: "#f1eefc",
                        borderColor: "rgba(136, 201, 153, 0.45)",
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        titleFont: { size: 13, weight: "600" },
                        bodyFont: { size: 12 },
                        callbacks: {
                            title: function (items) {
                                if (!items.length) return "";
                                return `Temperatura: ${items[0].label} K`;
                            },
                            label: function (item) {
                                return `${data.etiqueta}: ${formatearNumero(item.raw, 2)} ${data.unidad_y}`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
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
                            autoSkip: true,
                            maxTicksLimit: 15,
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

        renderStats(data.stats);
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
            if (window.mostrarToast) {
                window.mostrarToast(
                    "Gráfico generado",
                    `${data.stats.cantidad} puntos calculados.`,
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

        // Enter en los inputs dispara generar
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

        // Limpiar al cerrar
        modalElement.addEventListener("hidden.bs.modal", () => {
            if (chartInstance) {
                chartInstance.destroy();
                chartInstance = null;
            }
        });

        // Generar automáticamente al abrir
        modalElement.addEventListener("shown.bs.modal", () => {
            mostrarVacio();
            // Auto-generar con defaults si la mezcla es válida
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