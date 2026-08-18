(function () {
    "use strict";

    const GT = window.GraficoTarta;
    if (!GT) return;

    /*
    Construcción del SVG: defs, sombra, capas, tooltip, vacío.
    */

    GT.crearGradiente = function (id, colorArriba, colorAbajo) {
        const grad = GT.crear("linearGradient", {
            id,
            x1: "0",
            y1: "0",
            x2: "0",
            y2: "1",
        });
        grad.appendChild(
            GT.crear("stop", { offset: "0%", "stop-color": colorArriba })
        );
        grad.appendChild(
            GT.crear("stop", { offset: "100%", "stop-color": colorAbajo })
        );
        GT.state.capaDefs.appendChild(grad);
    };

    GT.asegurarGradientes = function () {
        if (GT.state.gradientesListos) return;
        const colores = GT.conseguirColores();
        Object.entries(colores).forEach(([elemento, color]) => {
            GT.crearGradiente(
                `grad-top-${elemento}`,
                GT.ajustarColor(color, 1.30),
                GT.ajustarColor(color, 0.94)
            );
            GT.crearGradiente(
                `grad-side-${elemento}`,
                GT.ajustarColor(color, 0.66),
                GT.ajustarColor(color, 0.42)
            );
        });
        GT.crearGradiente("grad-rest-top", "#332a52", "#2a2145");
        GT.crearGradiente("grad-rest-side", "#241d3d", "#1c1631");
        GT.state.gradientesListos = true;
    };

    GT.construir = function () {
        const S = GT.state;
        const C = GT.CONFIG;

        S.svg = GT.crear("svg", {
            viewBox: `0 0 ${C.ancho} ${C.alto}`,
            class: "tarta-svg",
            role: "img",
            "aria-label": "Gráfico de tarta 3D de la composición de la mezcla",
        });

        S.capaDefs = GT.crear("defs");
        const filtro = GT.crear("filter", {
            id: "tartaBlur",
            x: "-40%",
            y: "-40%",
            width: "180%",
            height: "180%",
        });
        filtro.appendChild(
            GT.crear("feGaussianBlur", {
                in: "SourceGraphic",
                stdDeviation: "7",
            })
        );
        S.capaDefs.appendChild(filtro);
        S.svg.appendChild(S.capaDefs);

        S.capaSombra = GT.crear("ellipse", {
            class: "tarta-sombra",
            cx: C.cx,
            cy: C.cy + C.profundidad + 8,
            rx: C.radio * 1.03,
            ry: C.radio * C.inclinacion * 0.9,
            fill: "rgba(0, 0, 0, 0.55)",
            filter: "url(#tartaBlur)",
        });
        S.svg.appendChild(S.capaSombra);

        S.capaSlices = GT.crear("g", { class: "tarta-capas" });
        S.svg.appendChild(S.capaSlices);

        S.contenedor.appendChild(S.svg);

        S.vacio = document.createElement("div");
        S.vacio.className = "grafico-tarta-vacio";
        S.vacio.innerHTML = `
            <i class="bi bi-pie-chart"></i>
            <p>Agregá elementos para<br>armar tu mezcla</p>
        `;
        S.contenedor.appendChild(S.vacio);

        S.tooltip = document.createElement("div");
        S.tooltip.className = "grafico-tarta-tooltip";
        S.tooltip.setAttribute("role", "status");
        S.contenedor.appendChild(S.tooltip);

        GT.asegurarGradientes();
        GT.conectarEventos();
    };
})();