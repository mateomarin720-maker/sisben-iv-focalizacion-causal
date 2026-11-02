# Resultados — Double Machine Learning (ATE, ATT, ATU)

Generado por `src/5_estimacion.py` (`_ate_att_atu`). Salida completa:
`docs/reports/estimacion_ate_att_atu_cate.txt`.

**Regenerado 2026-11-02 con los modelos auxiliares corregidos y con la
celda del Hot-Deck que incluye pisos.** Hasta esa fecha, la celda y el
departamento entraban a la propensión como códigos numéricos y no se
controlaban de verdad. Las cifras anteriores (por ejemplo +0,0235 en
`ipm_geih_score` y +0,0056 en `POBRE_GEIH`, ambas con IC que excluían el
0) no son válidas. Detalle en `DIAGNOSTICO_W_CELDA_EXACTA.md`.

**Cómo leer esta página:** el tratamiento se imputa con un sorteo al azar
dentro de la celda del Hot-Deck, así que el contraste del DML es una
**prueba placebo del emparejamiento**, no el efecto causal del Sisbén
(`SIMULACION_IDENTIFICACION.md`). Que dé ≈0 es lo esperado.

## Qué es

Double Machine Learning (Chernozhukov et al., 2018) con `LinearDML` de
`econml`: residualiza `Y` y `T` con modelos auxiliares por validación
cruzada y estima el efecto sobre los residuos. ATT y ATU son el mismo
modelo evaluado sobre los tratados y los no tratados. No son errores de
inclusión ni de exclusión, que son conceptos de focalización.

## Especificación

- **T:** 1 si `Grupo_hotdeck` ∈ {A, B} (46,7 % de los hogares GEIH sin
  ponderar; 63,7 % con la celda sin pisos).
- **Outcomes:** `ipm_geih_score` (0-8 privaciones), `POBRE_GEIH`
  (score ≥ 3), `log_ingreso_percapita` y `POBRE_MONETARIO`
  (reconstrucción de pobreza monetaria, `RESULTADOS_POBREZA_MONETARIA.md`).
- **W (dos especificaciones):** PROXY = indicadoras de departamento y de
  nivel de pisos + splines de edad del jefe y cuartos; CELDA EXACTA =
  indicadoras de la celda del sorteo (993).
- **X (heterogeneidad):** zona, sexo del jefe, paredes. Pisos salió de
  `X` al entrar a la celda.
- **Modelos auxiliares:** logística sobre indicadoras (`model_t`) y
  regresión con efectos fijos más splines (`model_y`).

## Resultado

| Outcome | W | ATE [IC 95 %] | ATT | ATU |
|---|---|---|---|---|
| `ipm_geih_score` | PROXY | −0,0052 [−0,0122; +0,0018] | −0,0062 | −0,0044 |
| `ipm_geih_score` | CELDA | −0,0021 [−0,0092; +0,0051] | −0,0016 | −0,0025 |
| `POBRE_GEIH` | PROXY | +0,0010 [−0,0014; +0,0033] | +0,0006 | +0,0013 |
| `POBRE_GEIH` | CELDA | −0,0026 [−0,0049; −0,0002] | −0,0031 | −0,0021 |
| `log_ingreso_percapita` | PROXY | −0,0056 [−0,0190; +0,0077] | −0,0066 | −0,0048 |
| `log_ingreso_percapita` | CELDA | +0,0006 [−0,0128; +0,0141] | +0,0007 | +0,0006 |
| `POBRE_MONETARIO` | PROXY | +0,0003 [−0,0031; +0,0037] | +0,0007 | −0,0001 |
| `POBRE_MONETARIO` | CELDA | −0,0002 [−0,0036; +0,0033] | −0,0000 | −0,0003 |

Propensión con la celda exacta: p5 = 0,142, p95 = 0,847, igual a la
empírica P(T | celda) (correlación 0,995). Con el proxy: p5 = 0,178,
p95 = 0,851. Con pisos en la celda, la propensión varía más entre celdas
que antes (p5 0,363 sin pisos).

## Cómo leerlo

- Siete de ocho ATE incluyen el cero; el octavo (`POBRE_GEIH` con la
  celda) lo excluye por poco (−0,26 puntos, límite superior −0,0002) y no
  se replica en `POBRE_MONETARIO`. Con ocho intervalos al 95 %, uno al
  borde es lo esperable por azar. Todos son despreciables en magnitud.
- El cambio de celda (sin pisos → con pisos) no movió la conclusión: con
  la celda anterior también eran siete de ocho, con el octavo en
  `log_ingreso_percapita`.
- ATE, ATT y ATU son casi iguales: no hay heterogeneidad entre tratados y
  no tratados, como corresponde a un efecto ≈0.
- La conclusión anterior de que "el residuo no colapsa a 0" y de que la
  vivienda explicaba ese residuo dependía del error de codificación. Con
  la celda controlada, el residuo desaparece.

## Se mantiene

- `LinearDRLearner` sigue descartado para ATT/ATU (valores absurdos por
  inestabilidad; ver docstring de `_ate_att_atu`).

## Limitaciones

- Tratamiento imputado por Hot-Deck, no observado: el DML no identifica
  el efecto del Sisbén con este diseño (`SIMULACION_IDENTIFICACION.md`).
- IPM-GEIH con 8 de 15 privaciones del IPM oficial
  (`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`).
- Pobreza monetaria reconstruida con microdatos públicos, no la oficial
  (clasifica igual al 93,9 % de los hogares que mide el DANE,
  `RESULTADOS_POBREZA_MONETARIA.md`).
- Sin ajuste por diseño muestral; el Sisbén solo cubre hogares inscritos
  (`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`); falta DPS/RUI.
