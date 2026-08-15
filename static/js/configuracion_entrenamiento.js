(function () {
    const STORAGE_KEY = "configuracion_variables_entrenamiento_v2";
    const OLD_STORAGE_KEY = "configuracion_variables_entrenamiento";

    let seleccion = new Set();

    function modalElement() {
        return document.getElementById("modalConfiguracionEntrenamiento");
    }

    function botonesVariables() {
        return document.querySelectorAll(
            "#modalConfiguracionEntrenamiento .variable-toggle"
        );
    }

    function variablesDisponibles() {
        return Array.from(botonesVariables())
            .map(boton => boton.dataset.variable)
            .filter(Boolean);
    }

    function contadorElement() {
        return document.getElementById("configContador");
    }

    function advertenciaElement() {
        return document.getElementById("configAdvertencia");
    }

    function defaultVariable() {
        const modal = modalElement();

        if (!modal) {
            const disponibles = variablesDisponibles();
            return disponibles.length ? disponibles[0] : "";
        }

        const desdeModal = modal.dataset.variableDefault || "";

        if (desdeModal && variablesDisponibles().includes(desdeModal)) {
            return desdeModal;
        }

        const disponibles = variablesDisponibles();
        return disponibles.length ? disponibles[0] : "";
    }

    function guardarSeleccion() {
        try {
            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(Array.from(seleccion))
            );
        } catch (error) {
            console.warn("No se pudo guardar la configuración en localStorage", error);
        }
    }

    function leerSeleccionGuardada() {
        try {
            let guardado = localStorage.getItem(STORAGE_KEY);

            if (guardado === null) {
                guardado = localStorage.getItem(OLD_STORAGE_KEY);
            }

            if (guardado === null) {
                return [];
            }

            const lista = JSON.parse(guardado);

            if (!Array.isArray(lista)) {
                return [];
            }

            return lista;
        } catch (error) {
            console.warn("No se pudo leer la configuración guardada", error);
            return [];
        }
    }

    function cargarSeleccion() {
        const disponibles = variablesDisponibles();
        const guardado = leerSeleccionGuardada();

        const validas = guardado.filter(variable =>
            disponibles.includes(variable)
        );

        if (validas.length > 0) {
            seleccion = new Set(validas);
        } else {
            const def = defaultVariable();
            seleccion = def ? new Set([def]) : new Set();
        }

        guardarSeleccion();
    }

    function setAdvertencia(visible) {
        const alerta = advertenciaElement();

        if (!alerta) {
            return;
        }

        alerta.style.display = visible ? "block" : "none";
    }

    function actualizarContador() {
        const contador = contadorElement();

        if (!contador) {
            return;
        }

        const cantidad = seleccion.size;

        if (cantidad === 1) {
            contador.textContent = "1 variable seleccionada";
        } else {
            contador.textContent = `${cantidad} variables seleccionadas`;
        }
    }

    function actualizarBotones() {
        botonesVariables().forEach(boton => {
            const variable = boton.dataset.variable;
            const activo = seleccion.has(variable);

            boton.classList.toggle("activo", activo);
            boton.setAttribute("aria-pressed", activo ? "true" : "false");
        });
    }

    function actualizarUI() {
        actualizarBotones();
        actualizarContador();

        if (seleccion.size > 0) {
            setAdvertencia(false);
        }
    }

    function toggleVariable(variable) {
        if (!variable) {
            return;
        }

        if (seleccion.has(variable)) {
            seleccion.delete(variable);
        } else {
            seleccion.add(variable);
        }

        guardarSeleccion();
        actualizarUI();
    }

    function seleccionarDefault() {
        const def = defaultVariable();

        if (!def) {
            seleccion.clear();
        } else {
            seleccion = new Set([def]);
        }

        guardarSeleccion();
        actualizarUI();
    }

    function limpiarSeleccion() {
        seleccion.clear();
        guardarSeleccion();
        actualizarUI();
    }

    function obtenerVariablesSeleccionadas() {
        return Array.from(seleccion);
    }

    function validarSeleccion() {
        if (seleccion.size > 0) {
            setAdvertencia(false);
            return true;
        }

        setAdvertencia(true);

        if (window.mostrarToast) {
            window.mostrarToast(
                "Atención",
                "Seleccioná al menos una variable para modelar.",
                true
            );
        }

        if (window.setMensaje) {
            window.setMensaje("Seleccioná al menos una variable para modelar.");
        }

        const modal = modalElement();

        if (modal && typeof bootstrap !== "undefined") {
            const instancia = bootstrap.Modal.getOrCreateInstance(modal);
            instancia.show();
        }

        return false;
    }

    function bindBotones() {
        botonesVariables().forEach(boton => {
            boton.addEventListener("click", () => {
                toggleVariable(boton.dataset.variable);
            });
        });

        const btnDefault = document.getElementById("btnConfigurarDensidad");

        if (btnDefault) {
            btnDefault.addEventListener("click", seleccionarDefault);
        }

        const btnLimpiar = document.getElementById("btnLimpiarVariables");

        if (btnLimpiar) {
            btnLimpiar.addEventListener("click", limpiarSeleccion);
        }
    }

    window.entrenarModelo = async function () {
        if (!validarSeleccion()) {
            return;
        }

        const variables = obtenerVariablesSeleccionadas();

        if (window.FlujoModelo) {
            window.FlujoModelo.setEntrenamientoCorriendo(true);
        }

        if (window.setOcupado) {
            window.setOcupado(true);
        }

        if (window.setMensaje) {
            window.setMensaje("Iniciando modelado...");
        }

        try {
            const respuesta = await fetch("/mezclas/entrenar", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ variables })
            });

            const data = await respuesta.json().catch(() => ({}));

            if (respuesta.status === 409) {
                if (window.setMensaje) {
                    window.setMensaje("Ya hay un entrenamiento en curso.");
                }

                if (window.iniciarPollEntrenamiento) {
                    window.iniciarPollEntrenamiento();
                }

                return;
            }

            if (!respuesta.ok || data.error) {
                throw new Error(data.error || "No se pudo iniciar el modelado");
            }

            if (window.iniciarPollEntrenamiento) {
                window.iniciarPollEntrenamiento();
            }

        } catch (error) {
            if (window.FlujoModelo) {
                window.FlujoModelo.setEntrenamientoCorriendo(false);
            }

            if (window.setMensaje) {
                window.setMensaje(error.message);
            }

            if (window.mostrarToast) {
                window.mostrarToast(
                    "Error de modelado",
                    error.message,
                    true
                );
            }

            if (window.setOcupado) {
                window.setOcupado(false);
            }
        }
    };

    window.ConfigEntrenamiento = {
        obtenerVariablesSeleccionadas,
        validarSeleccion,
        seleccionarDefault,
        limpiarSeleccion
    };

    function init() {
        if (!modalElement()) {
            return;
        }

        cargarSeleccion();
        bindBotones();
        actualizarUI();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();