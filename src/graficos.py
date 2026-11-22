"""Generación de gráficos comparativos en formato PNG."""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .configuracion import MODELOS


def generar_graficos(carpeta, filas_replicas, filas_cajas, comparacion):
    os.makedirs(carpeta, exist_ok=True)
    colores = ("#2878B5", "#F28E2B", "#59A14F")

    nombres = [fila["modelo"] for fila in comparacion]
    esperas = [fila["espera_promedio_min"] for fila in comparacion]
    figura, eje = plt.subplots(figsize=(8, 5))
    eje.bar(nombres, esperas, color=colores[: len(nombres)])
    eje.set_title("Tiempo promedio de espera por configuración")
    eje.set_ylabel("Espera promedio (minutos)")
    eje.set_xlabel("Configuración")
    eje.tick_params(axis="x", rotation=15)
    figura.tight_layout()
    figura.savefig(os.path.join(carpeta, "comparacion_tiempo_espera.png"), dpi=150)
    plt.close(figura)

    for campo, titulo, eje_y, nombre_archivo in (
        (
            "atencion_promedio_min",
            "Tiempo promedio de atención por caja",
            "Atención promedio (minutos)",
            "tiempo_atencion_por_cajero.png",
        ),
        (
            "utilizacion_porcentaje",
            "Utilización de las cajas",
            "Utilización (%)",
            "utilizacion_cajas.png",
        ),
    ):
        etiquetas = []
        valores = []
        for modelo in MODELOS:
            cajas_modelo = [f for f in filas_cajas if f["modelo"] == modelo]
            nombres_caja = sorted({f["caja"] for f in cajas_modelo})
            for caja in nombres_caja:
                items = [f for f in cajas_modelo if f["caja"] == caja]
                muestras = [float(item[campo]) for item in items]
                if campo == "atencion_promedio_min":
                    muestras = [
                        float(item[campo])
                        for item in items
                        if float(item["usuarios_atendidos"]) > 0
                    ]
                etiquetas.append("{}\n{}".format(modelo, caja.replace("Caja ", "")))
                valores.append(sum(muestras) / len(muestras) if muestras else 0.0)
        figura, eje = plt.subplots(figsize=(max(9, len(etiquetas) * 0.9), 5))
        eje.bar(etiquetas, valores, color=colores[0])
        eje.set_title(titulo)
        eje.set_ylabel(eje_y)
        eje.set_xlabel("Caja (configuración)")
        eje.tick_params(axis="x", labelrotation=55, labelsize=8)
        figura.tight_layout()
        figura.savefig(os.path.join(carpeta, nombre_archivo), dpi=150)
        plt.close(figura)

    operaciones = ("retiros", "pagos")
    modelos = list(MODELOS)
    figura, eje = plt.subplots(figsize=(8, 5))
    ancho = 0.25
    posiciones = list(range(len(modelos)))
    for indice, operacion in enumerate(operaciones):
        valores = [
            sum(
                float(fila["atendidos_" + operacion])
                for fila in filas_replicas
                if fila["modelo"] == modelo
            )
            / sum(1 for fila in filas_replicas if fila["modelo"] == modelo)
            for modelo in modelos
        ]
        desplazamiento = (indice - (len(operaciones) - 1) / 2) * ancho
        eje.bar(
            [posicion + desplazamiento for posicion in posiciones],
            valores,
            width=ancho,
            label=operacion.capitalize(),
        )
    eje.set_title("Promedio de usuarios atendidos por tipo de operación")
    eje.set_ylabel("Usuarios por jornada (promedio)")
    eje.set_xlabel("Configuración")
    eje.set_xticks(posiciones, modelos)
    eje.legend(title="Operación")
    figura.tight_layout()
    figura.savefig(
        os.path.join(carpeta, "usuarios_atendidos_por_operacion.png"), dpi=150
    )
    plt.close(figura)
