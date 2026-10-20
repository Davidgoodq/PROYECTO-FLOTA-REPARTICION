"""Ubicaciones de Ibague (barrios) y centro de reparto.
Las coordenadas provienen del geocodificador de OpenStreetMap (Nominatim)
y se usan tanto para calcular distancias como para dibujar el mapa.
"""

import unicodedata

from .modelo import Ubicacion
from .utilidades import distancia_km

# Bodega / centro de distribucion: punto de partida y llegada de cada ruta.
DEPOT = Ubicacion("Terminal de Transportes de Ibague", 4.4368081, -75.2343496)

# Barrios de Ibague con coordenadas reales (lat, lon).
_BARRIOS_RAW = [
    ("Ambalá", 4.4487784, -75.2010857),
    ("Aparco", 4.4072343, -75.1665164),
    ("Balcones de la Florida", 4.43, -75.18432),
    ("Belén", 4.4511451, -75.2430563),
    ("Boquerón", 4.420078, -75.2541567),
    ("Calambeo", 4.4585282, -75.2247203),
    ("Centro", 4.4419935, -75.2366416),
    ("Cádiz", 4.4374289, -75.2184787),
    ("El Carmen", 4.4432851, -75.2326318),
    ("El Salado", 4.4484691, -75.1439067),
    ("El Vergel", 4.4510754, -75.1963388),
    ("Galarza", 4.4296863, -75.2370092),
    ("Hipódromo", 4.4391654, -75.2251236),
    ("Jordán", 4.4412533, -75.1960645),
    ("La Campiña", 4.4427815, -75.1908952),
    ("La Esperanza", 4.4437582, -75.2251108),
    ("La Floresta", 4.4484598, -75.1619884),
    ("La Macarena", 4.433545, -75.2145159),
    ("La Pola", 4.4471598, -75.2449543),
    ("Las Américas", 4.4086996, -75.1455597),
    ("Las Delicias", 4.4603265, -75.2007237),
    ("Las Ferias", 4.4316183, -75.231525),
    ("Mirolindo", 4.42919, -75.20737),
    ("Nuevo Horizonte", 4.4073923, -75.1593838),
    ("Picaleña", 4.4299555, -75.1929699),
    ("Piedra Pintada", 4.4343606, -75.2082652),
    ("Prado", 4.4398, -75.1993),
    ("Ricaurte", 4.4314989, -75.2439481),
    ("San Antonio", 4.4328839, -75.2250919),
    ("San Jorge", 4.4476186, -75.2254375),
    ("San Simón", 4.4385922, -75.2185317),
    ("Santa Ana", 4.4444335, -75.1655025),
    ("Villa Café", 4.4278304, -75.1896986),
    ("Yuldaima", 4.4355243, -75.2403883),
]

BARRIOS = [Ubicacion(nombre, lat, lon) for nombre, lat, lon in _BARRIOS_RAW]


def normalizar(texto: str) -> str:
    """Convierte a minusculas y elimina tildes para comparar nombres."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.strip().lower()


# Indice por nombre normalizado: permite buscar "ambala" y encontrar "Ambalá".
_BARRIOS_POR_NOMBRE_NORM = {normalizar(b.nombre): b for b in BARRIOS}


def obtener_barrio_flexible(nombre: str):
    """Busca un barrio ignorando mayusculas y tildes. Devuelve None si no existe."""
    return _BARRIOS_POR_NOMBRE_NORM.get(normalizar(nombre))


def barrio_mas_cercano(lat: float, lon: float) -> Ubicacion:
    """Devuelve el barrio real mas cercano a unas coordenadas dadas."""
    destino = Ubicacion("_", lat, lon)
    return min(BARRIOS, key=lambda b: distancia_km(destino, b))
