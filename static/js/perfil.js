(function () {
"use strict";

// ==========================================================
// HELPERS
// ==========================================================
function setMensaje(texto, esError = false) {
    const box = document.getElementById("mensajePerfil");
    const span = document.getElementById("mensajePerfilTexto");
    if (!box || !span) return;
    span.textContent = texto;
    box.style.borderColor = esError ? "#e07f7f" : "";
    box.style.color = esError ? "#e0a97f" : "";
    box.style.display = texto ? "block" : "none";
}

function mostrarToast(titulo, mensaje, esError = false) {
    if (typeof window.mostrarToast === "function") {
        window.mostrarToast(titulo, mensaje, esError);
    }
}

function confirmar(mensaje, titulo) {
    if (typeof window.confirmarModerno === "function") {
        return window.confirmarModerno(mensaje, titulo);
    }
    return Promise.resolve(window.confirm(mensaje));
}

// ==========================================================
// ACTUALIZAR AVATAR EN TODA LA PÁGINA
// ==========================================================
function actualizarAvatarEnPagina() {
    const timestamp = Date.now();
    const urlAvatar = "/perfil/avatar?t=" + timestamp;

    // 1. Actualizar el preview del perfil
    const preview = document.getElementById("avatarPreview");
    if (preview) {
        if (preview.tagName === "IMG") {
            preview.src = urlAvatar;
        } else {
            // Era un placeholder div, reemplazar por img
            const img = document.createElement("img");
            img.id = "avatarPreview";
            img.src = urlAvatar;
            img.alt = "Foto de perfil";
            img.className = "avatar-preview";
            img.style.width = "140px";
            img.style.height = "140px";
            img.style.maxWidth = "140px";
            img.style.maxHeight = "140px";
            img.style.objectFit = "cover";
            img.style.borderRadius = "50%";
            preview.replaceWith(img);
        }
    }

    // 2. Actualizar el avatar del navbar (si existe)
    const navbarAvatar = document.querySelector(".avatar-navbar");
    if (navbarAvatar) {
        navbarAvatar.src = urlAvatar;
    }

    // 3. Habilitar botón eliminar
    const btnEliminar = document.getElementById("btnEliminarAvatar");
    if (btnEliminar) {
        btnEliminar.disabled = false;
    }
}

function mostrarPlaceholderAvatar() {
    const preview = document.getElementById("avatarPreview");
    if (!preview) return;
    const placeholder = document.createElement("div");
    placeholder.id = "avatarPreview";
    placeholder.className = "avatar-preview avatar-placeholder";
    placeholder.innerHTML = '<i class="bi bi-person-fill"></i>';
    preview.replaceWith(placeholder);

    // Actualizar navbar: reemplazar img por ícono
    const navbarAvatar = document.querySelector(".avatar-navbar");
    if (navbarAvatar) {
        const icono = document.createElement("i");
        icono.className = "bi bi-person-circle";
        navbarAvatar.replaceWith(icono);
    }
}

// ==========================================================
// DATOS PERSONALES
// ==========================================================
function initDatosPersonales() {
    const form = document.getElementById("formDatosPersonales");
    if (!form) return;

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const nombre = document.getElementById("inputNombre").value.trim();
        const email = document.getElementById("inputEmail").value.trim();

        setMensaje("Guardando datos...");

        try {
            const respuesta = await fetch("/perfil/actualizar_datos", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ nombre, email }),
            });
            const data = await respuesta.json().catch(() => ({}));
            if (!respuesta.ok || data.error) {
                throw new Error(data.error || "No se pudo guardar.");
            }
            setMensaje(data.mensaje || "Datos guardados.");
            mostrarToast("Perfil", data.mensaje || "Datos guardados.");
        } catch (error) {
            setMensaje(error.message, true);
            mostrarToast("Error", error.message, true);
        }
    });
}

// ==========================================================
// CAMBIAR CONTRASEÑA
// ==========================================================
function initCambiarPassword() {
    const form = document.getElementById("formCambiarPassword");
    if (!form) return;

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const passwordActual =
            document.getElementById("inputPasswordActual").value;
        const passwordNueva =
            document.getElementById("inputPasswordNueva").value;
        const passwordNueva2 =
            document.getElementById("inputPasswordNueva2").value;

        if (passwordNueva !== passwordNueva2) {
            setMensaje("Las contraseñas nuevas no coinciden.", true);
            return;
        }

        if (passwordNueva.length < 6) {
            setMensaje(
                "La nueva contraseña debe tener al menos 6 caracteres.",
                true
            );
            return;
        }

        setMensaje("Cambiando contraseña...");

        try {
            const respuesta = await fetch("/perfil/cambiar_password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    password_actual: passwordActual,
                    password_nueva: passwordNueva,
                    password_nueva2: passwordNueva2,
                }),
            });
            const data = await respuesta.json().catch(() => ({}));
            if (!respuesta.ok || data.error) {
                throw new Error(
                    data.error || "No se pudo cambiar la contraseña."
                );
            }
            setMensaje(data.mensaje || "Contraseña actualizada.");
            mostrarToast(
                "Contraseña",
                data.mensaje || "Contraseña actualizada."
            );
            form.reset();
        } catch (error) {
            setMensaje(error.message, true);
            mostrarToast("Error", error.message, true);
        }
    });
}

// ==========================================================
// AVATAR
// ==========================================================
function initAvatar() {
    const inputAvatar = document.getElementById("inputAvatar");
    const btnSubir = document.getElementById("btnSubirAvatar");
    const btnEliminar = document.getElementById("btnEliminarAvatar");

    if (!inputAvatar || !btnSubir) return;

    btnSubir.addEventListener("click", function () {
        inputAvatar.click();
    });

    inputAvatar.addEventListener("change", async function () {
        const file = inputAvatar.files[0];
        if (!file) return;

        // Validar tipo
        const extensionesPermitidas = [".png", ".jpg", ".jpeg", ".webp"];
        const extension = file.name
            .substring(file.name.lastIndexOf("."))
            .toLowerCase();
        if (!extensionesPermitidas.includes(extension)) {
            setMensaje("Solo se permiten imágenes PNG, JPG o WEBP.", true);
            inputAvatar.value = "";
            return;
        }

        // Validar tamaño (2 MB)
        if (file.size > 2 * 1024 * 1024) {
            setMensaje("La imagen no puede superar los 2 MB.", true);
            inputAvatar.value = "";
            return;
        }

        setMensaje("Subiendo foto de perfil...");

        const formData = new FormData();
        formData.append("avatar", file);

        try {
            const respuesta = await fetch("/perfil/avatar", {
                method: "POST",
                body: formData,
            });
            const data = await respuesta.json().catch(() => ({}));
            if (!respuesta.ok || data.error) {
                throw new Error(
                    data.error || "No se pudo subir la imagen."
                );
            }

            setMensaje(data.mensaje || "Foto actualizada.");
            mostrarToast("Perfil", data.mensaje || "Foto actualizada.");

            // Actualizar el avatar en toda la página
            // (preview + navbar) con la URL del servidor
            actualizarAvatarEnPagina();

        } catch (error) {
            setMensaje(error.message, true);
            mostrarToast("Error", error.message, true);
        } finally {
            inputAvatar.value = "";
        }
    });

    if (btnEliminar) {
        btnEliminar.addEventListener("click", async function () {
            const confirmado = await confirmar(
                "¿Seguro que querés eliminar tu foto de perfil?",
                "Eliminar foto"
            );
            if (!confirmado) return;

            setMensaje("Eliminando foto de perfil...");

            try {
                const respuesta = await fetch("/perfil/avatar", {
                    method: "DELETE",
                });
                const data = await respuesta.json().catch(() => ({}));
                if (!respuesta.ok || data.error) {
                    throw new Error(
                        data.error || "No se pudo eliminar."
                    );
                }

                setMensaje(data.mensaje || "Foto eliminada.");
                mostrarToast("Perfil", data.mensaje || "Foto eliminada.");

                // Reemplazar preview por placeholder
                mostrarPlaceholderAvatar();

                btnEliminar.disabled = true;
            } catch (error) {
                setMensaje(error.message, true);
                mostrarToast("Error", error.message, true);
            }
        });
    }
}

// ==========================================================
// INICIALIZACIÓN
// ==========================================================
function init() {
    initDatosPersonales();
    initCambiarPassword();
    initAvatar();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
})();