(function () {
    "use strict";

    const IAM = window.IAM;

    if (!IAM) {
        return;
    }

    /*
    Tablas de resultados:
    - R² del modelo
    - predicción
    - ordenamiento
    */

    IAM.renderTablaR2 = function () {
        const tbody = document.getElementById("tablaR2");
        const vacio = document.getElementById("r2Vacio");

        if (!tbody) {
            return;
        }

        if (IAM.state.datosR2.length === 0) {
            tbody.innerHTML = "";

            if (vacio) {
                vacio.style.display = "block";
            }

            IAM.notificarWorkflow();

            return;
        }

        if (vacio) {
            vacio.style.display = "none";
        }

        tbody.innerHTML = IAM.state.datosR2.map(row => {
            const clase = IAM.claseR2(row.r2);
            const pct = Math.max(0, Math.min(100, (Number(row.r2) || 0) * 100));

            const filasNumero = Number(row.filas_entrenadas);
            const filasTexto = Number.isFinite(filasNumero)
                ? filasNumero
                : "—";

            const excluidasTargetNumero = Number(row.filas_excluidas_target_invalido);
            const excluidasOutliersNumero = Number(row.filas_excluidas_outliers);

            let tituloFilas = "Filas reales del dataset usadas para entrenar esta variable.";

            if (Number.isFinite(filasNumero)) {
                tituloFilas = `Se usaron ${filasNumero} filas reales del dataset.`;

                if (
                    Number.isFinite(excluidasTargetNumero) &&
                    excluidasTargetNumero > 0
                ) {
                    tituloFilas += ` Se excluyeron ${excluidasTargetNumero} filas por valor objetivo <= 0.`;
                }

                if (
                    Number.isFinite(excluidasOutliersNumero) &&
                    excluidasOutliersNumero > 0
                ) {
                    tituloFilas += ` Se excluyeron ${excluidasOutliersNumero} filas como outliers.`;
                }
            }

            const r2Texto = (row.r2 === null || row.r2 === undefined)
                ? "—"
                : row.r2;

            return `
                <tr>
                    <td><span class="var-nombre">${IAM.escaparHtml(row.columna)}</span></td>
                    <td>
                        <div class="r2-celda">
                            <div class="r2-barra-bg">
                                <div class="r2-barra-fill r2-${clase}" style="width:${pct}%"></div>
                            </div>
                            <span class="r2-valor r2-txt-${clase}">${IAM.escaparHtml(r2Texto)}</span>
                        </div>
                    </td>
                    <td class="text-nowrap" title="${IAM.escaparHtml(tituloFilas)}">
                        <span class="r2-valor">${IAM.escaparHtml(filasTexto)}</span>
                    </td>
                </tr>
            `;
        }).join("");

        IAM.notificarWorkflow();
    };

    IAM.renderTablaPrediccion = function () {
        const tbody = document.getElementById("tablaPrediccion");
        const vacio = document.getElementById("prediccionVacia");
        const acciones = document.getElementById("accionesPrediccion");

        if (!tbody) {
            return;
        }

        if (IAM.state.datosPrediccion.length === 0) {
            tbody.innerHTML = "";

            if (vacio) {
                vacio.style.display = "block";
            }

            if (acciones) {
                acciones.style.display = "none";
            }

            IAM.notificarWorkflow();

            return;
        }

        if (vacio) {
            vacio.style.display = "none";
        }

        if (acciones) {
            acciones.style.display = "flex";
        }

        tbody.innerHTML = IAM.state.datosPrediccion.map(row => `
            <tr>
                <td><span class="var-nombre">${IAM.escaparHtml(row.columna)}</span></td>
                <td><span class="pred-valor">${IAM.escaparHtml(row.prediccion)}</span></td>
            </tr>
        `).join("");

        IAM.notificarWorkflow();
    };

    IAM.ordenarTabla = function (tabla, campo) {
        const key = `${tabla}_${campo}`;
        const direccion = IAM.state.ordenEstado[key] === "asc"
            ? "desc"
            : "asc";

        IAM.state.ordenEstado[key] = direccion;

        const datos = tabla === "r2"
            ? IAM.state.datosR2
            : IAM.state.datosPrediccion;

        datos.sort((a, b) => {
            let valA = IAM.normalizarValorOrden(a[campo]);
            let valB = IAM.normalizarValorOrden(b[campo]);

            if (valA === null && valB === null) {
                return 0;
            }

            if (valA === null) {
                return 1;
            }

            if (valB === null) {
                return -1;
            }

            if (typeof valA === "string" || typeof valB === "string") {
                const strA = String(valA);
                const strB = String(valB);

                return direccion === "asc"
                    ? strA.localeCompare(strB)
                    : strB.localeCompare(strA);
            }

            return direccion === "asc"
                ? valA - valB
                : valB - valA;
        });

        if (tabla === "r2") {
            IAM.renderTablaR2();
        } else {
            IAM.renderTablaPrediccion();
        }
    };
})();