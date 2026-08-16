(function () {
    "use strict";

    const IAM = window.IAM;

    if (!IAM) {
        return;
    }

    /*
    Lectura y validación de la temperatura del proceso.
    */

    IAM.obtenerTemperatura = function () {
        const input = document.getElementById("temperatura");

        if (!input) {
            return {
                cargada: false,
                valor: null
            };
        }

        const crudo = String(input.value || "").trim();

        if (crudo === "") {
            return {
                cargada: false,
                valor: null
            };
        }

        const numero = parseFloat(crudo);

        if (!Number.isFinite(numero) || numero <= 0) {
            return {
                cargada: false,
                valor: null
            };
        }

        return {
            cargada: true,
            valor: numero
        };
    };
})();