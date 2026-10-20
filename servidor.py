"""Servidor web del sistema de entregas (solo libreria estandar).
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src import flota as mod_flota
from src import optimizacion_espacio as opt_espacio
from src import optimizacion_rutas as opt_rutas
from src import paquetes as mod_paquetes
from src.modelo import Paquete
from src.ubicaciones import BARRIOS, DEPOT
from src.utilidades import paquetes_a_paradas

WEB_DIR = os.path.join(BASE_DIR, "web")
PUERTO = 8000

# estado del sistema: se carga al arrancar y se actualiza con cada peticion
ESTADO = {
    "flota": mod_flota.Flota.cargar(),
    "paquetes": [],
}

if os.path.exists(mod_paquetes.RUTA_PAQUETES):
    try:
        ESTADO["paquetes"] = mod_paquetes.leer_csv()
    except Exception:
        ESTADO["paquetes"] = []


# Funciones para convertir los datos a JSON

def vehiculo_json(v):
    return {
        "id": v.id,
        "tipo": v.tipo,
        "peso_max": v.peso_max,
        "volumen": v.volumen,
        "area": v.area,
        "largo": v.largo,
        "ancho": v.ancho,
        "alto": v.alto,
    }


def paquete_json(p):
    return {
        "id": p.id,
        "tipo": p.tipo,
        "peso": p.peso,
        "alto": p.alto,
        "ancho": p.ancho,
        "profundo": p.profundo,
        "volumen": p.volumen,
        "barrio": p.barrio,
        "lat": p.lat,
        "lon": p.lon,
    }


def ubicacion_json(u):
    return {"nombre": u.nombre, "lat": u.lat, "lon": u.lon}


def _flota_json(flota):
    """Convierte todos los vehiculos de una flota a JSON."""
    lista = []
    for v in flota.vehiculos:
        lista.append(vehiculo_json(v))
    return lista


def _resumen_paquetes(paquetes):
    """Resumen de los paquetes, igual para el GET y el POST."""
    return {
        "total": len(paquetes),
        "peso_total": round(sum(p.peso for p in paquetes), 2),
        "volumen_total": round(sum(p.volumen for p in paquetes), 3),
        "items": [paquete_json(p) for p in paquetes],
    }


def construir_optimizacion():
    """Ejecuta el empaque y las rutas, y arma todo lo que necesita la interfaz."""
    flota = ESTADO["flota"]
    paquetes = ESTADO["paquetes"]

    resultado = opt_espacio.asignar_paquetes(paquetes, flota.vehiculos)

    vehiculos = {}
    for v in flota.vehiculos:
        vehiculos[v.id] = v

    vehiculos_out = []
    total_opt = 0.0
    total_orig = 0.0
    total_paquetes = 0

    for vid in resultado.asignacion:
        lista = resultado.asignacion[vid]
        if len(lista) == 0:
            continue
        v = vehiculos[vid]
        est = opt_espacio.estadisticas_vehiculo(v, lista)
        paradas = paquetes_a_paradas(lista)
        res = opt_rutas.optimizar_ruta(vid, paradas)
        total_opt = total_opt + res.distancia_optima
        total_orig = total_orig + res.distancia_original
        total_paquetes = total_paquetes + len(lista)

        recorrido = [DEPOT] + list(res.paradas) + [DEPOT]
        vehiculos_out.append({
            "id": v.id,
            "tipo": v.tipo,
            "stats": est,
            "zonas": resultado.zonas.get(vid, []),
            "paquetes": [paquete_json(p) for p in lista],
            "ruta": {
                "paradas": [ubicacion_json(u) for u in res.paradas],
                "recorrido": [ubicacion_json(u) for u in recorrido],
                "dist_original": round(res.distancia_original, 2),
                "dist_vecino": round(res.distancia_vecino, 2),
                "dist_optima": round(res.distancia_optima, 2),
                "ahorro_km": round(res.ahorro_km, 2),
                "ahorro_pct": res.ahorro_porcentaje,
            },
        })

    ahorro = total_orig - total_opt
    if total_orig > 0:
        pct = 100 * ahorro / total_orig
    else:
        pct = 0.0

    return {
        "depot": ubicacion_json(DEPOT),
        "vehiculos": vehiculos_out,
        "sin_asignar": [paquete_json(p) for p in resultado.sin_asignar],
        "totales": {
            "vehiculos_usados": len(vehiculos_out),
            "vehiculos_disponibles": len(flota.vehiculos),
            "paquetes_asignados": total_paquetes,
            "paquetes_total": len(paquetes),
            "dist_optima": round(total_opt, 2),
            "dist_original": round(total_orig, 2),
            "ahorro_km": round(ahorro, 2),
            "ahorro_pct": round(pct, 1),
        },
    }


# API

def api_get(ruta):
    """Atiende los GET de la API y devuelve (codigo, respuesta)."""
    if ruta == "/api/catalogo":
        tipos = []
        for tipo in mod_flota.CATALOGO:
            peso, largo, ancho, alto = mod_flota.CATALOGO[tipo]
            tipos.append({
                "tipo": tipo,
                "peso_max": peso,
                "volumen": round(largo * ancho * alto, 3),
                "area": round(largo * ancho, 3),
                "largo": largo,
                "ancho": ancho,
                "alto": alto,
            })
        return 200, {"tipos": tipos}

    if ruta == "/api/flota":
        return 200, {"vehiculos": _flota_json(ESTADO["flota"])}

    if ruta == "/api/paquetes":
        return 200, _resumen_paquetes(ESTADO["paquetes"])

    if ruta == "/api/barrios":
        barrios = [ubicacion_json(b) for b in BARRIOS]
        return 200, {"barrios": barrios, "depot": ubicacion_json(DEPOT)}

    if ruta == "/api/optimizar":
        return 200, construir_optimizacion()

    return 404, {"error": "ruta no encontrada"}


def api_post(ruta, datos):

    flota = ESTADO["flota"]

    if ruta == "/api/flota":
        accion = datos.get("accion")

        if accion == "agregar":
            tipo = datos.get("tipo")
            cantidad = int(datos.get("cantidad", 0))
            if tipo not in mod_flota.CATALOGO or cantidad <= 0:
                return 400, {"error": "tipo o cantidad invalidos"}
            flota.agregar_tipo(tipo, cantidad)
            flota.guardar()
            return 200, {"vehiculos": _flota_json(flota)}

        if accion == "personalizado":
            try:
                v = mod_flota.Vehiculo(
                    datos["id"], datos.get("tipo", "Personalizado"),
                    float(datos["peso_max"]), float(datos["largo"]),
                    float(datos["ancho"]), float(datos["alto"]),
                )
            except (KeyError, ValueError):
                return 400, {"error": "datos del vehiculo invalidos"}
            flota.agregar(v)
            flota.guardar()
            return 200, {"vehiculos": _flota_json(flota)}

        if accion == "eliminar":
            flota.eliminar(datos.get("id", ""))
            flota.guardar()
            return 200, {"vehiculos": _flota_json(flota)}

        if accion == "vaciar":
            flota.vehiculos.clear()
            flota.guardar()
            return 200, {"vehiculos": []}

        return 400, {"error": "accion no reconocida"}

    if ruta == "/api/paquetes":
        accion = datos.get("accion")

        if accion == "generar":
            cantidad = int(datos.get("cantidad", 0))
            semilla = datos.get("semilla")
            if semilla is None or semilla == "":
                semilla = None
            else:
                semilla = int(semilla)
            if cantidad <= 0:
                return 400, {"error": "cantidad invalida"}
            ESTADO["paquetes"] = mod_paquetes.generar_paquetes(cantidad, semilla)
            mod_paquetes.guardar_csv(ESTADO["paquetes"])

        elif accion == "cargar":
            try:
                ESTADO["paquetes"] = mod_paquetes.leer_csv()
            except FileNotFoundError:
                return 404, {"error": "no existe data/paquetes.csv"}

        elif accion == "insertar":
            try:
                pid = datos.get("id")
                if not pid:
                    pid = f"PKG-{len(ESTADO['paquetes']) + 1:05d}"
                p = Paquete(
                    id=pid,
                    tipo=datos.get("tipo", "Caja mediana"),
                    peso=float(datos["peso"]),
                    alto=float(datos["alto"]),
                    ancho=float(datos["ancho"]),
                    profundo=float(datos["profundo"]),
                    barrio=datos["barrio"],
                    lat=float(datos["lat"]),
                    lon=float(datos["lon"]),
                )
            except (KeyError, ValueError):
                return 400, {"error": "datos del paquete invalidos"}
            ESTADO["paquetes"].append(p)
            mod_paquetes.guardar_csv(ESTADO["paquetes"])

        elif accion == "vaciar":
            ESTADO["paquetes"] = []
            mod_paquetes.guardar_csv(ESTADO["paquetes"])

        else:
            return 400, {"error": "accion no reconocida"}

        return 200, _resumen_paquetes(ESTADO["paquetes"])

    return 404, {"error": "ruta no encontrada"}


# Servidor HTTP

TIPOS_MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


class Handler(BaseHTTPRequestHandler):
    """Atiende las peticiones HTTP de la API y de los archivos de web/."""

    def log_message(self, formato, *args):
        """Imprime cada peticion en la consola del servidor."""
        print(f"  {self.address_string()} - {formato % args}")

    def _enviar_json(self, codigo, obj):
        """Manda una respuesta JSON con el codigo HTTP indicado."""
        cuerpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _servir_estatico(self, ruta):
        """Sirve un archivo de web/ y evita salirse de esa carpeta."""
        if ruta == "/" or ruta == "":
            ruta = "/index.html"
        relativo = ruta.lstrip("/").replace("/", os.sep)
        ruta_abs = os.path.normpath(os.path.join(WEB_DIR, relativo))
        if not ruta_abs.startswith(WEB_DIR) or not os.path.isfile(ruta_abs):
            self._enviar_json(404, {"error": "archivo no encontrado"})
            return
        with open(ruta_abs, "rb") as f:
            contenido = f.read()
        self.send_response(200)
        ext = os.path.splitext(ruta_abs)[1].lower()
        mime = TIPOS_MIME.get(ext, "application/octet-stream")
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def do_GET(self):
        """Atiende los GET: si es de la API va a la API, si no a web/."""
        if self.path.startswith("/api/"):
            ruta = self.path.split("?")[0]
            codigo, obj = api_get(ruta)
            self._enviar_json(codigo, obj)
        else:
            self._servir_estatico(self.path)

    def do_POST(self):
        """Atiende los POST de la API."""
        if not self.path.startswith("/api/"):
            self._enviar_json(404, {"error": "ruta no encontrada"})
            return

        largo = int(self.headers.get("Content-Length", 0))
        if largo:
            crudo = self.rfile.read(largo)
        else:
            crudo = b"{}"
        try:
            texto = crudo.decode("utf-8")
            if texto == "":
                texto = "{}"
            datos = json.loads(texto)
        except json.JSONDecodeError:
            self._enviar_json(400, {"error": "JSON invalido"})
            return
        ruta = self.path.split("?")[0]
        codigo, obj = api_post(ruta, datos)
        self._enviar_json(codigo, obj)


def main():
    """Arranca el servidor y abre la interfaz en el navegador."""
    import threading
    import webbrowser

    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Handler)
    except OSError as e:
        print("=" * 64, flush=True)
        print(f"  [!] No se pudo iniciar el servidor en el puerto {PUERTO}.", flush=True)
        print(f"      Detalle: {e}", flush=True)
        print("      Cierre la otra ventana que este usando ese puerto", flush=True)
        print("      o cambie PUERTO en servidor.py.", flush=True)
        print("=" * 64, flush=True)
        input("  Presione ENTER para salir...")
        return

    url = f"http://127.0.0.1:{PUERTO}/"
    print("=" * 64, flush=True)
    print("  Empresa de Transporte y Entregas - Ibague", flush=True)
    print(f"  Servidor activo en {url}", flush=True)
    print("  Se abrira el navegador automaticamente.", flush=True)
    print("  Presione Ctrl+C para detener.", flush=True)
    print("=" * 64, flush=True)

    def abrir_navegador():
        webbrowser.open(url)

    threading.Timer(1.0, abrir_navegador).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.", flush=True)
        servidor.server_close()


if __name__ == "__main__":
    main()
