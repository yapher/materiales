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
    btnPredecir.disabled = (
        !IAM.state.modeloListo ||
        !mezclaCompleta ||
        !temperaturaCargada
    );
    IAM.notificarWorkflow();
};

/*
Control de visibilidad del panel INLINE de densidad vs temperatura.
El panel aparece debajo de la composición SOLO cuando ya se realizó
al menos una predicción (datosPrediccion.length > 0).
Al aparecer por primera vez, dispara la generación automática del gráfico.
*/
IAM.actualizarVisibilidadGraficoDensidad = function () {
    const panel = document.getElementById("panelGraficoDensidadInline");
    if (!panel) {
        return;
    }

    const hayPrediccion = (
        IAM.state.datosPrediccion &&
        IAM.state.datosPrediccion.length > 0
    );

    const estabaVisible = panel.style.display !== "none";

    panel.style.display = hayPrediccion ? "block" : "none";

    // Si acabamos de mostrar el panel y hay mezcla válida,
    // generar el gráfico automáticamente.
    if (hayPrediccion && !estabaVisible) {
        if (
            window.GraficoDensidad &&
            typeof window.GraficoDensidad.generarAutomatico === "function"
        ) {
            // Pequeño delay para que el navegador termine de renderizar
            // el panel antes de dibujar el canvas.
            setTimeout(function () {
                window.GraficoDensidad.generarAutomatico();
            }, 120);
        }
    }
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