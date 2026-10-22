# Validación de los modelos de estimación (2026-10-21)

Qué se verificó de `src/5_estimacion.py` (DML: ATE, ATT, ATU y CATE) y qué
se encontró. Todo con **datos sintéticos de efecto verdadero = 0**, porque
los parquets reales viven en Azure; no se corrió sobre los datos reales.

## Qué funciona
- Los scripts de `src/3_`, `4_`, `5_` y `src/estimacion/` compilan.
- `5_estimacion.py` corre de punta a punta (outcome continuo y binario, ATE,
  ATT, ATU, CATE, importancia de variables) sobre un parquet sintético con
  las mismas columnas que `muestra_estimacion_2024.parquet`.
- Entorno probado: Python 3.13, econml 0.17.0, scikit-learn 1.9.1, shap 0.54.1, numpy 2.4.6.

## Hallazgo 1 — los controles W no reproducen la celda del Hot-Deck
El Hot-Deck sortea donante dentro de la celda `depto | ciclo de vida (4) | cuartos
agrupados (1, 2, 3+)` (`construir_celda`). La estimación controlaba por el
**código numérico** del departamento, la **edad en años** y el **conteo de
cuartos** con un logit lineal para el tratamiento. El código del depto no es
ordinal y los cuartos se agrupan, así que ese modelo no ajusta por la celda real.

Simulación (33 deptos × 3 ciclos × 3 tramos de cuartos, n = 30.000, 8 repeticiones, efecto verdadero 0):

| Controles W | ATE medio | Sesgo absoluto medio | Rango | IC95% que cubre 0 |
|---|---|---|---|---|
| Original (código depto + edad + cuartos, logit lineal) | +0,016 | 0,024 | −0,017 a +0,053 | 50 % |
| Celda del Hot-Deck como categórica (one-hot de `_hotdeck_celda`) | +0,003 | 0,015 | −0,024 a +0,035 | 88 % |

El sesgo del original (≈ 0,02 en escala 0-4) es del mismo orden que el efecto
estimado con datos reales (+0,014): **ese +0,014 puede ser un artefacto del
ajuste y no una fuga real**. No se puede afirmar con los datos reales; hay que
reestimar con la corrección. Con n = 290.968 el sesgo debería ser menor.

**Corrección** (rama `corrige-controles-celda`): W = one-hot de `_hotdeck_celda`.

## Hallazgo 2 — el diagnóstico de propensión del original engaña
En la prueba de punta a punta, la propensión del modelo original salió en
[0,39; 0,72] (p5 0,51, p95 0,68) cuando la real variaba entre 0,05 y 0,99. El
logit lineal alisa la variación entre celdas y esconde problemas de
superposición. Con W categórica el diagnóstico sí los muestra. Los
`min = 0.000` reales conviene revisarlos con el W corregido antes de
interpretarlos como violación de positividad.

## Hallazgo 3 — ATE = ATT = ATU por construcción
Dentro de la celda, el donante se sortea al azar: el grupo asignado es
independiente de las características del hogar receptor. Por eso ATT y ATU no
pueden diferir del ATE (en la prueba salieron iguales hasta el cuarto decimal).
Reportarlos como «error de inclusión / error de exclusión» es correcto como
definición, pero **este diseño no puede distinguirlos**. Sirven si se
estimaran con tratamiento observado (p. ej. elegibilidad real vs. clasificación).

## Hallazgo 4 — el CATE produce diferencias aunque el efecto sea 0
Con efecto verdadero 0, el CausalForest dio desviación estándar del CATE de
0,07-0,09 y diferencias por zona y por sexo del jefe de 0,01-0,03. Esas
diferencias son ruido. Un CATE «por sexo» o «por zona» con datos reales solo se
puede leer si supera esa banda de ruido; no basta con que el número sea distinto.

## Para reproducir
```
poetry run python -m src.validacion.simulacion_estimador_dml 30000 8
```
Tarda unos 4 minutos. Salida: tabla de sesgo y cobertura por variante.

## Pendiente
- Reestimar `5_estimacion.py` con W = celda (rama `corrige-controles-celda`) y comparar contra +0,0137 (IPM) y +0,0074 (POBRE).
- Confirmar que `_hotdeck_celda` llega a `muestra_estimacion_2024.parquet`.
- Ponderar por FEX y reportar errores por clúster/diseño muestral.
