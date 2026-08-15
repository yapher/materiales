(function () {
    "use strict";

    function escaparHtml(valor) {
        return String(valor)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function confirmar(mensaje, titulo) {
        if (typeof window.confirmarModerno === "function") {
            return window.confirmarModerno(mensaje, titulo);
        }

        return Promise.resolve(window.confirm(mensaje));
    }

    function initDatasetTabla(container) {
        const urlBase = container.getAttribute("data-url-base") || "";

        const cabeceraId = container.getAttribute("data-cabecera-id");
        const cuerpoId = container.getAttribute("data-cuerpo-id");

        const mensajeBoxId = container.getAttribute("data-mensaje-id");
        const mensajeTextoId = container.getAttribute("data-mensaje-texto-id");

        const totalId = container.getAttribute("data-total-id");

        const modalId = container.getAttribute("data-modal-id");
        const motivoId = container.getAttribute("data-motivo-id");

        const cabecera = document.getElementById(cabeceraId);
        const cuerpo = document.getElementById(cuerpoId);

        if (!urlBase || !cabecera || !cuerpo) {
            return;
        }

        let columnas = [];
        let filas = [];
        let editandoIndice = null;

        function setMensaje(texto, esError = false) {
            const box = document.getElementById(mensajeBoxId);
            const span = document.getElementById(mensajeTextoId);

            if (!box || !span) {
                return;
            }

            span.textContent = texto;

            box.style.borderColor = esError ? "#e07f7f" : "";
            box.style.color = esError ? "#e0a97f" : "";
            box.style.display = texto ? "block" : "none";
        }

        function actualizarTotal() {
            const totalEl = document.getElementById(totalId);

            if (!totalEl) {
                return;
            }

            totalEl.textContent = String(filas.length);
        }

        function mostrarMotivo(indice) {
            const fila = filas.find(f => f.indice === indice);

            if (!fila) {
                return;
            }

            const motivoEl = document.getElementById(motivoId);

            if (motivoEl) {
                motivoEl.textContent = fila.motivo || "Sin detalle.";
            }

            if (modalId && typeof bootstrap !== "undefined") {
                const modalEl = document.getElementById(modalId);

                if (modalEl) {
                    const modal = new bootstrap.Modal(modalEl);
                    modal.show();
                }
            }
        }

        function cargarTabla() {
            fetch(urlBase)
                .then(async respuesta => {
                    const data = await respuesta.json().catch(() => ({}));

                    if (!respuesta.ok || data.error) {
                        throw new Error(
                            data.error || `Error ${respuesta.status}`
                        );
                    }

                    return data;
                })
                .then(data => {
                    columnas = data.columnas || [];
                    filas = data.filas || [];
                    editandoIndice = null;

                    renderTabla();
                })
                .catch(error => {
                    setMensaje(error.message, true);
                });
        }

        function renderTabla() {
            actualizarTotal();

            cabecera.innerHTML = `
                <tr>
                    <th style="width:52px;">#</th>
                    <th title="Fila con datos inconsistentes"></th>
                    ${columnas.map(c => `<th>${escaparHtml(c)}</th>`).join("")}
                    <th>Acciones</th>
                </tr>
            `;

            if (!filas.length) {
                cuerpo.innerHTML = `
                    <tr>
                        <td colspan="${columnas.length + 3}" class="text-center text-muted py-4">
                            No hay filas para mostrar.
                        </td>
                    </tr>
                `;

                return;
            }

            cuerpo.innerHTML = filas.map((fila, indiceVisual) => {
                const numeroFila = indiceVisual + 1;
                const editando = editandoIndice === fila.indice;

                const advertencia = fila.inconsistente
                    ? `
                        <span
                            class="chip-advertencia"
                            data-accion="motivo"
                            data-indice="${fila.indice}"
                            title="Ver detalle"
                        >
                            <i class="bi bi-exclamation-triangle-fill"></i>
                        </span>
                    `
                    : "";

                const celdas = columnas.map(columna => {
                    const valor = fila.valores[columna];

                    if (editando) {
                        const valorInput =
                            valor === null || valor === undefined
                                ? ""
                                : escaparHtml(valor);

                        return `
                            <td>
                                <input
                                    type="number"
                                    step="any"
                                    class="form-control form-control-sm"
                                    style="min-width:90px;"
                                    data-col="${escaparHtml(columna)}"
                                    value="${valorInput}"
                                >
                            </td>
                        `;
                    }

                    const valorVisible =
                        valor === null || valor === undefined
                            ? '<span class="text-muted">—</span>'
                            : escaparHtml(valor);

                    return `<td>${valorVisible}</td>`;
                }).join("");

                const acciones = editando
                    ? `
                        <button
                            class="btn-fila-accion accion-guardar"
                            data-accion="guardar"
                            data-indice="${fila.indice}"
                            title="Guardar"
                        >
                            <i class="bi bi-check-lg"></i>
                        </button>

                        <button
                            class="btn-fila-accion accion-cancelar"
                            data-accion="cancelar"
                            data-indice="${fila.indice}"
                            title="Cancelar"
                        >
                            <i class="bi bi-x-lg"></i>
                        </button>
                    `
                    : `
                        <button
                            class="btn-fila-accion accion-editar"
                            data-accion="editar"
                            data-indice="${fila.indice}"
                            title="Editar"
                        >
                            <i class="bi bi-pencil"></i>
                        </button>

                        <button
                            class="btn-fila-accion accion-borrar"
                            data-accion="borrar"
                            data-indice="${fila.indice}"
                            title="Eliminar"
                        >
                            <i class="bi bi-trash"></i>
                        </button>

                        <a
                            class="btn-fila-accion accion-pdf"
                            href="${urlBase}/${fila.indice}/pdf"
                            title="Exportar a PDF"
                        >
                            <i class="bi bi-file-earmark-pdf"></i>
                        </a>
                    `;

                const claseFila = fila.inconsistente
                    ? "fila-inconsistente"
                    : "";

                return `
                    <tr class="${claseFila}" data-fila="${fila.indice}">
                        <td class="text-muted">${numeroFila}</td>
                        <td>${advertencia}</td>
                        ${celdas}
                        <td class="text-nowrap">
                            <div class="d-flex gap-1">
                                ${acciones}
                            </div>
                        </td>
                    </tr>
                `;
            }).join("");
        }

        function editarFila(indice) {
            editandoIndice = indice;
            renderTabla();

            const primerInput = container.querySelector(
                `tr[data-fila="${indice}"] input`
            );

            if (primerInput) {
                primerInput.focus();
            }
        }

        function cancelarEdicion() {
            editandoIndice = null;
            renderTabla();
        }

        function guardarFila(indice) {
            const filaTr = container.querySelector(
                `tr[data-fila="${indice}"]`
            );

            if (!filaTr) {
                return;
            }

            const inputs = filaTr.querySelectorAll("input[data-col]");

            const valores = {};

            inputs.forEach(input => {
                const columna = input.dataset.col;
                const crudo = input.value.trim();

                if (crudo === "") {
                    valores[columna] = null;
                    return;
                }

                const numero = Number(crudo);

                if (Number.isFinite(numero)) {
                    valores[columna] = numero;
                } else {
                    valores[columna] = crudo;
                }
            });

            setMensaje("Guardando cambios...");

            fetch(`${urlBase}/${indice}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(valores)
            })
                .then(async respuesta => {
                    const data = await respuesta.json().catch(() => ({}));

                    if (!respuesta.ok || data.error) {
                        throw new Error(
                            data.error || `Error ${respuesta.status}`
                        );
                    }

                    return data;
                })
                .then(data => {
                    setMensaje(data.mensaje || "Fila actualizada");
                    cargarTabla();
                })
                .catch(error => {
                    setMensaje(error.message, true);
                });
        }

        function borrarFila(indice) {
            confirmar(
                "¿Seguro que querés eliminar esta fila?",
                "Eliminar fila"
            ).then(ok => {
                if (!ok) {
                    return;
                }

                setMensaje("Eliminando fila...");

                fetch(`${urlBase}/${indice}`, {
                    method: "DELETE"
                })
                    .then(async respuesta => {
                        const data = await respuesta.json().catch(() => ({}));

                        if (!respuesta.ok || data.error) {
                            throw new Error(
                                data.error || `Error ${respuesta.status}`
                            );
                        }

                        return data;
                    })
                    .then(data => {
                        setMensaje(data.mensaje || "Fila eliminada");
                        cargarTabla();
                    })
                    .catch(error => {
                        setMensaje(error.message, true);
                    });
            });
        }

        container.addEventListener("click", function (evento) {
            const elemento = evento.target.closest("[data-accion]");

            if (!elemento || !container.contains(elemento)) {
                return;
            }

            const accion = elemento.getAttribute("data-accion");

            if (accion === "actualizar") {
                evento.preventDefault();
                cargarTabla();
                return;
            }

            const indice = parseInt(
                elemento.getAttribute("data-indice"),
                10
            );

            if (Number.isNaN(indice)) {
                return;
            }

            evento.preventDefault();

            if (accion === "motivo") {
                mostrarMotivo(indice);
            } else if (accion === "editar") {
                editarFila(indice);
            } else if (accion === "cancelar") {
                cancelarEdicion();
            } else if (accion === "guardar") {
                guardarFila(indice);
            } else if (accion === "borrar") {
                borrarFila(indice);
            }
        });

        cargarTabla();
    }

    function initAll() {
        document
            .querySelectorAll(".dataset-tabla-app")
            .forEach(initDatasetTabla);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initAll);
    } else {
        initAll();
    }
})();