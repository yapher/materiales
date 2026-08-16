(function () {
    "use strict";

    const IAM = window.IAM;

    if (!IAM) {
        return;
    }

    /*
    Helpers de formateo y normalización de valores.
    */

    IAM.escaparHtml = function (valor) {
        return String(valor)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    IAM.formatearPorcentaje = function (valor) {
        if (Number.isInteger(valor)) {
            return valor.toString();
        }

        return valor.toFixed(2).replace(/\.?0+$/, "");
    };

    IAM.normalizarValorOrden = function (valor) {
        if (valor === null || valor === undefined) {
            return null;
        }

        if (typeof valor === "number") {
            return valor;
        }

        const numero = Number(valor);

        if (!Number.isNaN(numero)) {
            return numero;
        }

        return String(valor);
    };

    IAM.claseR2 = function (valor) {
        if (valor >= 0.8) {
            return "bueno";
        }

        if (valor >= 0.5) {
            return "medio";
        }

        return "malo";
    };
})();