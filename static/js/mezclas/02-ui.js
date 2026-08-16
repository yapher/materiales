(function () {
    "use strict";

    const IAM = window.IAM;

    if (!IAM) {
        return;
    }

    /*
    UI transversal:
    - mensajes
    - toasts
    - modal de confirmación
    - notificación al workflow
    */

    IAM.setMensaje = function (texto) {
        const box = document.getElementById("mensajeBox");

        if (!box) {
            return;
        }

        document.getElementById("mensaje").textContent = texto;
        box.style.display = texto ? "block" : "none";
    };

    IAM.mostrarToast = function (titulo, mensaje, esError = false) {
        const contenedor = document.getElementById("toastContainer");

        if (!contenedor) {
            return;
        }

        const icono = esError
            ? "bi-exclamation-triangle-fill"
            : "bi-check-circle-fill";

        const clase = esError
            ? "toast-error"
            : "toast-exito";

        const div = document.createElement("div");
        div.className = `toast ${clase}`;
        div.setAttribute("role", "alert");

        div.innerHTML = `
            <div class="toast-header">
                <i class="bi ${icono} me-2"></i>
                <strong class="me-auto">${titulo}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${mensaje}</div>
        `;

        contenedor.appendChild(div);

        if (typeof bootstrap !== "undefined") {
            const toast = new bootstrap.Toast(div, { delay: 6000 });
            toast.show();

            div.addEventListener("hidden.bs.toast", () => div.remove());
        }
    };

    IAM.confirmarModerno = function (mensaje, titulo = "Confirmar") {
        return new Promise(resolve => {
            const modalEl = document.getElementById("modalConfirmar");

            if (!modalEl || typeof bootstrap === "undefined") {
                resolve(window.confirm(mensaje));
                return;
            }

            document.getElementById("confirmarMensaje").textContent = mensaje;
            document.getElementById("confirmarTitulo").textContent = titulo;

            const modal = new bootstrap.Modal(modalEl);
            const btnOk = document.getElementById("confirmarBotonOk");

            let resuelto = false;

            const limpiar = () => {
                btnOk.removeEventListener("click", onOk);
                modalEl.removeEventListener("hidden.bs.modal", onCancel);
            };

            const onOk = () => {
                resuelto = true;
                limpiar();
                modal.hide();
                resolve(true);
            };

            const onCancel = () => {
                limpiar();

                if (!resuelto) {
                    resolve(false);
                }
            };

            btnOk.addEventListener("click", onOk);
            modalEl.addEventListener("hidden.bs.modal", onCancel, { once: true });

            modal.show();
        });
    };

    IAM.notificarWorkflow = function () {
        if (window.FlujoModelo && typeof window.FlujoModelo.actualizar === "function") {
            window.FlujoModelo.actualizar();
        }

        document.dispatchEvent(new CustomEvent("mezclas:estado-actualizado"));
    };
})();