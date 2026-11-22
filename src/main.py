"""Punto de entrada para ejecutar el experimento completo."""

import argparse
import os

from .configuracion import JORNADA_MINUTOS, MODELOS
from .estadisticas import guardar_resultados
from .graficos import generar_graficos
from .simulacion import simular_replica


def ejecutar_experimento(replicas, semilla, duracion, carpeta_resultados):
    if replicas < 10:
        raise ValueError("Se requieren al menos 10 réplicas por configuración.")
    filas_replicas = []
    filas_cajas = []
    for indice_modelo, modelo in enumerate(MODELOS):
        for replica in range(1, replicas + 1):
            semilla_replica = semilla + indice_modelo * 1_000_003 + replica
            fila, cajas = simular_replica(
                modelo, replica, semilla_replica, duracion=duracion
            )
            filas_replicas.append(fila)
            filas_cajas.extend(cajas)

    resumen, _, comparacion = guardar_resultados(
        carpeta_resultados, filas_replicas, filas_cajas
    )
    generar_graficos(carpeta_resultados, filas_replicas, filas_cajas, comparacion)
    return resumen, comparacion


def main():
    parser = argparse.ArgumentParser(
        description="Simulación académica de colas bancarias con SimPy."
    )
    parser.add_argument("--replicas", type=int, default=10)
    parser.add_argument("--semilla", type=int, default=2026)
    parser.add_argument("--duracion", type=int, default=JORNADA_MINUTOS)
    parser.add_argument(
        "--salida",
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "resultados"),
    )
    argumentos = parser.parse_args()
    try:
        resumen, comparacion = ejecutar_experimento(
            argumentos.replicas,
            argumentos.semilla,
            argumentos.duracion,
            argumentos.salida,
        )
    except ValueError as error:
        parser.error(str(error))

    print("Resultados guardados en: {}".format(os.path.abspath(argumentos.salida)))
    print("\nResumen promedio por configuración:")
    for fila, comparacion_modelo in zip(resumen, comparacion):
        print(
            "- {}: llegados={:.1f}, atendidos={:.1f}, espera={:.3f} min, "
            "atención={:.3f} min, utilización media por caja={:.1f}%".format(
                fila["modelo"],
                fila["usuarios_llegados_promedio"],
                fila["usuarios_atendidos_promedio"],
                comparacion_modelo["espera_promedio_min"],
                comparacion_modelo["atencion_promedio_min"],
                comparacion_modelo["utilizacion_promedio_cajas_porcentaje"],
            )
        )


if __name__ == "__main__":
    main()
