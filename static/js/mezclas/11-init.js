(function () {
    "use strict";

    const IAM = window.IAM;

    if (!IAM) {
        return;
    }

    /*
    Inicialización y compatibilidad global.

    Este archivo:
    - expone funciones globales necesarias por onclick inline
    - expone window.MezclasApp
    - inicializa la página de mezclas si corresponde
    */

    window.agregarElemento = IAM.agregarElemento;
    window.eliminarElemento = IAM.eliminarElemento;
    window.predecir = IAM.predecir;
    window.exportarPrediccionPDF = IAM.exportarPrediccionPDF;
    window.guardarPrediccionDataset = IAM.guardarPrediccionDataset;
    window.ordenarTabla = IAM.ordenarTabla;
    window.iniciarPollEntrenamiento = IAM.iniciarPollEntrenamiento;

    window.setMensaje = IAM.setMensaje;
    window.setOcupado = IAM.setOcupado;
    window.mostrarToast = IAM.mostrarToast;
    window.confirmarModerno = IAM.confirmarModerno;

    window.MezclasApp = {
        getModeloListo() {
            return IAM.state.modeloListo;
        },

        hayPrediccion() {
            return IAM.state.datosPrediccion.length > 0;
        },

        getMix() {
            return IAM.getMix();
        },

        colores: IAM.COLORES_ELEMENTO
    };

    IAM.init = function () {
        const temperaturaEl = document.getElementById("temperatura");

        if (temperaturaEl) {
            temperaturaEl.addEventListener(
                "input",
                IAM.actualizarVisibilidadPredecir
            );
        }

        IAM.consultarEstadoEntrenamiento();

        if (document.getElementById("mixContainer")) {
            IAM.actualizarMix();
            IAM.setOcupado(false);
            IAM.comprobarEstadoServidor();
            IAM.restaurarUltimaPrediccion();
        }
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", IAM.init);
    } else {
        IAM.init();
    }
})();