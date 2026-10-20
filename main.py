"""Sistema de entregas de paquetes - Empresa de transporte (Ibague).
"""

import os
import sys

from src import flota as mod_flota
from src import optimizacion_espacio as opt_espacio
from src import optimizacion_rutas as opt_rutas
from src import paquetes as mod_paquetes
from src.flota import Flota
from src.modelo import Paquete
from src.ubicaciones import BARRIOS, DEPOT
from src.utilidades import barra_porcentaje, paquetes_a_paradas

RUTA_REPORTE = os.path.join("salidas", "reporte_optimizacion.txt")

# datos que van cambiando mientras el usuario usa el menu
_flota = Flota.cargar()
_paquetes = []
_resultado_empaque = None


def limpiar():
    """Limpia la pantalla."""
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def pausar():
    """Espera a que el usuario presione ENTER."""
    input("\nPresione ENTER para continuar...")


def titulo(texto):
    """Imprime un titulo de seccion."""
    print("\n" + "=" * 68)
    print(f" {texto}")
    print("=" * 68)



# Menu principal

def menu():
    """Muestra el menu principal y llama la funcion de cada opcion."""
    while True:
        limpiar()
        titulo("EMPRESA DE TRANSPORTE Y ENTREGAS - IBAGUE")
        print(f"  Bodega (inicio/fin de rutas): {DEPOT}")
        print(f"  Vehiculos en flota: {len(_flota)}   |   "
              f"Paquetes cargados: {len(_paquetes)}")
        print("-" * 68)
        print("  1. Configurar flota (camiones / carros / motos)")
        print("  2. Gestionar paquetes (generar CSV, cargar, insertar)")
        print("  3. Ver flota")
        print("  4. Ver paquetes")
        print("  5. Optimizar espacio y peso de los vehiculos")
        print("  6. Optimizar rutas de entrega")
        print("  7. Optimizacion COMPLETA + guardar reporte")
        print("  0. Salir")
        print("-" * 68)
        opcion = input("  Seleccione una opcion: ").strip()

        if opcion == "1":
            menu_flota()
        elif opcion == "2":
            menu_paquetes()
        elif opcion == "3":
            ver_flota()
        elif opcion == "4":
            ver_paquetes()
        elif opcion == "5":
            optimizar_espacio()
        elif opcion == "6":
            optimizar_rutas()
        elif opcion == "7":
            optimizacion_completa(guardar=True)
        elif opcion == "0":
            print("\n  Hasta luego.\n")
            break
        else:
            print("\n  Opcion no valida.")
            pausar()

# Flota

def menu_flota():
    """Opciones para configurar la flota."""
    limpiar()
    titulo("CAPACIDADES DISPONIBLES (catalogo)")
    for linea in mod_flota.catalogo_resumen():
        print(linea)
    print("\n  Como desea configurar la flota?")
    print("  1. Agregar vehiculos por tipo (cantidad)")
    print("  2. Agregar vehiculo personalizado")
    print("  3. Vaciar flota")
    print("  4. Volver")
    opcion = input("  Opcion: ").strip()

    if opcion == "1":
        tipos = list(mod_flota.CATALOGO.keys())
        print("\n  Tipos disponibles:")
        for i in range(len(tipos)):
            print(f"    {i + 1}. {tipos[i]}")
        try:
            sel = int(input("  Tipo (numero): ").strip())
            cantidad = int(input("  Cantidad: ").strip())
            if sel >= 1 and sel <= len(tipos) and cantidad > 0:
                tipo = tipos[sel - 1]
                nuevos = _flota.agregar_tipo(tipo, cantidad)
                _flota.guardar()
                print(f"\n  Se agregaron {len(nuevos)} vehiculos de tipo '{tipo}'.")
            else:
                print("\n  Datos invalidos.")
        except ValueError:
            print("\n  Debe ingresar numeros.")
    elif opcion == "2":
        agregar_vehiculo_personalizado()
    elif opcion == "3":
        _flota.vehiculos.clear()
        _flota.guardar()
        print("\n  Flota vaciada.")
    pausar()


def agregar_vehiculo_personalizado():
    """Pide los datos de un vehiculo y lo agrega a la flota."""
    try:
        tipo = input("  Nombre del tipo (ej. Furgon): ").strip() or "Personalizado"
        vid = input("  ID del vehiculo (ej. V-01): ").strip() or "V-01"
        peso = float(input("  Peso maximo (kg): ").strip())
        largo = float(input("  Largo del compartimento (m): ").strip())
        ancho = float(input("  Ancho del compartimento (m): ").strip())
        alto = float(input("  Alto del compartimento (m): ").strip())
        v = mod_flota.Vehiculo(vid, tipo, peso, largo, ancho, alto)
        _flota.agregar(v)
        _flota.guardar()
        print(f"\n  Vehiculo agregado: {v}")
    except ValueError:
        print("\n  Datos invalidos.")


def ver_flota():
    """Muestra los vehiculos registrados y el resumen por tipo."""
    limpiar()
    titulo("FLOTA DE VEHICULOS")
    if len(_flota.vehiculos) == 0:
        print("  No hay vehiculos. Configure la flota en la opcion 1.")
        pausar()
        return

    print(f"  {'ID':<8}{'Tipo':<14}{'Peso max':>10}{'Espacio':>12}{'Area':>9}   Dimensiones")
    print("  " + "-" * 66)
    for v in _flota.vehiculos:
        print(f"  {v.id:<8}{v.tipo:<14}{v.peso_max:>8.0f}kg{v.volumen:>10.2f}m3"
              f"{v.area:>7.2f}m2   {v.largo}x{v.ancho}x{v.alto} m")

    print("\n  Resumen por tipo:")
    resumen = _flota.resumen_por_tipo()
    for tipo in resumen:
        cant = resumen[tipo]
        peso_total = 0.0
        vol_total = 0.0
        for v in _flota.vehiculos:
            if v.tipo == tipo:
                peso_total = peso_total + v.peso_max
                vol_total = vol_total + v.volumen
        print(f"    {tipo:<14} x{cant}  capacidad total: {peso_total:.0f} kg / "
              f"{vol_total:.2f} m3")
    pausar()

# Paquetes

def menu_paquetes():
    """Opciones para generar, cargar e insertar paquetes."""
    global _paquetes
    limpiar()
    titulo("GESTION DE PAQUETES")
    print("  1. Generar paquetes aleatorios y exportar a CSV")
    print("  2. Cargar paquetes desde data/paquetes.csv")
    print("  3. Insertar un paquete manualmente (con barrio de entrega)")
    print("  4. Ver barrios disponibles en Ibague")
    print("  5. Volver")
    opcion = input("  Opcion: ").strip()

    if opcion == "1":
        try:
            cantidad = int(input("  Cantidad de paquetes: ").strip())
            semilla_txt = input("  Semilla aleatoria (ENTER para aleatoria): ").strip()
            if semilla_txt == "":
                semilla = None
            else:
                semilla = int(semilla_txt)
            if cantidad > 0:
                _paquetes = mod_paquetes.generar_paquetes(cantidad, semilla)
                ruta = mod_paquetes.guardar_csv(_paquetes)
                print(f"\n  Se generaron {cantidad} paquetes en '{ruta}'.")
        except ValueError:
            print("\n  Debe ingresar numeros.")
    elif opcion == "2":
        try:
            _paquetes = mod_paquetes.leer_csv()
            print(f"\n  Se cargaron {len(_paquetes)} paquetes.")
        except FileNotFoundError:
            print("\n  No existe data/paquetes.csv. Genere primero.")
        except (ValueError, KeyError) as e:
            print(f"\n  Error al leer CSV: {e}")
    elif opcion == "3":
        insertar_paquete()
    elif opcion == "4":
        listar_barrios()
    pausar()


def insertar_paquete():
    """Inserta manualmente un paquete con su barrio de entrega."""
    global _paquetes
    print("\n  --- Insertar paquete manual ---")
    print("  Tipos: Sobre, Caja pequena, Caja mediana, Caja grande, Paquete voluminoso")
    try:
        pid = input("  ID (ENTER para automatico): ").strip()
        if pid == "":
            pid = f"PKG-{len(_paquetes) + 1:05d}"
        tipo = input("  Tipo: ").strip() or "Caja mediana"
        peso = float(input("  Peso (kg): ").strip())
        alto = float(input("  Alto (m): ").strip())
        ancho = float(input("  Ancho (m): ").strip())
        profundo = float(input("  Profundo (m): ").strip())
        barrio = elegir_barrio()
        if barrio is None:
            return
        nuevo = Paquete(pid, tipo, peso, alto, ancho, profundo,
                        barrio.nombre, barrio.lat, barrio.lon)
        _paquetes.append(nuevo)
        mod_paquetes.guardar_csv(_paquetes)
        print(f"\n  Paquete insertado: {nuevo}")
    except ValueError:
        print("\n  Datos invalidos.")


def elegir_barrio():
    """Busca un barrio por nombre (sin importar mayusculas) y lo devuelve."""
    nombre = input("  Barrio de entrega en Ibague: ").strip()
    for b in BARRIOS:
        if b.nombre.lower() == nombre.lower():
            return b
    print(f"\n  Barrio '{nombre}' no encontrado.")
    listar_barrios()
    return None


def listar_barrios():
    """Lista los barrios de Ibague que estan en el catalogo."""
    print("\n  Barrios de Ibague disponibles:")
    for i in range(len(BARRIOS)):
        print(f"    {i + 1:>2}. {BARRIOS[i].nombre}")


def ver_paquetes():
    """Muestra los paquetes cargados y los totales."""
    limpiar()
    titulo("PAQUETES CARGADOS")
    if len(_paquetes) == 0:
        print("  No hay paquetes. Genere o cargue en la opcion 2.")
        pausar()
        return

    peso_total = 0.0
    vol_total = 0.0
    for p in _paquetes:
        peso_total = peso_total + p.peso
        vol_total = vol_total + p.volumen
    print(f"  Total paquetes: {len(_paquetes)}   "
          f"Peso total: {peso_total:.2f} kg   Volumen total: {vol_total:.3f} m3")
    print("  " + "-" * 66)
    print(f"  {'ID':<11}{'Tipo':<20}{'Peso':>7}{'Dim (m)':>18}   Barrio")
    print("  " + "-" * 66)
    for p in _paquetes[:40]:
        dims = f"{p.alto}x{p.ancho}x{p.profundo}"
        print(f"  {p.id:<11}{p.tipo:<20}{p.peso:>6.2f}kg{dims:>18}   {p.barrio}")
    if len(_paquetes) > 40:
        print(f"  ... y {len(_paquetes) - 40} paquetes mas.")
    pausar()

# Optimizacion

def _verificar_datos():
    """Revisa que haya flota y paquetes antes de optimizar."""
    if len(_flota) == 0:
        print("\n  [!] La flota esta vacia. Configurela en la opcion 1.")
        return False
    if len(_paquetes) == 0:
        print("\n  [!] No hay paquetes. Generelos o cargue en la opcion 2.")
        return False
    return True


def optimizar_espacio():
    """Calcula y muestra como quedarian cargados los vehiculos."""
    global _resultado_empaque
    limpiar()
    titulo("OPTIMIZACION DE ESPACIO Y PESO")
    if not _verificar_datos():
        pausar()
        return

    _resultado_empaque = opt_espacio.asignar_paquetes(_paquetes, _flota.vehiculos)
    imprimir_empaque(_resultado_empaque)
    pausar()


def imprimir_empaque(resultado):
    """Imprime cuanto se lleno cada vehiculo y los paquetes que no cupieron."""
    vehiculos = {}
    for v in _flota.vehiculos:
        vehiculos[v.id] = v

    total_asignados = 0
    for lista in resultado.asignacion.values():
        total_asignados = total_asignados + len(lista)
    print(f"\n  Paquetes asignados: {total_asignados} / {len(_paquetes)}")
    print("  " + "-" * 66)

    for vid in resultado.asignacion:
        lista = resultado.asignacion[vid]
        v = vehiculos[vid]
        est = opt_espacio.estadisticas_vehiculo(v, lista)
        print(f"\n  {vid} [{v.tipo}]  {est['paquetes']} paquetes")
        print(f"    Peso   : {est['peso']:>8.2f} / {est['peso_max']:<8.0f} kg  "
              f"{barra_porcentaje(est['peso'], est['peso_max'])}")
        print(f"    Espacio: {est['volumen']:>8.3f} / {est['volumen_max']:<8.3f} m3 "
              f"{barra_porcentaje(est['volumen'], est['volumen_max'])}")
        zonas = resultado.zonas.get(vid, [])
        if len(zonas) > 0:
            print(f"    Zona(s): {', '.join(zonas)}")

    if len(resultado.sin_asignar) > 0:
        print(f"\n  [!] {len(resultado.sin_asignar)} paquetes NO cupieron en la flota:")
        for p in resultado.sin_asignar[:15]:
            print(f"      {p.id} {p.tipo} {p.peso}kg -> {p.barrio}")
        if len(resultado.sin_asignar) > 15:
            print(f"      ... y {len(resultado.sin_asignar) - 15} mas.")
    else:
        print("\n  [OK] Todos los paquetes fueron asignados.")


def _resultado_actual():
    """Devuelve el empaque y las rutas (calcula el empaque si falta)."""
    global _resultado_empaque
    if _resultado_empaque is None:
        _resultado_empaque = opt_espacio.asignar_paquetes(_paquetes, _flota.vehiculos)

    vehiculos = {}
    for v in _flota.vehiculos:
        vehiculos[v.id] = v

    rutas = []
    for vid in _resultado_empaque.asignacion:
        lista = _resultado_empaque.asignacion[vid]
        if len(lista) == 0:
            continue
        paradas = paquetes_a_paradas(lista)
        res = opt_rutas.optimizar_ruta(vid, paradas)
        rutas.append((vehiculos[vid], res))
    return _resultado_empaque, rutas


def optimizar_rutas():
    """Calcula y muestra las rutas optimizadas y el ahorro."""
    limpiar()
    titulo("OPTIMIZACION DE RUTAS")
    if not _verificar_datos():
        pausar()
        return

    resultado, rutas = _resultado_actual()
    if len(rutas) == 0:
        print("\n  No hay rutas por calcular (revise el empaque).")
        pausar()
        return

    dist_total = 0.0
    dist_orig = 0.0
    for v, res in rutas:
        print()
        for linea in opt_rutas.explicar_ruta(res, v.tipo):
            print(linea)
        dist_total = dist_total + res.distancia_optima
        dist_orig = dist_orig + res.distancia_original

    print("\n  " + "-" * 66)
    print(f"  DISTANCIA TOTAL OPTIMIZADA : {dist_total:.2f} km")
    print(f"  DISTANCIA SIN OPTIMIZAR    : {dist_orig:.2f} km")
    ahorro = dist_orig - dist_total
    if dist_orig > 0:
        pct = 100 * ahorro / dist_orig
    else:
        pct = 0
    print(f"  AHORRO TOTAL               : {ahorro:.2f} km ({pct:.1f}%)")
    pausar()


def optimizacion_completa(guardar=False):
    """Ejecuta empaque y rutas, muestra el informe y opcionalmente lo guarda."""
    limpiar()
    titulo("OPTIMIZACION COMPLETA (ESPACIO + PESO + RUTAS)")
    if not _verificar_datos():
        pausar()
        return

    resultado, rutas = _resultado_actual()

    lineas = []
    lineas.append("=" * 68)
    lineas.append(" REPORTE DE OPTIMIZACION - EMPRESA DE ENTREGAS IBAGUE")
    lineas.append("=" * 68)
    lineas.append(f" Bodega: {DEPOT}")
    lineas.append(f" Vehiculos: {len(_flota)}   Paquetes: {len(_paquetes)}")
    lineas.append("")
    lineas.append("--- ASIGNACION DE ESPACIO Y PESO ---")

    vehiculos = {}
    for v in _flota.vehiculos:
        vehiculos[v.id] = v
    for vid in resultado.asignacion:
        lista = resultado.asignacion[vid]
        v = vehiculos[vid]
        est = opt_espacio.estadisticas_vehiculo(v, lista)
        zonas = resultado.zonas.get(vid, [])
        lineas.append(
            f" {vid} [{v.tipo}]  paquetes={est['paquetes']}  "
            f"peso={est['peso']}/{est['peso_max']}kg ({est['peso_pct']}%)  "
            f"espacio={est['volumen']}/{est['volumen_max']}m3 ({est['volumen_pct']}%)"
        )
        if len(zonas) > 0:
            lineas.append(f"     zona(s): {', '.join(zonas)}")
    if len(resultado.sin_asignar) > 0:
        lineas.append(f" [!] Sin asignar: {len(resultado.sin_asignar)} paquetes")
    lineas.append("")

    lineas.append("--- RUTAS OPTIMIZADAS ---")
    dist_total = 0.0
    dist_orig = 0.0
    for v, res in rutas:
        lineas.extend(opt_rutas.explicar_ruta(res, v.tipo))
        lineas.append("")
        dist_total = dist_total + res.distancia_optima
        dist_orig = dist_orig + res.distancia_original

    ahorro = dist_orig - dist_total
    if dist_orig > 0:
        pct = 100 * ahorro / dist_orig
    else:
        pct = 0
    lineas.append("-" * 68)
    lineas.append(f" DISTANCIA TOTAL OPTIMIZADA : {dist_total:.2f} km")
    lineas.append(f" DISTANCIA SIN OPTIMIZAR    : {dist_orig:.2f} km")
    lineas.append(f" AHORRO TOTAL               : {ahorro:.2f} km ({pct:.1f}%)")
    lineas.append("=" * 68)

    texto = "\n".join(lineas)
    print("\n" + texto)

    if guardar:
        carpeta = os.path.dirname(RUTA_REPORTE)
        if carpeta == "":
            carpeta = "."
        os.makedirs(carpeta, exist_ok=True)
        with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
            f.write(texto)
        print(f"\n  Reporte guardado en '{RUTA_REPORTE}'")
    pausar()


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n\n  Interrumpido por el usuario.\n")
        sys.exit(0)
