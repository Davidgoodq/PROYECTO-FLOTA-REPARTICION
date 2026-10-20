"""Funciones de apoyo generales: calculo de distancias y formateo de salidas.
Todas las distancias se expresan en kilometros y se calculan con la formula
de Haversine sobre coordenadas de latitud/longitud.
"""
import math
from typing import List
from .modelo import Paquete, Ubicacion

RADIO_TIERRA_KM = 6371.0


def distancia_km(a: Ubicacion, b: Ubicacion) -> float:

    dlat = math.radians(b.lat - a.lat)
    dlon = math.radians(b.lon - a.lon)
    lat1 = math.radians(a.lat)
    lat2 = math.radians(b.lat)
    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * RADIO_TIERRA_KM * math.asin(math.sqrt(h))


def distancia_tour(ubicaciones: List[Ubicacion], regresar: bool = True) -> float:

    if len(ubicaciones) < 2:
        return 0.0
    total = sum(
        distancia_km(ubicaciones[i], ubicaciones[i + 1])
        for i in range(len(ubicaciones) - 1)
    )
    if regresar:
        total += distancia_km(ubicaciones[-1], ubicaciones[0])
    return total


def matriz_distancias(puntos: List[Ubicacion]) -> List[List[float]]:

    n = len(puntos)
    m = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = distancia_km(puntos[i], puntos[j])
            m[i][j] = d
            m[j][i] = d
    return m


def paquetes_a_paradas(paquetes: List[Paquete]) -> List[Ubicacion]:
    unicos = dict.fromkeys(
        (p.barrio, p.lat, p.lon) for p in paquetes
    )
    return [Ubicacion(nombre, lat, lon) for nombre, lat, lon in unicos]


def barra_porcentaje(valor: float, total: float, ancho: int = 20) -> str:

    if total <= 0:
        frac = 0.0
    else:
        frac = max(0.0, min(1.0, valor / total))
    llenos = int(round(frac * ancho))
    return "[" + "#" * llenos + "-" * (ancho - llenos) + f"] {frac * 100:5.1f}%"
