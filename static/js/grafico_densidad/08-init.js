(function () {
"use strict";

const GD = window.GraficoDensidad;
if (!GD) {
    return;
}

/*
Inicialización del panel densidad vs. temperatura:
- botones de generar, PNG y PDF
- Enter en los inputs del rango
- checkboxes de capas (02-filtros.js)
*/

function inicializarPanel() {
    const btnGenerar = GD.$("gdBtnGenerar");
    if (btnGenerar) {
        btnGenerar.addEventListener("click", function () {
            GD.generar(false);
        });
    }

    const btnDescargar = GD.$("gdBtnDescargar");
    if (btnDescargar) {
        btnDescargar.addEventListener("click", GD.descargarPNG);
    }

    const btnPDF = GD.$("gdBtnPDF");
    if (btnPDF) {
        btnPDF.addEventListener("click", GD.exportarPDF);
    }

    ["gdTempMin", "gdTempMax", "gdIntervalo"].forEach(function (id) {
        const input = GD.$(id);
        if (input) {
            input.addEventListener("keydown", function (e) {
                if (e.key === "Enter") {
                    e.preventDefault();
                    GD.generar(false);
                }
            });
        }
    });

    GD.bindFiltros();
}

function init() {
    inicializarPanel();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
})();