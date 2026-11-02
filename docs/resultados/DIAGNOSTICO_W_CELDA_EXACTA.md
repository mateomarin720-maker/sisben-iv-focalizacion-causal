# Diagnóstico: ¿el residuo del DML dependía del proxy continuo de `W`?

Generado 2026-11-02 por `src/5_estimacion.py` (corrida con dos
especificaciones de `W` en el mismo script). Salida completa:
`docs/reports/estimacion_ate_att_atu_cate.txt`.

## La pregunta

Desde la corrección del 2026-10-28, `W = {geo_depto, jefe_edad,
viv_cuartos}` usa `jefe_edad` y `viv_cuartos` **continuos** como proxy de
los tramos **discretos** que el Hot-Deck usa de verdad para sortear el
donante (`geo_depto + ciclo de vida del jefe + tramo de cuartos`, ver
`emparejamiento_hotdeck_geih_sisben.py`). Esa discrepancia quedó
documentada como limitación desde el principio, pero nunca se había
probado empíricamente si importaba.

Se confirmó además que el sorteo real es verdaderamente aleatorio dentro
de la celda (`rng.integers`, sin ponderar por nada del receptor) — el
mismo mecanismo que simula `simulacion_identificacion.py` (rama
`simulacion-identificacion`, sin fusionar). Esa simulación muestra que,
con un sorteo así, el estimador debería dar ≈0 sin importar el efecto
verdadero, porque el donante sorteado no lleva información del receptor
específico, solo del promedio de la celda. Si el DML en datos reales con
la celda EXACTA seguía dando un efecto robusto, eso sería evidencia de
que el residuo no es un artefacto de especificación.

## El experimento

Se añadió `W_COLS_CELDA = ["hotdeck_celda_cat"]`: el código categórico de
`_hotdeck_celda`, la columna que `emparejamiento_hotdeck_geih_sisben.py`
ya guarda con la celda EXACTA usada en cada sorteo (376 celdas, 99,999 %
de los hogares en celda exacta — los otros 0,001 % quedaron en
`solo_depto_edad` y son estadísticamente irrelevantes). Se corrió
`5_estimacion.py` con AMBAS especificaciones (`W_COLS_PROXY`, la de
siempre, y `W_COLS_CELDA`, la nueva) para los dos outcomes.

## Resultado

| Outcome | W | ATE | ATT | ATU |
|---|---|---|---|---|
| `ipm_geih_score` (0-8) | PROXY (continuo) | +0,0206 [+0,0141;+0,0272] | +0,0214 [+0,0146;+0,0281] | +0,0193 [+0,0130;+0,0256] |
| `ipm_geih_score` (0-8) | **CELDA EXACTA** | **+0,0076 [+0,0008;+0,0143]** | +0,0090 [+0,0020;+0,0160] | **+0,0050 [-0,0016;+0,0116]** |
| `POBRE_GEIH` (K≥3) | PROXY (continuo) | +0,0052 [+0,0029;+0,0075] | +0,0055 [+0,0032;+0,0079] | +0,0046 [+0,0025;+0,0067] |
| `POBRE_GEIH` (K≥3) | **CELDA EXACTA** | **+0,0049 [+0,0026;+0,0072]** | +0,0052 [+0,0028;+0,0076] | +0,0044 [+0,0023;+0,0065] |

CATE (`CausalForestDML`, misma submuestra de 80.000):

| Outcome | W | CATE medio | Por zona (rural / urbana) | Por sexo (hombre / mujer) |
|---|---|---|---|---|
| `ipm_geih_score` | PROXY | +0,0237 | 0,0538 / 0,0193 | 0,0321 / 0,0152 |
| `ipm_geih_score` | **CELDA EXACTA** | +0,0119 | 0,0551 / 0,0055 | 0,0292 / **-0,0057** |
| `POBRE_GEIH` | PROXY | +0,0041 | 0,0203 / 0,0017 | 0,0076 / 0,0006 |
| `POBRE_GEIH` | **CELDA EXACTA** | +0,0042 | 0,0177 / 0,0022 | 0,0090 / **-0,0007** |

Un dato adicional revelador: con `W` = PROXY, la propensión `P(T=1|W)`
varía de 0,000 a 0,783 (p5=0,536, p95=0,731). Con `W` = CELDA EXACTA, varía
de 0,633 a 0,642 (p5=0,633, p95=0,640) — un rango casi 30 veces más
angosto. Esto confirma que el proxy continuo (edad/cuartos sin discretizar
+ logística) encontraba variación en la probabilidad de tratamiento que
la celda real NO tiene — la elegibilidad A/B apenas varía entre celdas
exactas, consistente con un sorteo aleatorio con una tasa casi constante.

## Cómo leerlo

**El resultado se divide en dos historias distintas según el outcome —
no es uniforme, y eso es lo más informativo del experimento:**

1. **`ipm_geih_score` (continuo): el proxy SÍ estaba inflando el efecto.**
   El ATE cae de +0,0206 a +0,0076 (-63 %) al pasar al `W` exacto, y el
   ATU ya **no excluye 0** (antes [+0,0130;+0,0256], ahora
   [-0,0016;+0,0116]). Esto confirma la hipótesis: una parte sustancial
   del efecto que se venía reportando para este outcome dependía de usar
   edad/cuartos continuos como proxy de la celda, no de la celda
   verdadera. El ATE con la celda exacta sigue sin incluir 0
   ([+0,0008;+0,0143]), pero por un margen mucho más estrecho — el límite
   inferior está a solo 0,0008 de cero.
2. **`POBRE_GEIH` (binario): el proxy casi no importaba.** El ATE pasa de
   +0,0052 a +0,0049 (-6 %), y los tres efectos (ATE/ATT/ATU) siguen
   excluyendo 0 con márgenes similares a los de antes. El residuo de este
   outcome NO se explica por el proxy continuo — sobrevive usando la
   celda idéntica al mecanismo real de sorteo.
3. **La heterogeneidad por sexo del jefe se vuelve NEGATIVA para `jefe_
   mujer`** con la celda exacta en los dos outcomes (`ipm_geih_score`:
   -0,0057; `POBRE_GEIH`: -0,0007) — un tercer patrón distinto al de las
   dos corridas anteriores (primero "jefa mujer domina", luego "zona
   domina, sexo chico y positivo", ahora "zona domina, sexo chico y
   mixto/negativo"). Esto refuerza que el patrón de heterogeneidad por
   sexo NUNCA ha sido estable entre especificaciones — no se puede seguir
   citando ninguna versión de ese hallazgo como robusta.
4. **La heterogeneidad por zona se mantiene y se acentúa** en
   `ipm_geih_score` (rural/urbana pasa de 2,8x a 10x) — la variable más
   estable de las cuatro entre todas las especificaciones probadas hasta
   ahora (proxy con 10 priv., proxy con 8 priv., celda exacta con 8
   priv.).

## Qué significa esto para la pregunta de validez causal

La simulación predice ≈0 bajo un sorteo limpio, sin importar el efecto
verdadero. Con la celda exacta:
- `ipm_geih_score` se ACERCA mucho a esa predicción (cae 63 %, el ATU dejó
  de ser significativo) — consistente con que buena parte de la señal
  anterior era un artefacto de especificación, no evidencia real de fuga.
- `POBRE_GEIH` NO se acerca — el efecto es prácticamente el mismo con las
  dos especificaciones. Esto es la pieza de evidencia más fuerte hasta
  ahora de que, específicamente para el outcome binario, hay algo que el
  mecanismo limpio de Hot-Deck no debería producir y sin embargo aparece
  de forma robusta. No se identifica aquí la causa exacta (ver
  limitaciones) — solo se descarta que sea el proxy continuo de `W`.

**No se puede concluir que `POBRE_GEIH` tenga un efecto causal
confirmado del Sisbén.** Sobrevivir este chequeo descarta UNA explicación
alternativa (el proxy), no todas — sigue pendiente de verificar contra
`viv_paredes`/`viv_pisos` sin homologar con Sisbén (la pista de mayor
importancia en el Causal Forest en las dos especificaciones) y contra
confusores no observados (DPS/RUI). Es, sin embargo, la versión del
indicador binario que ha sobrevivido más chequeos de robustez seguidos
(tautología + proxy continuo) sin moverse.

## Limitaciones de este diagnóstico

- No identifica POR QUÉ `POBRE_GEIH` no se mueve — solo descarta una
  explicación (el proxy). Explicaciones no descartadas: sobreajuste de
  los modelos de molestia (`GradientBoostingRegressor`/
  `LogisticRegression` con 376 categorías dummy), fuga vía
  `viv_paredes`/`viv_pisos` sin homologar, o algo genuinamente distinto
  al mecanismo que simula `simulacion_identificacion.py` (p. ej. esa
  simulación no modela una binarización del outcome como `POBRE_GEIH`,
  solo un continuo — la discrepancia entre outcomes podría originarse
  ahí, no se probó).
- `cotas_frechet_manski.py` ya usaba `construir_celda()` (la celda
  exacta) desde su implementación original — no tenía el problema del
  proxy continuo. Su cota ([-0,4083;+0,3080], ver
  `RESULTADOS_FRECHET_MANSKI.md`) es comparable directamente contra el
  nuevo ATE de celda exacta (+0,0049 para `POBRE_GEIH`), no contra el
  antiguo de proxy continuo.
- Solo se probó con `5_estimacion.py` (DML/Causal Forest). No se
  repitieron `4_dag_identificacion.py` ni la comparación de filtros SDP
  porque no dependen de esta especificación.
