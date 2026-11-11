# Resultados — índice y hallazgos consolidados

*Versión consolidada del 2026-11-02 (seguimiento general en [`../seguimiento/README.md`](../seguimiento/README.md)).* Todas las cifras de esta página
vienen de la misma corrida: GEIH con agosto corregido, vivienda con los
códigos verificados, celda del Hot-Deck con pisos, pobreza monetaria
reconstruida (contrastada con la base oficial del DANE) y modelos
auxiliares del DML con las categóricas como indicadoras. El
historial de correcciones está en
[`CHANGELOG_PENDIENTES.md`](../seguimiento/CHANGELOG_PENDIENTES.md).

## Lo esencial

Las cifras con asterisco (\*) son simuladas; las demás, datos reales.

1. **El Hot-Deck vincula GEIH y Sisbén solo a nivel de celda.** Dentro de
   cada celda el grupo se sortea al azar, así que el grupo imputado no
   lleva información del hogar receptor.
2. **Por eso el DML sobre el grupo imputado da ≈0**, y es lo esperado: es
   una prueba placebo del emparejamiento, no el efecto del Sisbén. Lo
   predice la simulación (§8) y lo confirman los datos reales (§4).
3. **Sin suponer que el sorteo reproduce la realidad, los datos no fijan
   ni el signo del efecto** (cotas de Fréchet-Manski, §5). Es el
   resultado de identificación central con las fuentes actuales.
4. **Evaluación semisintética\* (§9), corrida hasta la convergencia (432
   repeticiones):** con hogares reales y un efecto conocido (+0,095\* en
   log-ingreso, −0,033\* en pobreza), todo estimador devuelve ≈0 cuando el
   tratamiento viene del Hot-Deck, en los ocho escenarios. Con el
   tratamiento verdadero, regresión, DML y Causal Forest recuperan el
   efecto si la confusión es observable, y ninguno si no lo es; solo la
   discontinuidad en el corte resiste la confusión no observada, y
   necesita vínculo hogar por hogar.
5. **Reglas de focalización\* (OE3, §10), en el mismo mundo simulado:**
   un proxy de medios con variables del hogar logra 82-85 %\* de la
   reducción ideal de la brecha (FGT1) y baja el error de exclusión de
   43,5 %\* a 18,6 %\* frente a la clasificación imputada (60 %\*). Informar la
   regla con el CATE estimado la empeora (72 %\*), y con el CATE desde el
   Hot-Deck queda peor que el azar (44 %\* frente a 47 %\*).
6. **Variabilidad de la imputación (§11, datos reales):** dos sorteos
   del Hot-Deck coinciden en el grupo de un hogar solo el 34 % de las
   veces (63 % en A/B), pero la distribución nacional varía menos de 0,2
   puntos. La mitad de la varianza de un contraste con el grupo imputado
   viene del sorteo, y el único resultado del DML que excluía el cero
   (`POBRE_GEIH`) desaparece al combinar 100 sorteos.
7. Los outcomes están construidos y validados: IPM-GEIH (8 de 15
   privaciones) y pobreza monetaria reconstruida (33,2 % frente a 31,8 %
   oficial; clasifica igual al 93,9 % de los hogares de la base oficial).

## El pipeline

| # | Paso | Script | Documento |
|---|---|---|---|
| 1 | Hot-Deck | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py` | [`RESULTADOS_HOTDECK.md`](1_datos_y_enlace/RESULTADOS_HOTDECK.md) |
| 1b | Filtro del SDP (Bogotá) | `src/validacion/comparar_filtros_sdp.py` | [`COMPARACION_FILTROS_SDP.md`](1_datos_y_enlace/COMPARACION_FILTROS_SDP.md) |
| 1c | Celdas con pisos y paredes | `src/validacion/comparar_celdas_hotdeck_vivienda.py` | [`RESULTADOS_HOTDECK.md`](1_datos_y_enlace/RESULTADOS_HOTDECK.md) |
| 2 | Identificación (DAG) | `src/4_dag_identificacion.py` | [`IDENTIFICACION_CAUSAL.md`](2_diagnostico_datos_reales/IDENTIFICACION_CAUSAL.md) |
| 3 | Outcome IPM-GEIH | `src/3_preprocesamiento.py` | [`METODOLOGIA_INDICADOR_IPM_GEIH.md`](../insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md) |
| 3b | Outcome pobreza monetaria | `src/indicadores/pobreza_monetaria_geih.py`, `src/3b_preprocesamiento_monetario.py` | [`RESULTADOS_POBREZA_MONETARIA.md`](1_datos_y_enlace/RESULTADOS_POBREZA_MONETARIA.md) |
| 3c | Contraste con la base oficial del DANE | `src/validacion/comparar_pobreza_monetaria_oficial.py` | [`RESULTADOS_POBREZA_MONETARIA.md`](1_datos_y_enlace/RESULTADOS_POBREZA_MONETARIA.md) |
| 4 | DML: ATE/ATT/ATU | `src/5_estimacion.py` | [`RESULTADOS_DML_ATE_ATT_ATU.md`](2_diagnostico_datos_reales/RESULTADOS_DML_ATE_ATT_ATU.md) |
| 4b | Causal Forest: CATE | `src/5_estimacion.py` | [`RESULTADOS_CAUSALFOREST_CATE.md`](2_diagnostico_datos_reales/RESULTADOS_CAUSALFOREST_CATE.md) |
| 4c | Diagnóstico de `W` | `src/5_estimacion.py` | [`DIAGNOSTICO_W_CELDA_EXACTA.md`](2_diagnostico_datos_reales/DIAGNOSTICO_W_CELDA_EXACTA.md) |
| 5 | Cotas de Fréchet-Manski | `src/diagnostico/cotas_frechet_manski.py`, `src/diagnostico/cotas_frechet_modelos.py` | [`RESULTADOS_FRECHET_MANSKI.md`](2_diagnostico_datos_reales/RESULTADOS_FRECHET_MANSKI.md) |
| 5b | Errores de inclusión y exclusión con datos reales | `src/diagnostico/errores_focalizacion_frechet.py` | [`RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md`](2_diagnostico_datos_reales/RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md) |
| 6 | Representatividad del Sisbén | `src/validacion/verificar_representatividad_sisben.py` | [`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`](1_datos_y_enlace/RESULTADOS_REPRESENTATIVIDAD_SISBEN.md) |
| 7 | Selección de variables (OE1) | `src/diagnostico/seleccion_variables_lasso_shap.py` | [`RESULTADOS_SELECCION_VARIABLES_OE1.md`](2_diagnostico_datos_reales/RESULTADOS_SELECCION_VARIABLES_OE1.md) |
| 8 | Simulación de identificación | `src/simulacion/simulacion_identificacion.py` | [`SIMULACION_IDENTIFICACION.md`](3_simulacion/SIMULACION_IDENTIFICACION.md) |
| 9 | Evaluación semisintética | `src/simulacion/` | [`SIMULACION_SEMISINTETICA.md`](3_simulacion/SIMULACION_SEMISINTETICA.md) |
| 10 | Reglas de focalización (OE3) | `src/focalizacion/reglas_focalizacion.py` | [`RESULTADOS_REGLAS_FOCALIZACION.md`](4_focalizacion/RESULTADOS_REGLAS_FOCALIZACION.md) |
| 11 | Variabilidad de la imputación del Hot-Deck | `src/diagnostico/variabilidad_hotdeck.py` | [`RESULTADOS_VARIABILIDAD_HOTDECK.md`](1_datos_y_enlace/RESULTADOS_VARIABILIDAD_HOTDECK.md) |
| 12 | Recomendación de variables | `src/diagnostico/variables_candidatas_pobreza.py` | [`RECOMENDACION_VARIABLES_POBREZA.md`](2_diagnostico_datos_reales/RECOMENDACION_VARIABLES_POBREZA.md) |

## Resumen por paso

### 1. Hot-Deck

290.968 hogares GEIH, 3.106.489 donantes Sisbén (nacional + Bogotá
vigente). Celda: departamento + ciclo de vida del jefe + tramo de
cuartos + nivel de pisos homologado; 99,98 % en celda exacta (993
celdas). Grupo asignado (ponderado): **A 14,2 · B 29,4 · C 34,4 · D
22,0 %**. Bogotá se filtra por vigencia al 31-dic-2024 (§1b).

**Celdas con vivienda (1c).** Pisos entró a la celda el 2026-11-02: sube
la correlación entre P(T | celda) y la pobreza monetaria de 0,20 a 0,29
sin costo de cobertura; paredes no agrega nada encima. La celda sin pisos
(A 22,0 · B 33,8 · C 28,7 · D 15,6 %) queda como sensibilidad.

### 2. Identificación

Chequeo formal de d-separación: separando "elegibilidad del donante" de
"elegibilidad del receptor", el grupo imputado queda independiente del
resultado dada la celda. Es la versión gráfica de lo que muestran §4 y
§8. El diseño de una sola tabla (Sisbén III → IV) sigue bloqueado: falta
el corte III.

### 3. IPM-GEIH

8 de las 15 privaciones del IPM, en las 5 dimensiones; las de pisos y
paredes se retiraron por tautología con `X`. Score medio 1,45/8;
**`POBRE_GEIH` (score ≥ 3) 17,1 %** de los hogares.

### 3b. Pobreza monetaria reconstruida

Unidad de gasto sin servicio doméstico, `INGLABO` más los componentes
laborales que no incluye, hot-deck de no respuesta laboral dentro de
GEIH, arriendo imputado a propietarios y usufructuarios, tres líneas de
dominio, tasas por persona.

| | Reconstruida | Oficial DANE 2024 |
|---|---|---|
| FGT0 nacional | 33,2 % | 31,8 % |
| FGT0 13 ciudades / otras cabeceras / rural | 26,4 / 36,7 / 41,3 % | 24,0 / 34,8 / 42,5 % |
| FGT1 nacional | 13,5 % | 12,6 % |
| Pobreza extrema nacional | 12,5 % | 11,7 % |
| Gini nacional | 0,565 | 0,551 |

Es una reconstrucción experimental: el DANE cruza con registros
administrativos que no son públicos. **Contraste con la base oficial
(catálogo 874, §3c):** sobre los 275.057 hogares que mide el DANE (24
departamentos y Bogotá; la base no trae los 9 nuevos), la reconstrucción
clasifica igual al 93,9 %, con razón mediana de ingreso 1,00. Las líneas
oficiales por área explican 0,6 de los 1,4 puntos de diferencia.

**Decisión (2026-11-02):** la reconstrucción es el outcome principal
(cubre los 33 departamentos) y la clasificación oficial
(`POBRE_MONETARIO_OFICIAL`) es la prueba de robustez en los 24
departamentos y Bogotá. Los 9 departamentos restantes no están en la
base oficial con ningún otro código ni identificador.

### 4. DML y Causal Forest (diagnóstico placebo)

| Outcome | ATE, W = celda exacta [IC 95 %] |
|---|---|
| `ipm_geih_score` | −0,0021 [−0,0092; +0,0051] |
| `POBRE_GEIH` | −0,0026 [−0,0049; −0,0002] |
| `log_ingreso_percapita` | +0,0006 [−0,0128; +0,0141] |
| `POBRE_MONETARIO` | −0,0002 [−0,0036; +0,0033] |
| `POBRE_MONETARIO_OFICIAL` (robustez, 24 deptos.) | −0,0005 [−0,0041; +0,0030] |

Siete de ocho ATE (dos especificaciones de `W`) incluyen el cero; el
octavo lo excluye por poco (−0,26 puntos), como cabe esperar por azar en
ocho pruebas. El CATE medio también es ≈0. Hasta el 2026-11-02 la celda entraba como número a
la propensión y los efectos parecían robustos (+0,02, IC sin el 0): era
un artefacto. Detalle en §4c.

### 5. Fréchet-Manski

| Outcome | Cota del ATE sin CIA |
|---|---|
| `POBRE_GEIH` | [−0,261; +0,380] |
| `POBRE_MONETARIO` | [−0,418; +0,648] |
| `POBRE_MONETARIO_OFICIAL` (robustez, 24 deptos.) | [−0,407; +0,620] |

Ninguna celda excluye el 0. Toda la precisión de un punto estimado con
el grupo imputado vendría del supuesto, no de los datos.

**Con supuestos de monotonía (2026-11-04).** Estas cotas acotan el
contraste entre A/B y el resto. Para el ATE causal, sin supuestos la cota
de pobreza monetaria es [−0,571; +0,829]. Suponiendo que los A/B son al
menos tan pobres (selección monótona y dependencia positiva dentro de la
celda) y que el programa no aumenta la pobreza de nadie (respuesta
monótona), queda en **[−0,405; 0]**: el ancho baja de 1,40 a 0,41, pero
el signo lo pone el supuesto y la magnitud sigue sin identificarse (entre
0 y 40 puntos menos de pobreza). `POBRE_GEIH`: [−0,367; 0].

**Una cota por cada número de los modelos (2026-11-09).** Cada ATE, ATT
y ATU del DML y cada CATE por subgrupo del Causal Forest (zona, sexo del
jefe, paredes), en los cinco resultados, tiene ahora su cota de Fréchet
al lado. Ninguno de los 50 parámetros excluye el cero, y las cotas son
entre 140 y 210 veces más anchas que los IC del DML: en el IPM, el efecto
va de −1,4 a +1,6 privaciones. La incertidumbre se concentra en lo rural
(`POBRE_GEIH`: cota de ancho 1,07 frente a 0,34 en lo urbano).

**Errores de focalización con datos reales (2026-11-10,
[`RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md`](2_diagnostico_datos_reales/RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md)).**
Cotas de Fréchet por celda, sumadas con los factores de expansión de la
GEIH (A/B frente a pobreza monetaria). Error de exclusión: [0,9 %; 75,0 %].
Error de inclusión: [38,6 %; 84,5 %]. Al menos 39 % de los hogares A/B no
son pobres monetarios, sin ningún supuesto dentro de la celda. La
exclusión solo tiene piso donde hay menos A/B que pobres: Putumayo
(≥ 19,5 %), San Andrés (≥ 24,9 %) y Bogotá (≥ 5,2 %).

### 6. Representatividad

La cobertura del Sisbén frente a GEIH varía 32 veces entre departamentos
(0,4 % Valle a 12,8 % Putumayo): el registro no es una muestra uniforme.

### 7. Selección de variables (OE1)

LASSO, Ridge y SHAP sobre 150.000 hogares del Sisbén: `viv_pisos` es la
variable más importante en los tres métodos. Exactitud ≈53 % (línea base
30 %), bien calibrada, pero desigual por grupo: sensibilidad 0,64 en A y
0,39 (LASSO) o 0,22 (RandomForest) en D, que se confunde con C. Con
partición por municipio el F1 macro cae de 0,50 a 0,44. Predice el grupo
asignado, no la pobreza real. `docs/resultados/2_diagnostico_datos_reales/RESULTADOS_SELECCION_VARIABLES_OE1.md`.

Son dos problemas predictivos distintos, y solo el segundo dice algo sobre
errores de focalización:

| Modelo | Objetivo | Qué responde | Dónde |
|---|---|---|---|
| Clasificación | Grupo del Sisbén (A-D) | Qué características reproducen la clasificación | §7 |
| Pobreza | Pobreza monetaria de la GEIH, independiente del Sisbén | Qué características identifican hogares pobres | §12 |

La concordancia entre el grupo y la pobreza de un mismo hogar no se puede
medir: el grupo en la GEIH es imputado por celda (§1). Comparar reglas de
asignación con la pobreza como referencia solo se hace en el mundo
simulado (§10).

### 8. Simulación de identificación

Con datos sintéticos de efecto conocido: el Hot-Deck con contraste
dentro de la celda devuelve ≈0 sea cual sea el efecto verdadero; solo
una discontinuidad con puntaje continuo lo recupera.

### 9. Evaluación semisintética\*

Covariables, celda, ingreso y línea de pobreza reales de GEIH;
tratamiento y efecto simulados (P(T | celda) del Sisbén real). 432
repeticiones de 30.000 hogares, hasta que el error Monte Carlo de las 150
celdas quedó bajo el umbral (Causal Forest: 216).

| Estimación media | Verdadero | Oráculo | Vínculo 50 % | Hot-Deck |
|---|---|---|---|---|
| Confusión observada, LinearDML, log-ingreso | +0,095\* | +0,089\* | +0,040\* | −0,006\* |
| Confusión observada, LinearDML, pobreza | −0,033\* | −0,031\* | −0,014\* | +0,002\* |
| Confusión no observada fuerte, LinearDML, log-ingreso | +0,095\* | −0,778\* | −0,390\* | −0,003\* |
| Confusión no observada fuerte, LinearDML, pobreza | −0,033\* | +0,138\* | +0,070\* | +0,002\* |
| Regla de corte, RD, log-ingreso (efecto en el corte) | +0,090\* | +0,086\* | +0,042\* | −0,001\* |

Con Hot-Deck se pierde el efecto completo; con vínculo parcial se atenúa
en proporción a los hogares mal vinculados. Con confusión no observada
el signo se invierte aun con el tratamiento verdadero. LinearDML tiene
un sesgo pequeño (≈−0,005) y Causal Forest no recupera la
heterogeneidad. **Sensibilidad (2026-11-04):** la pérdida es
proporcional al tamaño del efecto (× 0,5 a × 2); la RD difusa, con 80 %
de participación, recupera el efecto en el corte con vínculo (0,086
frente a 0,090); el sesgo de LinearDML viene de la regularización de los
modelos auxiliares. Detalle en [`SIMULACION_SEMISINTETICA.md`](3_simulacion/SIMULACION_SEMISINTETICA.md).

\* Resultado simulado.

### 11. Variabilidad de la imputación del Hot-Deck

El mismo Hot-Deck con 100 semillas (la 42 reproduce el pipeline). Datos
reales.

| Nivel | Resultado |
|---|---|
| Hogar | Dos sorteos coinciden en el grupo el 34,4 % de las veces y en A/B el 62,7 % (igual a lo teórico de la celda); 39 % de los hogares con P(A/B) entre 0,3 y 0,7 |
| Celda | CV mediano de la proporción A/B 0,091 (0,049 ponderado); error relativo frente a los donantes 0,072 (0,039 ponderado); CV 0,17 en celdas de hasta 30 hogares |
| Nacional | Desviación de 0,10 a 0,15 puntos por grupo (CV ≤ 0,007) |
| Contraste placebo | Con Rubin, `POBRE_GEIH` pasa de −0,0030 (IC sin el 0, semilla 42) a −0,00003 [−0,0036; +0,0036]; 49-55 % de la varianza viene de la imputación |

Detalle en [`RESULTADOS_VARIABILIDAD_HOTDECK.md`](1_datos_y_enlace/RESULTADOS_VARIABILIDAD_HOTDECK.md).

### 10. Reglas de focalización (OE3)\*

Mismo mundo semisintético; todas las reglas con el mismo presupuesto
(los hogares A/B vigentes, 46,7 %). 300 repeticiones.

| Regla | Error de exclusión | % de la reducción ideal de FGT1 (proporcional / monto fijo) |
|---|---|---|
| Vigente (Hot-Deck) | 43,5 %\* | 60\* / 61\* |
| Aleatoria | 53,3 %\* | 47\* / 47\* |
| Proxy de medios por ingreso | 18,6 %\* | 82\* / 85\* |
| Proxy + CATE con vínculo | 26,1 %\* | 73\* / 72\* |
| Proxy + CATE con Hot-Deck | 54,9 %\* | 45\* / 44\* |

Con las fuentes actuales no hay efectos heterogéneos utilizables para
focalizar; un proxy de medios con variables del hogar sí mejora la
focalización. La regla vigente es la imputada por celda, no la del
Sisbén real. Detalle en [`RESULTADOS_REGLAS_FOCALIZACION.md`](4_focalizacion/RESULTADOS_REGLAS_FOCALIZACION.md).

**Mismo dinero (2026-11-09).** Con el mismo número de hogares, el proxy
de medios transfiere 13 %\* más que la vigente (monto fijo). Con el mismo
dinero baja de 85\* a 80\* % del ideal y sigue 19\* puntos por encima de
la vigente: el orden de las reglas no cambia.

**Heterogeneidad ampliada (2026-11-09,
[`RESULTADOS_HETEROGENEIDAD_AMPLIADA.md`](4_focalizacion/RESULTADOS_HETEROGENEIDAD_AMPLIADA.md)).**
Con el doble de variación del efecto (desviación 0,06\*), cinco
modificadores más y el Causal Forest viéndolos todos, la regla con CATE
sigue 4 a 11 puntos\* por debajo de la misma regla con efecto constante.
El error del CATE por hogar crece con la heterogeneidad (2,2 a 2,9 veces
su desviación\*).

\* Resultado simulado.

### 12. Recomendación de variables

Con datos reales de la GEIH, sin Hot-Deck: qué variables que no están en el
diccionario del Sisbén ayudan a identificar hogares pobres. Es una pregunta
abierta, no una conclusión causal. Calcular la composición del hogar con lo
que ya se recoge reduce el error de exclusión 5,40 puntos; todas las variables
nuevas, 1,40. Solo la cuenta de ahorros (−0,86) tiene un aporte claro y estable;
el estrato (−0,52) cumple el criterio por poco. Discapacidad, desplazamiento,
migración, etnia y condición campesina casi no cambian a quién se identifica. El
aporte puede estar sobreestimado: la GEIH no trae nevera, lavadora ni internet,
que el Sisbén sí recoge. En cantidades, en un mes promedio: la composición del
hogar identifica 261.400 hogares pobres más (796.700 personas) y la cuenta de
ahorros 41.500. Las ayudas del gobierno declaradas llegan a 2,8 millones de hogares,
con 78,5 % del dinero en los dos quintiles más pobres; 3,4 millones de hogares pobres
no declaran ninguna (descriptivo, no es un efecto). Detalle en
[`RECOMENDACION_VARIABLES_POBREZA.md`](2_diagnostico_datos_reales/RECOMENDACION_VARIABLES_POBREZA.md).

## Limitaciones generales

- El grupo Sisbén es imputado por emparejamiento, no observado en GEIH.
- IPM-GEIH con 8 de 15 privaciones; pobreza monetaria reconstruida.
- Sin ajuste por diseño muestral en la estimación.
- El Sisbén solo cubre hogares inscritos; falta DPS/RUI.
- `PER002` (edad en el Sisbén) corroborado indirectamente, no contra la ficha de ANDA.

## Cómo se generó

```bash
poetry run python -m src.emparejamiento.emparejamiento_hotdeck_geih_sisben
poetry run python -m src.validacion.comparar_filtros_sdp
poetry run python src/4_dag_identificacion.py
poetry run python src/3_preprocesamiento.py
poetry run python -m src.indicadores.pobreza_monetaria_geih
poetry run python -m src.validacion.comparar_pobreza_monetaria_oficial
poetry run python src/3b_preprocesamiento_monetario.py
poetry run python src/5_estimacion.py
poetry run python -m src.diagnostico.cotas_frechet_manski
poetry run python -m src.validacion.verificar_representatividad_sisben
poetry run python -m src.diagnostico.seleccion_variables_lasso_shap
poetry run python -m src.validacion.comparar_celdas_hotdeck_vivienda
poetry run python -m src.simulacion
poetry run python -m src.focalizacion.reglas_focalizacion
poetry run python -m src.simulacion.sensibilidad_semisintetica
poetry run python -m src.diagnostico.variabilidad_hotdeck 2
poetry run pytest tests/
```

Salidas crudas en `docs/reports/`.
