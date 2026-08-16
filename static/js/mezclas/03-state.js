(function () {
    "use strict";

    const IAM = window.IAM;

    if (!IAM) {
        return;
    }

    /*
    Estado de la mezcla y cálculos básicos.
    */

    IAM.calcularTotalMezcla = function () {
        const total = IAM.state.mix.reduce((acc, e) => acc + (e.pct || 0), 0);

        return Math.round(total * 1000) / 1000;
    };

    IAM.calcularRestanteMezcla = function () {
        const restante = 100 - IAM.calcularTotalMezcla();

        return Math.round(restante * 1000) / 1000;
    };

    IAM.getMix = function () {
        return JSON.parse(JSON.stringify(IAM.state.mix));
    };
})();