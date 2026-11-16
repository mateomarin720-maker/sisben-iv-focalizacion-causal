# Resultados — Double Machine Learning (ATE, ATT, ATU)

Generado por `src/5_estimacion.py` (`_ate_att_atu`). Salida completa:
`docs/reports/estimacion_ate_att_atu_cate.txt`.

**Regenerado 2026-11-02 con los modelos auxiliares corregidos y con la
celda del Hot-Deck que incluye pisos.** Hasta esa fecha, la celda y el
departamento entraban a la propensión como códigos numéricos y no se
controlaban de verdad. Las cifras anteriores (por ejemplo +0,0235 en
`ipm_geih_score` y +0,0056 en `POBRE_GEIH`, ambas con IC que excluían el
0) no son válidas. Detalle en `DIAGNOSTICO_W_CELDA_EXACTA.md`.

**Regenerado el 2026-11-14 con la celda que suma personas del hogar y
menores de 18 años** (3.721 celdas; `RESULTADOS_HOTDECK.md`). Con la
celda exacta los diez ATE siguen incluyendo el cero.

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

- **T:** 1 si `Grupo_hotdeck` ∈ {A, B} (47,0 % de los hogares GEIH sin
  ponderar; 46,7 % con la celda del 2026-11-02 y 63,7 % con la celda sin
  pisos).
- **Outcomes:** `ipm_geih_score` (0-8 privaciones), `POBRE_GEIH`
  (score ≥ 3), `log_ingreso_percapita` y `POBRE_MONETARIO`
  (reconstrucción de pobreza monetaria, `RESULTADOS_POBREZA_MONETARIA.md`).
- **W (dos especificaciones):** PROXY = indicadoras de departamento y de
  nivel de pisos + splines de edad del jefe, cuartos, personas y menores
  (términos aditivos); CELDA EXACTA = indicadoras de la celda del sorteo
  (3.721).
- **X (heterogeneidad):** zona, sexo del jefe, paredes. Pisos salió de
  `X` al entrar a la celda.
- **Modelos auxiliares:** logística sobre indicadoras (`model_t`) y
  regresión con efectos fijos más splines (`model_y`).

## Resultado

| Outcome | W | ATE [IC 95 %] | ATT | ATU |
|---|---|---|---|---|
| `ipm_geih_score` | PROXY | +0,0020 [−0,0056; +0,0096] | +0,0021 | +0,0020 |
| `ipm_geih_score` | CELDA | +0,0037 [−0,0042; +0,0116] | +0,0050 | +0,0025 |
| `POBRE_GEIH` | PROXY | +0,0035 [+0,0008; +0,0062] | +0,0034 | +0,0035 |
| `POBRE_GEIH` | CELDA | +0,0009 [−0,0018; +0,0037] | +0,0006 | +0,0012 |
| `log_ingreso_percapita` | PROXY | −0,0175 [−0,0317; −0,0033] | −0,0162 | −0,0187 |
| `log_ingreso_percapita` | CELDA | +0,0013 [−0,0131; +0,0158] | +0,0029 | −0,0000 |
| `POBRE_MONETARIO` | PROXY | +0,0038 [+0,0002; +0,0075] | +0,0043 | +0,0035 |
| `POBRE_MONETARIO` | CELDA | +0,0017 [−0,0021; +0,0055] | +0,0021 | +0,0013 |

Robustez con la clasificación oficial del DANE (`POBRE_MONETARIO_OFICIAL`,
275.057 hogares de 23 departamentos y Bogotá; se agregó el 2026-11-02):

| Outcome | W | ATE [IC 95 %] | ATT | ATU |
|---|---|---|---|---|
| `POBRE_MONETARIO_OFICIAL` | PROXY | +0,0035 [−0,0002; +0,0073] | +0,0033 | +0,0037 |
| `POBRE_MONETARIO_OFICIAL` | CELDA | +0,0009 [−0,0029; +0,0048] | +0,0006 | +0,0013 |

Propensión con la celda exacta: p5 = 0,054, p95 = 0,942, igual a la
empírica P(T | celda) (correlación 0,996). Con el proxy: p5 = 0,095,
p95 = 0,955. Con personas y menores la propensión varía más entre celdas
(con la celda del 2026-11-02: p5 0,142, p95 0,847; sin pisos, p5 0,363):
la celda separa mejor a los hogares A/B, y el solapamiento entre tratados
y no tratados dentro de cada valor de W es menor.

## Cómo leerlo

- **Con la celda exacta, los cinco ATE incluyen el cero** y son
  despreciables en magnitud (el placebo pasa). Con la celda del
  2026-11-02 también: `POBRE_GEIH` daba −0,0021 [−0,0045; +0,0004], y
  antes de corregir la vivienda del IPM-GEIH por zona, −0,0026 [−0,0049;
  −0,0002], al borde.
- **Con el proxy, tres de cinco ATE excluyen el cero** (`POBRE_GEIH`
  +0,0035, `log_ingreso_percapita` −0,0175, `POBRE_MONETARIO` +0,0038), y
  con la celda del 2026-11-02 ninguno lo hacía. No es un efecto: el proxy
  suma personas y menores como términos aditivos, mientras que la celda
  los cruza con departamento, edad, cuartos y pisos; con la celda más fina
  el proxy deja sin ajustar más de la variación de P(T | celda), y esa
  variación se correlaciona con el resultado. Es la razón por la que la
  especificación es la celda exacta y el proxy solo una comparación.
- Un solo sorteo del Hot-Deck subestima la incertidumbre. Repitiendo el
  sorteo 100 veces, el contraste de `POBRE_GEIH` promedia +0,0001 y solo
  el 4 % de los sorteos excluye el cero; con las reglas de Rubin el IC es
  [−0,0035; +0,0038] (`RESULTADOS_VARIABILIDAD_HOTDECK.md`). Los IC de
  esta página no incluyen la varianza de la imputación (≈ la mitad de la
  total).
- Los cambios de celda (sin pisos → con pisos → con personas y menores)
  no movieron la conclusión con la celda exacta.
- ATE, ATT y ATU son casi iguales: no hay heterogeneidad entre tratados y
  no tratados, como corresponde a un efecto ≈0.
- **El DML con la celda exacta no está sesgado por las celdas pequeñas**
  (comprobación del 2026-11-15). En la simulación, con 30.000 hogares y
  ≈8 por celda, LinearDML se sesga −0,035\* con efecto nulo
  (`SIMULACION_SEMISINTETICA.md`, punto 8). Con los 290.968 hogares
  reales (78 por celda en promedio, mediana 11), tres estimadores dan lo
  mismo:

  | Outcome | LinearDML (proyecto) | LinearDML casi sin regularizar | Regresión con efectos fijos de celda |
  |---|---|---|---|
  | `log_ingreso_percapita` | +0,0013 [−0,013; +0,016] | +0,0049 [−0,010; +0,019] | +0,0028 [−0,012; +0,017] |
  | `POBRE_MONETARIO` | +0,0017 [−0,002; +0,006] | +0,0009 [−0,003; +0,005] | −0,0003 [−0,004; +0,004] |
  | `POBRE_GEIH` | +0,0009 [−0,002; +0,004] | +0,0005 [−0,002; +0,003] | −0,0004 [−0,003; +0,002] |

  Las diferencias son de milésimas, muy por debajo del ancho de los IC.
  La regresión con efectos fijos usa la misma función que la simulación
  (`simulacion.estimadores.regresion_efectos_fijos`, X en indicadoras).
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
  (`docs/metodologia/METODOLOGIA_INDICADOR_IPM_GEIH.md`).
- Pobreza monetaria reconstruida con microdatos públicos, no la oficial
  (clasifica igual al 93,9 % de los hogares que mide el DANE,
  `RESULTADOS_POBREZA_MONETARIA.md`).
- Sin ajuste por diseño muestral; el Sisbén solo cubre hogares inscritos
  (`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`); falta DPS/RUI.
