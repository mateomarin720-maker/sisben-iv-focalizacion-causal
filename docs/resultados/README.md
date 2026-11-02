# Resultados — índice y hallazgos consolidados

*Versión consolidada del 2026-11-02.* Todas las cifras de esta página
vienen de la misma corrida: GEIH con agosto corregido, vivienda con los
códigos verificados, pobreza monetaria reconstruida con D1-D7 cerradas y
modelos auxiliares del DML con las categóricas como indicadoras. El
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
4. **El componente causal de la tesis pasa a la evaluación semisintética**
   (guía del tutor del 2026-10-27): efecto conocido sobre hogares reales,
   tratamiento reconstruido por Hot-Deck, y medir cuánto se degrada su
   recuperación. Pendiente.
5. Los outcomes están construidos y validados: IPM-GEIH (8 de 15
   privaciones) y pobreza monetaria reconstruida (33,2 % frente a 31,8 %
   oficial).

## El pipeline

| # | Paso | Script | Documento |
|---|---|---|---|
| 1 | Hot-Deck | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py` | [`RESULTADOS_HOTDECK.md`](RESULTADOS_HOTDECK.md) |
| 1b | Filtro del SDP (Bogotá) | `src/validacion/comparar_filtros_sdp.py` | [`COMPARACION_FILTROS_SDP.md`](COMPARACION_FILTROS_SDP.md) |
| 1c | Celdas con pisos y paredes | `src/validacion/comparar_celdas_hotdeck_vivienda.py` | [`RESULTADOS_HOTDECK.md`](RESULTADOS_HOTDECK.md) |
| 2 | Identificación (DAG) | `src/4_dag_identificacion.py` | [`IDENTIFICACION_CAUSAL.md`](IDENTIFICACION_CAUSAL.md) |
| 3 | Outcome IPM-GEIH | `src/3_preprocesamiento.py` | [`METODOLOGIA_INDICADOR_IPM_GEIH.md`](../insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md) |
| 3b | Outcome pobreza monetaria | `src/indicadores/pobreza_monetaria_geih.py`, `src/3b_preprocesamiento_monetario.py` | [`RESULTADOS_POBREZA_MONETARIA.md`](RESULTADOS_POBREZA_MONETARIA.md) |
| 4 | DML: ATE/ATT/ATU | `src/5_estimacion.py` | [`RESULTADOS_DML_ATE_ATT_ATU.md`](RESULTADOS_DML_ATE_ATT_ATU.md) |
| 4b | Causal Forest: CATE | `src/5_estimacion.py` | [`RESULTADOS_CAUSALFOREST_CATE.md`](RESULTADOS_CAUSALFOREST_CATE.md) |
| 4c | Diagnóstico de `W` | `src/5_estimacion.py` | [`DIAGNOSTICO_W_CELDA_EXACTA.md`](DIAGNOSTICO_W_CELDA_EXACTA.md) |
| 5 | Cotas de Fréchet-Manski | `src/estimacion/cotas_frechet_manski.py` | [`RESULTADOS_FRECHET_MANSKI.md`](RESULTADOS_FRECHET_MANSKI.md) |
| 6 | Representatividad del Sisbén | `src/validacion/verificar_representatividad_sisben.py` | [`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`](RESULTADOS_REPRESENTATIVIDAD_SISBEN.md) |
| 7 | Selección de variables (OE1) | `src/estimacion/seleccion_variables_lasso_shap.py` | [`RESULTADOS_SELECCION_VARIABLES_OE1.md`](RESULTADOS_SELECCION_VARIABLES_OE1.md) |
| 8 | Simulación de identificación | `src/validacion/simulacion_identificacion.py` | [`SIMULACION_IDENTIFICACION.md`](SIMULACION_IDENTIFICACION.md) |
| 9 | Evaluación semisintética | — | pendiente |

## Resumen por paso

### 1. Hot-Deck

290.968 hogares GEIH, 3.106.489 donantes Sisbén (nacional + Bogotá
vigente). Celda: departamento + ciclo de vida del jefe + tramo de
cuartos; 100 % en celda exacta (376 celdas). Grupo asignado (ponderado):
**A 22,0 · B 33,8 · C 28,7 · D 15,6 %**. Bogotá se filtra por vigencia
al 31-dic-2024 (§1b).

**Celdas con vivienda (1c).** Con pisos y paredes homologados: sumar
pisos sube la correlación entre P(T | celda) y la pobreza monetaria de
0,20 a 0,29, con cobertura de 99,98 %; paredes no agrega nada encima.
Pisos mueve la distribución de grupos (A 22 % → 14 %). La celda oficial
no se ha cambiado: es una decisión pendiente.

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
administrativos que no son públicos. Pendiente descargar la base oficial
(D1, catálogo 874).

### 4. DML y Causal Forest (diagnóstico placebo)

| Outcome | ATE, W = celda exacta [IC 95 %] |
|---|---|
| `ipm_geih_score` | +0,0011 [−0,0060; +0,0081] |
| `POBRE_GEIH` | +0,0004 [−0,0020; +0,0028] |
| `log_ingreso_percapita` | −0,0132 [−0,0264; −0,0001] |
| `POBRE_MONETARIO` | +0,0025 [−0,0009; +0,0058] |

Siete de ocho ATE (dos especificaciones de `W`) incluyen el cero; el CATE
medio también es ≈0. Hasta el 2026-11-02 la celda entraba como número a
la propensión y los efectos parecían robustos (+0,02, IC sin el 0): era
un artefacto. Detalle en §4c.

### 5. Fréchet-Manski

| Outcome | Cota del ATE sin CIA |
|---|---|
| `POBRE_GEIH` | [−0,411; +0,323] |
| `POBRE_MONETARIO` | [−0,538; +0,503] |

Ninguna celda excluye el 0. Toda la precisión de un punto estimado con
el grupo imputado vendría del supuesto, no de los datos.

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
poetry run python src/3b_preprocesamiento_monetario.py
poetry run python src/5_estimacion.py
poetry run python -m src.estimacion.cotas_frechet_manski
poetry run python -m src.validacion.verificar_representatividad_sisben
poetry run python -m src.estimacion.seleccion_variables_lasso_shap
poetry run python -m src.validacion.comparar_celdas_hotdeck_vivienda
poetry run pytest tests/
```

Salidas crudas en `docs/reports/`.
