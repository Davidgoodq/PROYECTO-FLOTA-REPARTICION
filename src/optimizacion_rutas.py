"""Optimizacion de rutas de entrega. """

from typing import List
from .modelo import ResultadoRuta, Ubicacion
from .ubicaciones import DEPOT
from .utilidades import distancia_tour, matriz_distancias


def _vecino_mas_cercano(dist: List[List[float]]) -> List[int]:

    n = len(dist)
    if n <= 1:
        return list(range(n))
    restantes = list(range(1, n))
    ruta = [0]
    actual = 0
    while restantes:
        siguiente = min(restantes, key=lambda j: dist[actual][j])
        restantes.remove(siguiente)
        ruta.append(siguiente)
        actual = siguiente
    return ruta


def _dos_opt(ruta: List[int], dist: List[List[float]]) -> List[int]:

    n = len(ruta)
    if n < 4:
        return list(ruta)

    mejorado = True
    while mejorado:
        mejorado = False
        for i in range(1, n - 1):
            for k in range(i + 1, n):
                a, b = ruta[i - 1], ruta[i]
                c = ruta[k]
                d = ruta[k + 1] if k + 1 < n else ruta[0]

                actual = dist[a][b] + dist[c][d]
                nuevo = dist[a][c] + dist[b][d]
                if nuevo + 1e-9 < actual:
                    ruta[i : k + 1] = reversed(ruta[i : k + 1])
                    mejorado = True
    return ruta


def optimizar_ruta(
    vehiculo_id: str,
    paradas: List[Ubicacion],
) -> ResultadoRuta:
    """Optimiza la ruta de un vehiculo y devuelve el detalle comparativo."""
    resultado = ResultadoRuta(vehiculo_id=vehiculo_id)

    if not paradas:
        return resultado

    # Orden original: bodega + paradas + bodega (en el orden en que se cargaron)
    original = [DEPOT] + list(paradas) + [DEPOT]
    resultado.orden_original = list(paradas)
    resultado.distancia_original = distancia_tour(original, regresar=False)

    # Matriz unica para todos los calculos de esta ruta (bodega + paradas).
    puntos = [DEPOT] + list(paradas)
    dist = matriz_distancias(puntos)
    
    tour_vecino = _vecino_mas_cercano(dist)
    resultado.distancia_vecino = distancia_tour(
        [puntos[i] for i in tour_vecino], regresar=True
    )

    tour_optimo = _dos_opt(tour_vecino, dist)
    ruta_optima = [puntos[i] for i in tour_optimo]
    resultado.distancia_optima = distancia_tour(ruta_optima, regresar=True)
    resultado.paradas = ruta_optima[1:]  # sin el deposito inicial

    return resultado


def explicar_ruta(resultado: ResultadoRuta, nombre_vehiculo: str) -> List[str]:
    """Genera las lineas que explican por que se eligio esa ruta."""
    orden = " -> ".join(
        [DEPOT.nombre] + [p.nombre for p in resultado.paradas] + [DEPOT.nombre]
    )
    return [
        f"  Ruta optimizada para {resultado.vehiculo_id} ({nombre_vehiculo}):",
        f"    Recorrido: {orden}",
        f"    Distancia orden de carga : {resultado.distancia_original:7.2f} km",
        f"    Distancia vecino cercano  : {resultado.distancia_vecino:7.2f} km",
        f"    Distancia optima (2-opt)  : {resultado.distancia_optima:7.2f} km",
        f"    AHORRO: {resultado.ahorro_km:.2f} km "
        f"({resultado.ahorro_porcentaje}% menos recorrido que el orden de carga)",
        "    Por que esta ruta: se visita primero el barrio mas cercano a la "
        "bodega y luego se encadenan los mas proximos entre si, evitando "
        "cruces; asi el vehiculo recorre menos kilometros y es mas eficiente.",
    ]
