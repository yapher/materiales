(function () {
    "use strict";

    function obtenerUrls() {
        const root = document.getElementById("adminApp");
        if (!root) {
            return {};
        }
        return {
            estado: root.getAttribute("data-estado-url"),
            recargar: root.getAttribute("data-recargar-url"),
            reset: root.getAttribute("data-reset-url"),
            subirDataset: root.getAttribute("data-subir-dataset-url"),
        };
    }

    function setMensajeAdmin(texto, esError = false) {
        const box = document.getElementById("mensajeAdmin");
        const span = document.getElementById("mensajeAdminTexto");
        if (!box || !span) {
            return;
        }
        span.textContent = texto;
        box.style.borderColor = esError ? "#e07f7f" : "";
        box.style.color = esError ? "#e0a97f" : "";
        box.style.display = texto ? "block" : "none";
    }

    function setBotonesBloqueados(bloqueado) {
        const ids = [
            "btnSubirDataset",
            "btnRecargarDataset",
            "btnResetModelo",
            "inputDatasetExcel",
        ];
        ids.forEach((id) => {
            const elemento = document.getElementById(id);
            if (elemento) {
                elemento.disabled = bloqueado;
            }
        });
    }

    function claseR2Admin(valor) {
        if (valor >= 0.8) return "bueno";
        if (valor >= 0.5) return "medio";
        return "malo";
    }

    function renderTablaR2Admin(modeloInfo) {
        const tbody = document.getElementById("tablaR2Admin");
        const vacio = document.getElementById("r2AdminVacio");
        const filas =
            modeloInfo && modeloInfo.entrenado
                ? modeloInfo.tabla_r2
                : [];
        if (!filas || filas.length === 0) {
            if (tbody) tbody.innerHTML = "";
            if (vacio) vacio.style.display = "block";
            return;
        }
        if (vacio) vacio.style.display = "none";
        tbody.innerHTML = filas
            .map((row) => {
                const clase = claseR2Admin(row.r2);
                return `
                    <tr>
                        <td><span class="var-nombre">${row.columna}</span></td>
                        <td><span class="r2-valor r2-txt-${clase}">${row.r2}</span></td>
                    </tr>
                `;
            })
            .join("");
    }

    function confirmar(mensaje, titulo) {
        if (typeof window.confirmarModerno === "function") {
            return window.confirmarModerno(mensaje, titulo);
        }
        return Promise.resolve(window.confirm(mensaje));
    }

    async function cargarEstado() {
        const urls = obtenerUrls();
        if (!urls.estado) {
            return;
        }
        try {
            const respuesta = await fetch(urls.estado);
            const data = await respuesta.json().catch(() => ({}));
            if (!respuesta.ok || data.error) {
                throw new Error(
                    data.error || "No se pudo cargar el estado."
                );
            }
            const estadoBox = document.getElementById("estadoBox");
            if (estadoBox) {
                estadoBox.innerHTML = `
                    <p class="mb-1"><strong>Tu sesión:</strong> <code>${data.usuario}</code></p>
                    <p class="mb-1"><strong>Dataset cargado:</strong> ${
                        data.dataset_cargado
                            ? "Sí (" + data.filas_dataset + " filas)"
                            : "No"
                    }</p>
                    <p class="mb-1"><strong>Modelo entrenado en memoria:</strong> ${
                        data.modelo_en_memoria ? "Sí" : "No"
                    }</p>
                    <p class="mb-0"><strong>Modelo persistido en disco:</strong> ${
                        data.modelo_persistido ? "Sí" : "No"
                    }</p>
                    ${
                        data.modelo_info && data.modelo_info.entrenado
                            ? `<p class="mb-0 mt-2 text-muted">
                                Último entrenamiento:
                                ${data.modelo_info.fecha}
                                (${data.modelo_info.tiempo_segundos}s)
                               </p>`
                            : ""
                    }
                `;
            }
            renderTablaR2Admin(data.modelo_info);
        } catch (error) {
            setMensajeAdmin(error.message, true);
        }
    }

    async function recargarDataset() {
        const urls = obtenerUrls();
        if (!urls.recargar) {
            return;
        }
        setBotonesBloqueados(true);
        setMensajeAdmin("Recargando dataset...");
        try {
            const respuesta = await fetch(urls.recargar, {
                method: "POST",
            });
            const data = await respuesta.json().catch(() => ({}));
            if (!respuesta.ok || data.error) {
                throw new Error(
                    data.error || "No se pudo recargar el dataset."
                );
            }
            if (typeof window.mostrarToast === "function") {
                window.mostrarToast(
                    "Dataset recargado",
                    data.mensaje || "Dataset recargado correctamente."
                );
            }
            setMensajeAdmin(
                data.mensaje || "Dataset recargado correctamente."
            );
            await cargarEstado();
        } catch (error) {
            setMensajeAdmin(error.message, true);
            if (typeof window.mostrarToast === "function") {
                window.mostrarToast(
                    "Error",
                    error.message,
                    true
                );
            }
        } finally {
            setBotonesBloqueados(false);
        }
    }

    async function resetModelo() {
        const urls = obtenerUrls();
        if (!urls.reset) {
            return;
        }
        const ok = await confirmar(
            "¿Seguro que querés borrar tu modelo? Vas a tener que reentrenar.",
            "Borrar modelo"
        );
        if (!ok) {
            return;
        }
        setBotonesBloqueados(true);
        setMensajeAdmin("Borrando modelo...");
        try {
            const respuesta = await fetch(urls.reset, {
                method: "POST",
            });
            const data = await respuesta.json().catch(() => ({}));
            if (!respuesta.ok || data.error) {
                throw new Error(
                    data.error || "No se pudo borrar el modelo."
                );
            }
            if (typeof window.mostrarToast === "function") {
                window.mostrarToast(
                    "Modelo borrado",
                    data.mensaje || "El modelo fue borrado."
                );
            }
            setMensajeAdmin(
                data.mensaje || "El modelo fue borrado."
            );
            await cargarEstado();
        } catch (error) {
            setMensajeAdmin(error.message, true);
            if (typeof window.mostrarToast === "function") {
                window.mostrarToast(
                    "Error",
                    error.message,
                    true
                );
            }
        } finally {
            setBotonesBloqueados(false);
        }
    }

    async function subirDataset(file) {
        const urls = obtenerUrls();
        if (!urls.subirDataset) {
            return;
        }
        const formData = new FormData();
        formData.append("archivo", file);
        setBotonesBloqueados(true);
        setMensajeAdmin(
            "Subiendo nuevo dataset y propagando a todos los usuarios..."
        );
        try {
            const respuesta = await fetch(urls.subirDataset, {
                method: "POST",
                body: formData,
            });
            const data = await respuesta.json().catch(() => ({}));
            if (!respuesta.ok || data.error) {
                throw new Error(
                    data.error || "No se pudo subir el dataset."
                );
            }
            if (typeof window.mostrarToast === "function") {
                const u = data.usuarios_actualizados || 0;
                const m = data.modelos_borrados || 0;
                window.mostrarToast(
                    "Nuevo dataset cargado",
                    `Dataset actualizado para ${u} usuario(s). ` +
                    `${m} modelo(s) borrado(s). ` +
                    "Todos deberán reentrenar."
                );
            }
            setMensajeAdmin(
                data.mensaje || "Dataset cargado correctamente."
            );
            await cargarEstado();
        } catch (error) {
            setMensajeAdmin(error.message, true);
            if (typeof window.mostrarToast === "function") {
                window.mostrarToast(
                    "Error al subir dataset",
                    error.message,
                    true
                );
            }
        } finally {
            setBotonesBloqueados(false);
        }
    }

    function inicializar() {
        const btnSubirDataset = document.getElementById("btnSubirDataset");
        const inputDatasetExcel = document.getElementById("inputDatasetExcel");
        const btnRecargarDataset = document.getElementById("btnRecargarDataset");
        const btnResetModelo = document.getElementById("btnResetModelo");

        if (btnSubirDataset && inputDatasetExcel) {
            btnSubirDataset.addEventListener("click", () => {
                inputDatasetExcel.click();
            });
        }

        if (inputDatasetExcel) {
            inputDatasetExcel.addEventListener("change", async (event) => {
                const file = event.target.files[0];
                if (!file) {
                    return;
                }
                const nombre = file.name.toLowerCase();
                if (
                    !nombre.endsWith(".xlsx") &&
                    !nombre.endsWith(".xlsm")
                ) {
                    setMensajeAdmin(
                        "Solo se permiten archivos Excel .xlsx o .xlsm.",
                        true
                    );
                    event.target.value = "";
                    return;
                }
                const ok = await confirmar(
                    "Se reemplazará el dataset maestro por el archivo seleccionado.\n\n" +
                    "⚠ IMPORTANTE:\n" +
                    "• Se actualizará el dataset personal de TODOS los usuarios.\n" +
                    "• Se borrarán los modelos entrenados de TODOS los usuarios.\n" +
                    "• Todos deberán reentrenar su modelo la próxima vez.\n\n" +
                    "¿Continuar?",
                    "Subir nuevo dataset"
                );
                if (!ok) {
                    event.target.value = "";
                    return;
                }
                await subirDataset(file);
                event.target.value = "";
            });
        }

        if (btnRecargarDataset) {
            btnRecargarDataset.addEventListener("click", recargarDataset);
        }

        if (btnResetModelo) {
            btnResetModelo.addEventListener("click", resetModelo);
        }

        cargarEstado();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", inicializar);
    } else {
        inicializar();
    }
})();