(function () {
    "use strict";

    const IAM = window.IAM;

    if (!IAM) {
        return;
    }

    /*
    Acciones de composición:
    - agregar elemento
    - eliminar elemento
    */

    IAM.agregarElemento = function () {
        const elemento = document.getElementById("elementoSel").value;
        const restante = IAM.calcularRestanteMezcla();

        let pct = parseFloat(
            document.getElementById("porcentajeSel").value
        );

        // Si el usuario deja vacío el campo, o pone algo inválido,
        // se sugiere automáticamente el porcentaje restante.
        if (isNaN(pct) || pct <= 0) {
            pct = restante;
        }

        pct = Math.round(pct * 1000) / 1000;

        if (!elemento) {
            return IAM.setMensaje("Selecciona un elemento");
        }

        if (isNaN(pct) || pct <= 0) {
            return IAM.setMensaje("Porcentaje inválido");
        }

        if (IAM.state.mix.some(e => e.elemento === elemento)) {
            return IAM.setMensaje("Elemento ya agregado");
        }

        const total = IAM.calcularTotalMezcla();

        if (total + pct > 100.001) {
            return IAM.setMensaje(
                `No puede superar 100% (actual: ${IAM.formatearPorcentaje(total)}%)`
            );
        }

        IAM.state.mix.push({
            elemento,
            pct
        });

        document.getElementById("elementoSel").value = "";
        document.getElementById("porcentajeSel").value = "";

        IAM.actualizarMix();
        IAM.setOcupado(false);

        IAM.state.datosPrediccion = [];
        IAM.renderTablaPrediccion();

        const nuevoTotal = IAM.calcularTotalMezcla();
        const nuevoRestante = IAM.calcularRestanteMezcla();

        IAM.setMensaje(
            `Total: ${IAM.formatearPorcentaje(nuevoTotal)}% — ` +
            `Restante: ${IAM.formatearPorcentaje(Math.max(0, nuevoRestante))}%`
        );
    };

    IAM.eliminarElemento = function (elemento) {
        IAM.state.mix = IAM.state.mix.filter(e => e.elemento !== elemento);

        IAM.state.datosPrediccion = [];
        IAM.renderTablaPrediccion();

        IAM.actualizarMix();
        IAM.setOcupado(false);

        const nuevoRestante = IAM.calcularRestanteMezcla();

        IAM.setMensaje(
            `Mezcla modificada. Restante: ${IAM.formatearPorcentaje(Math.max(0, nuevoRestante))}%. ` +
            `Ajustá el 100% y volvé a predecir.`
        );
    };
})();