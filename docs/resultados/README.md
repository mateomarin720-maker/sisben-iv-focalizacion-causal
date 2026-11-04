# Resultados — índice y hallazgos consolidados

*Versión consolidada del 2026-11-02 (seguimiento general en [`../seguimiento/README.md`](../seguimiento/README.md)).* Todas las cifras de esta página
vienen de la misma corrida: GEIH con agosto corregido, vivienda con los
códigos verificados, celda del Hot-Deck con pisos, pobreza monetaria
reconstruida (contrastada con la base oficial del DANE) y modelos
auxiliares del DML con las categóricas como indicadoras. El
historial de correcciones está en
[`CHANGELOG_PENDIENTES.md`](../seguimiento/CHANGELOG_PENDIENTES.md).

## Lo esencial

1. **El Hot-Deck vincula GEIH y Sisbén solo a nivel de celda.** Dentro de
   cada celda el grupo se sortea al azar, así que el grupo imputado no
   lleva información del hogar receptor.
2. **Por eso el DML sobre el grupo imputado da ≈0**, y es lo esperado: es
   una prueba placebo del emparejamiento, no el efecto del Sisbén. Lo
   predice la simulación (§8) y lo confirman los datos reales (§4).
3. **Sin suponer que el sorteo reproduce la realidad, los datos no fijan
   ni el signo del efecto** (cotas de Fréchet-Manski, §5). Es el
   resultado de identificación central con las fuentes actuales.
4. **Evaluación semisintética (§9), corrida hasta la convergencia (432
   repeticiones):** con hogares reales y un efecto conocido (+0,095 en
   log-ingreso, −0,033 en pobreza), todo estimador devuelve ≈0 cuando el
   tratamiento viene del Hot-Deck, en los ocho escenarios. Con el
   tratamiento verdadero, regresión, DML y Causal Forest recuperan el
   efecto si la confusión es observable, y ninguno si no lo es; solo la
   discontinuidad en el corte resiste la confusión no observada, y
   necesita vínculo hogar por hogar.
5. **Reglas de focalización (OE3, §10), en el mismo mundo simulado:**
   un proxy de medios con variables del hogar logra 82-85 % de la
   reducción ideal de la brecha (FGT1) y baja el error de exclusión de
   43,5 % a 18,6 % frente a la clasificación imputada (60 %). Informar la
   regla con el CATE estimado la empeora (72 %), y con el CATE desde el
   Hot-Deck queda peor que el azar (44 % frente a 47 %).
6. Los outcomes están construidos y validados: IPM-GEIH (8 de 15
   privaciones) y pobreza monetaria reconstruida (33,2 % frente a 31,8 %
   oficial; clasifica igual al 93,9 % de los hogares de la base oficial).

## El pipeline

| # | Paso | Script | Documento |
|---|---|---|---|
| 1 | Hot-Deck | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py` | [`RESULTADOS_HOTDECK.md`](RESULTADOS_HOTDECK.md) |
| 1b | Filtro del SDP (Bogotá) | `src/validacion/comparar_filtros_sdp.py` | [`COMPARACION_FILTROS_SDP.md`](COMPARACION_FILTROS_SDP.md) |
| 1c | Celdas con pisos y paredes | `src/validacion/comparar_celdas_hotdeck_vivienda.py` | [`RESULTADOS_HOTDECK.md`](RESULTADOS_HOTDECK.md) |
| 2 | Identificación (DAG) | `src/4_dag_identificacion.py` | [`IDENTIFICACION_CAUSAL.md`](IDENTIFICACION_CAUSAL.md) |
| 3 | Outcome IPM-GEIH | `src/3_preprocesamiento.py` | [`METODOLOGIA_INDICADOR_IPM_GEIH.md`](../insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md) |
| 3b | Outcome pobreza monetaria | `src/indicadores/pobreza_monetaria_geih.py`, `src/3b_preprocesamiento_monetario.py` | [`RESULTADOS_POBREZA_MONETARIA.md`](RESULTADOS_POBREZA_MONETARIA.md) |
| 3c | Contraste con la base oficial del DANE | `src/validacion/comparar_pobreza_monetaria_oficial.py` | [`RESULTADOS_POBREZA_MONETARIA.md`](RESULTADOS_POBREZA_MONETARIA.md) |
| 4 | DML: ATE/ATT/ATU | `src/5_estimacion.py` | [`RESULTADOS_DML_ATE_ATT_ATU.md`](RESULTADOS_DML_ATE_ATT_ATU.md) |
| 4b | Causal Forest: CATE | `src/5_estimacion.py` | [`RESULTADOS_CAUSALFOREST_CATE.md`](RESULTADOS_CAUSALFOREST_CATE.md) |
| 4c | Diagnóstico de `W` | `src/5_estimacion.py` | [`DIAGNOSTICO_W_CELDA_EXACTA.md`](DIAGNOSTICO_W_CELDA_EXACTA.md) |
| 5 | Cotas de Fréchet-Manski | `src/estimacion/cotas_frechet_manski.py` | [`RESULTADOS_FRECHET_MANSKI.md`](RESULTADOS_FRECHET_MANSKI.md) |
| 6 | Representatividad del Sisbén | `src/validacion/verificar_representatividad_sisben.py` | [`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`](RESULTADOS_REPRESENTATIVIDAD_SISBEN.md) |
| 7 | Selección de variables (OE1) | `src/estimacion/seleccion_variables_lasso_shap.py` | [`RESULTADOS_SELECCION_VARIABLES_OE1.md`](RESULTADOS_SELECCION_VARIABLES_OE1.md) |
| 8 | Simulación de identificación | `src/validacion/simulacion_identificacion.py` | [`SIMULACION_IDENTIFICACION.md`](SIMULACION_IDENTIFICACION.md) |
| 9 | Evaluación semisintética | `src/validacion/simulacion_semisintetica.py` | [`SIMULACION_SEMISINTETICA.md`](SIMULACION_SEMISINTETICA.md) |
| 10 | Reglas de focalización (OE3) | `src/validacion/reglas_focalizacion.py` | [`RESULTADOS_REGLAS_FOCALIZACION.md`](RESULTADOS_REGLAS_FOCALIZACION.md) |

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

### 6. Representatividad

La cobertura del Sisbén frente a GEIH varía 32 veces entre departamentos
(0,4 % Valle a 12,8 % Putumayo): el registro no es una muestra uniforme.

### 7. Selección de variables (OE1)

LASSO, Ridge y SHAP sobre 150.000 hogares del Sisbén: `viv_pisos` es la
variable más importante en los tres métodos. Exactitud ≈53 % (línea base
30 %), bien calibrada, pero desigual por grupo: sensibilidad 0,64 en A y
0,39 (LASSO) o 0,22 (RandomForest) en D, que se confunde con C. Con
partición por municipio el F1 macro cae de 0,50 a 0,44. Predice el grupo
asignado, no la pobreza real. `docs/resultados/RESULTADOS_SELECCION_VARIABLES_OE1.md`.

### 8. Simulación de identificación

Con datos sintéticos de efecto conocido: el Hot-Deck con contraste
dentro de la celda devuelve ≈0 sea cual sea el efecto verdadero; solo
una discontinuidad con puntaje continuo lo recupera.

### 9. Evaluación semisintética

Covariables, celda, ingreso y línea de pobreza reales de GEIH;
tratamiento y efecto simulados (P(T | celda) del Sisbén real). 432
repeticiones de 30.000 hogares, hasta que el error Monte Carlo de las 150
celdas quedó bajo el umbral (Causal Forest: 216).

| Estimación media | Verdadero | Oráculo | Vínculo 50 % | Hot-Deck |
|---|---|---|---|---|
| Confusión observada, LinearDML, log-ingreso | +0,095 | +0,089 | +0,041 | −0,006 |
| Confusión observada, LinearDML, pobreza | −0,033 | −0,031 | −0,015 | +0,002 |
| Confusión no observada fuerte, LinearDML, log-ingreso | +0,095 | −0,778 | −0,387 | −0,003 |
| Confusión no observada fuerte, LinearDML, pobreza | −0,033 | +0,138 | +0,070 | +0,002 |
| Regla de corte, RD, log-ingreso (efecto en el corte) | +0,090 | +0,086 | +0,042 | −0,001 |

Con Hot-Deck se pierde el efecto completo; con vínculo parcial se atenúa
en proporción a los hogares mal vinculados. Con confusión no observada
el signo se invierte aun con el tratamiento verdadero. LinearDML tiene
un sesgo pequeño (≈−0,005) y Causal Forest no recupera la
heterogeneidad. Detalle en [`SIMULACION_SEMISINTETICA.md`](SIMULACION_SEMISINTETICA.md).

### 10. Reglas de focalización (OE3)

Mismo mundo semisintético; todas las reglas con el mismo presupuesto
(los hogares A/B vigentes, 46,7 %). 300 repeticiones.

| Regla | Error de exclusión | % de la reducción ideal de FGT1 (proporcional / monto fijo) |
|---|---|---|
| Vigente (Hot-Deck) | 43,5 % | 60 / 61 |
| Aleatoria | 53,3 % | 47 / 47 |
| Proxy de medios por ingreso | 18,6 % | 82 / 85 |
| Proxy + CATE con vínculo | 26,1 % | 73 / 72 |
| Proxy + CATE con Hot-Deck | 55,5 % | 45 / 44 |

Con las fuentes actuales no hay efectos heterogéneos utilizables para
focalizar; un proxy de medios con variables del hogar sí mejora la
focalización. La regla vigente es la imputada por celda, no la del
Sisbén real. Detalle en [`RESULTADOS_REGLAS_FOCALIZACION.md`](RESULTADOS_REGLAS_FOCALIZACION.md).

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
poetry run python -m src.estimacion.cotas_frechet_manski
poetry run python -m src.validacion.verificar_representatividad_sisben
poetry run python -m src.estimacion.seleccion_variables_lasso_shap
poetry run python -m src.validacion.comparar_celdas_hotdeck_vivienda
poetry run python -m src.validacion.simulacion_semisintetica
poetry run python -m src.validacion.reglas_focalizacion
poetry run pytest tests/
```

Salidas crudas en `docs/reports/`.
