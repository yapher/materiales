(function () {
"use strict";

const GD = window.GraficoDensidad;
if (!GD) {
    return;
}

/*
Composición de la mezcla analizada:
chips de colores con elemento y porcentaje.
*/

GD.renderComposicion = function () {
    const contChips = GD.$("gdComposicionChips");
    const contenedor = GD.$("gdComposicion");
    if (!contChips) {
        return;
    }

    const mix = GD.getMezclaActual();
    if (!mix || mix.length === 0) {
        if (contenedor) {
            contenedor.style.display = "none";
        }
        return;
    }
    if (contenedor) {
        contenedor.style.display = "";
    }

    const colores = GD.getColoresElemento();
    const mixOrdenada = [...mix].sort(
        (a, b) => (b.pct || 0) - (a.pct || 0)
    );

    contChips.innerHTML = mixOrdenada.map(item => {
        const color = colores[item.elemento] || "#88c999";
        const pctStr = GD.formatearNumero(item.pct, 2);
        return `
            <div class="grafico-composicion-chip">
                <span
                    class="grafico-composicion-chip-color"
                    style="background:${color};"
                ></span>
                <span class="grafico-composicion-chip-elemento">
                    ${item.elemento}
                </span>
                <span class="grafico-composicion-chip-pct">
                    ${pctStr}%
                </span>
            </div>
        `;
    }).join("");

    const total = mix.reduce((acc, e) => acc + (e.pct || 0), 0);
    contChips.innerHTML += `
        <div class="grafico-composicion-chip grafico-composicion-total">
            <span class="grafico-composicion-chip-elemento">Total</span>
            <span class="grafico-composicion-chip-pct">
                ${GD.formatearNumero(total, 2)}%
            </span>
        </div>
    `;
};
})();