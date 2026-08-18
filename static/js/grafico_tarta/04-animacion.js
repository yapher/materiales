(function () {
    "use strict";

    const GT = window.GraficoTarta;
    if (!GT) return;

    /*
    Animación de transición entre estados de mezcla.
    */

    GT.animarHacia = function (nuevaMezcla) {
        const S = GT.state;
        const C = GT.CONFIG;
        if (!S.contenedor) return;

        const mezcla = Array.isArray(nuevaMezcla) ? nuevaMezcla : [];
        S.objetivo = mezcla.map((e) => ({
            elemento: String(e.elemento),
            pct: Math.max(0, Number(e.pct) || 0),
        }));

        if (S.animId) {
            cancelAnimationFrame(S.animId);
        }

        if (C.duracion <= 0) {
            S.valoresVisibles = new Map(
                S.objetivo
                    .filter((o) => o.pct > 0)
                    .map((o) => [o.elemento, o.pct])
            );
            GT.render();
            return;
        }

        const desde = new Map(S.valoresVisibles);
        const claves = new Set([
            ...desde.keys(),
            ...S.objetivo.map((o) => o.elemento),
        ]);
        const inicio = performance.now();

        function paso(ahora) {
            const t = Math.min(1, (ahora - inicio) / C.duracion);
            const suavizado = 1 - Math.pow(1 - t, 3);
            const nuevos = new Map();

            claves.forEach((clave) => {
                const de = desde.get(clave) || 0;
                const obj = S.objetivo.find((o) => o.elemento === clave);
                const a = obj ? obj.pct : 0;
                const valor = de + (a - de) * suavizado;
                if (valor > 0.01) {
                    nuevos.set(clave, valor);
                }
            });

            S.valoresVisibles = nuevos;
            GT.render();

            if (t < 1) {
                S.animId = requestAnimationFrame(paso);
            } else {
                S.animId = null;
                const finales = new Map();
                S.objetivo.forEach((o) => {
                    if (o.pct > 0.01) {
                        finales.set(o.elemento, o.pct);
                    }
                });
                S.valoresVisibles = finales;
                GT.render();
            }
        }

        S.animId = requestAnimationFrame(paso);
    };
})();