# Resultados — Selección de variables: LASSO, Ridge y SHAP (OE1)

Generado 2026-11-02 por
`src/diagnostico/seleccion_variables_lasso_shap.py`. Salida completa:
`docs/reports/seleccion_variables_lasso_ridge_shap.txt` (consola) y
`docs/reports/seleccion_variables_lasso_ridge_shap.csv` (tabla
combinada) y `docs/reports/seleccion_variables_metricas_por_clase.csv`
(por grupo).

## Qué es

Responde al objetivo específico 1: "determinar grupos y subgrupos de
variables para LASSO, Ridge y SHAP". **No es inferencia causal** — no
estima ningún efecto del Sisbén, es un ejercicio de selección/
importancia de variables: ¿qué características del hogar predicen mejor
el `Grupo` (A-D) que le asigna el Sisbén? Se usan tres métodos
complementarios para no depender de uno solo:
- **LASSO** (`LogisticRegressionCV`, regularización L1, multinomial):
  además de rankear importancia, lleva coeficientes exactamente a 0 —
  dice qué variables sobrarían del todo.
- **Ridge** (la misma regresión con L2): no elimina nada, pero su ranking
  de magnitud sirve para comparar contra LASSO — si coinciden, la señal
  es estable; si no, el L1 puede estar siendo agresivo con alguna
  variable correlacionada con otra.
- **SHAP** sobre `RandomForestClassifier`: importancia no lineal/con
  interacciones, para contrastar contra los dos modelos lineales.

## Por qué no hay circularidad

El Sisbén calcula `Grupo` internamente a partir de `I1`-`I15`/`H_5`
(privaciones ya agregadas) — CLAUDE.md prohíbe usarlas como outcome en la
parte causal por circularidad; aquí se extiende la misma regla a
predictores: usarlas equivaldría a redescubrir la fórmula propia del
Sisbén, no a aportar información nueva. Los predictores usados son
características del hogar independientes de ese cálculo interno —
vivienda, demografía del jefe y geografía, el mismo esquema canónico ya
armonizado para el Hot-Deck.

## Cómo se usa aquí

- **Outcome:** `Grupo` (A/B/C/D), sobre `sisben_estandarizado_2024_con_
  bogota.parquet` (3.093.411 hogares con las 10 variables completas).
- **Predictores numéricos** (orden establecido, van tal cual):
  `hog_num_personas`, `viv_cuartos` (conteos), `jefe_edad` (ciclo de vida
  3-6).
- **Predictores categóricos** (dirección/orden SIN verificar, van
  one-hot, nunca numéricos — mismo criterio que evitó el bug de
  `LinearDRLearner` con categóricas sin orden, ver CLAUDE.md):
  `viv_paredes`, `viv_pisos`, `viv_alcantarillado`, `viv_acueducto`,
  `jefe_sexo`, `geo_zona`.
- **Control geográfico** (incluido para no atribuirle a vivienda/
  demografía variación que es solo geografía; reportado aparte, no en el
  ranking principal): `geo_depto` (33 categorías, one-hot).
- **Submuestra:** 150.000 hogares (estratificada por `Grupo`, preserva
  las proporciones reales — B 30,4 %, C 29,7 %, A 23,4 %, D 16,5 %), por
  costo computacional de `LogisticRegressionCV` y SHAP. Split 70/30
  train/test.

## Resultado

| Variable | LASSO (Σ\|coef\|) | Ridge (Σ\|coef\|) | SHAP (RF, media \|valor\|) | Normalizado promedio |
|---|---|---|---|---|
| `geo_depto` (control) | 23,650 | 31,428 | 0,1584 | 0,846 |
| `viv_pisos` | 8,290 | 9,218 | 0,2952 | 0,548 |
| `hog_num_personas` | 1,566 | 1,569 | 0,1335 | 0,189 |
| `viv_alcantarillado` | 1,047 | 1,061 | 0,1321 | 0,175 |
| `viv_paredes` | 2,189 | 2,716 | 0,0701 | 0,139 |
| `jefe_sexo` | 1,736 | 1,743 | 0,0842 | 0,138 |
| `viv_cuartos` | 1,065 | 1,067 | 0,0695 | 0,105 |
| `viv_acueducto` | 0,140 | 0,172 | 0,0454 | 0,055 |
| `geo_zona` | 0,243 | 0,571 | 0,0291 | 0,042 |
| `jefe_edad` | 0,262 | 0,264 | 0,0230 | 0,033 |

Correlación de Spearman entre rankings: **LASSO-Ridge = 0,988** (casi
perfecta), LASSO-SHAP = 0,794, Ridge-SHAP = 0,806.

Precisión de clasificación (4 clases, test n=45.000; línea base — predecir
siempre la clase mayoritaria `B`, 30,4 % — sería ~0,30 de exactitud):

| Modelo | Exactitud | F1 macro |
|---|---|---|
| LASSO | 0,530 | 0,526 |
| Ridge | 0,530 | 0,526 |
| RandomForest (base de SHAP) | 0,527 | 0,499 |

Ninguna variable quedó eliminada por LASSO (todas con al menos un
coeficiente distinto de 0 en alguna de las 4 clases).

## Rendimiento por grupo, confusión y calibración (2026-11-02)

Agregado a pedido de la revisión: la exactitud global esconde diferencias
grandes entre grupos. Salida: `docs/reports/seleccion_variables_metricas_por_clase.csv`.

| Grupo | LASSO: precisión / sensibilidad | RandomForest: precisión / sensibilidad |
|---|---|---|
| A | 0,63 / 0,64 | 0,63 / 0,65 |
| B | 0,48 / 0,48 | 0,48 / 0,46 |
| C | 0,50 / 0,58 | 0,49 / 0,67 |
| D | 0,55 / **0,39** | 0,62 / **0,22** |

Matriz de confusión de LASSO (% de cada grupo real): el 45 % de los
hogares D se predicen como C, y el 31,5 % de los A como B. Los errores
casi siempre caen en el grupo vecino; casi nunca hay saltos de dos grupos
(A predicho como D: 0,1 %).

**Calibración:** la probabilidad media predicha coincide con la tasa
observada en cada grupo (por ejemplo D: 0,164 frente a 0,165) y el Brier
por grupo va de 0,11 (A, D) a 0,19 (B). Los modelos están bien
calibrados en promedio; el problema es de discriminación entre grupos
vecinos.

**Partición por municipio** (ningún municipio en entrenamiento y prueba a
la vez, RandomForest): F1 macro cae de 0,499 a **0,435** y la
sensibilidad de D de 0,22 a 0,12. La exactitud sube (0,527 → 0,541) solo
porque los municipios de prueba tienen más hogares A y B, que son los
más fáciles; no es una mejora. Parte del rendimiento de la partición
aleatoria venía de reconocer patrones locales del municipio.

**Lectura:** las variables del esquema canónico separan bien los
extremos pobres (A) y mal al grupo D, que se confunde con C. El modelo
predice el grupo **asignado** por el Sisbén, no la pobreza real: un 53 %
de exactitud no mide la validez del Sisbén frente a la pobreza.

## Cómo leerlo

- **`viv_pisos` es, con ventaja, la variable individual más importante en
  los tres métodos** (descontando `geo_depto`, que es un control, no una
  variable sustantiva) — consistente con que el material de piso sea uno
  de los componentes de mayor peso dentro del propio índice Sisbén.
- **LASSO y Ridge casi no difieren entre sí** (Spearman 0,988) — la
  regularización L1 no está siendo agresiva con ninguna variable
  correlacionada, y ninguna variable se elimina del todo. La señal de
  "qué importa" es estable entre los dos modelos lineales.
- **SHAP (no lineal) reordena el tercio medio de la tabla**: `hog_num_
  personas` y `viv_alcantarillado` suben notablemente (de los últimos
  lugares en LASSO/Ridge a 3º-4º en SHAP), mientras `viv_paredes` y
  `jefe_sexo` bajan. Esto sugiere que el tamaño del hogar y el acceso a
  alcantarillado interactúan con otras variables de forma no lineal que
  los modelos lineales no capturan — justo el tipo de divergencia que
  justifica correr los tres métodos en vez de solo uno.
- **`geo_depto` domina el ranking lineal por un motivo mecánico, no
  necesariamente sustantivo**: tiene 33 columnas dummy, así que la suma
  de `|coef|` se acumula sobre muchas más columnas que cualquier otra
  variable (que tiene 2-8). No es comparable uno a uno contra una
  variable con menos categorías — por eso se reporta aparte como
  "control", no se compara directamente en el ranking principal. SHAP
  (que promedia en vez de sumar) lo muestra de forma más moderada
  (2º lugar, no 1º).
- **La exactitud (~53 %) es muy superior a la línea base (~30 %) pero
  está lejos de ser perfecta** — las variables disponibles explican una
  parte real pero parcial de la clasificación del Sisbén; el resto
  depende de las ~15 privaciones (`I1`-`I15`/`H_5`) que, por diseño, NO
  se usan aquí (ver "Por qué no hay circularidad").

## Limitaciones

- Solo usa el esquema canónico armonizado para el Hot-Deck (10
  variables) — el Sisbén real recoge muchas más (ingresos, activos,
  educación de todos los miembros, etc.) que no están en la tabla
  estandarizada de este repositorio.
- Se usan los códigos del Sisbén en one-hot, dentro de una sola fuente.
  `viv_paredes`/`viv_pisos` ya están verificados con la ficha
  (`docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`); `jefe_sexo` no.
- Submuestra de 150.000 (no los 3,09 millones completos) por costo
  computacional — no se probó si el ranking cambia con el total.
- `RandomForestClassifier` con hiperparámetros fijos (300 árboles,
  profundidad 10, hoja mínima 20) sin búsqueda de hiperparámetros — un
  ajuste más fino podría mejorar su F1 macro (0,499, el más bajo de los
  tres) y cambiar algo el ranking de SHAP.
- No es un modelo causal: una variable importante para PREDECIR el
  `Grupo` no implica que el Sisbén la use con una dirección "correcta"
  de política, ni dice nada sobre el bienestar del hogar — ver
  `docs/resultados/2_diagnostico_datos_reales/RESULTADOS_DML_ATE_ATT_ATU.md` y
  `RESULTADOS_CAUSALFOREST_CATE.md` para la parte causal del proyecto.

## Cómo reproducirlo

```bash
poetry run python -m src.diagnostico.seleccion_variables_lasso_shap
```
