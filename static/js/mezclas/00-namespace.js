(function () {
    "use strict";

    /*
    Namespace global de la aplicación.

    Este archivo crea el objeto base que usan todos los módulos
    de static/js/mezclas/.

    No contiene lógica de negocio, solo el contenedor de estado
    y constantes globales.
    */

    window.IAM = window.IAM || {};

    window.IAM.state = {
        mix: [],
        modeloListo: false,
        ultimaMezcla: null,

        datosR2: [],
        datosPrediccion: [],

        ordenEstado: {},

        pollEntrenamiento: null
    };

    window.IAM.COLORES_ELEMENTO = {
        CaO:   "#60f06a",
        SiO2:  "#115b8f",
        Al2O3: "#e6731b",
        MgO:   "#a1bba0",
        Na2O:  "#dcf279",
        K2O:   "#f2c879",
        Li2O:  "#ba1c1c",
        CaF2:  "#c9a3f2",
        Fe2O3: "#e08a7f",
        MnO:   "#8c2f7c",
        TiO2:  "#9fd0d9"
    };
})();