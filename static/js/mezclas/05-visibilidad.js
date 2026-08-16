(function () {
    "use strict";

    const IAM = window.IAM;

    if (!IAM) {
        return;
    }

    /*
    Control de visibilidad y habilitación de acciones principales.
    */

    IAM.actualizarVisibilidadPredecir = function () {
        const btnPredecir = document.getElementById("btnPredecir");

        if (!btnPredecir) {
            return;
        }

        const total = IAM.calcularTotalMezcla();
        const mezclaCompleta = Math.abs(total - 100) < 0.001;

        const temperatura = IAM.obtenerTemperatura();
        const temperaturaCargada = temperatura.cargada;

        btnPredecir.style.display = IAM.state.modeloListo
            ? "inline-block"
            : "none";

        // El botón solo se habilita si:
        // 1) el modelo está entrenado,
        // 2) la mezcla suma exactamente 100%,
        // 3) la temperatura está cargada.
        btnPredecir.disabled = (
            !IAM.state.modeloListo ||
            !mezclaCompleta ||
            !temperaturaCargada
        );

        IAM.notificarWorkflow();
    };

    IAM.setOcupado = function (ocupado) {
        const datasetOk = (
            window.FlujoModelo &&
            typeof window.FlujoModelo.isDatasetListo === "function"
        )
            ? window.FlujoModelo.isDatasetListo()
            : true;

        const entrenamientoCorriendo = (
            window.FlujoModelo &&
            typeof window.FlujoModelo.isEntrenamientoCorriendo === "function"
        )
            ? window.FlujoModelo.isEntrenamientoCorriendo()
            : false;

        const btnEntrenar = document.getElementById("btnEntrenar");

        if (btnEntrenar) {
            btnEntrenar.disabled = (
                ocupado ||
                !datasetOk ||
                entrenamientoCorriendo
            );
        }

        IAM.actualizarVisibilidadPredecir();
    };
})();