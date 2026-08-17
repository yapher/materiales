(function () {
"use strict";

const GD = window.GraficoDensidad;
if (!GD) {
    return;
}

/*
Estadísticas del gráfico y ecuación de regresión.
*/

GD.renderStats = function (data) {
    const cont = GD.$("gdStats");
    if (!cont) {
        return;
    }

    const stats = data.stats;
    const reg = data.regresion;
    const cantidadReales = (data.puntos_reales || []).length;
    const cantidadRegIntervalos =
        (data.puntos_regresion_intervalos || []).length;

    cont.style.display = "";
    let html = `
        <div class="grafico-stat-card">
            <div class="grafico-stat-label">Mínima</div>
            <div class="grafico-stat-valor stat-min">${GD.formatearNumero(stats.min)} <small style="font-size:0.7em;">kg/m³</small></div>
        </div>
        <div class="grafico-stat-card">
            <div class="grafico-stat-label">Máxima</div>
            <div class="grafico-stat-valor stat-max">${GD.formatearNumero(stats.max)} <small style="font-size:0.7em;">kg/m³</small></div>
        </div>
        <div class="grafico-stat-card">
            <div class="grafico-stat-label">Promedio</div>
            <div class="grafico-stat-valor stat-avg">${GD.formatearNumero(stats.promedio)} <small style="font-size:0.7em;">kg/m³</small></div>
        </div>
        <div class="grafico-stat-card">
            <div class="grafico-stat-label">Puntos predichos</div>
            <div class="grafico-stat-valor">${stats.cantidad}</div>
        </div>
    `;

    if (reg) {
        html += `
            <div class="grafico-stat-card">
                <div class="grafico-stat-label">R² del ajuste</div>
                <div class="grafico-stat-valor stat-r2">${GD.formatearNumero(reg.r2, 4)}</div>
            </div>
            <div class="grafico-stat-card">
                <div class="grafico-stat-label">Pendiente</div>
                <div class="grafico-stat-valor stat-pendiente">${GD.formatearNumero(reg.pendiente, 4)}</div>
            </div>
        `;
    }

    html += `
        <div class="grafico-stat-card">
            <div class="grafico-stat-label">Puntos regresión</div>
            <div class="grafico-stat-valor stat-regresion">${cantidadRegIntervalos}</div>
        </div>
        <div class="grafico-stat-card">
            <div class="grafico-stat-label">Datos reales</div>
            <div class="grafico-stat-valor stat-real">${cantidadReales}</div>
        </div>
    `;

    cont.innerHTML = html;
};

GD.renderEcuacion = function (data) {
    const ecuacion = GD.$("gdEcuacion");
    if (!ecuacion) {
        return;
    }

    const reg = data.regresion;
    // La ecuación solo se muestra si la capa de regresión está activa.
    const visible = (
        GD.state.filtros.regresion &&
        reg &&
        reg.pendiente !== null &&
        reg.pendiente !== undefined
    );

    if (!visible) {
        ecuacion.style.display = "none";
        return;
    }

    const signo = reg.intercepto >= 0 ? "+" : "−";
    const b = Math.abs(reg.intercepto);
    ecuacion.innerHTML = `
        <span class="grafico-ecuacion-label">Ajuste lineal:</span>
        <span>ρ = ${GD.formatearNumero(reg.pendiente, 4)} · T ${signo} ${GD.formatearNumero(b, 2)}</span>
    `;
    ecuacion.style.display = "";
};
})();