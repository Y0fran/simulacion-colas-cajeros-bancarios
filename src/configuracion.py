"""Parámetros y distribuciones del ejercicio bancario."""

from dataclasses import dataclass


JORNADA_MINUTOS = 480
PROPORCION_OPERACIONES = {"retiros": 0.70, "pagos": 0.30}


@dataclass(frozen=True)
class CategoriaUsuario:
    nombre: str
    media_servicio: float
    media_entre_llegadas: float
    probabilidad: float


CATEGORIAS = {
    "retiros": (
        CategoriaUsuario("rapido", 1, 1, 0.23),
        CategoriaUsuario("normal", 2, 2, 0.40),
        CategoriaUsuario("lento", 3, 3, 0.17),
        CategoriaUsuario("muy_lento", 4, 3, 0.20),
    ),
    "pagos": (
        CategoriaUsuario("rapido", 3, 1, 0.10),
        CategoriaUsuario("normal", 3, 2, 0.20),
        CategoriaUsuario("lento", 5, 3, 0.30),
        CategoriaUsuario("muy_lento", 7, 4, 0.40),
    ),
}

MODELOS = {
    "Modelo A": {"retiros": 1, "pagos": 2},
    "Modelo B": {"retiros": 2, "pagos": 1},
    "Modelo 4 cajas": {"retiros": 2, "pagos": 2},
}
