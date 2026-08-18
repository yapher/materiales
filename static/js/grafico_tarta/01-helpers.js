(function () {
    "use strict";

    const GT = window.GraficoTarta;
    if (!GT) return;

    /*
    Helpers: creación de elementos SVG, formateo, colores.
    */

    GT.crear = function (tag, attrs = {}) {
        const nodo = document.createElementNS(GT.NS, tag);
        Object.entries(attrs).forEach(([k, v]) => {
            nodo.setAttribute(k, v);
        });
        return nodo;
    };

    GT.conseguirColores = function () {
        if (window.MezclasApp && window.MezclasApp.colores) {
            return Object.assign(
                {},
                GT.COLORES_DEFAULT,
                window.MezclasApp.colores
            );
        }
        return GT.COLORES_DEFAULT;
    };

    GT.ajustarColor = function (color, factor) {
        let hex = String(color).replace("#", "");
        if (hex.length === 3) {
            hex = hex.split("").map((c) => c + c).join("");
        }
        const n = parseInt(hex, 16);
        const r = Math.min(255, Math.max(0, Math.round(((n >> 16) & 255) * factor)));
        const g = Math.min(255, Math.max(0, Math.round(((n >> 8) & 255) * factor)));
        const b = Math.min(255, Math.max(0, Math.round((n & 255) * factor)));
        return `rgb(${r}, ${g}, ${b})`;
    };

    GT.formatearNumero = function (valor) {
        const redondeado = Math.round(valor * 100) / 100;
        if (Number.isInteger(redondeado)) {
            return String(redondeado);
        }
        return redondeado.toFixed(2).replace(/\.?0+$/, "");
    };

    GT.obtenerTotalVisible = function () {
        let total = 0;
        GT.state.valoresVisibles.forEach((v) => {
            total += Number(v) || 0;
        });
        return total;
    };

    GT.punto = function (angulo, escala = 1) {
        const C = GT.CONFIG;
        const rad = (angulo * Math.PI) / 180;
        return {
            x: C.cx + C.radio * escala * Math.cos(rad),
            y: C.cy + C.radio * C.inclinacion * escala * Math.sin(rad),
        };
    };
})();