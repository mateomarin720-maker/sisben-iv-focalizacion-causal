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
cuartos × nivel de pisos (993 celdas; hasta el 2026-11-02 sin pisos, 376
celdas). Si el DML controla de verdad esa celda, el efecto
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
0,995, diferencia absoluta media 0,008 (con la celda sin pisos: 0,998 y
0,004).

## Resultado (con la corrección y la celda con pisos)

| Outcome | W | ATE [IC 95 %] | ATT | ATU |
|---|---|---|---|---|
| `ipm_geih_score` (0-8) | PROXY | −0,0052 [−0,0122; +0,0018] | −0,0062 | −0,0044 |
| `ipm_geih_score` (0-8) | CELDA EXACTA | −0,0021 [−0,0092; +0,0051] | −0,0016 | −0,0025 |
| `POBRE_GEIH` | PROXY | +0,0010 [−0,0014; +0,0033] | +0,0006 | +0,0013 |
| `POBRE_GEIH` | CELDA EXACTA | −0,0026 [−0,0049; −0,0002] | −0,0031 | −0,0021 |
| `log_ingreso_percapita` | PROXY | −0,0056 [−0,0190; +0,0077] | −0,0066 | −0,0048 |
| `log_ingreso_percapita` | CELDA EXACTA | +0,0006 [−0,0128; +0,0141] | +0,0007 | +0,0006 |
| `POBRE_MONETARIO` | PROXY | +0,0003 [−0,0031; +0,0037] | +0,0007 | −0,0001 |
| `POBRE_MONETARIO` | CELDA EXACTA | −0,0002 [−0,0036; +0,0033] | −0,0000 | −0,0003 |

`POBRE_MONETARIO` y `log_ingreso_percapita` usan la reconstrucción de
pobreza monetaria del 2026-11-02 (`RESULTADOS_POBREZA_MONETARIA.md`).

CATE (`CausalForestDML`, submuestra de 80.000):

| Outcome | W | CATE medio | sd | Rural / urbana |
|---|---|---|---|---|
| `ipm_geih_score` | CELDA EXACTA | −0,0045 | 0,031 | +0,0085 / −0,0064 |
| `POBRE_GEIH` | CELDA EXACTA | −0,0002 | 0,008 | +0,0057 / −0,0011 |
| `log_ingreso_percapita` | CELDA EXACTA | +0,0084 | 0,042 | +0,0014 / +0,0094 |
| `POBRE_MONETARIO` | CELDA EXACTA | +0,0003 | 0,008 | −0,0020 / +0,0006 |

## Cómo leerlo

1. **Siete de los ocho ATE incluyen el cero**, y todos son de una magnitud
   despreciable (≤ 0,26 puntos porcentuales en las tasas de pobreza). Es
   lo que predice la simulación para un sorteo aleatorio dentro de la
   celda: el contraste es una **prueba placebo** del emparejamiento, no
   una estimación del efecto del Sisbén.
2. El único que excluye el cero (`POBRE_GEIH` con la celda exacta,
   −0,26 puntos, límite superior −0,0002) no se replica en
   `POBRE_MONETARIO`. Con ocho pruebas, uno al borde del 5 % es lo
   esperable por azar. Con la celda sin pisos pasaba lo mismo, en
   `log_ingreso_percapita`.
3. **Proxy y celda exacta ya no difieren** de forma relevante. La
   diferencia que se reportaba antes (ATE de `ipm_geih_score` −58 %,
   outcomes monetarios "más fuertes" con la celda) era producto del
   error, no del proxy.
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
  efectos fijos y splines: es lo que permite controlar 993 celdas sin una
  matriz densa de 291.000 × 993. Pierde no linealidades de `X`, pero `X`
  son 3 variables (zona, sexo del jefe, paredes) y la etapa final
  de `LinearDML` es lineal en `X` de todos modos.
- Los modelos no ajustan por el diseño muestral de GEIH.
