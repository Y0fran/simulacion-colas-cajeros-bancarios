import csv
import os
import tempfile
import unittest

from src.configuracion import CATEGORIAS, MODELOS
from src.estadisticas import calcular_metricas_mm1
from src.main import ejecutar_experimento
from src.simulacion import simular_replica


class PruebasSimulacion(unittest.TestCase):
    def test_probabilidades_y_tiempos_son_validos(self):
        for categorias in CATEGORIAS.values():
            self.assertAlmostEqual(sum(c.probabilidad for c in categorias), 1.0)
            for categoria in categorias:
                self.assertGreater(categoria.media_servicio, 0)
                self.assertGreater(categoria.media_entre_llegadas, 0)

    def test_modelos_tienen_tres_o_cuatro_cajas(self):
        self.assertEqual(sum(MODELOS["Modelo A"].values()), 3)
        self.assertEqual(sum(MODELOS["Modelo B"].values()), 3)
        self.assertEqual(sum(MODELOS["Modelo 4 cajas"].values()), 4)

    def test_metricas_mm1_y_condicion_de_estabilidad(self):
        metricas = calcular_metricas_mm1(2, 3)
        self.assertAlmostEqual(metricas["rho"], 2 / 3)
        self.assertAlmostEqual(metricas["L"], 2)
        with self.assertRaises(ValueError):
            calcular_metricas_mm1(3, 3)

    def test_replica_se_ejecuta_y_conserva_usuarios(self):
        fila, cajas = simular_replica("Modelo A", 1, 1234, duracion=60)
        self.assertEqual(len(cajas), 3)
        self.assertEqual(
            fila["usuarios_llegados"],
            fila["usuarios_atendidos"]
            + fila["esperando_al_cierre"]
            + fila["en_servicio_al_cierre"],
        )
        for caja in cajas:
            self.assertGreaterEqual(caja["utilizacion_porcentaje"], 0)
            self.assertLessEqual(caja["utilizacion_porcentaje"], 100)

    def test_experimento_genera_csv_y_graficos(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ejecutar_experimento(10, 81, 45, carpeta)
            esperados = (
                "resultados_por_replica.csv",
                "resumen_general.csv",
                "estadisticas_por_cajero.csv",
                "estadisticas_por_tipo_usuario.csv",
                "comparacion_modelos.csv",
                "comparacion_tiempo_espera.png",
                "tiempo_atencion_por_cajero.png",
                "utilizacion_cajas.png",
                "usuarios_atendidos_por_operacion.png",
            )
            for nombre in esperados:
                with self.subTest(archivo=nombre):
                    self.assertTrue(os.path.isfile(os.path.join(carpeta, nombre)))
                    self.assertGreater(os.path.getsize(os.path.join(carpeta, nombre)), 0)
            with open(
                os.path.join(carpeta, "resultados_por_replica.csv"),
                newline="",
                encoding="utf-8",
            ) as archivo:
                filas = list(csv.DictReader(archivo))
            self.assertEqual(len(filas), 30)


if __name__ == "__main__":
    unittest.main()
