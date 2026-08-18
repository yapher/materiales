(function () {
    "use strict";

    const GT = window.GraficoTarta;
    if (!GT) return;

    /*
    Lógica de dibujo: caminos SVG, slices, render completo.
    */

    GT.caminoTapa = function (a0, a1) {
        const C = GT.CONFIG;
        const rx = C.radio;
        const ry = C.radio * C.inclinacion;
        let barrido = a1 - a0;

        if (barrido >= 359.9) {
            const p0 = GT.punto(a0);
            const pm = GT.punto(a0 + 180);
            return [
                `M ${C.cx} ${C.cy}`,
                `L ${p0.x} ${p0.y}`,
                `A ${rx} ${ry} 0 1 1 ${pm.x} ${pm.y}`,
                `A ${rx} ${ry} 0 1 1 ${p0.x} ${p0.y}`,
                "Z",
            ].join(" ");
        }

        const p0 = GT.punto(a0);
        const p1 = GT.punto(a1);
        const grande = barrido > 180 ? 1 : 0;
        return [
            `M ${C.cx} ${C.cy}`,
            `L ${p0.x} ${p0.y}`,
            `A ${rx} ${ry} 0 ${grande} 1 ${p1.x} ${p1.y}`,
            "Z",
        ].join(" ");
    };

    GT.caminoPared = function (a0, a1) {
        const C = GT.CONFIG;
        const s0 = Math.max(a0, 0);
        const s1 = Math.min(a1, 180);
        if (s1 - s0 <= 0.1) return null;

        const rx = C.radio;
        const ry = C.radio * C.inclinacion;
        const grande = s1 - s0 > 180 ? 1 : 0;
        const p0 = GT.punto(s0);
        const p1 = GT.punto(s1);
        const h = C.profundidad;

        return [
            `M ${p0.x} ${p0.y}`,
            `A ${rx} ${ry} 0 ${grande} 1 ${p1.x} ${p1.y}`,
            `L ${p1.x} ${p1.y + h}`,
            `A ${rx} ${ry} 0 ${grande} 0 ${p0.x} ${p0.y + h}`,
            "Z",
        ].join(" ");
    };

    GT.dibujarSlice = function (item, a0, a1) {
        const C = GT.CONFIG;
        const barrido = a1 - a0;
        if (barrido <= 0.05) return;

        const grupo = GT.crear("g", {
            class: item.restante
                ? "tarta-slice tarta-restante"
                : "tarta-slice",
            "data-elemento": item.id,
            "data-angulo-medio": String((a0 + a1) / 2),
        });

        const pared = GT.caminoPared(a0, a1);
        if (pared) {
            grupo.appendChild(
                GT.crear("path", {
                    class: "tarta-pared",
                    d: pared,
                    fill: item.restante
                        ? "url(#grad-rest-side)"
                        : `url(#grad-side-${item.id})`,
                })
            );
        }

        grupo.appendChild(
            GT.crear("path", {
                class: "tarta-tapa",
                d: GT.caminoTapa(a0, a1),
                fill: item.restante
                    ? "url(#grad-rest-top)"
                    : `url(#grad-top-${item.id})`,
            })
        );

        if (barrido >= C.anguloMinimoEtiqueta) {
            const pos = GT.punto((a0 + a1) / 2, 0.62);
            const etiqueta = GT.crear("text", {
                class: "tarta-etiqueta",
                x: pos.x,
                y: pos.y,
                "text-anchor": "middle",
                "dominant-baseline": "middle",
            });
            etiqueta.textContent = item.restante ? "Restante" : item.id;
            if (item.restante) {
                etiqueta.setAttribute(
                    "style",
                    "fill:#e6e1f7; stroke: rgba(20,16,31,0.55);"
                );
            }
            grupo.appendChild(etiqueta);
        }

        GT.state.capaSlices.appendChild(grupo);
    };

    GT.render = function () {
        const S = GT.state;
        const C = GT.CONFIG;
        if (!S.capaSlices) return;

        S.sliceActiva = null;
        if (S.tooltip) {
            S.tooltip.classList.remove("tooltip-visible");
        }

        while (S.capaSlices.firstChild) {
            S.capaSlices.removeChild(S.capaSlices.firstChild);
        }

        const total = GT.obtenerTotalVisible();
        const restante = Math.max(0, 100 - total);
        const hayDatos = total > 0.05 || restante > 0.05;
        const completo = Math.abs(total - 100) < 0.001;
        const excedido = total > 100.001;

        if (S.vacio) {
            S.vacio.style.display = "none";
        }

        S.contenedor.classList.toggle("grafico-tarta-con-datos", hayDatos);

        if (S.panel) {
            S.panel.classList.toggle("grafico-completo", completo);
            S.panel.classList.toggle("grafico-excedido", excedido);
        }

        if (S.badgeEstado) {
            if (excedido) {
                S.badgeEstado.textContent =
                    `Excedido ${GT.formatearNumero(total - 100)}%`;
            } else {
                S.badgeEstado.textContent =
                    `Restante ${GT.formatearNumero(restante)}%`;
            }
            S.badgeEstado.classList.toggle("estado-completo", completo);
            S.badgeEstado.classList.toggle("estado-excedido", excedido);
        }

        if (!hayDatos) {
            S.svg.setAttribute("aria-label", "Composición vacía");
            return;
        }

        const referencia = Math.max(total, 100);
        const items = [];

        S.objetivo.forEach((o) => {
            const pct = S.valoresVisibles.get(o.elemento) || 0;
            if (pct > 0.01) {
                items.push({ id: o.elemento, pct, restante: false });
            }
        });

        S.valoresVisibles.forEach((pct, elemento) => {
            const enObjetivo = S.objetivo.some(
                (o) => o.elemento === elemento
            );
            if (!enObjetivo && pct > 0.01) {
                items.push({ id: elemento, pct, restante: false });
            }
        });

        if (restante > 0.05 && !excedido) {
            items.push({ id: GT.ID_RESTANTE, pct: restante, restante: true });
        }

        let angulo = -90;
        items.forEach((item) => {
            const barrido = (item.pct / referencia) * 360;
            GT.dibujarSlice(item, angulo, angulo + barrido);
            angulo += barrido;
        });

        const resumen = items
            .filter((i) => !i.restante)
            .map((i) => `${i.id} ${GT.formatearNumero(i.pct)}%`)
            .join(", ");

        if (total <= 0.05) {
            S.svg.setAttribute(
                "aria-label",
                `Composición pendiente: restante ${GT.formatearNumero(restante)}%`
            );
        } else if (completo) {
            S.svg.setAttribute(
                "aria-label",
                `Composición completa: ${resumen}`
            );
        } else {
            S.svg.setAttribute(
                "aria-label",
                `Composición al ${GT.formatearNumero(total)}%: ${resumen}. ` +
                `Restante ${GT.formatearNumero(restante)}%`
            );
        }
    };
})();