# Anexo: trazabilidad de las cifras

Cada cifra de la tesis con el archivo de `docs/reports/` del que sale y el comando que regenera ese archivo. El anexo se genera leyendo esos archivos (`python -m src.utils.anexo_trazabilidad`); si una cifra no está en su fuente, el generador falla.

\* Resultado simulado (semisintético): el efecto verdadero lo fija el investigador; no es una estimación con datos reales.

## Base: datos y enlace

| Cifra | Valor | Archivo | Dónde | Comando |
|---|---|---|---|---|
| Hogares de la GEIH 2024 en la muestra | 290.968 | `resultado_hotdeck.txt` | «Hogares GEIH fusionados» | `poetry run python -m src.emparejamiento.emparejamiento_hotdeck_geih_sisben` |
| Hogares donantes del Sisbén (nacional y Bogotá vigente) | 3.106.489 | `resultado_hotdeck.txt` | «Donante Sisbén» | `poetry run python -m src.emparejamiento.emparejamiento_hotdeck_geih_sisben` |
| Hogares en celda exacta del Hot-Deck | 99,92 % | `comparacion_filtros_sdp.csv` | fila `vigencia_31dic2024`, `pct_celda_exacta` | `poetry run python -m src.validacion.comparar_filtros_sdp` |
| Grupo asignado por Hot-Deck (ponderado) | A 14,9 % · B 29,7 % · C 33,8 % · D 21,6 % | `comparacion_filtros_sdp.csv` | fila `vigencia_31dic2024`, `grupo_nacional_*_pct` | `poetry run python -m src.validacion.comparar_filtros_sdp` |
| Pobreza monetaria (FGT0 por personas): reconstruida frente a oficial | 33,24 % frente a 31,83 % | `comparacion_pobreza_monetaria_oficial.txt` | filas `fgt0_reconstruida` y `fgt0_oficial`, columna nacional | `poetry run python -m src.validacion.comparar_pobreza_monetaria_oficial` |
| Hogares con la misma clasificación que la base oficial | 93,93 % de 275.057 hogares | `comparacion_pobreza_monetaria_oficial.txt` | fila `pct_hogares_misma_clasificacion`, columna nacional | `poetry run python -m src.validacion.comparar_pobreza_monetaria_oficial` |
| Pobreza extrema, brecha (FGT1) y Gini: reconstruida frente a oficial | extrema 12,5 % frente a 11,7 %; FGT1 13,5 frente a 12,6; Gini 0,565 frente a 0,551 | `pobreza_monetaria_geih.txt` | fila `nacional`: `fgt0_extrema`, `fgt1_pobreza`, `gini` y sus columnas `_oficial` | `poetry run python -m src.indicadores.pobreza_monetaria_geih` |
| Cobertura del Sisbén frente a los hogares de la GEIH, mismo marco (mín.–máx. de los departamentos del archivo nacional; nacional) | 4,8 % – 26,9 %; 16,8 % | `representatividad_sisben_por_depto.csv` | `razon_cobertura` con `marco` = departamento, sin Bogotá (SDP); nacional = suma de registrados / suma de hogares | `poetry run python -m src.validacion.verificar_representatividad_sisben` |
| Parte de la varianza del contraste que viene de la imputación (100 sorteos), por resultado | `POBRE_MONETARIO` 53,2 %; `POBRE_GEIH` 46,7 %; `log_ingreso_percapita` 48,6 % | `variabilidad_hotdeck_estimacion.csv` | `fraccion_info_imputacion`, una fila por resultado | `poetry run python -m src.diagnostico.variabilidad_hotdeck 2` |
| Contraste placebo de `POBRE_GEIH` combinado con Rubin | +0,00014 [−0,0035; +0,0038] | `variabilidad_hotdeck_estimacion.csv` | fila `POBRE_GEIH` | `poetry run python -m src.diagnostico.variabilidad_hotdeck 2` |

## Componente 1: diagnóstico con datos reales

| Cifra | Valor | Archivo | Dónde | Comando |
|---|---|---|---|---|
| ATE del DML (placebo), controles = celda exacta: `ipm_geih_score` | +0,0037 [−0,0042; +0,0116] | `estimacion_ate_att_atu_cate.txt` | bloque `ipm_geih_score`, «W = CELDA EXACTA», línea «ATE» | `poetry run python src/5_estimacion.py` |
| ATE del DML (placebo), controles = celda exacta: `POBRE_GEIH` | +0,0009 [−0,0018; +0,0037] | `estimacion_ate_att_atu_cate.txt` | bloque `POBRE_GEIH`, «W = CELDA EXACTA», línea «ATE» | `poetry run python src/5_estimacion.py` |
| ATE del DML (placebo), controles = celda exacta: `log_ingreso_percapita` | +0,0013 [−0,0131; +0,0158] | `estimacion_ate_att_atu_cate.txt` | bloque `log_ingreso_percapita`, «W = CELDA EXACTA», línea «ATE» | `poetry run python src/5_estimacion.py` |
| ATE del DML (placebo), controles = celda exacta: `POBRE_MONETARIO` | +0,0017 [−0,0021; +0,0055] | `estimacion_ate_att_atu_cate.txt` | bloque `POBRE_MONETARIO`, «W = CELDA EXACTA», línea «ATE» | `poetry run python src/5_estimacion.py` |
| ATE del DML (placebo), controles = celda exacta: `POBRE_MONETARIO_OFICIAL` | +0,0009 [−0,0029; +0,0048] | `estimacion_ate_att_atu_cate.txt` | bloque `POBRE_MONETARIO_OFICIAL`, «W = CELDA EXACTA», línea «ATE» | `poetry run python src/5_estimacion.py` |
| Cota del contraste A/B frente al resto, sin el supuesto del vínculo, pobreza monetaria | [−0,360; +0,637] (ancho 1,00) | `cotas_frechet_manski_monotonia.csv` | `POBRE_MONETARIO`, supuesto `contraste` | `poetry run python -m src.diagnostico.cotas_frechet_manski` |
| Cota del ATE sin supuestos (peor caso), pobreza monetaria | [−0,489; +0,808] (ancho 1,30) | `cotas_frechet_manski_monotonia.csv` | `POBRE_MONETARIO`, supuesto `ate_sin_supuestos` | `poetry run python -m src.diagnostico.cotas_frechet_manski` |
| Cota del ATE con selección y respuesta monótonas, pobreza monetaria | [−0,359; +0,000] (ancho 0,36) | `cotas_frechet_manski_monotonia.csv` | `POBRE_MONETARIO`, supuesto `ate_mts_mtr_dep_positiva` | `poetry run python -m src.diagnostico.cotas_frechet_manski` |
| Ancho de la cota sin supuestos = 1 + 2Δ (Δ: ancho medio de Fréchet de P(Y=1, T=1)) | Δ = 0,149; 1 + 2Δ = 1,30 | `proposiciones.txt` | línea «Δ medio ponderado» (sale de `cotas_frechet_manski_pobre_monetario.csv`) | `poetry run python -m src.diagnostico.proposiciones` |
| Parámetros de los modelos (ATE, ATT, ATU y CATE por subgrupo) cuya cota excluye el cero | 0 de 50 | `cotas_frechet_modelos.csv` | filas con `muestra` = `todas`, columna `excluye_0` | `poetry run python -m src.diagnostico.cotas_frechet_modelos` |
| Error de exclusión (A/B frente a pobreza monetaria), cota por celda agregada | [2,8 %; 57,7 %] | `errores_focalizacion_frechet.csv` | fila nacional, elegible `A-B`, `exclusion_lo` / `exclusion_hi` | `poetry run python -m src.diagnostico.errores_focalizacion_frechet` |
| Error de inclusión, cota por celda agregada | [41,2 %; 74,4 %] | `errores_focalizacion_frechet.csv` | fila nacional, elegible `A-B`, `inclusion_lo` / `inclusion_hi` | `poetry run python -m src.diagnostico.errores_focalizacion_frechet` |
| Exactitud al predecir el grupo del Sisbén (LASSO; F1 macro) | 53,0 %; 0,53 | `seleccion_variables_lasso_ridge_shap.txt` | línea «LASSO (L1)» | `poetry run python -m src.diagnostico.seleccion_variables_lasso_shap` |
| Reducción del error de exclusión al calcular la composición del hogar (puntos) | 5,23 | `variables_candidatas_deltas.csv` | `ficha` frente a `ficha_derivadas`, métrica `exclusion`, logística | `poetry run python -m src.diagnostico.variables_candidatas_pobreza 6` |
| Reducción del error de exclusión con todas las variables nuevas (puntos) | 1,34 [+1,12; +1,59] | `variables_candidatas_deltas.csv` | `todo` frente a `ficha_derivadas` | `poetry run python -m src.diagnostico.variables_candidatas_pobreza 6` |
| Aporte del estrato al error de exclusión (puntos) | −0,49 | `variables_candidatas_deltas.csv` | `+estrato` frente a `ficha_derivadas` | `poetry run python -m src.diagnostico.variables_candidatas_pobreza 6` |
| Aporte de la cuenta de ahorros al error de exclusión (puntos) | −0,81 | `variables_candidatas_posterior.csv` | `+cuenta`, métrica `exclusion` | `poetry run python -m src.diagnostico.variables_candidatas_pobreza 6` |

## Componente 2: simulación semisintética

| Cifra | Valor | Archivo | Dónde | Comando |
|---|---|---|---|---|
| Repeticiones (Causal Forest) y celdas de resultados | 456 (216); 166 celdas | `simulacion_semisintetica_resumen.csv` | columna `reps`; filas del archivo | `poetry run python -m src.simulacion` |
| Cómo se cuentan las celdas de resultados | 8 escenarios × 3 vínculos × 2 resultados = 48 combinaciones × 3 estimadores = 144, + 16 `causal_forest` + 6 `discontinuidad_rd` = 166 | `simulacion_semisintetica_resumen.csv` | columnas `escenario`, `vinculo`, `outcome`, `estimador` | `poetry run python -m src.simulacion` |
| Fuerza de la confusión no observada (γ, peso de U en la asignación) | leve 0,25 · media 0,50 · fuerte 1,00 | `src/simulacion/escenarios.py` | `ESCENARIOS`, clave `gamma` | `poetry run python -m src.simulacion` |
| Efecto verdadero, log-ingreso | +0,0949\* | `simulacion_semisintetica_resumen.csv` | `efecto_verdadero`, outcome `log_ingreso` | `poetry run python -m src.simulacion` |
| Efecto verdadero, pobreza monetaria | −0,0328\* | `simulacion_semisintetica_resumen.csv` | `efecto_verdadero`, outcome `pobre_monetario` | `poetry run python -m src.simulacion` |
| Confusión observada, LinearDML, log_ingreso | oráculo +0,059\* (cob. 0,64\*); vínculo 50 % +0,011\* (cob. 0,07\*); Hot-Deck −0,034\* (cob. 0,00\*) | `simulacion_semisintetica_resumen.csv` | escenario `confusion_observada`, estimador `linear_dml`, `estimacion` y `cobertura` | `poetry run python -m src.simulacion` |
| Confusión observada, LinearDML, pobre_monetario | oráculo −0,020\* (cob. 0,44\*); vínculo 50 % −0,002\* (cob. 0,00\*); Hot-Deck +0,014\* (cob. 0,00\*) | `simulacion_semisintetica_resumen.csv` | escenario `confusion_observada`, estimador `linear_dml`, `estimacion` y `cobertura` | `poetry run python -m src.simulacion` |
| Confusión no observada fuerte, LinearDML, log_ingreso | oráculo −0,852\* (cob. 0,00\*); vínculo 50 % −0,436\* (cob. 0,00\*); Hot-Deck −0,022\* (cob. 0,01\*) | `simulacion_semisintetica_resumen.csv` | escenario `confusion_no_observada`, estimador `linear_dml`, `estimacion` y `cobertura` | `poetry run python -m src.simulacion` |
| Confusión no observada fuerte, LinearDML, pobre_monetario | oráculo +0,136\* (cob. 0,00\*); vínculo 50 % +0,074\* (cob. 0,00\*); Hot-Deck +0,013\* (cob. 0,00\*) | `simulacion_semisintetica_resumen.csv` | escenario `confusion_no_observada`, estimador `linear_dml`, `estimacion` y `cobertura` | `poetry run python -m src.simulacion` |
| Regla de corte, RD (efecto en el corte), log_ingreso | oráculo +0,094\* (cob. 0,96\*); vínculo 50 % +0,048\* (cob. 0,85\*); Hot-Deck +0,001\* (cob. 0,67\*) | `simulacion_semisintetica_resumen.csv` | escenario `regla_corte`, estimador `discontinuidad_rd`, `estimacion` y `cobertura` | `poetry run python -m src.simulacion` |
| Sesgo de LinearDML con efecto nulo (oráculo, log-ingreso) | −0,0352\* (cobertura 0,65\*) | `simulacion_semisintetica_resumen.csv` | escenario `efecto_nulo`, `linear_dml`, `oraculo` | `poetry run python -m src.simulacion` |
| Error del CATE del Causal Forest (PEHE, oráculo; asignación aleatoria, confusión observada y efecto nulo) | 0,052 – 0,085\* | `simulacion_semisintetica_resumen.csv` | `causal_forest`, `oraculo`, esos tres escenarios, columna `pehe` | `poetry run python -m src.simulacion` |
| Repeticiones de la sensibilidad | 408 | `sensibilidad_semisintetica_resumen.csv` | columna `reps` | `poetry run python -m src.simulacion.sensibilidad_semisintetica` |
| Sesgo de LinearDML con efecto nulo (oraculo): regularización del proyecto frente a casi nula | −0,0363\* (z −27,7\*) frente a −0,0152\* (z −10,8\*) | `sensibilidad_semisintetica_resumen.csv` | `efecto_nulo`, `oraculo`, `sesgo` y `z_sesgo` | `poetry run python -m src.simulacion.sensibilidad_semisintetica` |
| Sesgo de LinearDML con efecto nulo (hotdeck): regularización del proyecto frente a casi nula | −0,0376\* (z −29,8\*) frente a −0,0161\* (z −11,6\*) | `sensibilidad_semisintetica_resumen.csv` | `efecto_nulo`, `hotdeck`, `sesgo` y `z_sesgo` | `poetry run python -m src.simulacion.sensibilidad_semisintetica` |

## Componente 3: reglas de focalización

| Cifra | Valor | Archivo | Dónde | Comando |
|---|---|---|---|---|
| Vigente (Hot-Deck): error de exclusión; % de la reducción ideal de FGT1 (proporcional / monto fijo) | 27,8 %\*; 75\* / 75\* | `reglas_focalizacion_resumen.csv` | regla `vigente_hotdeck`, presupuesto `hogares` | `poetry run python -m src.focalizacion.reglas_focalizacion` |
| Aleatoria: error de exclusión; % de la reducción ideal de FGT1 (proporcional / monto fijo) | 53,1 %\*; 47\* / 47\* | `reglas_focalizacion_resumen.csv` | regla `aleatoria`, presupuesto `hogares` | `poetry run python -m src.focalizacion.reglas_focalizacion` |
| Proxy de medios por ingreso: error de exclusión; % de la reducción ideal de FGT1 (proporcional / monto fijo) | 16,3 %\*; 84\* / 86\* | `reglas_focalizacion_resumen.csv` | regla `pmt_ingreso`, presupuesto `hogares` | `poetry run python -m src.focalizacion.reglas_focalizacion` |
| Proxy + CATE con vínculo: error de exclusión; % de la reducción ideal de FGT1 (proporcional / monto fijo) | 30,2 %\*; 68\* / 61\* | `reglas_focalizacion_resumen.csv` | regla `pmt_brecha_cate`, presupuesto `hogares` | `poetry run python -m src.focalizacion.reglas_focalizacion` |
| Proxy + CATE con Hot-Deck: error de exclusión; % de la reducción ideal de FGT1 (proporcional / monto fijo) | 66,6 %\*; 34\* / 27\* | `reglas_focalizacion_resumen.csv` | regla `pmt_brecha_cate_hd`, presupuesto `hogares` | `poetry run python -m src.focalizacion.reglas_focalizacion` |
| Repeticiones de las reglas | 300 | `reglas_focalizacion_resumen.csv` | columna `reps` | `poetry run python -m src.focalizacion.reglas_focalizacion` |
| Proxy de medios con el mismo dinero que la vigente: % del ideal (gasto relativo con el mismo número de hogares) | 87\* (0,99\*) | `reglas_focalizacion_resumen.csv` | `pmt_ingreso`, monto fijo, presupuestos `dinero` y `hogares` | `poetry run python -m src.focalizacion.reglas_focalizacion` |

## Repositorio

| Cifra | Valor | Archivo | Dónde | Comando |
|---|---|---|---|---|
| Pruebas automáticas | 320 | `tests/` | `pytest --collect-only` | `poetry run python -m pytest tests/` |
| Errores conocidos reintroducidos por la prueba de mutación | 83 | `tests/mutaciones.py` | lista `MUTACIONES` | `python tests/mutaciones.py` |
