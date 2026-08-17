(function () {
"use strict";

const GD = window.GraficoDensidad;
if (!GD) {
    return;
}

/*
Filtros de capas del gráfico.
Por defecto se muestra SOLO la densidad predicha.
La regresión lineal (línea violeta + cuadrados rojos) y los
datos reales del dataset (triángulos amarillos) se habilitan
con los checkboxes gdFiltroRegresion y gdFiltroReales.

Al cambiar un filtro se re-renderiza el gráfico usando los datos
ya cargados (state.ultimaConsulta), SIN volver a consultar al
backend.
*/

GD.leerFiltrosDesdeUI = function () {
    const chkRegresion = GD.$("gdFiltroRegresion");
    const chkReales = GD.$("gdFiltroReales");

    GD.state.filtros.predicha = true; // siempre visible
    GD.state.filtros.regresion = chkRegresion
        ? chkRegresion.checked
        : false;
    GD.state.filtros.reales = chkReales
        ? chkReales.checked
        : false;

    // Estado visual de los chips
    [chkRegresion, chkReales].forEach(function (chk) {
        if (!chk) {
            return;
        }
        const label = chk.closest(".grafico-filtro-check");
        if (label) {
            label.classList.toggle("filtro-activo", chk.checked);
        }
    });
};

GD.aplicarFiltros = function () {
    GD.leerFiltrosDesdeUI();
    // Re-renderiza con los datos ya cargados, sin nuevo fetch.
    if (GD.state.ultimaConsulta) {
        GD.renderChart(GD.state.ultimaConsulta);
    }
};

GD.bindFiltros = function () {
    ["gdFiltroRegresion", "gdFiltroReales"].forEach(function (id) {
        const checkbox = GD.$(id);
        if (checkbox) {
            checkbox.addEventListener("change", GD.aplicarFiltros);
        }
    });
    // Estado visual inicial (ambos desactivados por defecto).
    GD.leerFiltrosDesdeUI();
};
})();