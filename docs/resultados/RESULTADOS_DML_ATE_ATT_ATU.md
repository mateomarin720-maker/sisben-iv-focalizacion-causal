# Resultados — Double Machine Learning (ATE, ATT, ATU)

Generado 2026-10-21 por `src/5_estimacion.py` (`_ate_att_atu`), primera
corrida real (no de prueba) sobre el outcome y el Hot-Deck con vivienda
sumada a la celda. Salida completa:
`docs/reports/estimacion_ate_att_atu_cate.txt`.

## Qué es

Double Machine Learning (Chernozhukov et al., 2018): estima el efecto
causal de un tratamiento binario controlando por covariables con modelos de
aprendizaje automático (no supone una forma funcional lineal para los
modelos de molestia `Y~W` y `T~W`), con validación cruzada (`LinearDML` de
`econml`).

## Cómo se usa aquí

- **Tratamiento (T):** `1` si `Grupo_hotdeck ∈ {A,B}` (elegibilidad A/B del
  Sisbén, el tratamiento del diseño principal).
- **Outcomes:** `ipm_geih_score` (continuo, 0-4 privaciones) y
  `POBRE_GEIH` (binario, score ≥ 2) — ver `src/3_preprocesamiento.py` para
  qué privaciones incluye y cuáles no.
- **W (controles de los modelos de molestia):** `geo_depto`, `jefe_edad`,
  `viv_cuartos` — la celda COMPLETA del Hot-Deck tal como quedó
  implementada tras sumarle vivienda.
- **X (heterogeneidad del efecto):** `geo_zona`, `jefe_sexo`,
  `viv_paredes`, `viv_pisos` — covariables NO usadas en la celda.
- **ATT y ATU** se calculan con el MISMO `LinearDML` ya ajustado,
  evaluando `effect()`/`ate()` solo sobre los hogares tratados (ATT) o no
  tratados (ATU) — no con un estimador doblemente robusto aparte (ver
  "Qué se descartó" abajo).

## Resultado

| Outcome | ATE | ATT (error de inclusión) | ATU (error de exclusión) |
|---|---|---|---|
| `ipm_geih_score` (0-4) | +0,0137 [+0,0084; +0,0190] | +0,0136 [+0,0083; +0,0189] | +0,0139 [+0,0085; +0,0192] |
| `POBRE_GEIH` (0/1) | +0,0074 [+0,0040; +0,0108] | +0,0074 [+0,0040; +0,0108] | +0,0073 [+0,0040; +0,0106] |

Intervalos de confianza al 95 %. Propensión `P(T=1|W)`: p5=0,632,
p95=0,819 (mediana de cobertura razonable; mínimo observado 0,000 en
alguna combinación puntual de depto×edad×cuartos — ver limitaciones).

## Cómo leerlo

- Los tres efectos son prácticamente **iguales entre sí** — no es un error,
  es lo esperable: con solo 4 covariables de heterogeneidad (zona, sexo,
  paredes, pisos) el modelo lineal no encuentra mucha diferencia entre
  cómo responden tratados y no tratados, así que ATE≈ATT≈ATU.
- Los intervalos de confianza **excluyen 0** en los dos outcomes — hay una
  asociación estadísticamente distinta de cero entre el grupo asignado por
  Hot-Deck y las privaciones del jefe, **incluso controlando por la celda
  completa del Hot-Deck** (depto+edad+cuartos).
- **Esto NO se puede leer como "el Sisbén causa más pobreza".** Según el
  chequeo formal de d-separación (`IDENTIFICACION_CAUSAL.md`), condicionar
  en la celda completa del Hot-Deck debería dejar el grupo asignado
  independiente del resultado. Que quede una asociación de +1,4 p.p. (en
  una escala 0-4) sugiere que `viv_paredes`/`viv_pisos` — que SÍ entran
  como X pero no como W — siguen capturando algo de la correlación
  geográfica que no absorbe `geo_depto`. Es la misma historia que ya
  apareció con el outcome de prueba (empleo/ingreso, 2026-10-21): falta
  verificar y, si corresponde, sumar también paredes/pisos a la celda.
- La magnitud es pequeña (1,4 % de una escala de 4 privaciones, 0,7 p.p.
  en la probabilidad de ser `POBRE_GEIH`) — estadísticamente distinta de
  cero, pero no grande.

## Qué se descartó: `LinearDRLearner` para ATT/ATU

El primer intento usó `LinearDRLearner` (doblemente robusto) para ATT/ATU
por separado. Con las mismas covariables dio valores absurdos (+56, -191,
en una escala 0-4) — inestabilidad del estimador doblemente robusto,
probablemente por poca superposición de propensión en algunas celdas
puntuales (algunas combinaciones de depto×edad×cuartos quedan con
propensión muy cercana a 0 o 1). Se descartó ese camino y se reutilizó el
`LinearDML` ya estable, evaluado sobre cada subpoblación — un caso real de
"el modelo corrió sin error, pero el número no tenía sentido" que vale la
pena dejar documentado para no repetirlo.

## Limitaciones (aplican también a `RESULTADOS_CAUSALFOREST_CATE.md`)

- Tratamiento imputado por Hot-Deck, no observado.
- `W` usa `jefe_edad` y `viv_cuartos` continuos como proxy de la celda real
  (que es por tramos/ciclo de vida) — no es una réplica exacta de la
  celda discreta.
- Outcome reducido (4 de 15 privaciones), con la limitación conocida de
  `sin_cotizacion_pension_jefe` (mezcla informalidad, desempleo e
  inactividad) — ver `src/3_preprocesamiento.py`.
- Sin ajuste por diseño muestral de GEIH ni de Sisbén.
- Selección: el Sisbén solo cubre hogares inscritos.
- Falta DPS/RUI como confusores — el canal `elegibilidad -> participación
  DPS -> resultado` de la Figura 2 del documento de pipeline no tiene
  datos todavía.
- Propensión mínima observada = 0,000 en al menos una celda — posible
  violación puntual de superposición (positivity), no cuantificada a fondo
  en esta corrida.
