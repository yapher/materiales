(function () {
    "use strict";

    const IAM = window.IAM;

    if (!IAM) {
        return;
    }

    /*
    Render de la mezcla:
    - chips de elementos
    - progreso
    - restante
    - input de porcentaje sugerido
    - botón Agregar
    - gráfico
    */

    IAM.actualizarMix = function () {
        const cont = document.getElementById("mixContainer");

        if (!cont) {
            return;
        }

        cont.innerHTML = "";

        IAM.state.mix.forEach(e => {
            const color = IAM.COLORES_ELEMENTO[e.elemento] || "#88c999";

            const div = document.createElement("div");
            div.className = "mix-tag";

            div.innerHTML = `
                <div class="elemento-chip" style="background:${color}">${e.elemento}</div>
                <span class="mix-tag-pct">${IAM.formatearPorcentaje(e.pct)}%</span>
                <button onclick="eliminarElemento('${e.elemento}')">✕</button>
            `;

            cont.appendChild(div);
        });

        const total = IAM.calcularTotalMezcla();
        const restante = IAM.calcularRestanteMezcla();
        const restanteParaInput = Math.max(0, restante);

        const porcentajeMostrar = Math.min(total, 100);

        const totalEl = document.getElementById("porcentajeTotal");
        if (totalEl) {
            totalEl.textContent = IAM.formatearPorcentaje(total);
        }

        const restanteEl = document.getElementById("porcentajeRestante");
        if (restanteEl) {
            restanteEl.textContent = IAM.formatearPorcentaje(restanteParaInput);
        }

        const inputPorcentaje = document.getElementById("porcentajeSel");
        if (inputPorcentaje) {
            inputPorcentaje.value = restanteParaInput > 0
                ? IAM.formatearPorcentaje(restanteParaInput)
                : "";
        }

        const btnAgregar = document.getElementById("btnAgregarElemento");
        if (btnAgregar) {
            btnAgregar.disabled = restanteParaInput <= 0.001;
        }

        const barEl = document.getElementById("mixBar");
        if (barEl) {
            barEl.style.width = `${porcentajeMostrar}%`;

            barEl.classList.remove(
                "progreso-incompleto",
                "progreso-excedido",
                "progreso-completo"
            );

            if (total > 100.001) {
                barEl.classList.add("progreso-excedido");
            } else if (Math.abs(total - 100) < 0.001) {
                barEl.classList.add("progreso-completo");
            } else {
                barEl.classList.add("progreso-incompleto");
            }
        }

        IAM.actualizarVisibilidadPredecir();

        if (
            window.GraficoTarta &&
            typeof window.GraficoTarta.actualizar === "function"
        ) {
            window.GraficoTarta.actualizar(IAM.state.mix);
        }
    };
})();