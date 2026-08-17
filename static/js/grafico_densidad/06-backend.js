(function () {
"use strict";

const GD = window.GraficoDensidad;
if (!GD) {
    return;
}

/*
Consulta al backend y generación del gráfico.
*/

GD.validarEntrada = function () {
    const mix = GD.getMezclaActual();
    if (!mix || mix.length === 0) {
        GD.mostrarError(
            "Agregá elementos a la mezcla antes de generar el gráfico."
        );
        return null;
    }

    const total = mix.reduce((acc, e) => acc + (e.pct || 0), 0);
    if (Math.abs(total - 100) > 0.01) {
        GD.mostrarError(
            `La mezcla debe sumar 100% (actual: ${total.toFixed(2)}%).`
        );
        return null;
    }

    const { tempMin, tempMax, intervalo } = GD.getFormularioValores();
    if (isNaN(tempMin) || isNaN(tempMax) || isNaN(intervalo)) {
        GD.mostrarError("Completá los tres parámetros del rango.");
        return null;
    }
    if (tempMax <= tempMin) {
        GD.mostrarError(
            "La temperatura máxima debe ser mayor que la mínima."
        );
        return null;
    }
    if (intervalo <= 0) {
        GD.mostrarError("El intervalo debe ser mayor que 0.");
        return null;
    }

    return { mix, tempMin, tempMax, intervalo };
};

GD.generar = async function (silencioso = false) {
    const entrada = GD.validarEntrada();
    if (!entrada) {
        return;
    }

    GD.setLoaderVisible(true);
    const btnGenerar = GD.$("gdBtnGenerar");
    if (btnGenerar) {
        btnGenerar.disabled = true;
    }

    try {
        const respuesta = await fetch("/mezclas/grafico_densidad", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                mix: entrada.mix,
                temp_min: entrada.tempMin,
                temp_max: entrada.tempMax,
                intervalo: entrada.intervalo,
            }),
        });
        const data = await respuesta.json().catch(() => ({}));
        if (!respuesta.ok || data.error) {
            throw new Error(
                data.error || `Error ${respuesta.status}`
            );
        }

        GD.state.ultimaConsulta = data;
        GD.renderChart(data);

        if (!silencioso && window.mostrarToast) {
            const cantReales = (data.puntos_reales || []).length;
            const cantRegInt =
                (data.puntos_regresion_intervalos || []).length;
            window.mostrarToast(
                "Gráfico generado",
                `${data.stats.cantidad} puntos predichos, ` +
                `${cantRegInt} puntos de regresión, ` +
                `${cantReales} datos reales.` +
                (data.regresion
                    ? ` R² = ${GD.formatearNumero(data.regresion.r2, 3)}.`
                    : ""),
                false
            );
        }
    } catch (error) {
        GD.mostrarError(error.message);
        if (!silencioso && window.mostrarToast) {
            window.mostrarToast("Error", error.message, true);
        }
    } finally {
        GD.setLoaderVisible(false);
        if (btnGenerar) {
            btnGenerar.disabled = false;
        }
    }
};

GD.generarAutomatico = function () {
    // Se llama cuando el panel se muestra por primera vez
    // tras una predicción (ver mezclas/05-visibilidad.js).
    GD.renderComposicion();
    GD.generar(true); // silencioso: no muestra toast
};
})();