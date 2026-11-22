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
cuartos × nivel de pisos × personas × menores (3.721 celdas desde el
2026-11-14; 993 con pisos y sin personas; hasta el 2026-11-02 sin pisos,
376 celdas). Si el DML controla de verdad esa celda, el efecto
estimado debería ser ≈0 sea cual sea el efecto verdadero, porque dentro
de la celda `T` no depende de nada del hogar receptor. Eso es lo que
predice la simulación (`SIMULACION_IDENTIFICACION.md`, estimador A).

Se comparan dos `W`:
- **PROXY:** departamento y nivel de pisos + edad del jefe y cuartos como
  continuas.
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
0,996, diferencia absoluta media 0,011 con la celda vigente (0,995 y 0,008
con la celda del 2026-11-02; 0,998 y 0,004 con la celda sin pisos).

## Resultado (con la corrección y la celda vigente; donantes ponderados por `fex` desde el 2026-11-21)

| Outcome | W | ATE [IC 95 %] | ATT | ATU |
|---|---|---|---|---|
| `ipm_geih_score` (0-8) | PROXY | +0,0083 [+0,0007; +0,0160] | +0,0082 | +0,0084 |
| `ipm_geih_score` (0-8) | CELDA EXACTA | +0,0058 [−0,0022; +0,0137] | +0,0067 | +0,0050 |
| `POBRE_GEIH` | PROXY | +0,0037 [+0,0010; +0,0064] | +0,0044 | +0,0032 |
| `POBRE_GEIH` | CELDA EXACTA | +0,0003 [−0,0025; +0,0031] | +0,0006 | +0,0001 |
| `log_ingreso_percapita` | PROXY | −0,0221 [−0,0360; −0,0082] | −0,0264 | −0,0185 |
| `log_ingreso_percapita` | CELDA EXACTA | −0,0014 [−0,0157; +0,0129] | −0,0055 | +0,0020 |
| `POBRE_MONETARIO` | PROXY | +0,0054 [+0,0018; +0,0091] | +0,0066 | +0,0045 |
| `POBRE_MONETARIO` | CELDA EXACTA | +0,0002 [−0,0036; +0,0040] | +0,0010 | −0,0005 |

`POBRE_MONETARIO` y `log_ingreso_percapita` usan la reconstrucción de
pobreza monetaria del 2026-11-02 (`RESULTADOS_POBREZA_MONETARIA.md`).

CATE (`CausalForestDML`, submuestra de 80.000):

| Outcome | W | CATE medio | sd | Rural / urbana |
|---|---|---|---|---|
| `ipm_geih_score` | CELDA EXACTA | +0,0132 | 0,032 | +0,0076 / +0,0141 |
| `POBRE_GEIH` | CELDA EXACTA | +0,0032 | 0,016 | −0,0003 / +0,0037 |
| `log_ingreso_percapita` | CELDA EXACTA | −0,0194 | 0,044 | −0,0486 / −0,0150 |
| `POBRE_MONETARIO` | CELDA EXACTA | +0,0039 | 0,012 | +0,0022 / +0,0042 |

## Cómo leerlo

1. **Con la celda exacta, los cuatro ATE incluyen el cero**, y todos son
   de una magnitud despreciable (≤ 0,03 puntos porcentuales en las tasas
   de pobreza). Es lo que predice la simulación para un sorteo aleatorio
   dentro de la celda: el contraste es una **prueba placebo** del
   emparejamiento, no una estimación del efecto del Sisbén. Con la celda
   del 2026-11-02, `POBRE_GEIH` llegó a quedar al borde (−0,0026
   [−0,0049; −0,0002]), algo esperable por azar con ocho pruebas.
2. **El proxy ya no basta** con la celda del 2026-11-14: con los donantes
   ponderados por `fex` sus cuatro ATE excluyen el cero
   (`ipm_geih_score` +0,0083, `POBRE_GEIH` +0,37 puntos,
   `log_ingreso_percapita` −0,0221, `POBRE_MONETARIO` +0,54 puntos; sin
   ponderar eran tres). El
   proxy suma personas y menores como términos aditivos y la celda los
   cruza con departamento, edad, cuartos y pisos; la parte de P(T | celda)
   que el proxy no reproduce se correlaciona con el resultado y aparece
   como un "efecto". Es la lección de este documento en otra forma: el
   control tiene que ser la celda del sorteo, no una aproximación.
3. La diferencia que se reportaba antes del 2026-11-02 (ATE de
   `ipm_geih_score` −58 %, outcomes monetarios "más fuertes" con la
   celda) era producto del error de codificación, no del proxy.
4. La heterogeneidad del CATE (sd 0,01-0,04) es del mismo orden que el
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
  efectos fijos y splines: es lo que permite controlar 3.721 celdas sin una
  matriz densa de 291.000 × 3.721. Pierde no linealidades de `X`, pero `X`
  son 3 variables (zona, sexo del jefe, paredes) y la etapa final
  de `LinearDML` es lineal en `X` de todos modos.
- Los modelos no ajustan por el diseño muestral de GEIH.
