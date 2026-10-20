"""Generacion y persistencia de paquetes.
"""

import csv
import os
import random
from typing import List

from .modelo import Paquete
from .ubicaciones import BARRIOS, barrio_mas_cercano, obtener_barrio_flexible

RUTA_PAQUETES = os.path.join("data", "paquetes.csv")

CAMPOS = [
    "id", "tipo", "peso_kg", "alto_m", "ancho_m", "profundo_m",
    "volumen_m3", "barrio", "lat", "lon",
]

# tipo -> (peso_min, peso_max, dim_min, dim_max)  (dimensiones en metros)
TIPOS = {
    "Sobre":              (0.05, 0.5, 0.22, 0.35),
    "Caja pequena":       (0.5, 3.0, 0.20, 0.35),
    "Caja mediana":       (3.0, 12.0, 0.35, 0.55),
    "Caja grande":        (12.0, 30.0, 0.50, 0.80),
    "Paquete voluminoso": (2.0, 15.0, 0.70, 1.20),
}

# Probabilidad relativa de cada tipo al generar paquetes aleatorios.
_PESOS_TIPO = {
    "Sobre": 30,
    "Caja pequena": 30,
    "Caja mediana": 20,
    "Caja grande": 15,
    "Paquete voluminoso": 5,
}


def _dimensiones_para(tipo: str, rng: random.Random):
    """Genera alto, ancho y profundo coherentes con el tipo de paquete."""
    if tipo == "Sobre":
        # Los sobres son planos: una de sus dimensiones es muy pequena.
        lado1 = round(rng.uniform(0.20, 0.32), 2)
        lado2 = round(rng.uniform(0.15, 0.25), 2)
        grueso = round(rng.uniform(0.01, 0.05), 2)
        return lado1, lado2, grueso
    _, _, dmin, dmax = TIPOS[tipo]
    dims = sorted(
        (round(rng.uniform(dmin, dmax), 2) for _ in range(3)),
        reverse=True,
    )
    return dims[0], dims[1], dims[2]


def generar_paquetes(cantidad: int, semilla: int = None) -> List[Paquete]:

    rng = random.Random(semilla)
    tipos = list(_PESOS_TIPO.keys())
    pesos = list(_PESOS_TIPO.values())
    paquetes: List[Paquete] = []
    for i in range(1, cantidad + 1):
        tipo = rng.choices(tipos, weights=pesos, k=1)[0]
        pmin, pmax, _, _ = TIPOS[tipo]
        peso = round(rng.uniform(pmin, pmax), 2)
        alto, ancho, profundo = _dimensiones_para(tipo, rng)
        barrio = rng.choice(BARRIOS)
        paquetes.append(
            Paquete(
                id=f"PKG-{i:05d}",
                tipo=tipo,
                peso=peso,
                alto=alto,
                ancho=ancho,
                profundo=profundo,
                barrio=barrio.nombre,
                lat=barrio.lat,
                lon=barrio.lon,
            )
        )
    return paquetes


def guardar_csv(paquetes: List[Paquete], ruta: str = RUTA_PAQUETES) -> str:
    """Guarda la lista de paquetes en un archivo CSV y devuelve la ruta."""
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writeheader()
        for p in paquetes:
            escritor.writerow(
                {
                    "id": p.id,
                    "tipo": p.tipo,
                    "peso_kg": p.peso,
                    "alto_m": p.alto,
             
                    "ancho_m": p.ancho,
                    "profundo_m": p.profundo,
                    "volumen_m3": p.volumen,
                    "barrio": p.barrio,
                    "lat": p.lat,
                    "lon": p.lon,
                }
            )
    return ruta


def leer_csv(ruta: str = RUTA_PAQUETES) -> List[Paquete]:

    paquetes: List[Paquete] = []
    with open(ruta, "r", newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            ubic = obtener_barrio_flexible(fila["barrio"])
            if ubic is None:
                ubic = barrio_mas_cercano(float(fila["lat"]), float(fila["lon"]))
            paquetes.append(
                Paquete(
                    id=fila["id"],
                    tipo=fila["tipo"],
                    peso=float(fila["peso_kg"]),
                    alto=float(fila["alto_m"]),
                    ancho=float(fila["ancho_m"]),
                    profundo=float(fila["profundo_m"]),
                    barrio=ubic.nombre,
                    lat=ubic.lat,
                    lon=ubic.lon,
                )
            )
    return paquetes
