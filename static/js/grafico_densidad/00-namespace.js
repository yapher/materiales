(function () {
"use strict";

/*
Namespace global del gráfico densidad vs. temperatura.
Este archivo crea el objeto base que usan todos los módulos
de static/js/grafico_densidad/.
No contiene lógica de negocio, solo el contenedor de estado.

Estado de filtros:
- predicha:  línea verde, SIEMPRE visible (no se puede apagar).
- regresion: línea violeta + cuadrados rojos. Default: apagada.
- reales:    triángulos amarillos del dataset. Default: apagados.
*/

window.GraficoDensidad = window.GraficoDensidad || {};

window.GraficoDensidad.state = {
    chartInstance: null,
    ultimaConsulta: null,
    filtros: {
        predicha: true,
        regresion: false,
        reales: false
    }
};
})();