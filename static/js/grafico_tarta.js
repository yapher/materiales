(function () {
"use strict";
const NS = "http://www.w3.org/2000/svg";
const ID_RESTANTE = "__restante__";
const STORAGE_KEY_TARTA = "grafico_tarta_visible";
const CONFIG = {
ancho: 400,
alto: 250,
cx: 200,
cy: 116,
radio: 132,
inclinacion: 0.52,
profundidad: 34,
duracion: 650,
elevacionHover: 8,
anguloMinimoEtiqueta: 20,
};
if (
window.matchMedia &&
window.matchMedia("(prefers-reduced-motion: reduce)").matches
) {
CONFIG.duracion = 0;
}
const COLORES_DEFAULT = {
CaO: "#8fd694",
SiO2: "#7fb8e0",
Al2O3: "#e0a97f",
MgO: "#a3e0a0",
Na2O: "#f2d879",
K2O: "#f2c879",
Li2O: "#f2e79c",
CaF2: "#c9a3f2",
Fe2O3: "#e08a7f",
MnO: "#d99fd0",
TiO2: "#9fd0d9",
};
let panel = null;
let contenedor = null;
let svg = null;
let capaDefs = null;
let capaSombra = null;
let capaSlices = null;
let tooltip = null;
let vacio = null;
let badgeEstado = null;
let objetivo = [];
let valoresVisibles = new Map();
let animId = null;
let sliceActiva = null;
let gradientesListos = false;
function conseguirColores() {
if (window.MezclasApp && window.MezclasApp.colores) {
return Object.assign({}, COLORES_DEFAULT, window.MezclasApp.colores);
}
return COLORES_DEFAULT;
}
function ajustarColor(color, factor) {
let hex = String(color).replace("#", "");
if (hex.length === 3) {
hex = hex.split("").map((c) => c + c).join("");
}
const n = parseInt(hex, 16);
const r = Math.min(255, Math.max(0, Math.round(((n >> 16) & 255) * factor)));
const g = Math.min(255, Math.max(0, Math.round(((n >> 8) & 255) * factor)));
const b = Math.min(255, Math.max(0, Math.round((n & 255) * factor)));
return `rgb(${r}, ${g}, ${b})`;
}
function formatearNumero(valor) {
const redondeado = Math.round(valor * 100) / 100;
if (Number.isInteger(redondeado)) {
return String(redondeado);
}
return redondeado.toFixed(2).replace(/\.?0+$/, "");
}
function obtenerTotalVisible() {
let total = 0;
valoresVisibles.forEach((v) => {
total += Number(v) || 0;
});
return total;
}
function crear(tag, attrs = {}) {
const nodo = document.createElementNS(NS, tag);
Object.entries(attrs).forEach(([k, v]) => {
nodo.setAttribute(k, v);
});
return nodo;
}
function punto(angulo, escala = 1) {
const rad = (angulo * Math.PI) / 180;
return {
x: CONFIG.cx + CONFIG.radio * escala * Math.cos(rad),
y: CONFIG.cy + CONFIG.radio * CONFIG.inclinacion * escala * Math.sin(rad),
};
}
function construir() {
svg = crear("svg", {
viewBox: `0 0 ${CONFIG.ancho} ${CONFIG.alto}`,
class: "tarta-svg",
role: "img",
"aria-label": "Gráfico de tarta 3D de la composición de la mezcla",
});
capaDefs = crear("defs");
const filtro = crear("filter", {
id: "tartaBlur",
x: "-40%",
y: "-40%",
width: "180%",
height: "180%",
});
filtro.appendChild(
crear("feGaussianBlur", {
in: "SourceGraphic",
stdDeviation: "7",
})
);
capaDefs.appendChild(filtro);
svg.appendChild(capaDefs);
capaSombra = crear("ellipse", {
class: "tarta-sombra",
cx: CONFIG.cx,
cy: CONFIG.cy + CONFIG.profundidad + 8,
rx: CONFIG.radio * 1.03,
ry: CONFIG.radio * CONFIG.inclinacion * 0.9,
fill: "rgba(0, 0, 0, 0.55)",
filter: "url(#tartaBlur)",
});
svg.appendChild(capaSombra);
capaSlices = crear("g", {
class: "tarta-capas",
});
svg.appendChild(capaSlices);
contenedor.appendChild(svg);
vacio = document.createElement("div");
vacio.className = "grafico-tarta-vacio";
vacio.innerHTML = `
<i class="bi bi-pie-chart"></i>
<p>Agregá elementos para<br>armar tu mezcla</p>
`;
contenedor.appendChild(vacio);
tooltip = document.createElement("div");
tooltip.className = "grafico-tarta-tooltip";
tooltip.setAttribute("role", "status");
contenedor.appendChild(tooltip);
asegurarGradientes();
conectarEventos();
}
function crearGradiente(id, colorArriba, colorAbajo) {
const grad = crear("linearGradient", {
id,
x1: "0",
y1: "0",
x2: "0",
y2: "1",
});
grad.appendChild(
crear("stop", {
offset: "0%",
"stop-color": colorArriba,
})
);
grad.appendChild(
crear("stop", {
offset: "100%",
"stop-color": colorAbajo,
})
);
capaDefs.appendChild(grad);
}
function asegurarGradientes() {
if (gradientesListos) return;
const colores = conseguirColores();
Object.entries(colores).forEach(([elemento, color]) => {
crearGradiente(
`grad-top-${elemento}`,
ajustarColor(color, 1.30),
ajustarColor(color, 0.94)
);
crearGradiente(
`grad-side-${elemento}`,
ajustarColor(color, 0.66),
ajustarColor(color, 0.42)
);
});
crearGradiente("grad-rest-top", "#332a52", "#2a2145");
crearGradiente("grad-rest-side", "#241d3d", "#1c1631");
gradientesListos = true;
}
function caminoTapa(a0, a1) {
const rx = CONFIG.radio;
const ry = CONFIG.radio * CONFIG.inclinacion;
let barrido = a1 - a0;
if (barrido >= 359.9) {
const p0 = punto(a0);
const pm = punto(a0 + 180);
return [
`M ${CONFIG.cx} ${CONFIG.cy}`,
`L ${p0.x} ${p0.y}`,
`A ${rx} ${ry} 0 1 1 ${pm.x} ${pm.y}`,
`A ${rx} ${ry} 0 1 1 ${p0.x} ${p0.y}`,
"Z",
].join(" ");
}
const p0 = punto(a0);
const p1 = punto(a1);
const grande = barrido > 180 ? 1 : 0;
return [
`M ${CONFIG.cx} ${CONFIG.cy}`,
`L ${p0.x} ${p0.y}`,
`A ${rx} ${ry} 0 ${grande} 1 ${p1.x} ${p1.y}`,
"Z",
].join(" ");
}
function caminoPared(a0, a1) {
const s0 = Math.max(a0, 0);
const s1 = Math.min(a1, 180);
if (s1 - s0 <= 0.1) return null;
const rx = CONFIG.radio;
const ry = CONFIG.radio * CONFIG.inclinacion;
const grande = s1 - s0 > 180 ? 1 : 0;
const p0 = punto(s0);
const p1 = punto(s1);
const h = CONFIG.profundidad;
return [
`M ${p0.x} ${p0.y}`,
`A ${rx} ${ry} 0 ${grande} 1 ${p1.x} ${p1.y}`,
`L ${p1.x} ${p1.y + h}`,
`A ${rx} ${ry} 0 ${grande} 0 ${p0.x} ${p0.y + h}`,
"Z",
].join(" ");
}
function dibujarSlice(item, a0, a1) {
const barrido = a1 - a0;
if (barrido <= 0.05) return;
const grupo = crear("g", {
class: item.restante ? "tarta-slice tarta-restante" : "tarta-slice",
"data-elemento": item.id,
"data-angulo-medio": String((a0 + a1) / 2),
});
const pared = caminoPared(a0, a1);
if (pared) {
grupo.appendChild(
crear("path", {
class: "tarta-pared",
d: pared,
fill: item.restante
? "url(#grad-rest-side)"
: `url(#grad-side-${item.id})`,
})
);
}
grupo.appendChild(
crear("path", {
class: "tarta-tapa",
d: caminoTapa(a0, a1),
fill: item.restante
? "url(#grad-rest-top)"
: `url(#grad-top-${item.id})`,
})
);
if (barrido >= CONFIG.anguloMinimoEtiqueta) {
const pos = punto((a0 + a1) / 2, 0.62);
const etiqueta = crear("text", {
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
capaSlices.appendChild(grupo);
}
function render() {
if (!capaSlices) return;
sliceActiva = null;
if (tooltip) {
tooltip.classList.remove("tooltip-visible");
}
while (capaSlices.firstChild) {
capaSlices.removeChild(capaSlices.firstChild);
}
const total = obtenerTotalVisible();
const restante = Math.max(0, 100 - total);
const hayDatos = total > 0.05 || restante > 0.05;
const completo = Math.abs(total - 100) < 0.001;
const excedido = total > 100.001;
if (vacio) {
vacio.style.display = "none";
}
contenedor.classList.toggle("grafico-tarta-con-datos", hayDatos);
if (panel) {
panel.classList.toggle("grafico-completo", completo);
panel.classList.toggle("grafico-excedido", excedido);
}
if (badgeEstado) {
if (excedido) {
badgeEstado.textContent = `Excedido ${formatearNumero(total - 100)}%`;
} else {
badgeEstado.textContent = `Restante ${formatearNumero(restante)}%`;
}
badgeEstado.classList.toggle("estado-completo", completo);
badgeEstado.classList.toggle("estado-excedido", excedido);
}
if (!hayDatos) {
svg.setAttribute("aria-label", "Composición vacía");
return;
}
const referencia = Math.max(total, 100);
const items = [];
objetivo.forEach((o) => {
const pct = valoresVisibles.get(o.elemento) || 0;
if (pct > 0.01) {
items.push({
id: o.elemento,
pct,
restante: false,
});
}
});
valoresVisibles.forEach((pct, elemento) => {
const enObjetivo = objetivo.some((o) => o.elemento === elemento);
if (!enObjetivo && pct > 0.01) {
items.push({
id: elemento,
pct,
restante: false,
});
}
});
if (restante > 0.05 && !excedido) {
items.push({
id: ID_RESTANTE,
pct: restante,
restante: true,
});
}
let angulo = -90;
items.forEach((item) => {
const barrido = (item.pct / referencia) * 360;
dibujarSlice(item, angulo, angulo + barrido);
angulo += barrido;
});
const resumen = items
.filter((i) => !i.restante)
.map((i) => `${i.id} ${formatearNumero(i.pct)}%`)
.join(", ");
if (total <= 0.05) {
svg.setAttribute(
"aria-label",
`Composición pendiente: restante ${formatearNumero(restante)}%`
);
} else if (completo) {
svg.setAttribute(
"aria-label",
`Composición completa: ${resumen}`
);
} else {
svg.setAttribute(
"aria-label",
`Composición al ${formatearNumero(total)}%: ${resumen}. ` +
`Restante ${formatearNumero(restante)}%`
);
}
}
function animarHacia(nuevaMezcla) {
if (!contenedor) return;
const mezcla = Array.isArray(nuevaMezcla) ? nuevaMezcla : [];
objetivo = mezcla.map((e) => ({
elemento: String(e.elemento),
pct: Math.max(0, Number(e.pct) || 0),
}));
if (animId) {
cancelAnimationFrame(animId);
}
if (CONFIG.duracion <= 0) {
valoresVisibles = new Map(
objetivo
.filter((o) => o.pct > 0)
.map((o) => [o.elemento, o.pct])
);
render();
return;
}
const desde = new Map(valoresVisibles);
const claves = new Set([
...desde.keys(),
...objetivo.map((o) => o.elemento),
]);
const inicio = performance.now();
function paso(ahora) {
const t = Math.min(1, (ahora - inicio) / CONFIG.duracion);
const suavizado = 1 - Math.pow(1 - t, 3);
const nuevos = new Map();
claves.forEach((clave) => {
const de = desde.get(clave) || 0;
const obj = objetivo.find((o) => o.elemento === clave);
const a = obj ? obj.pct : 0;
const valor = de + (a - de) * suavizado;
if (valor > 0.01) {
nuevos.set(clave, valor);
}
});
valoresVisibles = nuevos;
render();
if (t < 1) {
animId = requestAnimationFrame(paso);
} else {
animId = null;
const finales = new Map();
objetivo.forEach((o) => {
if (o.pct > 0.01) {
finales.set(o.elemento, o.pct);
}
});
valoresVisibles = finales;
render();
}
}
animId = requestAnimationFrame(paso);
}
function conectarEventos() {
svg.addEventListener("pointerover", (ev) => {
const grupo = ev.target.closest
? ev.target.closest(".tarta-slice")
: null;
if (!grupo) {
desactivarSlice();
return;
}
activarSlice(grupo, ev.clientX, ev.clientY);
});
svg.addEventListener("pointermove", (ev) => {
if (sliceActiva) {
posicionarTooltip(ev.clientX, ev.clientY);
}
});
svg.addEventListener("pointerleave", desactivarSlice);
document.addEventListener(
"pointerdown",
(ev) => {
if (contenedor && !contenedor.contains(ev.target)) {
desactivarSlice();
}
},
true
);
}
function activarSlice(grupo, clientX, clientY) {
if (sliceActiva && sliceActiva !== grupo) {
sliceActiva.classList.remove("tarta-slice-activa");
sliceActiva.style.transform = "";
}
sliceActiva = grupo;
capaSlices.appendChild(grupo);
grupo.classList.add("tarta-slice-activa");
const mid = parseFloat(grupo.dataset.anguloMedio || "0");
const rad = (mid * Math.PI) / 180;
const dx = CONFIG.elevacionHover * Math.cos(rad);
const dy = CONFIG.elevacionHover * Math.sin(rad) * CONFIG.inclinacion;
grupo.style.transform = `translate(${dx}px, ${dy}px)`;
mostrarTooltip(grupo.dataset.elemento, clientX, clientY);
}
function desactivarSlice() {
if (sliceActiva) {
sliceActiva.classList.remove("tarta-slice-activa");
sliceActiva.style.transform = "";
sliceActiva = null;
}
if (tooltip) {
tooltip.classList.remove("tooltip-visible");
}
}
function mostrarTooltip(elemento, clientX, clientY) {
if (!tooltip) return;
const colores = conseguirColores();
const esRestante = elemento === ID_RESTANTE;
const totalVisible = obtenerTotalVisible();
const pct = esRestante
? Math.max(0, 100 - totalVisible)
: (valoresVisibles.get(elemento) || 0);
const label = esRestante ? "Restante" : elemento;
const color = esRestante
? "#6f6a85"
: (colores[elemento] || "#88c999");
tooltip.innerHTML = `
<span
class="grafico-tarta-tooltip-chip"
style="background:${color};"
></span>
<strong>${label}</strong>
<span class="grafico-tarta-tooltip-pct">
${formatearNumero(pct)}%
</span>
`;
tooltip.classList.add("tooltip-visible");
posicionarTooltip(clientX, clientY);
}
function posicionarTooltip(clientX, clientY) {
if (!tooltip || !contenedor) return;
const rect = contenedor.getBoundingClientRect();
let x = clientX - rect.left;
let y = clientY - rect.top;
x = Math.min(Math.max(x, 60), Math.max(rect.width - 60, 60));
y = Math.max(y, 46);
tooltip.style.left = `${x}px`;
tooltip.style.top = `${y}px`;
}
// ==========================================================
// TOGGLE: mostrar/ocultar la tarta 3D con un switch
// ==========================================================
function initToggleTarta() {
const checkbox = document.getElementById("checkGraficoTarta");
const panelTarta = document.getElementById("panelGraficoTarta");
if (!checkbox || !panelTarta) return;
// Leer preferencia guardada
let visible = false;
try {
visible = localStorage.getItem(STORAGE_KEY_TARTA) === "true";
} catch (e) {
visible = false;
}
checkbox.checked = visible;
panelTarta.style.display = visible ? "block" : "none";
checkbox.addEventListener("change", function () {
const mostrar = checkbox.checked;
panelTarta.style.display = mostrar ? "block" : "none";
try {
localStorage.setItem(STORAGE_KEY_TARTA, String(mostrar));
} catch (e) {}
if (mostrar) {
// Re-renderizar al mostrar por si la mezcla cambió
render();
}
});
}
window.GraficoTarta = {
actualizar(mix) {
animarHacia(mix);
},
};
function init() {
contenedor = document.getElementById("graficoTarta");
if (!contenedor) return;
panel = contenedor.closest(".grafico-tarta-panel");
badgeEstado = document.getElementById("graficoTartaEstado");
construir();
render();
// Inicializar el toggle del switch
initToggleTarta();
if (
window.MezclasApp &&
typeof window.MezclasApp.getMix === "function"
) {
const mix = window.MezclasApp.getMix();
if (Array.isArray(mix) && mix.length > 0) {
objetivo = mix.map((e) => ({
elemento: String(e.elemento),
pct: Math.max(0, Number(e.pct) || 0),
}));
valoresVisibles = new Map(
objetivo.map((o) => [o.elemento, o.pct])
);
render();
}
}
}
if (document.readyState === "loading") {
document.addEventListener("DOMContentLoaded", init);
} else {
init();
}
})();