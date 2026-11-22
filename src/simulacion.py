"""Simulación de eventos discretos del banco mediante SimPy."""

from dataclasses import dataclass
import random

import simpy

from .configuracion import CATEGORIAS, MODELOS, PROPORCION_OPERACIONES


@dataclass
class Usuario:
    identificador: int
    operacion: str
    categoria: str
    llegada: float
    servicio: float
    caja: str
    inicio_servicio: float
    fin_servicio: float


@dataclass
class Caja:
    identificador: str
    operacion: str
    disponible_en: float = 0.0
    usuarios: list | None = None

    def __post_init__(self):
        if self.usuarios is None:
            self.usuarios = []


def _promedio(valores):
    return sum(valores) / len(valores) if valores else 0.0


def simular_replica(modelo, replica, semilla, duracion=480):
    """Ejecuta una réplica y devuelve métricas globales y por caja."""
    if modelo not in MODELOS:
        raise ValueError("Modelo desconocido: {}".format(modelo))
    if duracion <= 0:
        raise ValueError("La duración debe ser positiva.")

    generador = random.Random(semilla)
    entorno = simpy.Environment()
    cajas = []
    for operacion, cantidad in MODELOS[modelo].items():
        for numero in range(1, cantidad + 1):
            nombre = "Caja {} {}".format(operacion, numero)
            cajas.append(Caja(nombre, operacion))

    usuarios = []
    cajas_por_operacion = {
        operacion: [caja for caja in cajas if caja.operacion == operacion]
        for operacion in PROPORCION_OPERACIONES
    }

    def atender(usuario, inicio):
        yield entorno.timeout(max(0.0, inicio - entorno.now))
        yield entorno.timeout(usuario.servicio)

    def generar_llegadas():
        identificador = 0
        while True:
            operacion = generador.choices(
                list(PROPORCION_OPERACIONES),
                weights=list(PROPORCION_OPERACIONES.values()),
                k=1,
            )[0]
            categorias = CATEGORIAS[operacion]
            categoria = generador.choices(
                categorias, weights=[item.probabilidad for item in categorias], k=1
            )[0]
            intervalo = generador.expovariate(1 / categoria.media_entre_llegadas)
            yield entorno.timeout(intervalo)
            if entorno.now > duracion:
                break

            identificador += 1
            servicio = generador.expovariate(1 / categoria.media_servicio)
            caja = min(
                cajas_por_operacion[operacion],
                key=lambda item: (max(0.0, item.disponible_en - entorno.now),
                                  cajas.index(item)),
            )
            inicio = max(entorno.now, caja.disponible_en)
            fin = inicio + servicio
            caja.disponible_en = fin
            usuario = Usuario(
                identificador=identificador,
                operacion=operacion,
                categoria=categoria.nombre,
                llegada=entorno.now,
                servicio=servicio,
                caja=caja.identificador,
                inicio_servicio=inicio,
                fin_servicio=fin,
            )
            caja.usuarios.append(usuario)
            usuarios.append(usuario)
            entorno.process(atender(usuario, inicio))

    entorno.process(generar_llegadas())
    entorno.run(until=duracion)

    atendidos = [usuario for usuario in usuarios if usuario.fin_servicio <= duracion]
    esperando_cierre = [
        usuario for usuario in usuarios if usuario.inicio_servicio >= duracion
    ]
    en_servicio_cierre = [
        usuario
        for usuario in usuarios
        if usuario.inicio_servicio < duracion < usuario.fin_servicio
    ]
    tiempos_espera = {
        usuario.identificador: usuario.inicio_servicio - usuario.llegada
        for usuario in usuarios
    }

    conteos = {
        operacion: {
            categoria.nombre: sum(
                1
                for usuario in usuarios
                if usuario.operacion == operacion
                and usuario.categoria == categoria.nombre
            )
            for categoria in CATEGORIAS[operacion]
        }
        for operacion in CATEGORIAS
    }
    atendidos_por_operacion = {
        operacion: sum(
            1 for usuario in atendidos if usuario.operacion == operacion
        )
        for operacion in CATEGORIAS
    }

    fila_replica = {
        "modelo": modelo,
        "replica": replica,
        "duracion_minutos": duracion,
        "usuarios_llegados": len(usuarios),
        "usuarios_atendidos": len(atendidos),
        "esperando_al_cierre": len(esperando_cierre),
        "en_servicio_al_cierre": len(en_servicio_cierre),
        "espera_promedio_min": _promedio(
            [tiempos_espera[u.identificador] for u in atendidos]
        ),
        "atencion_promedio_min": _promedio([u.servicio for u in atendidos]),
        "sistema_promedio_min": _promedio(
            [u.fin_servicio - u.llegada for u in atendidos]
        ),
    }
    for operacion in CATEGORIAS:
        fila_replica["llegados_{}".format(operacion)] = sum(conteos[operacion].values())
        fila_replica["atendidos_{}".format(operacion)] = atendidos_por_operacion[
            operacion
        ]
        for categoria in CATEGORIAS[operacion]:
            fila_replica["{}_{}".format(operacion, categoria.nombre)] = conteos[
                operacion
            ][categoria.nombre]

    filas_cajas = []
    for caja in cajas:
        usuarios_caja = caja.usuarios
        completados_caja = [
            usuario for usuario in usuarios_caja if usuario.fin_servicio <= duracion
        ]
        usuarios_esperando = [
            usuario
            for usuario in usuarios_caja
            if usuario.inicio_servicio >= duracion
        ]
        usuarios_en_servicio = [
            usuario
            for usuario in usuarios_caja
            if usuario.inicio_servicio < duracion < usuario.fin_servicio
        ]
        ocupado = sum(
            max(0.0, min(usuario.fin_servicio, duracion) - usuario.inicio_servicio)
            for usuario in usuarios_caja
            if usuario.inicio_servicio < duracion
        )
        filas_cajas.append(
            {
                "modelo": modelo,
                "replica": replica,
                "caja": caja.identificador,
                "operacion": caja.operacion,
                "usuarios_atendidos": len(completados_caja),
                "atencion_promedio_min": _promedio(
                    [u.servicio for u in completados_caja]
                ),
                "espera_promedio_min": _promedio(
                    [tiempos_espera[u.identificador] for u in completados_caja]
                ),
                "sistema_promedio_min": _promedio(
                    [u.fin_servicio - u.llegada for u in completados_caja]
                ),
                "utilizacion_porcentaje": ocupado / duracion * 100,
                "esperando_al_cierre": len(usuarios_esperando),
                "en_servicio_al_cierre": len(usuarios_en_servicio),
            }
        )
        fila_replica[
            "utilizacion_{}_porcentaje".format(caja.identificador.replace(" ", "_"))
        ] = ocupado / duracion * 100

    return fila_replica, filas_cajas
