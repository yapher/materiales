(function () {
    "use strict";

    /*
    Namespace global del gráfico de tarta 3D.
    Crea el contenedor de estado y configuración.
    */

    window.GraficoTarta = window.GraficoTarta || {};

    window.GraficoTarta.CONFIG = {
        ancho: 400,
        alto: 250,
        cx: 200,
        cy: 116,
        radio: 132,
        inclinacion: 0.52,
        profundidad: 34,
        duracion: 650,
        elevacionHover: 8,
        anguloMinimoEtiqueta: 20,
    };

    // Respetar preferencia de reducir movimiento
    if (
        window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
        window.GraficoTarta.CONFIG.duracion = 0;
    }

    window.GraficoTarta.COLORES_DEFAULT = {
        CaO: "#8fd694",
        SiO2: "#7fb8e0",
        Al2O3: "#e0a97f",
        MgO: "#a3e0a0",
        Na2O: "#f2d879",
        K2O: "#f2c879",
        Li2O: "#f2e79c",
        CaF2: "#c9a3f2",
        Fe2O3: "#e08a7f",
        MnO: "#d99fd0",
        TiO2: "#9fd0d9",
    };

    window.GraficoTarta.state = {
        panel: null,
        contenedor: null,
        svg: null,
        capaDefs: null,
        capaSombra: null,
        capaSlices: null,
        tooltip: null,
        vacio: null,
        badgeEstado: null,
        objetivo: [],
        valoresVisibles: new Map(),
        animId: null,
        sliceActiva: null,
        gradientesListos: false,
    };

    window.GraficoTarta.STORAGE_KEY = "grafico_tarta_visible";
    window.GraficoTarta.ID_RESTANTE = "__restante__";
    window.GraficoTarta.NS = "http://www.w3.org/2000/svg";
})();