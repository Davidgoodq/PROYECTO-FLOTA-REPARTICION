"""Optimizacion de espacio, peso y numero de vehiculos."""

from typing import Dict, List, Optional, Tuple
from .modelo import Paquete, ResultadoEmpaque, Ubicacion, Vehiculo
from .ubicaciones import DEPOT
from .utilidades import distancia_km

# Tolerancia para comparaciones de punto flotante (evita rechazos por redondeos).
_TOLERANCIA = 1e-9


def _capacidad(v: Vehiculo) -> Tuple[float, float]:
    """Clave de ordenamiento: (peso maximo, volumen) del vehiculo."""
    return (v.peso_max, v.volumen)


def _cabe(vehiculo: Vehiculo, peso_actual: float, vol_actual: float, paquete: Paquete) -> bool:
    """Indica si un paquete entra en el vehiculo dado el uso actual del mismo."""
    if peso_actual + paquete.peso > vehiculo.peso_max + _TOLERANCIA:
        return False
    if vol_actual + paquete.volumen > vehiculo.volumen + _TOLERANCIA:
        return False
    dims_pkg = paquete.dimensiones_ordenadas
    dims_veh = vehiculo.dimensiones_ordenadas
    return not any(p > v + _TOLERANCIA for p, v in zip(dims_pkg, dims_veh))


def _cabe_todo(vehiculo: Vehiculo, peso_actual: float, vol_actual: float, lista: List[Paquete]) -> bool:
    """Indica si TODA una lista de paquetes cabe en el vehiculo (sin repartir)."""
    if not lista:
        return True
    peso = peso_actual + sum(p.peso for p in lista)
    if peso > vehiculo.peso_max + _TOLERANCIA:
        return False
    vol = vol_actual + sum(p.volumen for p in lista)
    if vol > vehiculo.volumen + _TOLERANCIA:
        return False
    dims_veh = vehiculo.dimensiones_ordenadas
    for p in lista:
        if any(a > b + _TOLERANCIA for a, b in zip(p.dimensiones_ordenadas, dims_veh)):
            return False
    return True


def _ordenar_barrios_por_cercania(barrios: List[Ubicacion]) -> List[Ubicacion]:
    """Ordena los barrios con la heuristica del vecino mas cercano desde la bodega."""
    if not barrios:
        return []
    restantes = list(barrios)
    orden: List[Ubicacion] = []
    actual = DEPOT
    while restantes:
        siguiente = min(restantes, key=lambda u: distancia_km(actual, u))
        restantes.remove(siguiente)
        orden.append(siguiente)
        actual = siguiente
    return orden


def _grupos_por_zona(paquetes: List[Paquete]) -> List[Tuple[str, List[Paquete]]]:
    """Agrupa los paquetes por barrio y ordena las zonas por cercania a la bodega.

    Dentro de cada zona los paquetes van del mas grande al mas pequeno,
    lo que facilita rellenar mejor el espacio disponible.
    """
    por_barrio: Dict[str, List[Paquete]] = {}
    for p in paquetes:
        por_barrio.setdefault(p.barrio, []).append(p)

    ubicaciones = [
        Ubicacion(barrio, ps[0].lat, ps[0].lon)
        for barrio, ps in por_barrio.items()
    ]
    cadena = _ordenar_barrios_por_cercania(ubicaciones)

    return [
        (u.nombre, sorted(por_barrio[u.nombre], key=lambda p: p.volumen, reverse=True))
        for u in cadena
    ]


def _empaquetar_zonas(
    grupos: List[Tuple[str, List[Paquete]]],
    vehiculos: List[Vehiculo],
    permitir_sobrantes: bool = False,
) -> Tuple[Optional[Dict[str, List[Paquete]]], List[Paquete]]:
    """Empaqueta zona por zona (barrio completo) usando los vehiculos en orden.

    Los vehiculos se usan del mas capaz al menos capaz. Por cada zona se
    intenta, en este orden:

    1. Cargarla completa en el vehiculo actual.
    2. Cargarla completa en el siguiente vehiculo (sin partir el barrio).
    3. Repartirla paquete por paquete si aun asi no cabe en uno solo.

    Devuelve (asignacion, sobrantes). Si `permitir_sobrantes` es False y algo
    no cabe, devuelve (None, []) para indicar que esa combinacion no sirve.
    """
    if not vehiculos:
        if permitir_sobrantes:
            return {}, [p for _, ps in grupos for p in ps]
        return None, []

    vehs = sorted(vehiculos, key=_capacidad, reverse=True)
    asignacion: Dict[str, List[Paquete]] = {v.id: [] for v in vehs}
    # Uso acumulado de cada vehiculo: evita recalcular sumas en cada intento.
    peso_acum: Dict[str, float] = {v.id: 0.0 for v in vehs}
    vol_acum: Dict[str, float] = {v.id: 0.0 for v in vehs}
    sobrantes: List[Paquete] = []
    idx = 0  # indice del vehiculo en uso

    for _, lista in grupos:
        if not lista:
            continue
        actual = vehs[idx]
        id_actual = actual.id

        # 1) Todo el barrio entra en el vehiculo actual.
        if _cabe_todo(actual, peso_acum[id_actual], vol_acum[id_actual], lista):
            asignacion[id_actual].extend(lista)
            peso_acum[id_actual] += sum(p.peso for p in lista)
            vol_acum[id_actual] += sum(p.volumen for p in lista)
            continue

        # 2) No cabe en el actual: abrir el siguiente para el barrio completo
        #    (asi no se reparte el barrio entre dos vehiculos).
        if idx + 1 < len(vehs):
            siguiente = vehs[idx + 1]
            if _cabe_todo(siguiente, 0.0, 0.0, lista):
                idx += 1
                asignacion[siguiente.id].extend(lista)
                peso_acum[siguiente.id] += sum(p.peso for p in lista)
                vol_acum[siguiente.id] += sum(p.volumen for p in lista)
                continue

        # 3) El barrio por si solo no cabe en un vehiculo: hay que repartirlo.
        for p in lista:
            colocado = False
            while idx < len(vehs):
                v = vehs[idx]
                if _cabe(v, peso_acum[v.id], vol_acum[v.id], p):
                    asignacion[v.id].append(p)
                    peso_acum[v.id] += p.peso
                    vol_acum[v.id] += p.volumen
                    colocado = True
                    break
                idx += 1
            if not colocado:
                if permitir_sobrantes:
                    sobrantes.append(p)
                    idx = len(vehs) - 1
                else:
                    return None, []

    return asignacion, sobrantes


def _minimo_numero_vehiculos(
    grupos: List[Tuple[str, List[Paquete]]], vehiculos: List[Vehiculo]
) -> Optional[int]:
    """Menor cantidad de vehiculos capaces de atender todas las zonas.

    Usa busqueda binaria: si `k` vehiculos alcanzan, cualquier numero mayor
    tambien alcanza, por lo que no hace falta probar todos los valores.
    """
    desc = sorted(vehiculos, key=_capacidad, reverse=True)
    if not desc:
        return None

    izq, der = 1, len(desc)
    while izq < der:
        medio = (izq + der) // 2
        if _empaquetar_zonas(grupos, desc[:medio])[0] is not None:
            der = medio
        else:
            izq = medio + 1

    if _empaquetar_zonas(grupos, desc[:izq])[0] is not None:
        return izq
    return None


def _seleccionar_vehiculos(
    grupos: List[Tuple[str, List[Paquete]]], vehiculos: List[Vehiculo], k: int
) -> List[Vehiculo]:
    """Elige `k` vehiculos factibles con la MENOR capacidad total posible.

    Empieza con los `k` vehiculos mas pequenos y va reemplazando los de menor
    capacidad por otros mayores hasta que la carga entre.
    """
    asc = sorted(vehiculos, key=_capacidad)
    if k >= len(asc):
        return list(asc)

    seleccion = asc[:k]
    restantes = asc[k:]
    if _empaquetar_zonas(grupos, seleccion)[0] is not None:
        return seleccion

    while restantes:
        seleccion.pop(0)
        seleccion.append(restantes.pop(0))
        seleccion.sort(key=_capacidad)
        if _empaquetar_zonas(grupos, seleccion)[0] is not None:
            return seleccion
    return asc[-k:]


def asignar_paquetes(
    paquetes: List[Paquete],
    vehiculos: List[Vehiculo],
) -> ResultadoEmpaque:
    """Asigna los paquetes a la flota respetando zonas completas y minimizando vehiculos."""
    resultado = ResultadoEmpaque()

    if not vehiculos:
        resultado.sin_asignar = list(paquetes)
        return resultado
    if not paquetes:
        return resultado

    grupos = _grupos_por_zona(paquetes)

    k = _minimo_numero_vehiculos(grupos, vehiculos)
    if k is None:
        seleccion = list(vehiculos)
    else:
        seleccion = _seleccionar_vehiculos(grupos, vehiculos, k)

    asignacion, sobrantes = _empaquetar_zonas(grupos, seleccion, permitir_sobrantes=True)
    resultado.sin_asignar = sobrantes
    usadas = asignacion or {}

    # Solo se reportan los vehiculos realmente usados, del mas grande al mas pequeno.
    for v in sorted(seleccion, key=_capacidad, reverse=True):
        lista = usadas.get(v.id, [])
        if lista:
            resultado.asignacion[v.id] = lista
            resultado.zonas[v.id] = list(dict.fromkeys(p.barrio for p in lista))

    return resultado


def estadisticas_vehiculo(
    vehiculo: Vehiculo, paquetes: List[Paquete]
) -> Dict[str, float]:
    """Calcula la ocupacion de peso y espacio de un vehiculo con sus paquetes."""
    peso = sum(p.peso for p in paquetes)
    volumen = sum(p.volumen for p in paquetes)
    return {
        "paquetes": len(paquetes),
        "peso": round(peso, 2),
        "peso_max": vehiculo.peso_max,
        "peso_pct": round(100 * peso / vehiculo.peso_max, 1) if vehiculo.peso_max else 0,
        "volumen": round(volumen, 3),
        "volumen_max": vehiculo.volumen,
        "volumen_pct": round(100 * volumen / vehiculo.volumen, 1) if vehiculo.volumen else 0,
    }
