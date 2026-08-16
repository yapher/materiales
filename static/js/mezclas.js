let mix = [];
let modeloListo = false;
let ultimaMezcla = null;

const COLORES_ELEMENTO = {
    CaO:   "#60f06a",
    SiO2:  "#115b8f",
    Al2O3: "#e6731b",
    MgO:   "#a1bba0",
    Na2O:  "#dcf279",
    K2O:   "#f2c879",
    Li2O:  "#ba1c1c",
    CaF2:  "#c9a3f2",
    Fe2O3: "#e08a7f",
    MnO:   "#8c2f7c",
    TiO2:  "#9fd0d9",
};

function escaparHtml(valor) {
    return String(valor)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

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

function notificarWorkflow() {
    if (window.FlujoModelo && typeof window.FlujoModelo.actualizar === 'function') {
        window.FlujoModelo.actualizar();
    }

    document.dispatchEvent(new CustomEvent('mezclas:estado-actualizado'));
}

function calcularTotalMezcla() {
    const total = mix.reduce((acc, e) => acc + (e.pct || 0), 0);
    return Math.round(total * 1000) / 1000;
}

function calcularRestanteMezcla() {
    const restante = 100 - calcularTotalMezcla();
    return Math.round(restante * 1000) / 1000;
}

function formatearPorcentaje(valor) {
    if (Number.isInteger(valor)) {
        return valor.toString();
    }

    return valor.toFixed(2).replace(/\.?0+$/, '');
}

function obtenerTemperatura() {
    const input = document.getElementById('temperatura');

    if (!input) {
        return {
            cargada: false,
            valor: null
        };
    }

    const crudo = String(input.value || '').trim();

    if (crudo === '') {
        return {
            cargada: false,
            valor: null
        };
    }

    const numero = parseFloat(crudo);

    if (!Number.isFinite(numero) || numero <= 0) {
        return {
            cargada: false,
            valor: null
        };
    }

    return {
        cargada: true,
        valor: numero
    };
}

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
            <span class="mix-tag-pct">${formatearPorcentaje(e.pct)}%</span>
            <button onclick="eliminarElemento('${e.elemento}')">✕</button>`;

        cont.appendChild(div);
    });

    const total = calcularTotalMezcla();
    const restante = calcularRestanteMezcla();
    const restanteParaInput = Math.max(0, restante);

    const porcentajeMostrar = Math.min(total, 100);

    const totalEl = document.getElementById('porcentajeTotal');
    if (totalEl) {
        totalEl.textContent = formatearPorcentaje(total);
    }

    const restanteEl = document.getElementById('porcentajeRestante');
    if (restanteEl) {
        restanteEl.textContent = formatearPorcentaje(restanteParaInput);
    }

    const inputPorcentaje = document.getElementById('porcentajeSel');
    if (inputPorcentaje) {
        inputPorcentaje.value = restanteParaInput > 0
            ? formatearPorcentaje(restanteParaInput)
            : '';
    }

    const btnAgregar = document.getElementById('btnAgregarElemento');
    if (btnAgregar) {
        btnAgregar.disabled = restanteParaInput <= 0.001;
    }

    const barEl = document.getElementById('mixBar');
    if (barEl) {
        barEl.style.width = `${porcentajeMostrar}%`;

        barEl.classList.remove(
            'progreso-incompleto',
            'progreso-excedido',
            'progreso-completo'
        );

        if (total > 100.001) {
            barEl.classList.add('progreso-excedido');
        } else if (Math.abs(total - 100) < 0.001) {
            barEl.classList.add('progreso-completo');
        } else {
            barEl.classList.add('progreso-incompleto');
        }
    }

    actualizarVisibilidadPredecir();

    if (window.GraficoTarta && typeof window.GraficoTarta.actualizar === 'function') {
        window.GraficoTarta.actualizar(mix);
    }
}

function setMensaje(texto) {
    const box = document.getElementById('mensajeBox');
    if (!box) return;

    document.getElementById('mensaje').textContent = texto;
    box.style.display = texto ? 'block' : 'none';
}

function actualizarVisibilidadPredecir() {
    const btnPredecir = document.getElementById('btnPredecir');
    if (!btnPredecir) return;

    const total = calcularTotalMezcla();
    const mezclaCompleta = Math.abs(total - 100) < 0.001;

    const temperatura = obtenerTemperatura();
    const temperaturaCargada = temperatura.cargada;

    btnPredecir.style.display = modeloListo ? 'inline-block' : 'none';

    // El botón solo se habilita si:
    // 1) el modelo está entrenado,
    // 2) la mezcla suma exactamente 100%,
    // 3) la temperatura está cargada.
    btnPredecir.disabled = !modeloListo || !mezclaCompleta || !temperaturaCargada;

    notificarWorkflow();
}

function setOcupado(ocupado) {
    const datasetOk = (window.FlujoModelo && typeof window.FlujoModelo.isDatasetListo === 'function')
        ? window.FlujoModelo.isDatasetListo()
        : true;

    const entrenamientoCorriendo = (window.FlujoModelo && typeof window.FlujoModelo.isEntrenamientoCorriendo === 'function')
        ? window.FlujoModelo.isEntrenamientoCorriendo()
        : false;

    const btnEntrenar = document.getElementById('btnEntrenar');

    if (btnEntrenar) {
        btnEntrenar.disabled = ocupado || !datasetOk || entrenamientoCorriendo;
    }

    actualizarVisibilidadPredecir();
}

function agregarElemento() {
    const elemento = document.getElementById('elementoSel').value;
    const restante = calcularRestanteMezcla();

    let pct = parseFloat(document.getElementById('porcentajeSel').value);

    // Si el usuario deja vacío el campo, o pone algo inválido,
    // se sugiere automáticamente el porcentaje restante.
    if (isNaN(pct) || pct <= 0) {
        pct = restante;
    }

    pct = Math.round(pct * 1000) / 1000;

    if (!elemento) return setMensaje('Selecciona un elemento');

    if (isNaN(pct) || pct <= 0) {
        return setMensaje('Porcentaje inválido');
    }

    if (mix.some(e => e.elemento === elemento)) {
        return setMensaje('Elemento ya agregado');
    }

    const total = calcularTotalMezcla();

    if (total + pct > 100.001) {
        return setMensaje(
            `No puede superar 100% (actual: ${formatearPorcentaje(total)}%)`
        );
    }

    mix.push({
        elemento,
        pct
    });

    document.getElementById('elementoSel').value = '';
    document.getElementById('porcentajeSel').value = '';

    actualizarMix();
    setOcupado(false);

    datosPrediccion = [];
    renderTablaPrediccion();

    const nuevoTotal = calcularTotalMezcla();
    const nuevoRestante = calcularRestanteMezcla();

    setMensaje(
        `Total: ${formatearPorcentaje(nuevoTotal)}% — ` +
        `Restante: ${formatearPorcentaje(Math.max(0, nuevoRestante))}%`
    );
}

function eliminarElemento(elemento) {
    mix = mix.filter(e => e.elemento !== elemento);

    datosPrediccion = [];
    renderTablaPrediccion();

    actualizarMix();
    setOcupado(false);

    const nuevoRestante = calcularRestanteMezcla();

    setMensaje(
        `Mezcla modificada. Restante: ${formatearPorcentaje(Math.max(0, nuevoRestante))}%. ` +
        `Ajustá el 100% y volvé a predecir.`
    );
}

let pollEntrenamiento = null;

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

            if (window.FlujoModelo) {
                window.FlujoModelo.setEntrenamientoCorriendo(!!data.corriendo);
            }

            if (data.corriendo) {
                if (badge) badge.style.display = 'inline-flex';
                if (progresoDiv) progresoDiv.style.display = 'block';

                if (data.total) {
                    actualizarBarraProgreso(data.progreso, data.total);

                    setMensaje(
                        `Entrenando ${data.progreso} / ${data.total} variables... ` +
                        `(${data.columna || '...'}) — ${data.tiempo}s`
                    );
                } else {
                    setMensaje('Entrenando...');
                }

                if (window.FlujoModelo) window.FlujoModelo.actualizar();

                return;
            }

            if (badge) badge.style.display = 'none';

            if (pollEntrenamiento) {
                clearInterval(pollEntrenamiento);
                pollEntrenamiento = null;
            }

            setOcupado(false);

            if (data.error) {
                mostrarToast('Error de entrenamiento', data.error, true);
                setMensaje(data.error);

                if (window.FlujoModelo) window.FlujoModelo.actualizar();

                return;
            }

            if (data.listo) {
                if (progresoDiv) progresoDiv.style.display = 'block';

                actualizarBarraProgreso(
                    data.progreso || data.total || 1,
                    data.total || 1
                );

                const yaVisto = localStorage.getItem('entrenamiento_visto') === data.fecha;

                modeloListo = true;

                actualizarVisibilidadPredecir();
                setOcupado(false);

                if (Array.isArray(data.tabla_r2)) {
                    datosR2 = data.tabla_r2;
                    renderTablaR2();
                }

                if (!yaVisto) {
                    mostrarToast(
                        'Modelo entrenado',
                        `Entrenamiento completado en ${data.tiempo}s.`
                    );

                    localStorage.setItem('entrenamiento_visto', data.fecha);
                }

                setMensaje(`Modelo entrenado en ${data.tiempo}s`);
            }

            if (window.FlujoModelo) window.FlujoModelo.actualizar();
        })
        .catch(() => {});
}

function predecir() {
    const temperatura = obtenerTemperatura();

    if (!temperatura.cargada) {
        return setMensaje('Ingresá la temperatura del proceso en K');
    }

    const total = calcularTotalMezcla();

    if (Math.abs(total - 100) > 0.001) {
        return setMensaje(
            `La mezcla debe sumar 100% (actual: ${formatearPorcentaje(total)}%)`
        );
    }

    setOcupado(true);
    setMensaje('Calculando predicción...');

    fetch('/mezclas/predecir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            mix,
            temperatura: temperatura.valor
        })
    })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);

            datosPrediccion = data.tabla_prediccion;

            ultimaMezcla = {
                mix: JSON.parse(JSON.stringify(mix)),
                temperatura: temperatura.valor
            };

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

let datosR2 = [];
let datosPrediccion = [];
let ordenEstado = {};

function claseR2(valor) {
    if (valor >= 0.8) return 'bueno';
    if (valor >= 0.5) return 'medio';
    return 'malo';
}

function normalizarValorOrden(valor) {
    if (valor === null || valor === undefined) {
        return null;
    }

    if (typeof valor === 'number') {
        return valor;
    }

    const numero = Number(valor);

    if (!Number.isNaN(numero)) {
        return numero;
    }

    return String(valor);
}

function renderTablaR2() {
    const tbody = document.getElementById('tablaR2');
    const vacio = document.getElementById('r2Vacio');

    if (!tbody) return;

    if (datosR2.length === 0) {
        tbody.innerHTML = '';

        if (vacio) vacio.style.display = 'block';

        notificarWorkflow();

        return;
    }

    if (vacio) vacio.style.display = 'none';

    tbody.innerHTML = datosR2.map(row => {
        const clase = claseR2(row.r2);
        const pct = Math.max(0, Math.min(100, (Number(row.r2) || 0) * 100));

        const filasNumero = Number(row.filas_entrenadas);
        const filasTexto = Number.isFinite(filasNumero) ? filasNumero : '—';

        const excluidasTargetNumero = Number(row.filas_excluidas_target_invalido);
        const excluidasOutliersNumero = Number(row.filas_excluidas_outliers);

        let tituloFilas = 'Filas reales del dataset usadas para entrenar esta variable.';

        if (Number.isFinite(filasNumero)) {
            tituloFilas = `Se usaron ${filasNumero} filas reales del dataset.`;

            if (Number.isFinite(excluidasTargetNumero) && excluidasTargetNumero > 0) {
                tituloFilas += ` Se excluyeron ${excluidasTargetNumero} filas por valor objetivo <= 0.`;
            }

            if (Number.isFinite(excluidasOutliersNumero) && excluidasOutliersNumero > 0) {
                tituloFilas += ` Se excluyeron ${excluidasOutliersNumero} filas como outliers.`;
            }
        }

        const r2Texto = (row.r2 === null || row.r2 === undefined) ? '—' : row.r2;

        return `
            <tr>
                <td><span class="var-nombre">${escaparHtml(row.columna)}</span></td>
                <td>
                    <div class="r2-celda">
                        <div class="r2-barra-bg">
                            <div class="r2-barra-fill r2-${clase}" style="width:${pct}%"></div>
                        </div>
                        <span class="r2-valor r2-txt-${clase}">${escaparHtml(r2Texto)}</span>
                    </div>
                </td>
                <td class="text-nowrap" title="${escaparHtml(tituloFilas)}">
                    <span class="r2-valor">${escaparHtml(filasTexto)}</span>
                </td>
            </tr>`;
    }).join('');

    notificarWorkflow();
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

        notificarWorkflow();

        return;
    }

    if (vacio) vacio.style.display = 'none';
    if (acciones) acciones.style.display = 'flex';

    tbody.innerHTML = datosPrediccion.map(row => `
        <tr>
            <td><span class="var-nombre">${escaparHtml(row.columna)}</span></td>
            <td><span class="pred-valor">${escaparHtml(row.prediccion)}</span></td>
        </tr>`).join('');

    notificarWorkflow();
}

function ordenarTabla(tabla, campo) {
    const key = `${tabla}_${campo}`;
    const direccion = ordenEstado[key] === 'asc' ? 'desc' : 'asc';

    ordenEstado[key] = direccion;

    const datos = tabla === 'r2' ? datosR2 : datosPrediccion;

    datos.sort((a, b) => {
        let valA = normalizarValorOrden(a[campo]);
        let valB = normalizarValorOrden(b[campo]);

        if (valA === null && valB === null) {
            return 0;
        }

        if (valA === null) {
            return 1;
        }

        if (valB === null) {
            return -1;
        }

        if (typeof valA === 'string' || typeof valB === 'string') {
            const strA = String(valA);
            const strB = String(valB);

            return direccion === 'asc'
                ? strA.localeCompare(strB)
                : strB.localeCompare(strA);
        }

        return direccion === 'asc' ? valA - valB : valB - valA;
    });

    if (tabla === 'r2') {
        renderTablaR2();
    } else {
        renderTablaPrediccion();
    }
}

function comprobarEstadoServidor() {
    fetch('/mezclas/estado')
        .then(r => r.ok ? r.json() : null)
        .then(data => {
            if (!data) return;

            if (data.dataset_cargado && window.FlujoModelo) {
                window.FlujoModelo.setDatasetListo(true);
            }

            if (data.modelo_info && Array.isArray(data.modelo_info.tabla_r2)) {
                datosR2 = data.modelo_info.tabla_r2;
                renderTablaR2();
            }

            if (data.modelo_en_memoria || data.modelo_persistido) {
                modeloListo = true;

                actualizarVisibilidadPredecir();
                setOcupado(false);
            }

            notificarWorkflow();
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

            ultimaMezcla = {
                mix: data.mix,
                temperatura: data.temperatura
            };

            const inputTemp = document.getElementById('temperatura');

            if (inputTemp && data.temperatura !== undefined && data.temperatura !== null) {
                inputTemp.value = data.temperatura;
            }

            actualizarMix();
            renderTablaPrediccion();
        })
        .catch(() => {});
}

consultarEstadoEntrenamiento();

if (document.getElementById('mixContainer')) {
    const temperaturaEl = document.getElementById('temperatura');

    if (temperaturaEl) {
        temperaturaEl.addEventListener('input', actualizarVisibilidadPredecir);
    }

    actualizarMix();
    setOcupado(false);
    comprobarEstadoServidor();
    restaurarUltimaPrediccion();
}

window.MezclasApp = {
    getModeloListo() {
        return modeloListo;
    },

    hayPrediccion() {
        return datosPrediccion.length > 0;
    },

    getMix() {
        return JSON.parse(JSON.stringify(mix));
    },

    colores: COLORES_ELEMENTO,
};