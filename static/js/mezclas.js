let mix = [];
let modeloListo = false;
let ultimaMezcla = null;  // { mix, temperatura } de la ultima prediccion exitosa

// Paleta inspirada en familias de la tabla periódica, una por elemento
const COLORES_ELEMENTO = {
    CaO:   "#8fd694",
    SiO2:  "#7fb8e0",
    Al2O3: "#e0a97f",
    MgO:   "#a3e0a0",
    Na2O:  "#f2d879",
    K2O:   "#f2c879",
    Li2O:  "#f2e79c",
    CaF2:  "#c9a3f2",
    Fe2O3: "#e08a7f",
    MnO:   "#d99fd0",
    TiO2:  "#9fd0d9",
};

// ============================
// Utilidades de UI compartidas: modal de confirmacion y toasts
// ============================

function confirmarModerno(mensaje, titulo = 'Confirmar') {
    return new Promise(resolve => {
        const modalEl = document.getElementById('modalConfirmar');
        if (!modalEl || typeof bootstrap === 'undefined') {
            resolve(window.confirm(mensaje));
            return;
        }

        document.getElementById('confirmarMensaje').textContent = mensaje;
        document.getElementById('confirmarTitulo').textContent = titulo;

        const modal = new bootstrap.Modal(modalEl);
        const btnOk = document.getElementById('confirmarBotonOk');
        let resuelto = false;

        const limpiar = () => {
            btnOk.removeEventListener('click', onOk);
            modalEl.removeEventListener('hidden.bs.modal', onCancel);
        };
        const onOk = () => {
            resuelto = true;
            limpiar();
            modal.hide();
            resolve(true);
        };
        const onCancel = () => {
            limpiar();
            if (!resuelto) resolve(false);
        };

        btnOk.addEventListener('click', onOk);
        modalEl.addEventListener('hidden.bs.modal', onCancel, { once: true });
        modal.show();
    });
}

function mostrarToast(titulo, mensaje, esError = false) {
    const contenedor = document.getElementById('toastContainer');
    if (!contenedor) return;

    const icono = esError ? 'bi-exclamation-triangle-fill' : 'bi-check-circle-fill';
    const clase = esError ? 'toast-error' : 'toast-exito';

    const div = document.createElement('div');
    div.className = `toast ${clase}`;
    div.setAttribute('role', 'alert');
    div.innerHTML = `
        <div class="toast-header">
            <i class="bi ${icono} me-2"></i>
            <strong class="me-auto">${titulo}</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">${mensaje}</div>`;

    contenedor.appendChild(div);

    if (typeof bootstrap !== 'undefined') {
        const toast = new bootstrap.Toast(div, { delay: 6000 });
        toast.show();
        div.addEventListener('hidden.bs.toast', () => div.remove());
    }
}

// ============================
// Composicion de la mezcla
// ============================

function actualizarMix() {
    const cont = document.getElementById('mixContainer');
    if (!cont) return;
    cont.innerHTML = '';
    mix.forEach(e => {
        const color = COLORES_ELEMENTO[e.elemento] || '#88c999';
        const div = document.createElement('div');
        div.className = 'mix-tag';
        div.innerHTML = `
            <div class="elemento-chip" style="background:${color}">${e.elemento}</div>
            <span class="mix-tag-pct">${e.pct}%</span>
            <button onclick="eliminarElemento('${e.elemento}')">✕</button>`;
        cont.appendChild(div);
    });

    const total = mix.reduce((acc, e) => acc + e.pct, 0);
    const totalEl = document.getElementById('porcentajeTotal');
    if (totalEl) totalEl.textContent = total;
    const barEl = document.getElementById('mixBar');
    if (barEl) barEl.style.width = `${Math.min(total, 100)}%`;
}

function setMensaje(texto) {
    const box = document.getElementById('mensajeBox');
    if (!box) return;
    document.getElementById('mensaje').textContent = texto;
    box.style.display = texto ? 'block' : 'none';
}

function actualizarVisibilidadPredecir() {
    // El boton Predecir solo se muestra si ya hay un modelo entrenado.
    const btnPredecir = document.getElementById('btnPredecir');
    if (!btnPredecir) return;
    btnPredecir.style.display = modeloListo ? 'inline-block' : 'none';
}

function setOcupado(ocupado) {
    const total = mix.reduce((a, e) => a + e.pct, 0);

    const btnEntrenar = document.getElementById('btnEntrenar');
    if (btnEntrenar) btnEntrenar.disabled = ocupado;

    const btnPredecir = document.getElementById('btnPredecir');
    if (btnPredecir) btnPredecir.disabled = ocupado || !modeloListo || total !== 100;

    actualizarVisibilidadPredecir();
}

function agregarElemento() {
    const elemento = document.getElementById('elementoSel').value;
    const pct = parseFloat(document.getElementById('porcentajeSel').value);

    if (!elemento) return setMensaje('Selecciona un elemento');
    if (isNaN(pct)) return setMensaje('Porcentaje inválido');
    if (mix.some(e => e.elemento === elemento)) return setMensaje('Elemento ya agregado');

    const total = mix.reduce((a, e) => a + e.pct, 0);
    if (total + pct > 100) return setMensaje('No puede superar 100%');

    mix.push({ elemento, pct });
    document.getElementById('elementoSel').value = '';
    document.getElementById('porcentajeSel').value = '';
    actualizarMix();
    setOcupado(false);

    datosPrediccion = [];
    renderTablaPrediccion();

    setMensaje(`Total: ${mix.reduce((a, e) => a + e.pct, 0)}%`);
}

function eliminarElemento(elemento) {
    mix = mix.filter(e => e.elemento !== elemento);

    datosPrediccion = [];
    renderTablaPrediccion();

    actualizarMix();
    setOcupado(false);
    setMensaje('Mezcla modificada. Ajustá el 100% y volvé a predecir.');
}

function cargarDataset() {
    setOcupado(true);
    setMensaje("Verificando dataset...");

    fetch("/mezclas/cargar_dataset", { method: "POST" })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            setMensaje(`Dataset listo (${data.filas} filas)`);
        })
        .catch(err => setMensaje(err.message))
        .finally(() => setOcupado(false));
}

// ============================
// Entrenamiento: se dispara con un POST y el progreso se sigue por
// POLLING (GET /mezclas/entrenar/estado), no por streaming. Por eso
// sigue funcionando aunque el usuario cambie de pagina: el poll corre
// en TODAS las paginas (ver el bloque de inicializacion, al final del
// archivo), no solo en la de Predicción.
// ============================

let pollEntrenamiento = null;

function entrenar() {
    setOcupado(true);
    setMensaje('Iniciando entrenamiento...');

    fetch('/mezclas/entrenar', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            iniciarPollEntrenamiento();
        })
        .catch(err => {
            setMensaje(err.message);
            setOcupado(false);
        });
}

function iniciarPollEntrenamiento() {
    if (pollEntrenamiento) return;
    consultarEstadoEntrenamiento();
    pollEntrenamiento = setInterval(consultarEstadoEntrenamiento, 1200);
}

function actualizarBarraProgreso(actual, total) {
    const barra = document.getElementById('barraProgreso');
    if (!barra) return;
    const pct = total > 0 ? Math.round((actual / total) * 100) : 0;
    barra.style.width = `${pct}%`;
    barra.textContent = `${pct}%`;
}

function consultarEstadoEntrenamiento() {
    fetch('/mezclas/entrenar/estado')
        .then(r => r.ok ? r.json() : null)
        .then(data => {
            if (!data) return;

            const badge = document.getElementById('badgeEntrenando');
            const progresoDiv = document.getElementById('progresoEntrenamiento');

            if (data.corriendo) {
                if (badge) badge.style.display = 'inline-flex';
                if (progresoDiv) progresoDiv.style.display = 'block';

                if (data.total) {
                    actualizarBarraProgreso(data.progreso, data.total);
                    setMensaje(`Entrenando ${data.progreso} / ${data.total} variables... (${data.columna || '...'}) — ${data.tiempo}s`);
                } else {
                    setMensaje('Entrenando...');
                }
                return;
            }

            // Ya no esta corriendo: se detiene el polling.
            if (badge) badge.style.display = 'none';
            if (pollEntrenamiento) {
                clearInterval(pollEntrenamiento);
                pollEntrenamiento = null;
            }
            setOcupado(false);

            if (data.error) {
                mostrarToast('Error de entrenamiento', data.error, true);
                setMensaje(data.error);
                return;
            }

            if (data.listo) {
                const yaVisto = localStorage.getItem('entrenamiento_visto') === data.fecha;

                modeloListo = true;
                actualizarVisibilidadPredecir();
                setOcupado(false);

                if (Array.isArray(data.tabla_r2)) {
                    datosR2 = data.tabla_r2;
                    renderTablaR2();
                }

                if (!yaVisto) {
                    mostrarToast('Modelo entrenado', `Entrenamiento completado en ${data.tiempo}s.`);
                    localStorage.setItem('entrenamiento_visto', data.fecha);
                }

                setMensaje(`Modelo entrenado en ${data.tiempo}s`);
            }
        })
        .catch(() => {});
}

// ============================
// Prediccion
// ============================

function predecir() {
    const temperatura = document.getElementById('temperatura').value;
    if (!temperatura) return setMensaje('Ingresa la temperatura del proceso');

    setOcupado(true);
    setMensaje('Calculando predicción...');

    fetch('/mezclas/predecir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mix, temperatura })
    })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);

            datosPrediccion = data.tabla_prediccion;
            ultimaMezcla = { mix: JSON.parse(JSON.stringify(mix)), temperatura };
            renderTablaPrediccion();

            setMensaje('Predicción calculada');
        })
        .catch(err => setMensaje(err.message))
        .finally(() => setOcupado(false));
}

async function exportarPrediccionPDF() {
    if (!ultimaMezcla) return;

    setMensaje('Generando PDF...');

    try {
        const r = await fetch('/mezclas/predecir/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(ultimaMezcla),
        });
        if (!r.ok) throw new Error('No se pudo generar el PDF');

        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'prediccion_mezcla.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        setMensaje('PDF descargado');
    } catch (err) {
        setMensaje(err.message);
    }
}

async function guardarPrediccionDataset() {
    if (!ultimaMezcla) return;

    const confirmado = await confirmarModerno(
        '¿Agregar esta predicción como una fila nueva a tu dataset?',
        'Guardar predicción'
    );
    if (!confirmado) return;

    setMensaje('Guardando en el dataset...');

    fetch('/mezclas/guardar_prediccion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ultimaMezcla),
    })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            mostrarToast('Guardado', data.mensaje);
            setMensaje(data.mensaje);
        })
        .catch(err => setMensaje(err.message));
}

// ============================
// Render de tablas
// ============================

let datosR2 = [];
let datosPrediccion = [];
let ordenEstado = {};

function claseR2(valor) {
    if (valor >= 0.8) return 'bueno';
    if (valor >= 0.5) return 'medio';
    return 'malo';
}

function renderTablaR2() {
    const tbody = document.getElementById('tablaR2');
    const vacio = document.getElementById('r2Vacio');
    if (!tbody) return;

    if (datosR2.length === 0) {
        tbody.innerHTML = '';
        if (vacio) vacio.style.display = 'block';
        return;
    }
    if (vacio) vacio.style.display = 'none';

    tbody.innerHTML = datosR2.map(row => {
        const clase = claseR2(row.r2);
        const pct = Math.max(0, Math.min(100, row.r2 * 100));
        return `
            <tr>
                <td><span class="var-nombre">${row.columna}</span></td>
                <td>
                    <div class="r2-celda">
                        <div class="r2-barra-bg">
                            <div class="r2-barra-fill r2-${clase}" style="width:${pct}%"></div>
                        </div>
                        <span class="r2-valor r2-txt-${clase}">${row.r2}</span>
                    </div>
                </td>
            </tr>`;
    }).join('');
}

function renderTablaPrediccion() {
    const tbody = document.getElementById('tablaPrediccion');
    const vacio = document.getElementById('prediccionVacia');
    const acciones = document.getElementById('accionesPrediccion');
    if (!tbody) return;

    if (datosPrediccion.length === 0) {
        tbody.innerHTML = '';
        if (vacio) vacio.style.display = 'block';
        if (acciones) acciones.style.display = 'none';
        return;
    }
    if (vacio) vacio.style.display = 'none';
    if (acciones) acciones.style.display = 'flex';

    tbody.innerHTML = datosPrediccion.map(row => `
        <tr>
            <td><span class="var-nombre">${row.columna}</span></td>
            <td><span class="pred-valor">${row.prediccion}</span></td>
        </tr>`).join('');
}

function ordenarTabla(tabla, campo) {
    const key = `${tabla}_${campo}`;
    const direccion = ordenEstado[key] === 'asc' ? 'desc' : 'asc';
    ordenEstado[key] = direccion;

    const datos = tabla === 'r2' ? datosR2 : datosPrediccion;

    datos.sort((a, b) => {
        let valA = a[campo], valB = b[campo];
        if (typeof valA === 'string') {
            return direccion === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
        }
        return direccion === 'asc' ? valA - valB : valB - valA;
    });

    if (tabla === 'r2') renderTablaR2();
    else renderTablaPrediccion();
}

// ============================
// Estado del modelo + restaurar la ultima prediccion guardada
// (persisten en el servidor: sobreviven a cambiar de pagina, cerrar
// el navegador, o cerrar sesion y volver a entrar)
// ============================

function comprobarEstadoServidor() {
    fetch("/mezclas/estado")
        .then(r => r.ok ? r.json() : null)
        .then(data => {
            if (!data) return;
            if (data.modelo_en_memoria || data.modelo_persistido) {
                modeloListo = true;
                actualizarVisibilidadPredecir();
                setOcupado(false);
            }
        })
        .catch(() => {});
}

function restaurarUltimaPrediccion() {
    if (!document.getElementById('tablaPrediccion')) return;

    fetch('/mezclas/ultima_prediccion')
        .then(r => r.ok ? r.json() : null)
        .then(data => {
            if (!data || !data.tabla_prediccion || !data.mix) return;

            mix = data.mix;
            datosPrediccion = data.tabla_prediccion;
            ultimaMezcla = { mix: data.mix, temperatura: data.temperatura };

            const inputTemp = document.getElementById('temperatura');
            if (inputTemp && data.temperatura !== undefined) {
                inputTemp.value = data.temperatura;
            }

            actualizarMix();
            renderTablaPrediccion();
        })
        .catch(() => {});
}

// ============================
// Inicializacion: corre en TODAS las paginas (mezclas.js se carga
// desde base.html), no solo en Predicción, para que el polling del
// entrenamiento y el badge del navbar funcionen sin importar donde
// este el usuario.
// ============================

consultarEstadoEntrenamiento();

if (document.getElementById('mixContainer')) {
    actualizarMix();
    setOcupado(false);
    comprobarEstadoServidor();
    restaurarUltimaPrediccion();
}
