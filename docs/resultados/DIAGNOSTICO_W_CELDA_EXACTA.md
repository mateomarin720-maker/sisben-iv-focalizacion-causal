# Diagnóstico: ¿el residuo del DML dependía del proxy continuo de `W`?

Generado 2026-11-02 por `src/5_estimacion.py` (corrida con dos
especificaciones de `W` en el mismo script). Ampliado el mismo día al
conectar `muestra_estimacion_monetaria_2024.parquet` (outcome de pobreza
monetaria, ver `RESULTADOS_POBREZA_MONETARIA.md`) como tercer y cuarto
outcome. **Cifras regeneradas el 2026-11-02 tras corregir el bug de
agosto** (códigos `"1.0"` del `.DTA`, ver CHANGELOG): las conclusiones se
mantienen salvo la del ATU de `ipm_geih_score` (punto 1). Salida completa:
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
siempre, y `W_COLS_CELDA`, la nueva).

Outcomes: `ipm_geih_score` y `POBRE_GEIH` (IPM-GEIH), y
`log_ingreso_percapita` (`log1p(ingreso_percapita)`, para que la cola
derecha extrema del ingreso no domine el ajuste por error cuadrático de
`GradientBoostingRegressor`) y `POBRE_MONETARIO` (línea de pobreza DANE
2024 por zona): 4 outcomes × 2 especificaciones de `W`.

## Resultado

| Outcome | W | ATE | ATT | ATU |
|---|---|---|---|---|
| `ipm_geih_score` (0-8) | PROXY (continuo) | +0,0235 [+0,0170;+0,0301] | +0,0245 [+0,0177;+0,0312] | +0,0219 [+0,0156;+0,0283] |
| `ipm_geih_score` (0-8) | **CELDA EXACTA** | **+0,0098 [+0,0029;+0,0166]** | +0,0113 [+0,0043;+0,0183] | **+0,0071 [+0,0004;+0,0137]** |
| `POBRE_GEIH` (K≥3) | PROXY (continuo) | +0,0056 [+0,0034;+0,0079] | +0,0060 [+0,0036;+0,0083] | +0,0049 [+0,0029;+0,0070] |
| `POBRE_GEIH` (K≥3) | **CELDA EXACTA** | **+0,0058 [+0,0035;+0,0081]** | +0,0061 [+0,0038;+0,0085] | +0,0052 [+0,0031;+0,0073] |
| `log_ingreso_percapita` (log1p) | PROXY (continuo) | -0,0294 [-0,0479;-0,0108] | -0,0290 [-0,0475;-0,0104] | -0,0300 [-0,0490;-0,0111] |
| `log_ingreso_percapita` (log1p) | **CELDA EXACTA** | **-0,0467 [-0,0653;-0,0282]** | -0,0470 [-0,0655;-0,0285] | -0,0463 [-0,0651;-0,0275] |
| `POBRE_MONETARIO` (línea DANE) | PROXY (continuo) | +0,0141 [+0,0106;+0,0175] | +0,0142 [+0,0107;+0,0177] | +0,0138 [+0,0104;+0,0173] |
| `POBRE_MONETARIO` (línea DANE) | **CELDA EXACTA** | **+0,0158 [+0,0123;+0,0192]** | +0,0158 [+0,0123;+0,0193] | +0,0157 [+0,0123;+0,0192] |

CATE (`CausalForestDML`, misma submuestra de 80.000):

| Outcome | W | CATE medio | Por zona (rural / urbana) | Por sexo (hombre / mujer) |
|---|---|---|---|---|
| `ipm_geih_score` | PROXY | +0,0228 | 0,0448 / 0,0195 | 0,0288 / 0,0167 |
| `ipm_geih_score` | **CELDA EXACTA** | +0,0085 | 0,0434 / 0,0033 | 0,0238 / **-0,0071** |
| `POBRE_GEIH` | PROXY | +0,0033 | 0,0139 / 0,0017 | 0,0056 / 0,0009 |
| `POBRE_GEIH` | **CELDA EXACTA** | +0,0031 | 0,0090 / 0,0022 | 0,0067 / **-0,0006** |
| `log_ingreso_percapita` | PROXY | -0,0466 | -0,0512 / -0,0459 | -0,0379 / -0,0555 |
| `log_ingreso_percapita` | **CELDA EXACTA** | -0,0605 | -0,0847 / -0,0569 | -0,0449 / -0,0765 |
| `POBRE_MONETARIO` | PROXY | +0,0149 | 0,0098 / 0,0157 | 0,0103 / 0,0197 |
| `POBRE_MONETARIO` | **CELDA EXACTA** | +0,0164 | 0,0070 / 0,0178 | 0,0099 / 0,0232 |

Un dato adicional revelador: con `W` = PROXY, la propensión `P(T=1|W)`
varía de 0,000 a 0,783 (p5=0,536, p95=0,731). Con `W` = CELDA EXACTA, varía
de 0,633 a 0,642 (p5=0,633, p95=0,640) — un rango casi 30 veces más
angosto. Esto confirma que el proxy continuo (edad/cuartos sin discretizar
+ logística) encontraba variación en la probabilidad de tratamiento que
la celda real NO tiene — la elegibilidad A/B apenas varía entre celdas
exactas, consistente con un sorteo aleatorio con una tasa casi constante.

## Cómo leerlo

**El resultado no es uniforme entre outcomes, y eso es lo más informativo
del experimento:**

1. **`ipm_geih_score` (continuo): el proxy SÍ estaba inflando el efecto.**
   El ATE cae de +0,0235 a +0,0098 (-58 %) al pasar al `W` exacto. El
   ATU queda apenas por encima de 0 ([+0,0004;+0,0137]). Antes de
   corregir el bug de agosto la versión anterior lo daba como no
   significativo ([-0,0016;+0,0116]); con los datos corregidos excluye 0
   por un margen mínimo, así que no conviene apoyarse en ninguna de las
   dos lecturas. Una parte sustancial del efecto de este outcome dependía
   de usar edad/cuartos continuos como proxy de la celda.
2. **`POBRE_GEIH` (binario): el proxy casi no importaba.** El ATE pasa de
   +0,0056 a +0,0058 (+4 %), y los tres efectos (ATE/ATT/ATU) siguen
   excluyendo 0 con márgenes similares. El residuo de este outcome NO se
   explica por el proxy continuo — sobrevive usando la celda idéntica al
   mecanismo real de sorteo.
3. **La heterogeneidad por sexo del jefe es NEGATIVA para `jefe_mujer`**
   con la celda exacta en los dos outcomes IPM-GEIH (`ipm_geih_score`:
   -0,0071; `POBRE_GEIH`: -0,0006), y positiva y grande en los dos
   monetarios. El patrón por sexo nunca ha sido estable entre
   especificaciones ni entre outcomes — no se puede citar como robusto.
4. **La heterogeneidad por zona se mantiene y se acentúa** en
   `ipm_geih_score` (rural/urbana pasa de 2,3x a 13x) — la variable más
   estable entre todas las especificaciones probadas para IPM-GEIH. En
   `POBRE_MONETARIO` va en sentido contrario (más efecto urbano), algo
   que todavía no se ha examinado.
5. **Los outcomes monetarios no se encogen con la celda exacta: se
   mantienen o se amplían.**
   - `log_ingreso_percapita`: el ATE pasa de -0,0294 a **-0,0467** (+59 %
     en magnitud). El signo es estable (Grupo A/B se asocia con MENOR
     ingreso per cápita) y el intervalo se aleja de 0.
   - `POBRE_MONETARIO`: el ATE pasa de +0,0141 a **+0,0158** (+12 %). Signo
     estable (Grupo A/B se asocia con MAYOR probabilidad de pobreza
     monetaria), intervalo lejos de 0 en las dos especificaciones.
   - Al contrario de `ipm_geih_score`, aquí el proxy continuo estaba
     **atenuando** el efecto: con la celda que reproduce el sorteo real,
     el efecto sobre pobreza monetaria es más fuerte, no más débil.

## Qué significa esto para la pregunta de validez causal

La simulación predice ≈0 bajo un sorteo limpio, sin importar el efecto
verdadero. Con la celda exacta:
- `ipm_geih_score` se ACERCA a esa predicción (cae 58 %, el ATU queda en
  el borde de 0) — consistente con que buena parte de la señal anterior
  era un artefacto de especificación.
- `POBRE_GEIH` NO se acerca — el efecto es prácticamente el mismo con las
  dos especificaciones. Para el outcome binario aparece algo que el
  mecanismo limpio de Hot-Deck no debería producir. No se identifica aquí
  la causa (ver limitaciones); solo se descarta que sea el proxy de `W`.
- `log_ingreso_percapita` y `POBRE_MONETARIO` tampoco se acercan a 0: se
  alejan. Es la evidencia más fuerte del proyecto de que el efecto
  reportado no es un artefacto del proxy continuo de `W`.

**No se puede concluir que `POBRE_GEIH`, `log_ingreso_percapita` o
`POBRE_MONETARIO` tengan un efecto causal confirmado del Sisbén.**
Sobrevivir este chequeo descarta UNA explicación alternativa (el proxy),
no todas. `viv_paredes`/`viv_pisos` siguen siendo las variables de mayor
importancia en el Causal Forest en las cuatro combinaciones; ya están
homologadas con el Sisbén (`docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`),
pero todavía no se probó si sumarlas a la celda del Hot-Deck explica el
residuo. Faltan también los confusores no observados (DPS/RUI).

## Limitaciones de este diagnóstico

- No identifica POR QUÉ `POBRE_GEIH` no se mueve — solo descarta una
  explicación (el proxy). Explicaciones no descartadas: sobreajuste de
  los modelos de molestia (`GradientBoostingRegressor`/
  `LogisticRegression` con 376 categorías dummy), vivienda fuera de la
  celda del Hot-Deck, o algo distinto al mecanismo que simula
  `simulacion_identificacion.py` (esa simulación no modela una
  binarización del outcome como `POBRE_GEIH`, solo un continuo).
- `cotas_frechet_manski.py` ya usaba `construir_celda()` (la celda
  exacta) desde su implementación original — no tenía el problema del
  proxy continuo. Su cota para `POBRE_GEIH` ([-0,4114;+0,3230], ver
  `RESULTADOS_FRECHET_MANSKI.md`) se compara con el ATE de celda exacta
  (+0,0058), no con el de proxy continuo.
- Solo se probó con `5_estimacion.py` (DML/Causal Forest). No se
  repitieron `4_dag_identificacion.py` ni la comparación de filtros SDP
  porque no dependen de esta especificación.
- `log_ingreso_percapita`/`POBRE_MONETARIO` heredan las limitaciones de
  `3b_preprocesamiento_monetario.py`: sobreestiman la pobreza en 5-6
  puntos porcentuales frente a las cifras oficiales y tienen siete
  diferencias metodológicas documentadas en
  `docs/metodologia/pobreza_monetaria/00_auditoria_y_metodologia.md`
  (§7). Eso afecta el nivel de `POBRE_MONETARIO`, pero ambas
  especificaciones de `W` comparten el mismo sesgo de nivel, así que la
  diferencia entre ellas (lo que mide este diagnóstico) no depende de
  corregirlo.
