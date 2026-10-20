"use strict";

const ESTADO = {
  catalogo: [],
  flota: [],
  paquetes: { total: 0, peso_total: 0, volumen_total: 0, items: [] },
  barrios: [],
  depot: null,
  optimizacion: null,
};

let mapaActual = null;
let tabActiva = 0;

/* ------------------------- Utilidades de UI ------------------------- */
const $ = (id) => document.getElementById(id);

function aviso(texto, tipo = "") {
  const el = $("aviso");
  el.textContent = texto;
  el.className = "aviso visible " + tipo;
  clearTimeout(aviso._t);
  aviso._t = setTimeout(() => (el.className = "aviso"), 3200);
}

async function api(metodo, ruta, cuerpo) {
  const opciones = { method: metodo };
  if (cuerpo !== undefined) {
    opciones.headers = { "Content-Type": "application/json" };
    opciones.body = JSON.stringify(cuerpo);
  }
  const resp = await fetch(ruta, opciones);
  const datos = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(datos.error || "Error en el servidor");
  return datos;
}

/* --------------------- Ilustraciones (foto) ------------------------- */
const COLORES = {
  "Moto": "#e2701c",
  "Carro": "#1f6feb",
  "Camioneta": "#7a5cf0",
  "Camion": "#2f9e6b",
  "Camion grande": "#b8382f",
};

function colorVehiculo(tipo) {
  if (COLORES[tipo]) return COLORES[tipo];
  for (const clave in COLORES) {
    if (tipo && tipo.toLowerCase().startsWith(clave.toLowerCase().slice(0, 5))) {
      return COLORES[clave];
    }
  }
  return "#445566";
}

function svgVehiculo(tipo) {
  const c = colorVehiculo(tipo);
  const t = tipo ? tipo.toLowerCase() : "";
  const cuerpo = `<rect width="200" height="120" fill="none"/>`;

  if (t.includes("moto") || t.includes("bici")) {
    return `<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
      <circle cx="48" cy="90" r="24" fill="#2b2b2b"/>
      <circle cx="48" cy="90" r="10" fill="#c9cdd4"/>
      <circle cx="156" cy="90" r="24" fill="#2b2b2b"/>
      <circle cx="156" cy="90" r="10" fill="#c9cdd4"/>
      <path d="M48 90 L78 48 L124 48 L156 90" stroke="${c}" stroke-width="11"
            fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M70 48 L124 48 L138 72" stroke="${c}" stroke-width="9"
            fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      <rect x="100" y="34" width="34" height="15" rx="5" fill="#dbe9ff"/>
    </svg>`;
  }
  if (t.includes("camion grande") || t.includes("trailer")) {
    return `<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
      <rect x="8" y="18" width="112" height="72" rx="5" fill="${c}"/>
      <rect x="8" y="18" width="112" height="72" rx="5" fill="#000" opacity=".08"/>
      <path d="M124 34 L158 34 Q176 34 184 54 L190 84 L124 84 Z" fill="${c}" opacity=".75"/>
      <rect x="132" y="42" width="34" height="22" rx="3" fill="#dbe9ff"/>
      <circle cx="42" cy="94" r="15" fill="#2b2b2b"/><circle cx="42" cy="94" r="6" fill="#c9cdd4"/>
      <circle cx="98" cy="94" r="15" fill="#2b2b2b"/><circle cx="98" cy="94" r="6" fill="#c9cdd4"/>
      <circle cx="164" cy="94" r="15" fill="#2b2b2b"/><circle cx="164" cy="94" r="6" fill="#c9cdd4"/>
    </svg>`;
  }
  if (t.includes("camion")) {
    return `<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
      <rect x="10" y="26" width="104" height="60" rx="4" fill="${c}"/>
      <path d="M116 40 L150 40 Q166 40 174 60 L180 86 L116 86 Z" fill="${c}" opacity=".75"/>
      <rect x="124" y="48" width="32" height="20" rx="3" fill="#dbe9ff"/>
      <circle cx="42" cy="90" r="15" fill="#2b2b2b"/><circle cx="42" cy="90" r="6" fill="#c9cdd4"/>
      <circle cx="96" cy="90" r="15" fill="#2b2b2b"/><circle cx="96" cy="90" r="6" fill="#c9cdd4"/>
      <circle cx="158" cy="90" r="15" fill="#2b2b2b"/><circle cx="158" cy="90" r="6" fill="#c9cdd4"/>
    </svg>`;
  }
  if (t.includes("camioneta") || t.includes("van") || t.includes("furgon")) {
    return `<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
      <path d="M18 90 L18 46 Q18 32 34 32 L118 32 L118 90 Z" fill="${c}"/>
      <path d="M118 90 L118 46 L150 46 Q166 46 174 60 L182 90 Z" fill="${c}" opacity=".75"/>
      <rect x="126" y="52" width="30" height="22" rx="3" fill="#dbe9ff"/>
      <circle cx="52" cy="92" r="14" fill="#2b2b2b"/><circle cx="52" cy="92" r="6" fill="#c9cdd4"/>
      <circle cx="152" cy="92" r="14" fill="#2b2b2b"/><circle cx="152" cy="92" r="6" fill="#c9cdd4"/>
    </svg>`;
  }
  /* Carro por defecto */
  return `<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
    ${cuerpo}
    <rect x="14" y="62" width="172" height="30" rx="12" fill="${c}"/>
    <path d="M50 62 L68 34 Q72 28 80 28 L128 28 Q136 28 140 34 L158 62 Z" fill="${c}" opacity=".8"/>
    <rect x="76" y="34" width="24" height="22" rx="3" fill="#dbe9ff"/>
    <rect x="106" y="34" width="24" height="22" rx="3" fill="#dbe9ff"/>
    <circle cx="58" cy="92" r="15" fill="#2b2b2b"/><circle cx="58" cy="92" r="6" fill="#c9cdd4"/>
    <circle cx="142" cy="92" r="15" fill="#2b2b2b"/><circle cx="142" cy="92" r="6" fill="#c9cdd4"/>
  </svg>`;
}

/* ------------------------- Render de estado ------------------------- */
function actualizarEstado() {
  $("estado-vehiculos").textContent = ESTADO.flota.length;
  $("estado-paquetes").textContent = ESTADO.paquetes.total;
}

function renderFlota() {
  const cont = $("lista-flota");
  if (!ESTADO.flota.length) {
    cont.innerHTML = `<span class="chip resumen">Sin vehículos en la flota</span>`;
    return;
  }
  cont.innerHTML = ESTADO.flota
    .map(
      (v) =>
        `<span class="chip">${v.tipo} · ${v.id} (${v.peso_max} kg)
           <button title="Eliminar" data-eliminar="${v.id}">✕</button></span>`
    )
    .join("");
  cont.querySelectorAll("[data-eliminar]").forEach((b) =>
    b.addEventListener("click", () => eliminarVehiculo(b.dataset.eliminar))
  );
}

function renderPaquetes() {
  const p = ESTADO.paquetes;
  $("resumen-paquetes").innerHTML = `
    <span class="chip resumen">Paquetes: ${p.total}</span>
    <span class="chip resumen">Peso: ${p.peso_total} kg</span>
    <span class="chip resumen">Espacio: ${p.volumen_total} m³</span>`;
}

function renderCatalogo() {
  $("tipo-vehiculo").innerHTML = ESTADO.catalogo
    .map(
      (t) =>
        `<option value="${t.tipo}">${t.tipo} · ${t.peso_max} kg / ${t.volumen} m³</option>`
    )
    .join("");
}

function renderBarrios() {
  $("pq-barrio").innerHTML = ESTADO.barrios
    .map((b) => `<option value="${b.nombre}">${b.nombre}</option>`)
    .join("");
}

/* ------------------------- Acciones flota ------------------------- */
async function agregarFlota() {
  try {
    const datos = await api("POST", "/api/flota", {
      accion: "agregar",
      tipo: $("tipo-vehiculo").value,
      cantidad: parseInt($("cantidad-vehiculo").value, 10),
    });
    ESTADO.flota = datos.vehiculos;
    renderFlota();
    actualizarEstado();
    aviso("Vehículos agregados a la flota", "ok");
  } catch (e) {
    aviso(e.message, "error");
  }
}

async function agregarPersonalizado() {
  try {
    const datos = await api("POST", "/api/flota", {
      accion: "personalizado",
      id: $("pv-id").value || "V-" + (ESTADO.flota.length + 1),
      tipo: $("pv-tipo").value || "Personalizado",
      peso_max: $("pv-peso").value,
      largo: $("pv-largo").value,
      ancho: $("pv-ancho").value,
      alto: $("pv-alto").value,
    });
    ESTADO.flota = datos.vehiculos;
    renderFlota();
    actualizarEstado();
    aviso("Vehículo personalizado agregado", "ok");
  } catch (e) {
    aviso(e.message, "error");
  }
}

async function eliminarVehiculo(id) {
  const datos = await api("POST", "/api/flota", { accion: "eliminar", id });
  ESTADO.flota = datos.vehiculos;
  renderFlota();
  actualizarEstado();
}

async function vaciarFlota() {
  const datos = await api("POST", "/api/flota", { accion: "vaciar" });
  ESTADO.flota = datos.vehiculos;
  renderFlota();
  actualizarEstado();
}

/* ------------------------- Acciones paquetes ------------------------- */
async function generarPaquetes() {
  try {
    const datos = await api("POST", "/api/paquetes", {
      accion: "generar",
      cantidad: parseInt($("cantidad-paquetes").value, 10),
      semilla: $("semilla-paquetes").value,
    });
    ESTADO.paquetes = datos;
    renderPaquetes();
    actualizarEstado();
    aviso(`Se generaron ${datos.total} paquetes (data/paquetes.csv)`, "ok");
  } catch (e) {
    aviso(e.message, "error");
  }
}

async function cargarCsv() {
  try {
    const datos = await api("POST", "/api/paquetes", { accion: "cargar" });
    ESTADO.paquetes = datos;
    renderPaquetes();
    actualizarEstado();
    aviso(`CSV cargado: ${datos.total} paquetes`, "ok");
  } catch (e) {
    aviso(e.message, "error");
  }
}

async function vaciarPaquetes() {
  const datos = await api("POST", "/api/paquetes", { accion: "vaciar" });
  ESTADO.paquetes = datos;
  renderPaquetes();
  actualizarEstado();
}

async function insertarPaquete() {
  const barrio = ESTADO.barrios.find((b) => b.nombre === $("pq-barrio").value);
  if (!barrio) return aviso("Seleccione un barrio válido", "error");
  try {
    const datos = await api("POST", "/api/paquetes", {
      accion: "insertar",
      id: $("pq-id").value,
      tipo: $("pq-tipo").value,
      peso: $("pq-peso").value,
      alto: $("pq-alto").value,
      ancho: $("pq-ancho").value,
      profundo: $("pq-profundo").value,
      barrio: barrio.nombre,
      lat: barrio.lat,
      lon: barrio.lon,
    });
    ESTADO.paquetes = datos;
    renderPaquetes();
    actualizarEstado();
    $("pq-id").value = "";
    aviso("Paquete insertado", "ok");
  } catch (e) {
    aviso(e.message, "error");
  }
}

/* ------------------------- Optimización ------------------------- */
async function optimizar() {
  if (!ESTADO.flota.length) return aviso("Primero configura la flota", "error");
  if (!ESTADO.paquetes.total) return aviso("Primero genera o carga paquetes", "error");
  try {
    const datos = await api("GET", "/api/optimizar");
    ESTADO.optimizacion = datos;
    tabActiva = 0;
    renderResumen(datos.totales);
    renderAviso(datos);
    renderTabs(datos.vehiculos);
    renderVehiculo(0);
    aviso("Optimización completada", "ok");
  } catch (e) {
    aviso(e.message, "error");
  }
}

function renderAviso(datos) {
  const el = $("aviso-sin-asignar");
  const libre = datos.totales.vehiculos_disponibles - datos.totales.vehiculos_usados;
  if (datos.sin_asignar.length) {
    el.hidden = false;
    el.className = "banner-warn";
    el.innerHTML =
      `<b>${datos.sin_asignar.length} paquetes no cupieron</b> en la flota ` +
      `(capacidad insuficiente). Se usaron ${datos.totales.vehiculos_usados} de ` +
      `${datos.totales.vehiculos_disponibles} vehículos. Agrega vehículos o revisa ` +
      `el tamaño de los paquetes.`;
  } else if (libre > 0) {
    el.hidden = false;
    el.className = "banner-warn banner-ok";
    el.innerHTML =
      `Se usaron <b>${datos.totales.vehiculos_usados}</b> de ` +
      `${datos.totales.vehiculos_disponibles} vehículos. ` +
      `Quedaron <b>${libre}</b> sin usar porque no se necesitaban.`;
  } else {
    el.hidden = true;
  }
}

function renderResumen(t) {
  $("resumen-cards").hidden = false;
  $("r-usados").textContent = `${t.vehiculos_usados}/${t.vehiculos_disponibles}`;
  $("r-asignados").textContent = `${t.paquetes_asignados}/${t.paquetes_total}`;
  $("r-opt").textContent = `${t.dist_optima} km`;
  $("r-sin").textContent = `${t.dist_original} km`;
  $("r-ahorro").textContent = `${t.ahorro_pct}% (${t.ahorro_km} km)`;
}

function renderTabs(vehiculos) {
  const tabs = $("tabs");
  if (!vehiculos.length) {
    tabs.innerHTML = "";
    $("detalle-vehiculo").innerHTML = `<div class="placeholder">
      <p>Ningún vehículo recibió paquetes. Aumenta la flota o reduce el tamaño de los paquetes.</p>
    </div>`;
    return;
  }
  tabs.innerHTML = vehiculos
    .map(
      (v, i) =>
        `<button class="tab ${i === tabActiva ? "activo" : ""}" data-tab="${i}">
           <span class="punto" style="background:${colorVehiculo(v.tipo)}"></span>
           ${v.id} · ${v.tipo}
         </button>`
    )
    .join("");
  tabs.querySelectorAll("[data-tab]").forEach((b) =>
    b.addEventListener("click", () => {
      tabActiva = parseInt(b.dataset.tab, 10);
      renderTabs(vehiculos);
      renderVehiculo(tabActiva);
    })
  );
}

function barra(etiqueta, valor, max, unidad) {
  const pct = max > 0 ? Math.min(100, (valor / max) * 100) : 0;
  const clase = pct > 85 ? "barra-fill alto" : "barra-fill";
  return `<div class="barra">
      <div class="barra-head"><span>${etiqueta}</span>
        <span>${valor} / ${max} ${unidad} (${pct.toFixed(1)}%)</span></div>
      <div class="barra-track"><div class="${clase}" style="width:${pct}%"></div></div>
    </div>`;
}

function renderVehiculo(indice) {
  const v = ESTADO.optimizacion.vehiculos[indice];
  if (!v) return;
  if (mapaActual) {
    mapaActual.remove();
    mapaActual = null;
  }

  const filas = v.paquetes
    .map(
      (p) => `<div class="fila-paquete">
        <span class="pid">${p.id}</span>
        <span class="barrio">${p.barrio}<br><span class="tag">${p.tipo}</span>
          ${p.alto}×${p.ancho}×${p.profundo} m</span>
        <span class="peso">${p.peso} kg</span>
      </div>`
    )
    .join("");

  const r = v.ruta;
  const html = `
    <div class="vehiculo-card">
      <div class="card-top">
        <div class="vehiculo-foto">
          <div class="foto">${svgVehiculo(v.tipo)}</div>
          <h3>${v.id}</h3>
          <p class="tipo">${v.tipo}</p>
          ${barra("Peso", v.stats.peso, v.stats.peso_max, "kg")}
          ${barra("Espacio", v.stats.volumen, v.stats.volumen_max, "m³")}
        </div>
        <div class="paquetes">
          <h4>Paquetes que lleva (${v.paquetes.length})</h4>
          <div class="lista-paquetes">${filas}</div>
        </div>
      </div>
      <div class="card-mapa">
        <h4>Mapa de la ruta · ${v.ruta.paradas.length} paradas</h4>
        <div id="mapa" class="mapa"></div>
        <div class="ruta-info">
          <span>Orden de carga: <b>${r.dist_original} km</b></span>
          <span>Ruta óptima: <b>${r.dist_optima} km</b></span>
          <span class="ganancia">Ahorro: ${r.ahorro_km} km (${r.ahorro_pct}%)</span>
          <span>Zona(s): <b>${(v.zonas || []).join(", ") || "—"}</b></span>
        </div>
      </div>
    </div>`;
  $("detalle-vehiculo").innerHTML = html;

  dibujarMapa(v);
}

function dibujarMapa(v) {
  const depot = ESTADO.optimizacion.depot;
  mapaActual = L.map("mapa").setView([depot.lat, depot.lon], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap",
  }).addTo(mapaActual);

  // Bodega
  const iconoDepot = L.divIcon({
    className: "",
    html: `<div class="marker-depot">B</div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
  L.marker([depot.lat, depot.lon], { icon: iconoDepot })
    .addTo(mapaActual)
    .bindPopup(`<b>${depot.nombre}</b><br>Inicio y fin de la ruta`);

  // Paradas numeradas en el orden de la ruta optimizada
  v.ruta.paradas.forEach((p, i) => {
    const icono = L.divIcon({
      className: "",
      html: `<div class="marker-parada">${i + 1}</div>`,
      iconSize: [26, 26],
      iconAnchor: [13, 13],
    });
    L.marker([p.lat, p.lon], { icon: icono })
      .addTo(mapaActual)
      .bindPopup(`<b>${i + 1}. ${p.nombre}</b>`);
  });

  // Linea del recorrido (bodega -> paradas -> bodega)
  const puntos = v.ruta.recorrido.map((u) => [u.lat, u.lon]);
  const linea = L.polyline(puntos, {
    color: "#1f6feb", weight: 4, opacity: 0.5, dashArray: "6 8",
  }).addTo(mapaActual);
  mapaActual.fitBounds(L.latLngBounds(puntos), { padding: [30, 30] });

  trazarRutaReal(v, linea);
}

/* Dibuja la ruta siguiendo las calles reales con el API OSRM.
   Si no hay conexion, deja la linea recta como respaldo. */
async function trazarRutaReal(v, linea) {
  const coords = v.ruta.recorrido.map((u) => `${u.lon},${u.lat}`).join(";");
  const url =
    `https://router.project-osrm.org/route/v1/driving/${coords}` +
    `?overview=full&geometries=geojson`;
  try {
    const resp = await fetch(url);
    const datos = await resp.json();
    if (datos.code === "Ok" && datos.routes && datos.routes[0]) {
      const geom = datos.routes[0].geometry.coordinates.map((c) => [c[1], c[0]]);
      linea.setLatLngs(geom);
      linea.setStyle({ opacity: 0.85, dashArray: null, color: "#1f6feb" });
    }
  } catch (e) {
    /* Sin conexion: se conserva la linea recta aproximada. */
  }
}

/* ------------------------- Inicio ------------------------- */
async function inicializar() {
  $("logo").innerHTML = svgVehiculo("Camion");
  $("placeholder-logo").innerHTML = svgVehiculo("Camion");

  try {
    const [cat, flota, paquetes, barrios] = await Promise.all([
      api("GET", "/api/catalogo"),
      api("GET", "/api/flota"),
      api("GET", "/api/paquetes"),
      api("GET", "/api/barrios"),
    ]);
    ESTADO.catalogo = cat.tipos;
    ESTADO.flota = flota.vehiculos;
    ESTADO.paquetes = paquetes;
    ESTADO.barrios = barrios.barrios;
    ESTADO.depot = barrios.depot;
  } catch (e) {
    aviso("No se pudo conectar con el servidor", "error");
    return;
  }

  renderCatalogo();
  renderBarrios();
  renderFlota();
  renderPaquetes();
  actualizarEstado();

  $("btn-agregar-flota").addEventListener("click", agregarFlota);
  $("btn-vaciar-flota").addEventListener("click", vaciarFlota);
  $("btn-agregar-personalizado").addEventListener("click", agregarPersonalizado);
  $("btn-generar").addEventListener("click", generarPaquetes);
  $("btn-cargar-csv").addEventListener("click", cargarCsv);
  $("btn-vaciar-paquetes").addEventListener("click", vaciarPaquetes);
  $("btn-insertar-paquete").addEventListener("click", insertarPaquete);
  $("btn-optimizar").addEventListener("click", optimizar);
}

document.addEventListener("DOMContentLoaded", inicializar);
