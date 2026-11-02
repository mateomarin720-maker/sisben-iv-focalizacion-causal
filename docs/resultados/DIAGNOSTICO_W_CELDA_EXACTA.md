# Diagnóstico: ¿el DML controla la celda del Hot-Deck?

Generado 2026-11-02 por `src/5_estimacion.py` (dos especificaciones de
`W`, cuatro outcomes). Salida completa:
`docs/reports/estimacion_ate_att_atu_cate.txt`.

**Reescrito el 2026-11-02.** La primera versión de este documento venía de
un modelo de propensión mal especificado (ver "El error") y llegaba a la
conclusión contraria. Esas cifras ya no valen.

## La pregunta

El tratamiento imputado (`T` = Grupo A/B del donante) se sortea al azar
dentro de una celda: departamento × ciclo de vida del jefe × tramo de
cuartos (376 celdas). Si el DML controla de verdad esa celda, el efecto
estimado debería ser ≈0 sea cual sea el efecto verdadero, porque dentro
de la celda `T` no depende de nada del hogar receptor. Eso es lo que
predice la simulación (`SIMULACION_IDENTIFICACION.md`, estimador A).

Se comparan dos `W`:
- **PROXY:** departamento + edad del jefe y cuartos como continuas (la
  especificación usada hasta octubre).
- **CELDA EXACTA:** la celda del sorteo (`_hotdeck_celda`).

## El error (corregido 2026-11-02)

Los modelos auxiliares recibían la celda (0..375) y el departamento
(0..32) como **números**, no como categorías. La logística de propensión
leía la celda como una escala ordinal y no podía separar las celdas:

| | P(T=1 \| W) estimada antes | Real, P(T \| celda) en los datos |
|---|---|---|
| Rango | 0,633-0,642 | 0,093-1,000 |
| p5-p95 | 0,633-0,640 | 0,360-0,872 |

Es decir, la "celda exacta" no controlaba la celda: dejaba casi toda la
variación entre celdas sin ajustar y el efecto "sobrevivía" por eso. Es
el mismo tipo de error que ya estaba documentado en `CLAUDE.md` para
`econml` (categóricas sin orden dentro de un modelo lineal), esta vez en
los modelos auxiliares.

**Corrección:** las categóricas sin orden (celda, departamento, material de
paredes y pisos) entran a los modelos auxiliares como variables
indicadoras. `model_t` es una logística sobre las indicadoras y `model_y`
una regresión con efectos fijos más splines de las continuas. Con la
celda exacta, la propensión estimada reproduce la empírica: correlación
0,998, diferencia absoluta media 0,004.

## Resultado (con la corrección)

| Outcome | W | ATE [IC 95 %] | ATT | ATU |
|---|---|---|---|---|
| `ipm_geih_score` (0-8) | PROXY | +0,0002 [−0,0067; +0,0072] | +0,0009 | −0,0009 |
| `ipm_geih_score` (0-8) | CELDA EXACTA | +0,0011 [−0,0060; +0,0081] | +0,0016 | +0,0001 |
| `POBRE_GEIH` | PROXY | +0,0016 [−0,0008; +0,0039] | +0,0018 | +0,0012 |
| `POBRE_GEIH` | CELDA EXACTA | +0,0004 [−0,0020; +0,0028] | +0,0006 | +0,0001 |
| `log_ingreso_percapita` | PROXY | −0,0098 [−0,0229; +0,0033] | −0,0107 | −0,0083 |
| `log_ingreso_percapita` | CELDA EXACTA | −0,0132 [−0,0264; −0,0001] | −0,0141 | −0,0117 |
| `POBRE_MONETARIO` | PROXY | +0,0019 [−0,0015; +0,0053] | +0,0019 | +0,0018 |
| `POBRE_MONETARIO` | CELDA EXACTA | +0,0025 [−0,0009; +0,0058] | +0,0025 | +0,0024 |

`POBRE_MONETARIO` y `log_ingreso_percapita` ya usan la reconstrucción de
pobreza monetaria del 2026-11-02 (`RESULTADOS_POBREZA_MONETARIA.md`).

CATE (`CausalForestDML`, submuestra de 80.000):

| Outcome | W | CATE medio | sd | Rural / urbana |
|---|---|---|---|---|
| `ipm_geih_score` | CELDA EXACTA | +0,0024 | 0,031 | +0,0165 / +0,0003 |
| `POBRE_GEIH` | CELDA EXACTA | −0,0018 | 0,011 | +0,0028 / −0,0025 |
| `log_ingreso_percapita` | CELDA EXACTA | −0,0206 | 0,063 | −0,0621 / −0,0144 |
| `POBRE_MONETARIO` | CELDA EXACTA | +0,0023 | 0,012 | −0,0010 / +0,0028 |

## Cómo leerlo

1. **Siete de los ocho ATE incluyen el cero**, y todos son de una magnitud
   despreciable (≤ 0,25 puntos porcentuales en las tasas de pobreza). Es
   lo que predice la simulación para un sorteo aleatorio dentro de la
   celda: el contraste es una **prueba placebo** del emparejamiento, no
   una estimación del efecto del Sisbén.
2. El único que roza la significancia (`log_ingreso_percapita` con la
   celda exacta, límite superior −0,0001) es del orden de 1 % del
   ingreso y no se replica en `POBRE_MONETARIO`. Con ocho pruebas, uno
   al borde del 5 % es lo esperable por azar.
3. **Proxy y celda exacta ya no difieren** de forma relevante. La
   diferencia que se reportaba antes (ATE de `ipm_geih_score` −58 %,
   outcomes monetarios "más fuertes" con la celda) era producto del
   error, no del proxy.
4. La heterogeneidad del CATE (sd 0,01-0,06) es del mismo orden que el
   ruido de un bosque causal con efectos ≈0; no se debe interpretar como
   efectos diferenciales.

## Qué cambia en las conclusiones del proyecto

- Se retira la afirmación de que los efectos monetarios con la celda
  exacta eran "la evidencia de robustez más fuerte del proyecto". Además
  de ser producto del error, un efecto que crece al cambiar la
  especificación no es por sí mismo evidencia de robustez: demuestra
  sensibilidad a `W`, y para saber si un estimador recupera el efecto
  hace falta conocer el efecto verdadero (la simulación semisintética).
- Los resultados de DML y Causal Forest se presentan como **diagnóstico**
  del emparejamiento: confirman en datos reales lo que la simulación
  predice (≈0 por construcción).
- La evidencia de identificación sobre el efecto en sí son las cotas de
  Fréchet-Manski (`RESULTADOS_FRECHET_MANSKI.md`): sin suponer
  independencia condicional, los datos no fijan ni el signo del efecto.

## Limitaciones

- `model_y` pasó de `GradientBoostingRegressor` a una regresión con
  efectos fijos y splines: es lo que permite controlar 376 celdas sin una
  matriz densa de 291.000 × 376. Pierde no linealidades de `X`, pero `X`
  son 4 variables (zona, sexo del jefe, paredes, pisos) y la etapa final
  de `LinearDML` es lineal en `X` de todos modos.
- Los modelos no ajustan por el diseño muestral de GEIH.
