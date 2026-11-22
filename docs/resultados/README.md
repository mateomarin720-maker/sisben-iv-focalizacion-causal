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
de un hogar solo el 41 % de las veces, aunque la distribución nacional
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
   menos 41 % de los hogares A/B no son pobres monetarios (inclusión
   [41,2 %; 74,4 %]); la exclusión va de 2,8 % a 57,7 % y solo tiene un
   piso apreciable donde hay menos A/B que pobres (San Andrés, Putumayo,
   Bogotá, Cundinamarca, Guaviare).
4. Predecir el grupo del Sisbén y predecir la pobreza son problemas
   distintos: el primero acierta 53 %; el segundo es el que sirve para
   recomendar variables.

**Componente 2: simulación semisintética\*.** Con hogares reales y un
efecto conocido (+0,095\* en log-ingreso), todo estimador devuelve ≈0
cuando el tratamiento viene del Hot-Deck. Con el tratamiento verdadero,
la regresión con efectos fijos de celda recupera el efecto si la confusión es
observable, y ninguno si no lo es; solo la discontinuidad en el corte
resiste la confusión no observada, y necesita vínculo hogar por hogar.

**Componente 3: reglas de focalización\*.** Un proxy de medios con
variables del hogar logra 83-86 %\* de la reducción ideal de la brecha
(FGT1), frente a 72-73 %\* de la clasificación imputada, también con el mismo
dinero. Ordenar por el CATE estimado empeora la focalización, aun con el
doble de heterogeneidad del efecto.

## Base: datos y enlace entre fuentes

| Paso | Script | Documento |
|---|---|---|
| Hot-Deck y celdas con vivienda | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py`, `src/validacion/comparar_celdas_hotdeck_vivienda.py` | [`RESULTADOS_HOTDECK.md`](1_datos_y_enlace/RESULTADOS_HOTDECK.md) |
| Filtro del SDP (Bogotá) | `src/validacion/comparar_filtros_sdp.py` | [`COMPARACION_FILTROS_SDP.md`](1_datos_y_enlace/COMPARACION_FILTROS_SDP.md) |
| Outcome IPM-GEIH | `src/3_preprocesamiento.py` | [`METODOLOGIA_INDICADOR_IPM_GEIH.md`](../metodologia/METODOLOGIA_INDICADOR_IPM_GEIH.md) |
| Validación del IPM-GEIH contra la ECV y el IPM oficial | `src/validacion/validar_ipm_geih_ecv.py` | [`VALIDACION_IPM_GEIH_ECV.md`](1_datos_y_enlace/VALIDACION_IPM_GEIH_ECV.md) |
| Pobreza monetaria y contraste oficial | `src/indicadores/pobreza_monetaria_geih.py`, `src/3b_preprocesamiento_monetario.py`, `src/validacion/comparar_pobreza_monetaria_oficial.py` | [`RESULTADOS_POBREZA_MONETARIA.md`](1_datos_y_enlace/RESULTADOS_POBREZA_MONETARIA.md) |
| Representatividad del Sisbén | `src/validacion/verificar_representatividad_sisben.py` | [`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`](1_datos_y_enlace/RESULTADOS_REPRESENTATIVIDAD_SISBEN.md) |
| Variabilidad de la imputación | `src/diagnostico/variabilidad_hotdeck.py` | [`RESULTADOS_VARIABILIDAD_HOTDECK.md`](1_datos_y_enlace/RESULTADOS_VARIABILIDAD_HOTDECK.md) |
| Imputación fraccional (FHDI), alternativa al sorteo | `src/emparejamiento/fhdi/` | [`RESULTADOS_FHDI.md`](1_datos_y_enlace/RESULTADOS_FHDI.md) |

**Hot-Deck.** 290.968 hogares GEIH, 3.106.489 donantes del Sisbén
(nacional y Bogotá vigente). Celda: departamento, ciclo de vida del jefe,
tramo de cuartos, nivel de pisos homologado, personas del hogar (1-2 / 3+)
y menores de 18 años (0 / 1 / 2+); 99,92 % en celda exacta (3.721
celdas). Grupo asignado (ponderado): **A 13,6 · B 28,6 · C 36,4 · D
21,4 %**. El donante se sortea según su factor de expansión: el Sisbén
nacional de ANDA es una muestra (1,83 millones de hogares, 11,4 millones
expandidos) que sobrerrepresenta A y B; sin ponderar (hasta el
2026-11-21) salía A/B 44,7 % en vez de 42,2 %. Personas y menores
entraron el 2026-11-14: cierran el ancho de
la cota de Fréchet por celda de 0,200 a 0,149 y suben la correlación de
P(T | celda) con la pobreza monetaria de 0,29 a 0,41; el resto del
catálogo no aporta, no homologa o es una privación del IPM. Bogotá se filtra por vigencia al 31 de diciembre de 2024.
Pisos entró a la celda el 2026-11-02: sube la correlación entre
P(T | celda) y la pobreza monetaria de 0,20 a 0,29 sin costo de
cobertura; paredes no agrega nada encima.

**IPM-GEIH.** 8 de las 15 privaciones del IPM, en las 5 dimensiones; las
de pisos y paredes se retiraron por tautología con las covariables.
Score medio 1,38/8; **`POBRE_GEIH` (score ≥ 3) 13,9 %** de los hogares (14,5 % ponderado; 17,1 % antes de corregir la vivienda por zona).
Validado contra la ECV y el IPM oficial 2024: con las mismas reglas, la
ECV 2024 da 14,2 % y la GEIH 2024 14,5 % (ponderados), con correlación de
0,99 entre departamentos; hogar por hogar, el proxy da 13,8 % frente a
9,2 % oficial, kappa 0,51 y correlación de rangos 0,76. K = 3 es el mejor
corte. La validación encontró que vivienda usaba la regla urbana en el
campo; se corrigió el 2026-11-11 y se regeneró el 2026-11-12
(`VALIDACION_IPM_GEIH_ECV.md`).

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

Sobre los 275.057 hogares que mide la base oficial (23 departamentos y
Bogotá), la reconstrucción clasifica igual al 93,9 %. La reconstrucción
es el resultado principal (cubre los 33 departamentos); la clasificación
oficial, la prueba de robustez.

**Representatividad.** Sobre el mismo marco (en 9 departamentos la GEIH solo
cubre la capital), con el Sisbén nacional expandido por su `fex`, la
cobertura frente a la GEIH va de 55,3 % (Chocó) a 97,3 % (Norte de
Santander) en los departamentos del archivo nacional y es 41,5 % en Bogotá;
68,3 % en el agregado (16,8 % contando filas, hasta el 2026-11-21). Sube con
la pobreza de la celda, y dentro de la celda los inscritos no se parecen
del todo a la población: el registro no es una muestra uniforme, y el grupo
imputado es la clasificación que el hogar tendría si se inscribiera.

**Variabilidad de la imputación** (100 semillas; la 42 reproduce el
pipeline).

| Nivel | Resultado |
|---|---|
| Hogar | Dos sorteos coinciden en el grupo el 42,5 % de las veces y en A/B el 71,2 % |
| Celda | CV mediano de la proporción A/B 0,150 (0,120 ponderado): la celda más fina tiene menos hogares por celda |
| Nacional | Desviación de 0,08 a 0,16 puntos por grupo (CV ≤ 0,005) |
| Contraste placebo | Con Rubin, `POBRE_GEIH` da +0,0002 [−0,0037; +0,0041] (semilla 42: −0,0007); 47-51 % de la varianza viene de la imputación |

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
| `ipm_geih_score` | +0,0058 [−0,0022; +0,0137] |
| `POBRE_GEIH` | +0,0003 [−0,0025; +0,0031] |
| `log_ingreso_percapita` | −0,0014 [−0,0157; +0,0129] |
| `POBRE_MONETARIO` | +0,0002 [−0,0036; +0,0040] |
| `POBRE_MONETARIO_OFICIAL` (robustez, 23 deptos. y Bogotá) | +0,0007 [−0,0032; +0,0046] |

Con la celda exacta los cinco ATE incluyen el cero. Con el proxy, los
cinco lo excluyen porque el proxy no cruza las variables de la celda
(`RESULTADOS_DML_ATE_ATT_ATU.md`); no es un efecto. Un sorteo subestima
la incertidumbre: con 100 sorteos y Rubin, `POBRE_GEIH` da [−0,0037;
+0,0041]. El CATE medio también es ≈0.

- **Dentro de la celda (2026-11-20):** la regresión con efectos fijos de
  celda y el LinearDML con Y y T sin la media de la celda dan lo mismo
  que el LinearDML vigente (diferencias de 0,004 o menos, todos los IC
  con el cero): con 78 hogares por celda no aparece el sesgo de la
  simulación.
- **Con el enlace fraccional (FHDI)** el tratamiento es la proporción de
  A/B de la celda y no varía dentro de ella: el DML es **no
  identificable** con las dos especificaciones de controles.

**Cotas de Fréchet-Manski.**

| Outcome | Cota del ATE sin el supuesto del vínculo |
|---|---|
| `POBRE_GEIH` | [−0,260; +0,308] |
| `POBRE_MONETARIO` | [−0,361; +0,637] |
| `POBRE_MONETARIO_OFICIAL` (robustez, 23 deptos. y Bogotá) | [−0,359; +0,619] |

- **Con supuestos de monotonía**, la cota del ATE de pobreza monetaria
  queda en **[−0,359; 0]**. Los supuestos son: los A/B son al menos tan
  pobres y el programa no aumenta la pobreza de nadie. El ancho baja de
  1,30 a 0,36, pero el signo lo pone el supuesto. El ancho 1,30 es
  1 + 2Δ: la cota de Manski (ancho 1) más el doble del ancho medio de
  Fréchet de la conjunta no observada, Δ = 0,149
  (`docs/anexos_tesis/PROPOSICIONES.md`). Con la celda del 2026-11-02,
  Δ = 0,200 y el ancho era 1,40: personas y menores en la celda cierran
  la cota 0,10.
- **Una cota por cada parámetro de los modelos:** son entre 100 y 180
  veces más anchas que los IC del DML. En el IPM, el efecto va de −1,3 a
  +1,5 privaciones. La incertidumbre se concentra en lo rural.

**Errores de focalización con datos reales** (A/B frente a pobreza
monetaria, cotas por celda sumadas con los factores de expansión).
Exclusión [2,8 %; 57,7 %]; inclusión [41,2 %; 74,4 %] (con la celda
anterior, [0,9 %; 75,0 %] y [38,6 %; 84,5 %]). La exclusión solo tiene
piso donde hay menos A/B que pobres: San Andrés (≥ 35,0 %), Putumayo
(≥ 26,0 %), Bogotá (≥ 11,5 %), Cundinamarca y Guaviare (≥ 8 %).

**Selección y recomendación de variables.** Son dos problemas
predictivos distintos, y solo el segundo dice algo sobre errores de
focalización:

| Modelo | Objetivo | Resultado |
|---|---|---|
| Clasificación (OE1) | Grupo del Sisbén (A-D) | LASSO, Ridge y SHAP sobre 150.000 hogares: exactitud ≈53 % (línea base 30 %); `viv_pisos` es la variable más importante; sensibilidad 0,64 en A y 0,22-0,39 en D; con partición por municipio el F1 macro cae de 0,50 a 0,44 |
| Pobreza | Pobreza monetaria de la GEIH, independiente del Sisbén | Calcular la composición del hogar con lo que ya se recoge reduce el error de exclusión 5,64 puntos; todas las variables nuevas, 1,37. La cuenta de ahorros (−0,84) tiene el aporte más claro y estable; el estrato pasa el umbral por poco (−0,55, "recomendar"; con el presupuesto anterior, −0,49, "considerar") |

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
tratamiento y efecto simulados (P(T | celda) del Sisbén real). 456
repeticiones de 30.000 hogares, hasta que el error Monte Carlo de todas
las celdas quedó bajo el umbral (2026-11-15, celda con personas y
menores).

| Estimación media | Verdadero | Oráculo | Vínculo 50 % | Hot-Deck |
|---|---|---|---|---|
| Confusión observada, regresión EF celda, log-ingreso | +0,095\* | +0,090\* | +0,045\* | +0,001\* |
| Confusión observada, LinearDML, log-ingreso | +0,095\* | +0,059\* | +0,011\* | −0,034\* |
| Confusión observada, regresión EF celda, pobreza | −0,033\* | −0,032\* | −0,016\* | +0,000\* |
| Confusión no observada fuerte, regresión EF celda, log-ingreso | +0,095\* | −0,860\* | −0,431\* | −0,002\* |
| Confusión no observada fuerte, regresión EF celda, pobreza | −0,033\* | +0,129\* | +0,065\* | +0,000\* |
| Regla de corte, RD, log-ingreso (efecto en el corte) | +0,093\* | +0,094\* | +0,048\* | +0,001\* |

LinearDML queda sesgado (−0,035\* con efecto nulo) porque la encuesta
simulada deja ≈8 hogares por celda: la regularización y el ajuste
cruzado de sus modelos auxiliares dejan confusión entre celdas. Con
datos reales (78 hogares por celda en promedio) no aparece: LinearDML,
casi sin regularizar y la regresión con efectos fijos dan el mismo ATE
(`SIMULACION_SEMISINTETICA.md`, punto 8).

Con Hot-Deck se pierde el efecto completo; con vínculo parcial se atenúa
en proporción a los hogares mal vinculados. Con confusión no observada
el signo se invierte aun con el tratamiento verdadero. Es una evaluación
controlada de identificación y de cuánto degrada la integración
imperfecta, no una validación universal de los estimadores.

## Componente 3: reglas de focalización\*

| Paso | Script | Documento |
|---|---|---|
| Reglas con el mismo número de hogares y con el mismo dinero | `src/focalizacion/reglas_focalizacion.py` | [`RESULTADOS_REGLAS_FOCALIZACION.md`](4_focalizacion/RESULTADOS_REGLAS_FOCALIZACION.md) |
| Heterogeneidad ampliada y compleja del efecto | `src/focalizacion/heterogeneidad_ampliada.py`, `src/focalizacion/reglas_ampliadas.py heterogeneidad` | [`RESULTADOS_HETEROGENEIDAD_AMPLIADA.md`](4_focalizacion/RESULTADOS_HETEROGENEIDAD_AMPLIADA.md) |

Mismo mundo semisintético; presupuesto = los hogares A/B vigentes
(47,0 %). 300 repeticiones.

| Regla | Error de exclusión | % de la reducción ideal de FGT1 (proporcional / monto fijo) |
|---|---|---|
| Vigente (Hot-Deck) | 27,8 %\* | 75\* / 75\* |
| Aleatoria | 53,1 %\* | 47\* / 47\* |
| Proxy de medios por ingreso | 16,3 %\* | 84\* / 86\* |
| Proxy + CATE con vínculo | 30,2 %\* | 68\* / 61\* |
| Proxy + CATE con Hot-Deck | 66,6 %\* | 34\* / 27\* |

- **Mismo dinero:** con la celda nueva el proxy de medios gasta lo
  mismo que la vigente (0,99\*); con el mismo dinero queda en 87\* % del
  ideal y el orden de las reglas no cambia.
- **Heterogeneidad ampliada:** con el doble de variación del efecto y el
  Causal Forest viendo todos los modificadores, la regla con CATE sigue
  9 a 16 puntos\* por debajo de la misma regla con efecto constante. Con
  el efecto verdadero, la ganancia sobre el PMT sube a 1,3-3,0\* puntos;
  el LinearDML le gana al bosque si el efecto es lineal y pierde si no.
- **Causal Forest dentro de la celda y enlace fraccional (2026-11-19/20):**
  sin el sesgo de estimar la celda, el CATE con vínculo mejora 3 a 13
  puntos\* y queda en 74-79 %\* del ideal, todavía 2 a 11 puntos\* bajo
  el PMT por brecha; con Hot-Deck queda en el azar (49-55 %\*), no por
  debajo. Con el enlace fraccional sin vínculo el CATE no es
  identificable, y la vigente da lo mismo que con el sorteo (74-77 %\*).
  La conclusión no cambia (`RESULTADOS_REGLAS_FOCALIZACION.md`,
  `RESULTADOS_HETEROGENEIDAD_AMPLIADA.md`).
- **Controles (2026-11-14):** con el efecto verdadero en vez del CATE
  estimado, la regla llega a 85\* / 87\* % del ideal, casi igual que el
  proxy de medios; con un LinearDML, que tiene la forma correcta del
  efecto, 70\* / 62\*, como el Causal Forest. Los dos CATE además salen
  sesgados en su nivel (ATE +0,06\* frente a +0,095\*) por las celdas
  con pocos hogares de entrenamiento. El problema no es el modelo:
  con esta heterogeneidad, conocer el efecto aporta casi nada.
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
