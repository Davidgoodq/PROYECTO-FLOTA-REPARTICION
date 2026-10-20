"""Gestion de la flota de vehiculos."""
import json
import os
from collections import Counter
from typing import Dict, List

from .modelo import Vehiculo

RUTA_FLOTA = os.path.join("data", "flota.json")

# Catalogo por defecto: tipo -> (peso_max_kg, largo, ancho, alto)
CATALOGO = {
    "Moto":          (25,   0.50, 0.40, 0.40),
    "Carro":         (200,  1.50, 1.20, 0.90),
    "Camioneta":     (800,  2.60, 1.70, 1.60),
    "Camion":        (3500, 5.00, 2.30, 2.20),
    "Camion grande": (9000, 8.00, 2.40, 2.50),
}


def crear_vehiculo(vehiculo_id: str, tipo: str) -> Vehiculo:
    """Crea un vehiculo usando las capacidades del catalogo."""
    if tipo not in CATALOGO:
        raise ValueError(f"Tipo de vehiculo desconocido: {tipo}")
    peso_max, largo, ancho, alto = CATALOGO[tipo]
    return Vehiculo(vehiculo_id, tipo, float(peso_max), largo, ancho, alto)


def catalogo_resumen() -> List[str]:
    """Devuelve una linea por tipo con su capacidad de peso y espacio."""
    lineas = []
    for tipo, (peso, largo, ancho, alto) in CATALOGO.items():
        vol = round(largo * ancho * alto, 2)
        area = round(largo * ancho, 2)
        lineas.append(
            f"  {tipo:<14} peso_max={peso:>5} kg  "
            f"espacio={vol:>6} m3 ({area} m2)"
        )
    return lineas


class Flota:
    """Conjunto de vehiculos disponibles para repartir las entregas."""

    def __init__(self, vehiculos: List[Vehiculo] = None):
        self.vehiculos: List[Vehiculo] = vehiculos or []

    def agregar(self, vehiculo: Vehiculo) -> None:
        """Agrega un vehiculo ya construido a la flota."""
        self.vehiculos.append(vehiculo)

    def agregar_tipo(self, tipo: str, cantidad: int) -> List[Vehiculo]:
        """Agrega `cantidad` vehiculos del tipo indicado con IDs consecutivos."""
        nuevos = []
        for _ in range(cantidad):
            vid = self._siguiente_id(tipo)
            v = crear_vehiculo(vid, tipo)
            self.vehiculos.append(v)
            nuevos.append(v)
        return nuevos

    def _siguiente_id(self, tipo: str) -> str:
        """Genera un ID legible y unico (ej. CG-01) a partir del tipo."""
        prefijo = "".join(p[0] for p in tipo.upper().split())[:3]
        n = sum(1 for v in self.vehiculos if v.tipo == tipo) + 1
        candidato = f"{prefijo}-{n:02d}"
        existentes = {v.id for v in self.vehiculos}
        while candidato in existentes:
            n += 1
            candidato = f"{prefijo}-{n:02d}"
        return candidato

    def eliminar(self, vehiculo_id: str) -> bool:
        """Elimina un vehiculo por ID. Devuelve True si existia."""
        v = next((v for v in self.vehiculos if v.id == vehiculo_id), None)
        if v is None:
            return False
        self.vehiculos.remove(v)
        return True

    def obtener(self, vehiculo_id: str) -> Vehiculo:
        """Devuelve el vehiculo con ese ID, o None si no existe."""
        return next((v for v in self.vehiculos if v.id == vehiculo_id), None)

    def __len__(self) -> int:
        return len(self.vehiculos)

    def resumen_por_tipo(self) -> Dict[str, int]:
        """Cantidad de vehiculos agrupada por tipo."""
        return dict(Counter(v.tipo for v in self.vehiculos))

    def guardar(self, ruta: str = RUTA_FLOTA) -> None:
        """Guarda la flota en JSON (crea la carpeta si no existe)."""
        os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
        datos = [
            {
                "id": v.id,
                "tipo": v.tipo,
                "peso_max": v.peso_max,
                "largo": v.largo,
                "ancho": v.ancho,
                "alto": v.alto,
            }
            for v in self.vehiculos
        ]
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

    @classmethod
    def cargar(cls, ruta: str = RUTA_FLOTA) -> "Flota":
        """Carga la flota desde JSON. Si el archivo no existe, devuelve una vacia."""
        if not os.path.exists(ruta):
            return cls()
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        flota = cls()
        for d in datos:
            flota.agregar(
                Vehiculo(
                    d["id"], d["tipo"], d["peso_max"],
                    d["largo"], d["ancho"], d["alto"],
                )
            )
        return flota
