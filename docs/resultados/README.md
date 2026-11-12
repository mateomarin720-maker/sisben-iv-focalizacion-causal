# Resultados: índice y hallazgos consolidados

Los resultados siguen la estructura de la tesis: una base de datos y
enlace entre fuentes y tres componentes. Cada carpeta tiene un documento
por paso; las salidas crudas están en `docs/reports/`. Historial de
correcciones: [`CHANGELOG_PENDIENTES.md`](../seguimiento/CHANGELOG_PENDIENTES.md).

Las cifras con asterisco (\*) son simuladas; las demás, datos reales.

| Carpeta | Pregunta | Tipo de evidencia |
|---|---|---|
| [`1_datos_y_enlace/`](#base-datos-y-enlace-entre-fuentes) | ¿Las fuentes están bien medidas y cómo se vinculan? | Datos reales |
| [`2_diagnostico_datos_reales/`](#componente-1-diagnóstico-con-datos-reales) | ¿Qué permiten decir los datos sobre la clasificación, la pobreza y el efecto? | Datos reales |
| [`3_simulacion/`](#componente-2-simulación-semisintética) | ¿Qué estimador recupera un efecto conocido según el vínculo entre fuentes? | Simulada\* |
| [`4_focalizacion/`](#componente-3-reglas-de-focalización) | ¿Cómo cambian los errores de focalización con otras reglas? | Simulada\* |

## Lo esencial

**Base.** El Hot-Deck vincula la GEIH y el Sisbén solo a nivel de celda:
dentro de cada celda el grupo se sortea, así que el grupo imputado no
lleva información del hogar receptor. Dos sorteos coinciden en el grupo
de un hogar solo el 34 % de las veces, aunque la distribución nacional
varía menos de 0,2 puntos. Los resultados están construidos y validados:
IPM-GEIH (8 de 15 privaciones) y pobreza monetaria reconstruida (33,2 %
frente a 31,8 % oficial; clasifica igual al 93,9 % de los hogares de la
base oficial).

**Componente 1: diagnóstico con datos reales.**
1. El DML sobre el grupo imputado da ≈0: es un placebo del emparejamiento,
   no el efecto del Sisbén. Lo predice el DAG y lo confirma la simulación.
2. Sin suponer que el sorteo reproduce la realidad, los datos no fijan ni
   el signo del efecto. Ninguno de los 50 parámetros de los modelos (ATE,
   ATT, ATU y CATE por subgrupo, en cinco resultados) tiene una cota de
   Fréchet que excluya el cero.
3. Errores de focalización con datos reales, como cotas por celda: al
   menos 39 % de los hogares A/B no son pobres monetarios (inclusión
   [38,6 %; 84,5 %]); la exclusión va de 0,9 % a 75,0 % y solo tiene piso
   en Putumayo, San Andrés y Bogotá.
4. Predecir el grupo del Sisbén y predecir la pobreza son problemas
   distintos: el primero acierta 53 %; el segundo es el que sirve para
   recomendar variables.

**Componente 2: simulación semisintética\*.** Con hogares reales y un
efecto conocido (+0,095\* en log-ingreso), todo estimador devuelve ≈0
cuando el tratamiento viene del Hot-Deck. Con el tratamiento verdadero,
regresión, DML y Causal Forest recuperan el efecto si la confusión es
observable, y ninguno si no lo es; solo la discontinuidad en el corte
resiste la confusión no observada, y necesita vínculo hogar por hogar.

**Componente 3: reglas de focalización\*.** Un proxy de medios con
variables del hogar logra 82-85 %\* de la reducción ideal de la brecha
(FGT1), frente a 60 %\* de la clasificación imputada, también con el mismo
dinero. Ordenar por el CATE estimado empeora la focalización, aun con el
doble de heterogeneidad del efecto.

## Base: datos y enlace entre fuentes

| Paso | Script | Documento |
|---|---|---|
| Hot-Deck y celdas con vivienda | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py`, `src/validacion/comparar_celdas_hotdeck_vivienda.py` | [`RESULTADOS_HOTDECK.md`](1_datos_y_enlace/RESULTADOS_HOTDECK.md) |
| Filtro del SDP (Bogotá) | `src/validacion/comparar_filtros_sdp.py` | [`COMPARACION_FILTROS_SDP.md`](1_datos_y_enlace/COMPARACION_FILTROS_SDP.md) |
| Outcome IPM-GEIH | `src/3_preprocesamiento.py` | [`METODOLOGIA_INDICADOR_IPM_GEIH.md`](../insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md) |
| Validación del IPM-GEIH contra la ECV y el IPM oficial | `src/validacion/validar_ipm_geih_ecv.py` | [`VALIDACION_IPM_GEIH_ECV.md`](1_datos_y_enlace/VALIDACION_IPM_GEIH_ECV.md) |
| Pobreza monetaria y contraste oficial | `src/indicadores/pobreza_monetaria_geih.py`, `src/3b_preprocesamiento_monetario.py`, `src/validacion/comparar_pobreza_monetaria_oficial.py` | [`RESULTADOS_POBREZA_MONETARIA.md`](1_datos_y_enlace/RESULTADOS_POBREZA_MONETARIA.md) |
| Representatividad del Sisbén | `src/validacion/verificar_representatividad_sisben.py` | [`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`](1_datos_y_enlace/RESULTADOS_REPRESENTATIVIDAD_SISBEN.md) |
| Variabilidad de la imputación | `src/diagnostico/variabilidad_hotdeck.py` | [`RESULTADOS_VARIABILIDAD_HOTDECK.md`](1_datos_y_enlace/RESULTADOS_VARIABILIDAD_HOTDECK.md) |

**Hot-Deck.** 290.968 hogares GEIH, 3.106.489 donantes del Sisbén
(nacional y Bogotá vigente). Celda: departamento, ciclo de vida del jefe,
tramo de cuartos y nivel de pisos homologado; 99,98 % en celda exacta
(993 celdas). Grupo asignado (ponderado): **A 14,2 · B 29,4 · C 34,4 ·
D 22,0 %**. Bogotá se filtra por vigencia al 31 de diciembre de 2024.
Pisos entró a la celda el 2026-11-02: sube la correlación entre
P(T | celda) y la pobreza monetaria de 0,20 a 0,29 sin costo de
cobertura; paredes no agrega nada encima.

**IPM-GEIH.** 8 de las 15 privaciones del IPM, en las 5 dimensiones; las
de pisos y paredes se retiraron por tautología con las covariables.
Score medio 1,45/8; **`POBRE_GEIH` (score ≥ 3) 17,1 %** de los hogares.
Validado contra la ECV (2026-11-11): con las mismas reglas, la ECV 2024 da
19,6 % y la GEIH 2024 20,4 % (ponderados), con correlación de 0,99 entre
departamentos; hogar por hogar, contra el IPM oficial 2024, ordena igual
(correlación 0,72) pero con K = 3 duplica su tasa (18,7 % frente a 9,2 %),
por la zona rural: en las cabeceras da 6,5 % frente a 5,9 %. K = 4 reproduce
la tasa nacional. `VALIDACION_IPM_GEIH_ECV.md`.

**Pobreza monetaria reconstruida.** Unidad de gasto, `INGLABO` más los
componentes laborales que no incluye, hot-deck de no respuesta laboral,
arriendo imputado, tres líneas de dominio y tasas por persona.

| | Reconstruida | Oficial DANE 2024 |
|---|---|---|
| FGT0 nacional | 33,2 % | 31,8 % |
| FGT0 13 ciudades / otras cabeceras / rural | 26,4 / 36,7 / 41,3 % | 24,0 / 34,8 / 42,5 % |
| FGT1 nacional | 13,5 % | 12,6 % |
| Pobreza extrema nacional | 12,5 % | 11,7 % |
| Gini nacional | 0,565 | 0,551 |

Sobre los 275.057 hogares que mide la base oficial (24 departamentos y
Bogotá), la reconstrucción clasifica igual al 93,9 %. La reconstrucción
es el resultado principal (cubre los 33 departamentos); la clasificación
oficial, la prueba de robustez.

**Representatividad.** Sobre el mismo marco (en 9 departamentos la GEIH solo
cubre la capital), la cobertura del Sisbén frente a la GEIH va de 4,8 % (Valle) a
26,9 % (Boyacá) en los departamentos del archivo nacional, y 16,8 % en el agregado:
el registro no es una muestra uniforme.

**Variabilidad de la imputación** (100 semillas; la 42 reproduce el
pipeline).

| Nivel | Resultado |
|---|---|
| Hogar | Dos sorteos coinciden en el grupo el 34,4 % de las veces y en A/B el 62,7 % |
| Celda | CV mediano de la proporción A/B 0,091 (0,049 ponderado) |
| Nacional | Desviación de 0,10 a 0,15 puntos por grupo (CV ≤ 0,007) |
| Contraste placebo | Con Rubin, `POBRE_GEIH` pasa de −0,0030 (IC sin el 0, semilla 42) a −0,00003 [−0,0036; +0,0036]; 49-55 % de la varianza viene de la imputación |

## Componente 1: diagnóstico con datos reales

| Paso | Script | Documento |
|---|---|---|
| Identificación (DAG) | `src/4_dag_identificacion.py` | [`IDENTIFICACION_CAUSAL.md`](2_diagnostico_datos_reales/IDENTIFICACION_CAUSAL.md) |
| DML: ATE, ATT y ATU (placebo) | `src/5_estimacion.py` | [`RESULTADOS_DML_ATE_ATT_ATU.md`](2_diagnostico_datos_reales/RESULTADOS_DML_ATE_ATT_ATU.md) |
| Causal Forest: CATE | `src/5_estimacion.py` | [`RESULTADOS_CAUSALFOREST_CATE.md`](2_diagnostico_datos_reales/RESULTADOS_CAUSALFOREST_CATE.md) |
| Diagnóstico de los controles | `src/5_estimacion.py` | [`DIAGNOSTICO_W_CELDA_EXACTA.md`](2_diagnostico_datos_reales/DIAGNOSTICO_W_CELDA_EXACTA.md) |
| Cotas de Fréchet-Manski | `src/diagnostico/cotas_frechet_manski.py`, `src/diagnostico/cotas_frechet_modelos.py` | [`RESULTADOS_FRECHET_MANSKI.md`](2_diagnostico_datos_reales/RESULTADOS_FRECHET_MANSKI.md) |
| Errores de inclusión y exclusión | `src/diagnostico/errores_focalizacion_frechet.py` | [`RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md`](2_diagnostico_datos_reales/RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md) |
| Selección de variables (OE1) | `src/diagnostico/seleccion_variables_lasso_shap.py` | [`RESULTADOS_SELECCION_VARIABLES_OE1.md`](2_diagnostico_datos_reales/RESULTADOS_SELECCION_VARIABLES_OE1.md) |
| Recomendación de variables | `src/diagnostico/variables_candidatas_pobreza.py`, `src/diagnostico/incidencia_transferencias.py` | [`RECOMENDACION_VARIABLES_POBREZA.md`](2_diagnostico_datos_reales/RECOMENDACION_VARIABLES_POBREZA.md) |

**Identificación.** Cinco DAG con chequeos formales de d-separación:
- separando la elegibilidad del donante de la del receptor, el grupo
  imputado es independiente del resultado dada la celda;
- la elegibilidad real del hogar no se identifica con variables
  observadas;
- usar la proporción de A/B de los registrados como la de toda la celda
  exige que el registro no dependa de lo no observado.

El diseño de una sola tabla (Sisbén III a IV) no se ejecuta con los
datos del proyecto.

**DML y Causal Forest (placebo).**

| Outcome | ATE, controles = celda exacta [IC 95 %] |
|---|---|
| `ipm_geih_score` | −0,0021 [−0,0092; +0,0051] |
| `POBRE_GEIH` | −0,0026 [−0,0049; −0,0002] |
| `log_ingreso_percapita` | +0,0006 [−0,0128; +0,0141] |
| `POBRE_MONETARIO` | −0,0002 [−0,0036; +0,0033] |
| `POBRE_MONETARIO_OFICIAL` (robustez, 24 deptos.) | −0,0005 [−0,0041; +0,0030] |

Siete de ocho ATE (dos especificaciones de controles) incluyen el cero;
el octavo (`POBRE_GEIH`) desaparece al combinar 100 sorteos del Hot-Deck.
El CATE medio también es ≈0.

**Cotas de Fréchet-Manski.**

| Outcome | Cota del ATE sin el supuesto del vínculo |
|---|---|
| `POBRE_GEIH` | [−0,261; +0,380] |
| `POBRE_MONETARIO` | [−0,418; +0,648] |
| `POBRE_MONETARIO_OFICIAL` (robustez, 24 deptos.) | [−0,407; +0,620] |

- **Con supuestos de monotonía**, la cota del ATE de pobreza monetaria
  queda en **[−0,405; 0]**. Los supuestos son: los A/B son al menos tan
  pobres y el programa no aumenta la pobreza de nadie. El ancho baja de
  1,40 a 0,41, pero el signo lo pone el supuesto. El ancho 1,40 es
  1 + 2Δ: la cota de Manski (ancho 1) más el doble del ancho medio de
  Fréchet de la conjunta no observada, Δ = 0,20
  (`docs/anexos_tesis/PROPOSICIONES.md`).
- **Una cota por cada parámetro de los modelos:** son entre 140 y 210
  veces más anchas que los IC del DML. En el IPM, el efecto va de −1,4 a
  +1,6 privaciones. La incertidumbre se concentra en lo rural.

**Errores de focalización con datos reales** (A/B frente a pobreza
monetaria, cotas por celda sumadas con los factores de expansión).
Exclusión [0,9 %; 75,0 %]; inclusión [38,6 %; 84,5 %]. La exclusión solo
tiene piso donde hay menos A/B que pobres: Putumayo (≥ 19,5 %), San
Andrés (≥ 24,9 %) y Bogotá (≥ 5,2 %).

**Selección y recomendación de variables.** Son dos problemas
predictivos distintos, y solo el segundo dice algo sobre errores de
focalización:

| Modelo | Objetivo | Resultado |
|---|---|---|
| Clasificación (OE1) | Grupo del Sisbén (A-D) | LASSO, Ridge y SHAP sobre 150.000 hogares: exactitud ≈53 % (línea base 30 %); `viv_pisos` es la variable más importante; sensibilidad 0,64 en A y 0,22-0,39 en D; con partición por municipio el F1 macro cae de 0,50 a 0,44 |
| Pobreza | Pobreza monetaria de la GEIH, independiente del Sisbén | Calcular la composición del hogar con lo que ya se recoge reduce el error de exclusión 5,40 puntos; todas las variables nuevas, 1,40. Solo la cuenta de ahorros (−0,86) tiene un aporte claro y estable |

La concordancia entre el grupo y la pobreza de un mismo hogar no se puede
medir: el grupo en la GEIH es imputado por celda. Por eso los errores de
focalización con datos reales se acotan por celda, y las reglas se
comparan en el mundo simulado. Las ayudas del gobierno declaradas llegan
a 2,8 millones de hogares, con 78,5 % del dinero en los dos quintiles
más pobres (descriptivo).

## Componente 2: simulación semisintética\*

| Paso | Script | Documento |
|---|---|---|
| Simulación de identificación (datos sintéticos) | `src/simulacion/simulacion_identificacion.py` | [`SIMULACION_IDENTIFICACION.md`](3_simulacion/SIMULACION_IDENTIFICACION.md) |
| Evaluación semisintética y sensibilidad | `src/simulacion/`, `src/simulacion/sensibilidad_semisintetica.py` | [`SIMULACION_SEMISINTETICA.md`](3_simulacion/SIMULACION_SEMISINTETICA.md) |

Covariables, celda, ingreso y línea de pobreza reales de la GEIH;
tratamiento y efecto simulados (P(T | celda) del Sisbén real). 432
repeticiones de 30.000 hogares, hasta que el error Monte Carlo de todas
las celdas quedó bajo el umbral.

| Estimación media | Verdadero | Oráculo | Vínculo 50 % | Hot-Deck |
|---|---|---|---|---|
| Confusión observada, LinearDML, log-ingreso | +0,095\* | +0,089\* | +0,040\* | −0,006\* |
| Confusión observada, LinearDML, pobreza | −0,033\* | −0,031\* | −0,014\* | +0,002\* |
| Confusión no observada fuerte, LinearDML, log-ingreso | +0,095\* | −0,778\* | −0,390\* | −0,003\* |
| Confusión no observada fuerte, LinearDML, pobreza | −0,033\* | +0,138\* | +0,070\* | +0,002\* |
| Regla de corte, RD, log-ingreso (efecto en el corte) | +0,090\* | +0,086\* | +0,042\* | −0,001\* |

Con Hot-Deck se pierde el efecto completo; con vínculo parcial se atenúa
en proporción a los hogares mal vinculados. Con confusión no observada
el signo se invierte aun con el tratamiento verdadero. Es una evaluación
controlada de identificación y de cuánto degrada la integración
imperfecta, no una validación universal de los estimadores.

## Componente 3: reglas de focalización\*

| Paso | Script | Documento |
|---|---|---|
| Reglas con el mismo número de hogares y con el mismo dinero | `src/focalizacion/reglas_focalizacion.py` | [`RESULTADOS_REGLAS_FOCALIZACION.md`](4_focalizacion/RESULTADOS_REGLAS_FOCALIZACION.md) |
| Heterogeneidad ampliada y compleja del efecto | `src/focalizacion/heterogeneidad_ampliada.py` | [`RESULTADOS_HETEROGENEIDAD_AMPLIADA.md`](4_focalizacion/RESULTADOS_HETEROGENEIDAD_AMPLIADA.md) |

Mismo mundo semisintético; presupuesto = los hogares A/B vigentes
(46,7 %). 300 repeticiones.

| Regla | Error de exclusión | % de la reducción ideal de FGT1 (proporcional / monto fijo) |
|---|---|---|
| Vigente (Hot-Deck) | 43,5 %\* | 60\* / 61\* |
| Aleatoria | 53,4 %\* | 47\* / 47\* |
| Proxy de medios por ingreso | 18,6 %\* | 82\* / 85\* |
| Proxy + CATE con vínculo | 26,1 %\* | 73\* / 72\* |
| Proxy + CATE con Hot-Deck | 54,9 %\* | 45\* / 44\* |

- **Mismo dinero:** el proxy de medios transfiere 13 %\* más que la
  vigente con el mismo número de hogares; con el mismo dinero baja de
  85\* a 80\* % del ideal y el orden de las reglas no cambia.
- **Heterogeneidad ampliada:** con el doble de variación del efecto y el
  Causal Forest viendo todos los modificadores, la regla con CATE sigue
  4 a 11 puntos\* por debajo de la misma regla con efecto constante.
- La regla vigente es la imputada por celda, no la del Sisbén real.

## Limitaciones generales

- El grupo del Sisbén es imputado por emparejamiento, no observado en la
  GEIH; el registro solo cubre hogares inscritos.
- IPM-GEIH con 8 de 15 privaciones; pobreza monetaria reconstruida.
- Sin ajuste por diseño muestral en la estimación.
- La participación en programas no se observa.
- `PER002` (edad en el Sisbén) corroborado indirectamente, no contra la
  ficha de ANDA.

## Cómo se generó

El orden de ejecución y los comandos están en `CLAUDE.md` (sección
"Validación") y en `docs/metodologia/ARQUITECTURA_Y_REPLICACION.md`.
