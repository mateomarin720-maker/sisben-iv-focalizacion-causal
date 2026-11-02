# Resultados — Double Machine Learning (ATE, ATT, ATU)

Generado por `src/5_estimacion.py` (`_ate_att_atu`). Salida completa:
`docs/reports/estimacion_ate_att_atu_cate.txt`.

**Regenerado 2026-11-02 con los modelos auxiliares corregidos.** Hasta esa
fecha, la celda y el departamento entraban a la propensión como códigos
numéricos y no se controlaban de verdad. Las cifras anteriores (por
ejemplo +0,0235 en `ipm_geih_score` y +0,0056 en `POBRE_GEIH`, ambas con
IC que excluían el 0) no son válidas. Detalle en
`DIAGNOSTICO_W_CELDA_EXACTA.md`.

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

- **T:** 1 si `Grupo_hotdeck` ∈ {A, B} (63,7 % de los hogares GEIH).
- **Outcomes:** `ipm_geih_score` (0-8 privaciones), `POBRE_GEIH`
  (score ≥ 3), `log_ingreso_percapita` y `POBRE_MONETARIO`
  (reconstrucción de pobreza monetaria, `RESULTADOS_POBREZA_MONETARIA.md`).
- **W (dos especificaciones):** PROXY = indicadoras de departamento +
  splines de edad del jefe y cuartos; CELDA EXACTA = indicadoras de la
  celda del sorteo (376).
- **X (heterogeneidad):** zona, sexo del jefe, paredes, pisos.
- **Modelos auxiliares:** logística sobre indicadoras (`model_t`) y
  regresión con efectos fijos más splines (`model_y`).

## Resultado

| Outcome | W | ATE [IC 95 %] | ATT | ATU |
|---|---|---|---|---|
| `ipm_geih_score` | PROXY | +0,0002 [−0,0067; +0,0072] | +0,0009 | −0,0009 |
| `ipm_geih_score` | CELDA | +0,0011 [−0,0060; +0,0081] | +0,0016 | +0,0001 |
| `POBRE_GEIH` | PROXY | +0,0016 [−0,0008; +0,0039] | +0,0018 | +0,0012 |
| `POBRE_GEIH` | CELDA | +0,0004 [−0,0020; +0,0028] | +0,0006 | +0,0001 |
| `log_ingreso_percapita` | PROXY | −0,0098 [−0,0229; +0,0033] | −0,0107 | −0,0083 |
| `log_ingreso_percapita` | CELDA | −0,0132 [−0,0264; −0,0001] | −0,0141 | −0,0117 |
| `POBRE_MONETARIO` | PROXY | +0,0019 [−0,0015; +0,0053] | +0,0019 | +0,0018 |
| `POBRE_MONETARIO` | CELDA | +0,0025 [−0,0009; +0,0058] | +0,0025 | +0,0024 |

Propensión con la celda exacta: p5 = 0,363, p95 = 0,871, igual a la
empírica P(T | celda) (correlación 0,998). Con el proxy: p5 = 0,328,
p95 = 0,839.

## Cómo leerlo

- Siete de ocho ATE incluyen el cero; el octavo lo roza (−0,0001) y no se
  replica en `POBRE_MONETARIO`. Todos son despreciables en magnitud.
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
- Pobreza monetaria reconstruida con microdatos públicos, no la oficial.
- Sin ajuste por diseño muestral; el Sisbén solo cubre hogares inscritos
  (`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`); falta DPS/RUI.
