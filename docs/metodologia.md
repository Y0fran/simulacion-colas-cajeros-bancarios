# Metodología de simulación

## Modelo de eventos

Se simula una jornada de 480 minutos y se detiene la generación de llegadas al
cierre. Se ejecutan diez réplicas independientes por defecto para los modelos
A, B y la alternativa de cuatro cajas. La semilla configurable permite repetir
el experimento completo; cada combinación de modelo y réplica recibe una
semilla distinta y reproducible.

En cada llegada se selecciona una operación según las proporciones 70 % retiros
y 30 % pagos. Luego se selecciona una categoría usando las probabilidades de
la tabla correspondiente. El tiempo hasta la siguiente llegada es exponencial
con la media asociada a la categoría seleccionada; el servicio también es
exponencial y usa la media de servicio de dicha categoría. De esta manera, se
mantienen las proporciones de operaciones por selección aleatoria, aunque el
proceso agregado no es un Poisson homogéneo.

Cada caja tiene una cola FIFO independiente. El usuario se asigna a la caja
de su operación que tenga menor carga de trabajo estimada: tiempo hasta que
termine el último servicio ya asignado. Los tiempos de servicio se muestrean
al llegar y son conocidos por el mecanismo de asignación. No hay abandono ni
desplazamiento.

Al minuto 480 se dejan de crear usuarios. Solo cuentan como atendidos quienes
terminaron su servicio antes o exactamente al cierre. Los usuarios cuyo
servicio aún no comenzó se cuentan como esperando; quienes ya iniciaron y no
han terminado se cuentan como en servicio. La utilización mide el tiempo
ocupado dentro de la jornada, incluyendo servicios que continúan después del
cierre, y se divide entre 480 minutos.

## Configuraciones

| Configuración | Cajas para retiros | Cajas para pagos |
|---|---:|---:|
| Modelo A | 1 | 2 |
| Modelo B | 2 | 1 |
| Modelo 4 cajas | 2 | 2 |

La alternativa de cuatro cajas divide las cajas por igual entre las dos
operaciones. La carga ofrecida esperada, estimada con la mezcla de categorías,
es aproximadamente 0.63 servidores para retiros y 0.61 para pagos; por ello,
la capacidad adicional se asigna a ambos grupos. Es una aproximación, no una
medición de una jornada real.

## Referencia M/M/1

Para una cola M/M/1 homogénea, con tasa de llegada `lambda` y tasa de servicio
`mu`, la estabilidad requiere `lambda < mu`:

- `rho = lambda / mu`
- `L = lambda / (mu - lambda)`
- `Lq = lambda^2 / (mu * (mu - lambda))`
- `W = 1 / (mu - lambda)`
- `Wq = lambda / (mu * (mu - lambda))`

`L` y `Lq` representan promedios de usuarios en sistema y en cola; `W` y `Wq`
son tiempos promedio en sistema y en cola. La función
`calcular_metricas_mm1(lambda, mu)` de `src/estadisticas.py` devuelve estos
valores y rechaza tasas que no cumplan la condición de estabilidad.

Este ejercicio usa una aproximación M/M/1 condicionada por categoría: cada
tiempo individual es exponencial, pero las medias de llegada y servicio
dependen de la categoría seleccionada. Por tanto, el proceso agregado no es
una M/M/1 homogénea exacta. Las fórmulas analíticas son referencias y las
métricas de la simulación son las apropiadas para comparar los modelos.
