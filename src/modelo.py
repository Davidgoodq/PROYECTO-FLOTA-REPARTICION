"""Modelos de datos del sistema de entregas."""
from dataclasses import dataclass, field
from typing import List

@dataclass
class Ubicacion:
    """Un punto geografico identificado por nombre y coordenadas."""

    nombre: str
    lat: float
    lon: float

    def __str__(self) -> str:
        return f"{self.nombre} ({self.lat:.4f}, {self.lon:.4f})"


@dataclass
class Paquete:
    """Un paquete a entregar."""

    id: str
    tipo: str          # Sobre, Caja pequena, Caja mediana, Caja grande, Paquete voluminoso
    peso: float        # kg
    alto: float        # m
    ancho: float       # m
    profundo: float    # m
    barrio: str
    lat: float
    lon: float

    @property
    def volumen(self) -> float:
        """Volumen del paquete en metros cubicos."""
        return round(self.alto * self.ancho * self.profundo, 6)

    @property
    def area_base(self) -> float:
        """Area de la base del paquete en metros cuadrados."""
        return round(self.ancho * self.profundo, 6)

    @property
    def dimensiones_ordenadas(self) -> List[float]:
        """Dimensiones de mayor a menor, para comparar con el compartimento."""
        return sorted([self.alto, self.ancho, self.profundo], reverse=True)

    def __str__(self) -> str:
        return (
            f"{self.id} [{self.tipo}] {self.peso}kg "
            f"{self.alto}x{self.ancho}x{self.profundo}m -> {self.barrio}"
        )


@dataclass
class Vehiculo:
    """Un vehiculo de la flota.
    La capacidad de espacio se define por el compartimento de carga en metros
    (largo, ancho, alto), del que se derivan el volumen (m3) y el area (m2).
    """

    id: str
    tipo: str              # Moto, Carro, Camioneta, Camion, Camion grande
    peso_max: float        # kg
    largo: float           # m (compartimento)
    ancho: float           # m
    alto: float            # m

    @property
    def volumen(self) -> float:
        """Capacidad de carga en metros cubicos."""
        return round(self.largo * self.ancho * self.alto, 6)

    @property
    def area(self) -> float:
        """Area de piso del compartimento en metros cuadrados."""
        return round(self.largo * self.ancho, 6)

    @property
    def dimensiones_ordenadas(self) -> List[float]:
        """Dimensiones del compartimento de mayor a menor."""
        return sorted([self.largo, self.ancho, self.alto], reverse=True)

    def __str__(self) -> str:
        return (
            f"{self.id} [{self.tipo}] peso_max={self.peso_max}kg "
            f"espacio={self.volumen}m3 ({self.area}m2) "
            f"({self.largo}x{self.ancho}x{self.alto}m)"
        )


@dataclass
class ResultadoEmpaque:
    """Resultado de la optimizacion de espacio y peso.

    `asignacion` relaciona cada vehiculo usado con sus paquetes, `zonas`
    guarda los barrios atendidos por vehiculo y `sin_asignar` los paquetes
    que no cupieron en la flota.
    """

    asignacion: dict = field(default_factory=dict)      # vehiculo_id -> [Paquete]
    zonas: dict = field(default_factory=dict)           # vehiculo_id -> [barrio]
    sin_asignar: List[Paquete] = field(default_factory=list)


@dataclass
class ResultadoRuta:
    """Resultado de la optimizacion de ruta de un vehiculo.

    Conserva las distancias del orden original, del recorrido por vecino
    cercano y de la ruta final mejorada con 2-opt para comparar el ahorro.
    """

    vehiculo_id: str
    paradas: List[Ubicacion] = field(default_factory=list)
    orden_original: List[Ubicacion] = field(default_factory=list)
    distancia_original: float = 0.0
    distancia_vecino: float = 0.0
    distancia_optima: float = 0.0

    @property
    def ahorro_km(self) -> float:
        """Kilometros ahorrados frente al orden original de carga."""
        return round(self.distancia_original - self.distancia_optima, 3)

    @property
    def ahorro_porcentaje(self) -> float:
        """Porcentaje de ahorro respecto al orden original."""
        if self.distancia_original <= 0:
            return 0.0
        return round(100 * self.ahorro_km / self.distancia_original, 1)
