"""Agregación y exportación de las estadísticas de las réplicas."""

import csv
import os
from statistics import fmean

from .configuracion import CATEGORIAS, MODELOS


def _promedio(filas, campo):
    valores = [float(fila[campo]) for fila in filas]
    return fmean(valores) if valores else 0.0


def calcular_metricas_mm1(llegadas_lambda, servicio_mu):
    """Calcula métricas teóricas M/M/1 si ambas tasas permiten estabilidad."""
    if llegadas_lambda < 0 or servicio_mu <= 0:
        raise ValueError("Lambda debe ser no negativa y mu debe ser positiva.")
    if llegadas_lambda >= servicio_mu:
        raise ValueError("La cola M/M/1 no es estable: se requiere lambda < mu.")
    rho = llegadas_lambda / servicio_mu
    return {
        "lambda": llegadas_lambda,
        "mu": servicio_mu,
        "rho": rho,
        "L": llegadas_lambda / (servicio_mu - llegadas_lambda),
        "Lq": llegadas_lambda**2
        / (servicio_mu * (servicio_mu - llegadas_lambda)),
        "W": 1 / (servicio_mu - llegadas_lambda),
        "Wq": llegadas_lambda
        / (servicio_mu * (servicio_mu - llegadas_lambda)),
    }


def _escribir_csv(ruta, filas):
    if not filas:
        raise ValueError("No hay filas para escribir en {}".format(ruta))
    campos = list(dict.fromkeys(campo for fila in filas for campo in fila))
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)


def construir_resumen(filas_replicas, filas_cajas):
    resumen = []
    filas_tipos = []
    comparacion = []

    for modelo in MODELOS:
        replicas_modelo = [f for f in filas_replicas if f["modelo"] == modelo]
        cajas_modelo = [f for f in filas_cajas if f["modelo"] == modelo]
        fila = {
            "modelo": modelo,
            "replicas": len(replicas_modelo),
        }
        metricas = (
            "usuarios_llegados",
            "usuarios_atendidos",
            "esperando_al_cierre",
            "en_servicio_al_cierre",
            "espera_promedio_min",
            "atencion_promedio_min",
            "sistema_promedio_min",
        )
        for metrica in metricas:
            fila[metrica + "_promedio"] = _promedio(replicas_modelo, metrica)
        for operacion, categorias in CATEGORIAS.items():
            fila["llegados_{}_promedio".format(operacion)] = _promedio(
                replicas_modelo, "llegados_{}".format(operacion)
            )
            fila["atendidos_{}_promedio".format(operacion)] = _promedio(
                replicas_modelo, "atendidos_{}".format(operacion)
            )
            for categoria in categorias:
                campo = "{}_{}".format(operacion, categoria.nombre)
                fila[campo + "_promedio"] = _promedio(replicas_modelo, campo)

            filas_tipos.append(
                {
                    "modelo": modelo,
                    "operacion": operacion,
                    "usuarios_promedio_por_replica": fila[
                        "llegados_{}_promedio".format(operacion)
                    ],
                    **{
                        categoria.nombre + "_promedio": fila[
                            "{}_{}_promedio".format(operacion, categoria.nombre)
                        ]
                        for categoria in categorias
                    },
                }
            )
        utilizacion = _promedio(cajas_modelo, "utilizacion_porcentaje")
        atendidos_cajas = sum(float(f["usuarios_atendidos"]) for f in cajas_modelo) / len(
            replicas_modelo
        )
        fila["utilizacion_promedio_cajas_porcentaje"] = utilizacion
        fila["usuarios_atendidos_promedio_por_cajas"] = atendidos_cajas
        resumen.append(fila)

        cajas_agrupadas = {}
        for item in cajas_modelo:
            cajas_agrupadas.setdefault(item["caja"], []).append(item)
        medias_atencion = {
            caja: _promedio(
                [
                    item
                    for item in items
                    if float(item["usuarios_atendidos"]) > 0
                ],
                "atencion_promedio_min",
            )
            for caja, items in cajas_agrupadas.items()
            if any(float(item["usuarios_atendidos"]) > 0 for item in items)
        }
        if medias_atencion:
            caja_mayor = max(medias_atencion, key=medias_atencion.get)
            caja_menor = min(medias_atencion, key=medias_atencion.get)
        else:
            caja_mayor = caja_menor = ""

        comparacion.append(
            {
                "modelo": modelo,
                "espera_promedio_min": fila["espera_promedio_min_promedio"],
                "atencion_promedio_min": fila["atencion_promedio_min_promedio"],
                "sistema_promedio_min": fila["sistema_promedio_min_promedio"],
                "utilizacion_promedio_cajas_porcentaje": utilizacion,
                "usuarios_atendidos_promedio": fila["usuarios_atendidos_promedio"],
                "usuarios_llegados_promedio": fila["usuarios_llegados_promedio"],
                "caja_mayor_tiempo_atencion": caja_mayor,
                "mayor_tiempo_atencion_min": medias_atencion.get(caja_mayor, 0.0),
                "caja_menor_tiempo_atencion": caja_menor,
                "menor_tiempo_atencion_min": medias_atencion.get(caja_menor, 0.0),
                "nota_metodologica": (
                    "Aproximacion M/M/1 condicionada por categoria; el proceso "
                    "agregado no es una M/M/1 homogenea exacta."
                ),
                "nota_criterio_espera": (
                    "El ejercicio no especifica un maximo de espera aceptable; "
                    "la mejora debe interpretarse sin un umbral de servicio."
                ),
            }
        )

    espera_modelo_a = next(
        fila["espera_promedio_min"] for fila in comparacion if fila["modelo"] == "Modelo A"
    )
    for fila in comparacion:
        fila["diferencia_espera_vs_modelo_A_min"] = (
            fila["espera_promedio_min"] - espera_modelo_a
        )
    return resumen, filas_tipos, comparacion


def guardar_resultados(carpeta, filas_replicas, filas_cajas):
    os.makedirs(carpeta, exist_ok=True)
    resumen, tipos, comparacion = construir_resumen(filas_replicas, filas_cajas)
    _escribir_csv(os.path.join(carpeta, "resultados_por_replica.csv"), filas_replicas)
    _escribir_csv(os.path.join(carpeta, "resumen_general.csv"), resumen)
    _escribir_csv(os.path.join(carpeta, "estadisticas_por_cajero.csv"), filas_cajas)
    _escribir_csv(
        os.path.join(carpeta, "estadisticas_por_tipo_usuario.csv"), tipos
    )
    _escribir_csv(os.path.join(carpeta, "comparacion_modelos.csv"), comparacion)
    return resumen, tipos, comparacion
