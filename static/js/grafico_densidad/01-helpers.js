(function () {
"use strict";

const GD = window.GraficoDensidad;
if (!GD) {
    return;
}

/*
Helpers transversales del gráfico:
- acceso a elementos del DOM
- formateo de números
- lectura del formulario y de la mezcla
- estados del wrapper (loader / error / vacío)
*/

GD.$ = function (id) {
    return document.getElementById(id);
};

GD.formatearNumero = function (valor, decimales = 2) {
    if (valor === null || valor === undefined || isNaN(valor)) {
        return "—";
    }
    return Number(valor).toLocaleString("es-AR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: decimales,
    });
};

GD.getFormularioValores = function () {
    const tempMin = parseFloat(GD.$("gdTempMin")?.value);
    const tempMax = parseFloat(GD.$("gdTempMax")?.value);
    const intervalo = parseFloat(GD.$("gdIntervalo")?.value);
    return { tempMin, tempMax, intervalo };
};

GD.getMezclaActual = function () {
    if (window.IAM && typeof window.IAM.getMix === "function") {
        return window.IAM.getMix();
    }
    return [];
};

GD.getColoresElemento = function () {
    if (window.IAM && window.IAM.COLORES_ELEMENTO) {
        return window.IAM.COLORES_ELEMENTO;
    }
    return {};
};

GD.setLoaderVisible = function (visible) {
    const loader = GD.$("gdLoader");
    if (loader) {
        loader.style.display = visible ? "flex" : "none";
    }
};

GD.mostrarError = function (mensaje) {
    const wrapper = GD.$("gdWrapper");
    if (!wrapper) {
        return;
    }
    wrapper.innerHTML = `
        <div class="grafico-densidad-error">
            <i class="bi bi-exclamation-triangle-fill"></i>
            <p class="grafico-error-text mb-0">${mensaje}</p>
        </div>
    `;
};

GD.mostrarVacio = function () {
    const wrapper = GD.$("gdWrapper");
    if (!wrapper) {
        return;
    }
    wrapper.innerHTML = `
        <div class="grafico-densidad-empty">
            <i class="bi bi-graph-up"></i>
            <p class="mb-0">Ajustá los parámetros y presioná "Generar".</p>
        </div>
    `;
};
})();