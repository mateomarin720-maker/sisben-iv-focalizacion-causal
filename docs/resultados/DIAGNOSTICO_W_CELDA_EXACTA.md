# Diagnóstico: ¿el residuo del DML dependía del proxy continuo de `W`?

Generado 2026-11-02 por `src/5_estimacion.py` (corrida con dos
especificaciones de `W` en el mismo script). Ampliado el mismo día al
conectar `muestra_estimacion_monetaria_2024.parquet` (outcome de pobreza
monetaria, ver `RESULTADOS_POBREZA_MONETARIA.md`) como tercer y cuarto
outcome del mismo diagnóstico. Salida completa:
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
siempre, y `W_COLS_CELDA`, la nueva) para los dos outcomes IPM-GEIH.

El 2026-11-02 se repitió el mismo experimento conectando
`muestra_estimacion_monetaria_2024.parquet` (outcome de pobreza
monetaria, `3b_preprocesamiento_monetario.py`) a `5_estimacion.py`: se
agregó `log_ingreso_percapita` (`log1p(ingreso_percapita)`, para evitar
que la cola derecha extrema del ingreso domine el ajuste por error
cuadrático de `GradientBoostingRegressor`) y `POBRE_MONETARIO` (binario,
línea de pobreza DANE 2024 por zona) a la misma matriz de 4 outcomes × 2
especificaciones de `W`.

## Resultado

| Outcome | W | ATE | ATT | ATU |
|---|---|---|---|---|
| `ipm_geih_score` (0-8) | PROXY (continuo) | +0,0206 [+0,0141;+0,0272] | +0,0214 [+0,0146;+0,0281] | +0,0193 [+0,0130;+0,0256] |
| `ipm_geih_score` (0-8) | **CELDA EXACTA** | **+0,0076 [+0,0008;+0,0143]** | +0,0090 [+0,0020;+0,0160] | **+0,0050 [-0,0016;+0,0116]** |
| `POBRE_GEIH` (K≥3) | PROXY (continuo) | +0,0052 [+0,0029;+0,0075] | +0,0055 [+0,0032;+0,0079] | +0,0046 [+0,0025;+0,0067] |
| `POBRE_GEIH` (K≥3) | **CELDA EXACTA** | **+0,0049 [+0,0026;+0,0072]** | +0,0052 [+0,0028;+0,0076] | +0,0044 [+0,0023;+0,0065] |
| `log_ingreso_percapita` (log1p) | PROXY (continuo) | -0,0317 [-0,0539;-0,0096] | -0,0322 [-0,0543;-0,0101] | -0,0310 [-0,0535;-0,0085] |
| `log_ingreso_percapita` (log1p) | **CELDA EXACTA** | **-0,0468 [-0,0689;-0,0246]** | -0,0481 [-0,0702;-0,0260] | -0,0444 [-0,0669;-0,0219] |
| `POBRE_MONETARIO` (línea DANE) | PROXY (continuo) | +0,0136 [+0,0101;+0,0171] | +0,0137 [+0,0102;+0,0172] | +0,0134 [+0,0099;+0,0169] |
| `POBRE_MONETARIO` (línea DANE) | **CELDA EXACTA** | **+0,0152 [+0,0118;+0,0187]** | +0,0153 [+0,0117;+0,0188] | +0,0152 [+0,0117;+0,0187] |

CATE (`CausalForestDML`, misma submuestra de 80.000):

| Outcome | W | CATE medio | Por zona (rural / urbana) | Por sexo (hombre / mujer) |
|---|---|---|---|---|
| `ipm_geih_score` | PROXY | +0,0237 | 0,0538 / 0,0193 | 0,0321 / 0,0152 |
| `ipm_geih_score` | **CELDA EXACTA** | +0,0119 | 0,0551 / 0,0055 | 0,0292 / **-0,0057** |
| `POBRE_GEIH` | PROXY | +0,0041 | 0,0203 / 0,0017 | 0,0076 / 0,0006 |
| `POBRE_GEIH` | **CELDA EXACTA** | +0,0042 | 0,0177 / 0,0022 | 0,0090 / **-0,0007** |
| `log_ingreso_percapita` | PROXY | -0,0358 | -0,0310 / -0,0365 | -0,0269 / -0,0449 |
| `log_ingreso_percapita` | **CELDA EXACTA** | -0,0454 | -0,0683 / -0,0420 | -0,0322 / -0,0589 |
| `POBRE_MONETARIO` | PROXY | +0,0162 | 0,0103 / 0,0171 | 0,0113 / 0,0212 |
| `POBRE_MONETARIO` | **CELDA EXACTA** | +0,0156 | 0,0058 / 0,0171 | 0,0090 / 0,0224 |

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
5. **Los outcomes monetarios (`log_ingreso_percapita`, `POBRE_MONETARIO`)
   NO se encogen con la celda exacta — se mantienen o se amplían.** Esto
   es un tercer patrón, distinto a los dos anteriores:
   - `log_ingreso_percapita`: el ATE pasa de -0,0317 a **-0,0468** (+48 %
     en magnitud). El signo es estable (ser Grupo A/B del Sisbén se
     asocia con MENOR ingreso per cápita, consistente con la dirección
     esperada) y el intervalo de confianza se aleja más de 0, no se
     acerca.
   - `POBRE_MONETARIO`: el ATE pasa de +0,0136 a **+0,0152** (+12 %). El
     signo también es estable (Grupo A/B se asocia con MAYOR probabilidad
     de ser pobre monetario) y el intervalo se mantiene lejos de 0 en las
     dos especificaciones.
   - A diferencia de `ipm_geih_score`, donde el proxy continuo SÍ inflaba
     el efecto, aquí ocurre lo contrario: el proxy continuo (que
     introduce variación espuria en `P(T=1|W)`, ver el dato de propensión
     más abajo) estaba **atenuando** el efecto real. Con la celda exacta
     — que reproduce fielmente el mecanismo real de sorteo — el efecto
     sobre pobreza monetaria es más fuerte, no más débil.

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
- `log_ingreso_percapita` y `POBRE_MONETARIO` tampoco se acercan a 0 — al
  contrario, se alejan. Bajo la simulación de sorteo limpio, el resultado
  esperado para CUALQUIER outcome es ≈0 con la celda exacta; que estos
  dos outcomes se alejen de 0 en vez de acercarse es la evidencia más
  fuerte producida hasta ahora en todo el proyecto de que el efecto
  reportado no es un artefacto del proxy continuo de `W`. Dicho de otro
  modo: no solo sobrevive el chequeo — se fortalece con él.

**No se puede concluir que `POBRE_GEIH`, `log_ingreso_percapita` o
`POBRE_MONETARIO` tengan un efecto causal confirmado del Sisbén.**
Sobrevivir este chequeo descarta UNA explicación alternativa (el proxy),
no todas — sigue pendiente de verificar contra `viv_paredes`/`viv_pisos`
sin homologar con Sisbén (la pista de mayor importancia en el Causal
Forest en las cuatro combinaciones de outcome, incluidas las monetarias)
y contra confusores no observados (DPS/RUI). Son, sin embargo, las tres
versiones de indicador que han sobrevivido más chequeos de robustez
seguidos (tautología + proxy continuo) sin moverse hacia 0 — y en el caso
de los outcomes monetarios, moviéndose en la dirección contraria a la que
predeciría un artefacto de especificación.

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
- `log_ingreso_percapita`/`POBRE_MONETARIO` heredan la limitación de
  `3b_preprocesamiento_monetario.py`: el ingreso laboral viene de
  `INGLABO` (ya imputado por el DANE, no reconstruido a mano) pero el
  outcome sigue sobreestimando pobreza por 6-7 puntos porcentuales frente
  a FGT0/FGT1 oficiales (no se replica la imputación completa de la
  metodología DANE del ingreso per cápita de la unidad de gasto). Esto
  afecta el nivel de `POBRE_MONETARIO` (cuántos hogares caen bajo la
  línea), pero no debería invalidar la comparación PROXY vs. CELDA
  EXACTA dentro del mismo outcome — ambas especificaciones comparten el
  mismo sesgo de nivel, así que la diferencia entre ellas (lo que mide
  este diagnóstico) no depende de corregirlo.
