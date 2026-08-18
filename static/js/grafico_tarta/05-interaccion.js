(function () {
    "use strict";

    const GT = window.GraficoTarta;
    if (!GT) return;

    /*
    Interacción: hover, tooltip, toggle de visibilidad.
    */

    GT.conectarEventos = function () {
        const S = GT.state;

        S.svg.addEventListener("pointerover", (ev) => {
            const grupo = ev.target.closest
                ? ev.target.closest(".tarta-slice")
                : null;
            if (!grupo) {
                GT.desactivarSlice();
                return;
            }
            GT.activarSlice(grupo, ev.clientX, ev.clientY);
        });

        S.svg.addEventListener("pointermove", (ev) => {
            if (S.sliceActiva) {
                GT.posicionarTooltip(ev.clientX, ev.clientY);
            }
        });

        S.svg.addEventListener("pointerleave", GT.desactivarSlice);

        document.addEventListener(
            "pointerdown",
            (ev) => {
                if (S.contenedor && !S.contenedor.contains(ev.target)) {
                    GT.desactivarSlice();
                }
            },
            true
        );
    };

    GT.activarSlice = function (grupo, clientX, clientY) {
        const S = GT.state;
        const C = GT.CONFIG;

        if (S.sliceActiva && S.sliceActiva !== grupo) {
            S.sliceActiva.classList.remove("tarta-slice-activa");
            S.sliceActiva.style.transform = "";
        }

        S.sliceActiva = grupo;
        S.capaSlices.appendChild(grupo);
        grupo.classList.add("tarta-slice-activa");

        const mid = parseFloat(grupo.dataset.anguloMedio || "0");
        const rad = (mid * Math.PI) / 180;
        const dx = C.elevacionHover * Math.cos(rad);
        const dy = C.elevacionHover * Math.sin(rad) * C.inclinacion;
        grupo.style.transform = `translate(${dx}px, ${dy}px)`;

        GT.mostrarTooltip(grupo.dataset.elemento, clientX, clientY);
    };

    GT.desactivarSlice = function () {
        const S = GT.state;
        if (S.sliceActiva) {
            S.sliceActiva.classList.remove("tarta-slice-activa");
            S.sliceActiva.style.transform = "";
            S.sliceActiva = null;
        }
        if (S.tooltip) {
            S.tooltip.classList.remove("tooltip-visible");
        }
    };

    GT.mostrarTooltip = function (elemento, clientX, clientY) {
        const S = GT.state;
        if (!S.tooltip) return;

        const colores = GT.conseguirColores();
        const esRestante = elemento === GT.ID_RESTANTE;
        const totalVisible = GT.obtenerTotalVisible();
        const pct = esRestante
            ? Math.max(0, 100 - totalVisible)
            : (S.valoresVisibles.get(elemento) || 0);
        const label = esRestante ? "Restante" : elemento;
        const color = esRestante
            ? "#6f6a85"
            : (colores[elemento] || "#88c999");

        S.tooltip.innerHTML = `
            <span
                class="grafico-tarta-tooltip-chip"
                style="background:${color};"
            ></span>
            <strong>${label}</strong>
            <span class="grafico-tarta-tooltip-pct">
                ${GT.formatearNumero(pct)}%
            </span>
        `;

        S.tooltip.classList.add("tooltip-visible");
        GT.posicionarTooltip(clientX, clientY);
    };

    GT.posicionarTooltip = function (clientX, clientY) {
        const S = GT.state;
        if (!S.tooltip || !S.contenedor) return;

        const rect = S.contenedor.getBoundingClientRect();
        let x = clientX - rect.left;
        let y = clientY - rect.top;

        x = Math.min(Math.max(x, 60), Math.max(rect.width - 60, 60));
        y = Math.max(y, 46);

        S.tooltip.style.left = `${x}px`;
        S.tooltip.style.top = `${y}px`;
    };

    GT.initToggleTarta = function () {
        const checkbox = document.getElementById("checkGraficoTarta");
        const panelTarta = document.getElementById("panelGraficoTarta");
        if (!checkbox || !panelTarta) return;

        let visible = false;
        try {
            visible =
                localStorage.getItem(GT.STORAGE_KEY) === "true";
        } catch (e) {
            visible = false;
        }

        checkbox.checked = visible;
        panelTarta.style.display = visible ? "block" : "none";

        checkbox.addEventListener("change", function () {
            const mostrar = checkbox.checked;
            panelTarta.style.display = mostrar ? "block" : "none";
            try {
                localStorage.setItem(GT.STORAGE_KEY, String(mostrar));
            } catch (e) {}
            if (mostrar) {
                GT.render();
            }
        });
    };
})();