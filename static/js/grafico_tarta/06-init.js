(function () {
    "use strict";

    const GT = window.GraficoTarta;
    if (!GT) return;

    /*
    Inicialización y API pública.
    */

    GT.actualizar = function (mix) {
        GT.animarHacia(mix);
    };

    function init() {
        const S = GT.state;

        S.contenedor = document.getElementById("graficoTarta");
        if (!S.contenedor) return;

        S.panel = S.contenedor.closest(".grafico-tarta-panel");
        S.badgeEstado = document.getElementById("graficoTartaEstado");

        GT.construir();
        GT.render();
        GT.initToggleTarta();

        if (
            window.MezclasApp &&
            typeof window.MezclasApp.getMix === "function"
        ) {
            const mix = window.MezclasApp.getMix();
            if (Array.isArray(mix) && mix.length > 0) {
                S.objetivo = mix.map((e) => ({
                    elemento: String(e.elemento),
                    pct: Math.max(0, Number(e.pct) || 0),
                }));
                S.valoresVisibles = new Map(
                    S.objetivo.map((o) => [o.elemento, o.pct])
                );
                GT.render();
            }
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();