# Simulación de colas bancarias

## Descripción

Proyecto académico en Python y SimPy que simula la atención de retiros y pagos
en un banco durante una jornada de 8 horas (480 minutos). Compara dos
distribuciones de tres cajas y una alternativa de cuatro cajas, ejecuta
réplicas reproducibles, calcula estadísticas y genera CSV y gráficos.

## Objetivo académico

Aplicar teoría de colas y simulación de eventos discretos para estudiar cómo
afecta la asignación de cajas a los tiempos de espera, la utilización y la
cantidad de personas atendidas.

## Problema

Se comparan estas configuraciones:

| Modelo | Cajas para retiros | Cajas para consignaciones/pagos |
|---|---:|---:|
| A | 1 | 2 |
| B | 2 | 1 |
| 4 cajas | 2 | 2 |

La alternativa de cuatro cajas reparte la capacidad adicional entre ambos
grupos. Como aproximación, la carga ofrecida esperada por operación es similar:
con la mezcla de categorías, el promedio entre llegadas ponderado es 2.377 min,
la carga de retiros es aproximadamente 0.63 servidores y la de pagos 0.61.
Por ello, la cuarta caja se distribuye una por grupo adicional (2 y 2); estas
cargas aproximadas no sustituyen los resultados de la simulación. Se ejecutan
como mínimo 10 réplicas por modelo. No se fija un umbral de
espera aceptable: la relevancia de una mejora debe juzgarse con los resultados
y con el contexto del ejercicio, que no especifica un objetivo de servicio.

## Teoría de colas M/M/1

Una cola M/M/1 ideal supone llegadas Poisson homogéneas, servicio exponencial,
un servidor y una cola FIFO. Para tasas `lambda` y `mu`, con `lambda < mu`:

```text
rho = lambda / mu
L   = lambda / (mu - lambda)
Lq  = lambda² / [mu( mu - lambda)]
W   = 1 / (mu - lambda)
Wq  = lambda / [mu( mu - lambda)]
```

`rho` es la utilización, `L` y `Lq` son cantidades promedio en sistema y cola,
y `W` y `Wq` son tiempos promedio en sistema y cola.

En esta simulación las llegadas y los servicios son exponenciales condicionados
a la categoría del usuario, cuyas medias varían. Por ello, es una aproximación
de colas M/M/1 por categoría: el proceso agregado **no** es una M/M/1 homogénea
exacta. Las fórmulas anteriores son referencias teóricas; se deben utilizar
las métricas simuladas para comparar las configuraciones.

## Datos utilizados

Los tiempos están en minutos. La operación se selecciona en cada llegada con
70 % de probabilidad para retiros y 30 % para pagos.

| Operación | Categoría | Media servicio | Media entre llegadas | Probabilidad |
|---|---|---:|---:|---:|
| Retiro | Rápido | 1 | 1 | 0.23 |
| Retiro | Normal | 2 | 2 | 0.40 |
| Retiro | Lento | 3 | 3 | 0.17 |
| Retiro | Muy lento | 4 | 3 | 0.20 |
| Pago | Rápido | 3 | 1 | 0.10 |
| Pago | Normal | 3 | 2 | 0.20 |
| Pago | Lento | 5 | 3 | 0.30 |
| Pago | Muy lento | 7 | 4 | 0.40 |

Cada cliente se dirige a la caja de su operación con menor carga de trabajo
estimada. Las colas son independientes y FIFO. Al minuto 480 cesan las nuevas
llegadas; los clientes que todavía esperan o están siendo atendidos se
contabilizan aparte de quienes finalizaron.

## Estructura del repositorio

```text
Modulo_03/
├── src/
│   ├── configuracion.py
│   ├── estadisticas.py
│   ├── graficos.py
│   ├── main.py
│   └── simulacion.py
├── resultados/
├── docs/metodologia.md
├── tests/test_simulacion.py
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Requisitos e instalación

Se recomienda Python 3.10 o superior. Desde la terminal integrada de VS Code,
abra la carpeta `Modulo_03` y ejecute:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

En Windows, si PowerShell bloquea la activación del entorno, puede ejecutar
Python directamente con `.\.venv\Scripts\python.exe`.

## Ejecución

Desde la carpeta del proyecto:

```powershell
python -m src.main
```

Por defecto se realizan 10 réplicas por configuración, con semilla `2026` y
jornadas de 480 minutos. Opciones configurables:

```powershell
python -m src.main --replicas 20 --semilla 123 --duracion 480
```

Se requieren al menos 10 réplicas. `--salida` permite elegir otra carpeta para
guardar los archivos generados.

Para ejecutar las pruebas:

```powershell
python -m unittest discover -s tests -v
```

## Archivos de resultados

El programa genera en `resultados/`:

- `resultados_por_replica.csv`: métricas agregadas y cantidades por operación
  y categoría para cada réplica.
- `resumen_general.csv`: promedio de las métricas por configuración.
- `estadisticas_por_cajero.csv`: atendidos, promedios de espera/atención/sistema,
  utilización y usuarios pendientes por caja y réplica.
- `estadisticas_por_tipo_usuario.csv`: operaciones y promedios de usuarios por
  categoría en cada configuración.
- `comparacion_modelos.csv`: comparación de espera, atención, utilización,
  usuarios atendidos y cajas con menor/mayor promedio de atención.
- `comparacion_tiempo_espera.png`, `tiempo_atencion_por_cajero.png`,
  `utilizacion_cajas.png` y `usuarios_atendidos_por_operacion.png`: gráficos
  comparativos.

Los promedios de servicio y de espera se calculan sobre clientes que
completaron su atención antes del cierre; la utilización incluye todo el
servicio ocurrido dentro de la jornada. Los CSV también permiten separar los
usuarios que quedaron esperando o en servicio a las 480 minutos.

## Limitaciones y supuestos

- El modelo es una aproximación M/M/1 con tiempos exponenciales condicionados
  a categoría. Como las medias cambian según la categoría y el tipo de usuario
  condiciona los intervalos entre llegadas, el proceso agregado no es una cola
  M/M/1 homogénea exacta.
- Las proporciones 70/30 se aplican mediante selección aleatoria por cliente;
  las fracciones observadas en una réplica pueden diferir ligeramente.
- Se asume que no hay abandono, prioridades, interrupciones ni desplazamiento.
- La carga de una caja se estima con los tiempos de servicio ya asignados.
- No se proporcionó un máximo de espera aceptable; por ello, el informe compara
  resultados y no declara un umbral universal para decidir capacidad.
- Los resultados son estimaciones aleatorias reproducibles con la misma
  semilla, no predicciones garantizadas de un banco real.

> Este proyecto es un trabajo netamente académico y noo constituye un sistema bancario real ni está destinado a su implementación comercial.
