# Changelog del proyecto

Formato: más reciente primero. Rama de trabajo: `main`.

## 2026-11-12 (43) — Modelos regenerados con el IPM-GEIH corregido

### Cambiado
- Muestra de estimación regenerada con la vivienda por zona (`POBRE_GEIH` 20,4 % → 14,5 %
  ponderado, puntaje medio 1,45 → 1,38) y vuelta a correr la secuencia de `CLAUDE.md` en los
  módulos que usan el IPM-GEIH. El Hot-Deck y los resultados monetarios no cambian.
- DML con la celda exacta: `POBRE_GEIH` −0,0021 [−0,0045; +0,0004] (antes −0,0026, IC sin el
  cero); ahora los 8 ATE incluyen el cero. Rubin con 100 sorteos: −0,000004 [−0,0033; +0,0033],
  48,8 % de la varianza por la imputación.
- Fréchet-Manski de `POBRE_GEIH`: [−0,256; +0,278] (ancho 0,534, antes 0,641); 120 celdas
  degeneradas (antes 130). Errores de focalización A-B: exclusión [0,4 %; 65,8 %].
- Validación contra el IPM 2024 y la ECV: secciones A y B con el proxy corregido (13,8 %
  frente a 9,2 %, kappa 0,51; ECV 14,2 % y GEIH 14,5 %).
- Variables candidatas: `hog_sanitario` y `hog_agua` salen de la referencia al predecir el
  IPM-GEIH (son componentes del indicador), con prueba y mutación. Migración y condición
  campesina siguen aportando solo en el IPM-GEIH.

## 2026-11-11 (42) — IPM-GEIH: vivienda con la definición oficial por zona

### Corregido
- `sin_alcantarillado`, `sin_acueducto` y `hacinamiento` usaban la regla urbana en todo el
  país. Ahora siguen el algoritmo oficial del IPM (sección 4.5): en lo rural, excretas por
  `P5020` (inodoro sin conexión, bajamar o sin servicio), agua por `P5050` y hacinamiento
  > 3; en lo urbano, sin alcantarillado, sin acueducto y ≥ 3. Códigos verificados contra el
  diccionario y los datos (`tests/test_armonizacion.py`). Medido en memoria: el proxy pasa de
  18,7 % a 13,8 % (oficial 9,2 %), kappa de 0,41 a 0,51; rural de 63,7 % a 37,0 % (21,5 %);
  K = 3 sigue siendo el mejor corte. Prueba y mutación (269 pruebas, 59 de 59).

La muestra de estimación se regeneró en la entrada 43.

## 2026-11-11 (41) — Validación del IPM-GEIH contra la ECV

### Agregado
- `src/validacion/validar_ipm_geih_ecv.py` y `VALIDACION_IPM_GEIH_ECV.md`: el proxy de 8
  privaciones calculado en la ECV con las mismas reglas, leyendo de Azure en memoria. Hogar
  por hogar contra el IPM oficial 2024 (que sale de la ECV 2024): correlación 0,72,
  concordancia 85,6 %, sensibilidad 73,5 %, kappa 0,41 (K = 3); la sobreestimación es
  rural (cabeceras 6,5 % frente a 5,9 % oficial; resto 63,7 % frente a 21,5 %). ECV 2024 frente a GEIH 2024: 19,6 % y 20,4 %; correlación 0,99 entre los 24
  departamentos completos y 0,97 entre las 9 cabeceras de capital.
- Reglas del proxy en un solo lugar (`src/indicadores/ipm_proxy.py`), usadas por
  `3_preprocesamiento.py` (salida idéntica a la anterior) y por la validación. Prueba y
  mutación (267 pruebas, 58 de 58).
- ECV 2024 en el catálogo de datos (en Azure bajo `ecv/`).

### Corregido
- La base del IPM en `data/0_raw/ipm/nacional` es la de **2025** (catálogo 903); la de 2024
  está en Azure, `0_raw/ipm/2024/`, y es la que se usa.
- La tasa oficial que justificaba K = 3 (13,0 %) era la tasa sin ponderar de la base 2025;
  la oficial 2024, ponderada por hogares, es 9,2 %, y el corte más cercano es K = 4 (7,5 % en
  la base del IPM, 6,7 % en la GEIH). K = 3 se mantiene: cambiarlo es decisión del equipo.

## 2026-11-11 (40) — Figuras APA, factores de expansión y cobertura sobre el mismo marco

### Corregido
- **Cobertura del Sisbén mayor al 100 %.** En los 9 departamentos de la Orinoquía, la
  Amazonía y San Andrés la GEIH solo encuesta la cabecera de la capital (`CLASE` 1, `AREA`
  igual al departamento), y se dividía el Sisbén de todo el departamento entre ella
  (Putumayo 154 %). Ahora el Sisbén se cuenta solo en la cabecera de la capital: ninguna
  razón pasa de 41,5 % (Bogotá, que es el registro del SDP); en el archivo nacional va de
  4,8 % (Valle) a 26,9 % (Boyacá), 5,6 veces; 16,8 % en el agregado. Prueba y mutación
  (263 pruebas, 57 de 57 mutaciones).

### Agregado
- Figuras en formato APA con su número, título y nota (`docs/anexos_tesis/FIGURAS_APA.md`):
  DAG de la ignorabilidad condicional (sección 2.2), tres pasos del DML, DAG de la
  Proposición 1 y las nubes de una celda\* que dibujó el director. Los DAG comprueban su
  nota con d-separación al generarse.
- Uso del factor de expansión por análisis (`ARQUITECTURA_Y_REPLICACION.md`).
- Catálogo 819 de la GEIH 2024 y referencias APA de los conjuntos de datos del DANE.

## 2026-11-11 (39) — Anotaciones del director sobre el borrador

### Agregado
- `docs/anexos_tesis/PROPOSICIONES.md`: Proposiciones 1 a 3 con su prueba (el T imputado
  da efecto cero; la señal cae a L × efecto con una fracción L enlazada, y la fórmula con
  enlaces falsos; con imputación total la mitad de la varianza viene del sorteo) y la
  derivación del ancho de la cota sin supuestos con fuentes no enlazadas, 1 + 2Δ = 1,40.
- `src/diagnostico/proposiciones.py` las comprueba por Monte Carlo y con el archivo de
  cotas publicado (`docs/reports/proposiciones.txt`); `tests/test_proposiciones.py`.
- Figuras de la estabilidad del Hot-Deck (por celda y por hogar) y de la importancia de
  las variables del OE1.
- Anexo de trazabilidad: fracción de Rubin por resultado (48,9 %, 48,8 %, 54,5 %), pobreza
  extrema, FGT1 y Gini frente a la oficial, Δ de la cota, conteo de las 166 celdas de la
  simulación y fuerza γ de la confusión no observada.
- `CITATION.cff`. `tests/test_dependencias.py`: las versiones de `requirements-pruebas.txt`
  deben ser las que resolvió `poetry.lock` (un solo origen de versiones).
- Bibliografía: estado de las referencias que el borrador marca (Engstrom et al., Kasy y
  Sautmann, Roth et al., McBride y Nichols, BID, DNP-BID, DANE, Mora et al., Fedesarrollo,
  Castañeda) y las que faltan para las proposiciones.

### Hallazgo
- El rango 49 %-55 % de la varianza que viene del sorteo no son tres resultados: con
  M = 100 sorteos la fracción estimada varía unos ±3 puntos alrededor de 0,5
  (Proposición 3; en poblaciones sintéticas va de 0,45 a 0,58).

## 2026-11-11 (38) — Apoyo al documento escrito y dos cifras corregidas

### Agregado
- `docs/anexos_tesis/`: anexo de trazabilidad (cada cifra con su archivo y comando),
  contrato de datos como tabla, modelo base y validación de los ejercicios predictivos,
  bibliografía verificada con DOI y cinco figuras (arquitectura, cotas por celda, errores
  de exclusión por departamento, atenuación con el vínculo y propensión por celda).
- `src/utils/anexo_trazabilidad.py` y `src/utils/figuras_tesis.py` los generan desde
  `docs/reports/`; el anexo falla si una cifra no está en su fuente. Prueba en
  `tests/test_anexo_trazabilidad.py`.

### Corregido
- Regla aleatoria: error de exclusión 53,4 % (no 53,3 %) y 46,6 % del ideal con efecto
  proporcional (no 46,7 %), en el índice, la guía y el documento de reglas.
- "Con monto fijo son iguales en las reglas sin CATE": el proxy por brecha, sin CATE,
  también cambia (exclusión 19,0 % frente a 19,7 %).

## 2026-11-11 (37) — Módulo de simulación completo y regularización como sensibilidad

### Agregado
- Paso 6 del diseño, modo simulado: `src/simulacion/calibrar.py` resume la GEIH y el Sisbén
  en `parametros/poblacion_2024.json` (solo agregados; ningún grupo de menos de 30 hogares)
  y `generador.py` produce hogares sintéticos con las columnas canónicas. Reproduce zona,
  sexo del jefe, ingreso y P(T | celda); la pobreza sale en 30,0 % frente a 28,0 % y la
  relación entre P(T | celda) y pobreza se atenúa (0,24 frente a 0,29).
- Paso 7, modo de datos propios: `datos_propios.py` estima con el grupo observado (DML con
  la celda exacta y cota de Fréchet) y rotula el Hot-Deck como placebo. Con la GEIH
  enlazada reproduce exactamente `5_estimacion.py` y las cotas publicadas.
- `python -m src.simulacion simulado | propios --salida CARPETA`; sin subcomando, la corrida
  de la tesis igual que antes (misma firma, mismas salidas).
- Pruebas en `tests/test_simulacion_generador.py` y dos mutaciones.

### Cambiado
- La regularización de los modelos auxiliares (alpha 1, C 10) queda como parámetro de
  `_modelos_auxiliares`; la casi nula (`CASI_SIN_REGULARIZAR`) es la sensibilidad. Se probó
  como vigente y se revirtió para que las cifras del documento sigan trazables:
  `5_estimacion.py` reproduce su reporte publicado línea por línea. Prueba y mutación.
- `RESULTADOS_CAUSALFOREST_CATE.md`: la heterogeneidad no es pequeña, no es identificable
  con estas fuentes (cotas por subgrupo).

## 2026-11-10 (36) — Auditoría del repositorio para el jurado

### Cambiado
- README raíz, `docs/README.md` e índice de resultados organizados en la base y los tres
  componentes; `src/README.md` y `src/diagnostico/README.md` reescritos.
- Conteos al día (243 pruebas, 53 mutaciones) en README, guía, resumen, arquitectura,
  `tests/README.md` y `requirements-pruebas.txt`.
- Sin frases que propongan pedir datos nuevos: DPS figura como fuera del alcance, y la
  discontinuidad con puntaje continuo y el diseño Sisbén III a IV como no aplicables con
  datos reales.
- La comparación de proxies del IPM queda marcada como insumo (fases 3 a 5 no ejecutadas).
- Salida de consola de los DAG regenerada.

- `pyproject.toml` sin las dependencias que el código no usa (`dowhy`, `causal-learn`,
  `graphviz`, `seaborn`, `xgboost`, `jupyterlab`). `poetry.lock` regenerado: de 152 a 54
  paquetes, sin cambio de versión en ninguno de los que quedan.
- Límite de 60 minutos en la integración continua: con 53 errores, la prueba de mutación
  pasa de 30 minutos.

## 2026-11-10 (35) — Representatividad del Sisbén con los hogares de un mes promedio

### Corregido
- `verificar_representatividad_sisben.py` sumaba los factores de expansión de los 12 meses
  de la GEIH (214,9 millones de hogares en vez de 17,9). Las coberturas salían 12 veces
  menores: ahora 4,8 % (Valle) a 154 % (Putumayo), 17,3 % nacional, en vez de 0,4 % a
  12,8 % y 1,4 %. El factor de variación (32 veces) no cambia. Prueba y mutación.
- En Putumayo y Vichada la GEIH expande a pocos hogares y la razón supera o roza el 100 %;
  ahí compara marcos distintos y no se lee como cobertura.
- Los demás scripts ya dividían por 12 o solo usan proporciones.

## 2026-11-10 (34) — Código y resultados organizados por componente

### Cambiado
- `src/` y `docs/resultados/` siguen la estructura de la tesis: una base de datos y enlace y
  tres componentes (diagnóstico con datos reales, simulación semisintética y reglas de
  focalización). Los nombres de los archivos no cambian; solo la carpeta.

| Antes | Ahora |
|---|---|
| `src/estimacion/` | `src/diagnostico/` |
| `src/validacion/variabilidad_hotdeck.py` | `src/diagnostico/` |
| `src/validacion/reglas_focalizacion.py`, `heterogeneidad_ampliada.py` | `src/focalizacion/` |
| `src/validacion/sensibilidad_semisintetica.py`, `simulacion_identificacion.py` | `src/simulacion/` |
| `docs/resultados/*.md` | `docs/resultados/{1_datos_y_enlace, 2_diagnostico_datos_reales, 3_simulacion, 4_focalizacion}/` |

- `src/validacion/` queda solo con los chequeos de calidad de los datos.
- Rutas, imports, comandos de validación, pruebas y mutaciones actualizados; enlaces
  verificados. Las entradas anteriores de este changelog conservan las rutas de su fecha.
- Respaldo del estado anterior: etiqueta `respaldo/antes-reorganizacion`.

## 2026-11-10 (33) — DAG del proyecto rehechos

### Cambiado
- `src/4_dag_identificacion.py`: diagramas con cajas ajustadas al texto, colores por fuente
  (GEIH, Sisbén, ambas, Hot-Deck, simulación), borde punteado para lo no observado, leyenda
  y flechas que no cruzan cajas. El diagrama literal resalta el camino que X no bloquea.
- Diseño refinado: la celda X (depto, ciclo de vida, cuartos, pisos) se separa de Z (zona,
  sexo del jefe, paredes); el resultado incluye pobreza monetaria, IPM e ingreso.

### Agregado
- `dag_fusion_fuentes.png`: qué observa cada base y el registro en el Sisbén. El registro solo
  es ignorable si no depende de U: es el supuesto de las cotas y de los errores de focalización.
- `dag_simulacion.png`: el generador semisintético; ajustar por X y Z identifica el efecto solo
  sin confusión no observada, y el T del Hot-Deck es independiente de Y dada la celda.
- `IDENTIFICACION_CAUSAL.md` regenerado con los 11 chequeos de d-separación; prueba y mutación.

## 2026-11-10 (32) — Errores de inclusión y exclusión con datos reales

### Agregado
- `src/estimacion/errores_focalizacion_frechet.py`: errores de focalización del Sisbén con
  datos reales, como cotas de Fréchet por celda sumadas con los factores de expansión de la
  GEIH, a nivel nacional y por departamento (comentario del director).
- A/B frente a pobreza monetaria: exclusión [0,9 %; 75,0 %], inclusión [38,6 %; 84,5 %].
  Al menos 39 % de los A/B no son pobres monetarios. La exclusión solo tiene piso en
  Putumayo (19,5 %), San Andrés (24,9 %) y Bogotá (5,2 %).
- Resultados: `RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md`. Pruebas y una mutación.

## 2026-11-09 (31) — Una cota de Fréchet por cada parámetro de los modelos

### Agregado
- `src/estimacion/cotas_frechet_modelos.py`: cota del ATE, ATT y ATU del DML y del CATE
  por subgrupo del Causal Forest (zona, sexo del jefe, paredes), en los cinco resultados,
  incluidos el IPM continuo y el log-ingreso.
- Ninguno de los 50 parámetros excluye el cero; las cotas son 140 a 210 veces más anchas
  que los IC del DML. Las binarias del ATE reproducen las publicadas.
- Sexo del jefe verificado con la ficha del Sisbén IV (pregunta 47) y GEIH (`P3271`):
  1 = hombre, 2 = mujer en las dos fuentes.

## 2026-11-09 (30) — Heterogeneidad ampliada del efecto en las reglas de focalización

### Agregado
- `src/validacion/heterogeneidad_ampliada.py`: las reglas con un efecto de desviación
  0,06 (el doble) y cinco modificadores más (ampliado) o con interacción, forma no lineal
  y departamentos (complejo). El CATE sigue empeorando la focalización (4 a 11 puntos\*).

### Corregido
- `ajustar_bosque` armaba el codificador de los modelos auxiliares para las 3 X de base:
  con más X, la celda (el confusor) quedaba fuera sin dar error (ATE −0,25\* en vez de
  +0,095\*). Prueba con confusión por celda y mutación. El nivel básico no cambia.

## 2026-11-09 (29) — Mismo dinero en las reglas de focalización y ajustes de redacción

### Agregado
- Presupuesto en dinero (monto fijo): todas las reglas gastan lo mismo que la vigente.
  El orden no cambia; el proxy de medios baja de 85\* a 80\* % del ideal. Columna
  `gasto_rel`. Las filas con el mismo número de hogares se reproducen exactamente.

### Cambiado
- `SIMULACION_SEMISINTETICA.md`: papel de cada variable en el DAG y alcance de la
  evaluación (controlada, no una validación universal).
- Índice de resultados: separa el modelo que predice el grupo del Sisbén (§7) del que
  predice la pobreza (§12).
- `RESULTADOS_REGLAS_FOCALIZACION.md`: qué representa el CATE con monto fijo.

## 2026-11-08 (28) — Simulación regenerada con la cadena de respaldos

### Cambiado
- Se regeneran la evaluación semisintética, las reglas de focalización y la sensibilidad
  con la cadena de respaldos del Hot-Deck y las marcas de resultado simulado.
- Ninguna conclusión cambia. La estimación que más se mueve en las tablas principales
  cambia 0,003; la exclusión de PMT + CATE con Hot-Deck pasa de 55,5 % a 54,9 %.
- Se matiza la causa del sesgo de LinearDML: casi sin regularizar deja de ser
  significativo con oráculo y vínculo del 50 %, pero no con Hot-Deck (z −2,6).
- Asterisco en las tablas y cifras simuladas de los documentos de resultados.

## 2026-11-08 (27) — Anexo de arquitectura y replicación

### Nuevo
- `docs/metodologia/ARQUITECTURA_Y_REPLICACION.md`: capas de datos con su volumen,
  flujo, controles de calidad y tres rutas de réplica.

## 2026-11-08 (26) — Depuración del repositorio

### Cambiado
- Quedan las ramas `main` y `ediciones-hotdeck-sdp`; `corrige-controles-celda` se
  conserva en la etiqueta `archivo/corrige-controles-celda`.
- Se retiran `prueba_ate_att_cate.py`, `preparar_outcome_prueba_empleo.py` y su salida:
  una prueba exploratoria con un outcome provisional y la celda anterior.
- Se retiran `6_refutacion.py` y `7_reporte/` (sin implementar; lo previsto lo cubren
  la simulación y las reglas de focalización), `src/preprocesamiento/` y `notebooks/`
  (vacías), `validar_linkage.py` (esperaba columnas que no existen) y
  `validar_cobertura_celdas_hotdeck.py` (diagnóstico puntual ya resuelto).
- `README.md` presenta el enfoque vigente en tres bloques.

## 2026-11-08 (25) — Asterisco en los resultados simulados (paso 5 del diseño)

### Cambiado
- `reportes.py`: asterisco en cada cifra de las tablas y en la figura, con nota al
  pie; columnas `simulado` y `modo` en los CSV de la evaluación, la sensibilidad y
  las reglas de focalización.
- Pruebas: 2 en `test_simulacion_semisintetica.py` y 1 mutación. 214 pruebas, 43 de
  43 mutaciones detectadas.

## 2026-11-08 (24) — Incidencia de ayudas declaradas y cantidades de población

### Nuevo
- `src/estimacion/incidencia_transferencias.py`: a quién llegan las ayudas declaradas
  en la GEIH (`P750S2`, `P1661S1`-`S3`), en hogares y personas. Descriptivo.
- `variables_candidatas_pobreza.py ... poblacion`: hogares y personas con cada variable
  y pobres que cada modelo gana y pierde con el mismo presupuesto.
- Secciones nuevas en `RECOMENDACION_VARIABLES_POBREZA.md`.
- Pruebas: `test_incidencia_transferencias.py` y 2 en `test_variables_candidatas.py`;
  4 mutaciones. 212 pruebas, 42 de 42 mutaciones detectadas.

## 2026-11-06 (23) — Recomendación de variables para ampliar la medición de pobreza

### Nuevo
- `src/estimacion/variables_candidatas_pobreza.py`: modelos anidados sobre
  la pobreza de la GEIH 2024 (lo que ya se recoge frente a 8 grupos de
  candidatas), con criterio de decisión fijado antes de ver resultados.
- `docs/resultados/RECOMENDACION_VARIABLES_POBREZA.md`. Composición del hogar
  −5,40 puntos de exclusión; cuenta de ahorros −0,86; estrato −0,52.
- Pruebas: `test_variables_candidatas.py` y etiquetas en `test_armonizacion.py`;
  8 mutaciones. 204 pruebas, 38 de 38 mutaciones detectadas.

### Hallado
- La GEIH trae participación declarada en programas (`P750S2`, `P1661S1`-`S3`);
  matiz anotado en la guía.

## 2026-11-04 (22) — Cadena de respaldos en el Hot-Deck simulado (paso 4 del diseño)

### Cambiado
- `claves_por_nivel` (módulo del Hot-Deck) define la cadena celda → sin
  pisos → depto + edad → depto; la usan `hotdeck()` y la simulación. El
  Hot-Deck del pipeline da el mismo resultado que antes.
- `vinculo.sortear_donante` recibe una columna de celda por nivel y sube
  por la cadena; antes, sin donantes en la celda, sorteaba en todo el
  registro. `base.preparar_base` calcula los códigos de cada nivel.
  La evaluación guarda `pct_respaldo` por repetición.
- Firmas de configuración nuevas en la evaluación, la sensibilidad y las
  reglas de focalización. Con los datos reales cambia el 0,03 % de la
  encuesta; las cifras publicadas se regeneran con el asterisco (paso 5).
- Prueba de equivalencia: excluye solo la combinación que usa respaldos
  (repetición 2, `confusion_no_observada_leve`); lo demás, idéntico.

### Pruebas
- 2 nuevas en `test_simulacion_semisintetica.py` y 1 mutación. 178
  pruebas, 30 de 30 mutaciones detectadas.

## 2026-11-04 (21) — Módulo `src/simulacion/`: contrato y traslado (pasos 1-3 del diseño)

### Nuevo
- `src/simulacion/`: `contrato`, `base`, `escenarios`, `asignacion`,
  `vinculo`, `estimadores`, `evaluacion`, `reportes` y `__main__`
  (`python -m src.simulacion [n_jobs]`).
- `contrato.py`: columnas obligatorias de las tablas de hogares y de
  registro con sus dominios; `validar()` falla nombrando cada columna
  faltante o código fuera de dominio. Desaparece `COLUMNAS` (permitía
  remapear nombres). La celda se calcula con `construir_celda`, no se
  recibe.
- Pruebas: `test_simulacion_contrato.py`, `test_simulacion_equivalencia.py`
  (referencia en `tests/referencia/`, generada con la versión anterior) y
  2 en `test_simulacion_semisintetica.py`; 3 mutaciones. 176 pruebas, 29
  de 29 mutaciones detectadas.

### Cambiado
- `src/validacion/simulacion_semisintetica.py` se borra; la sensibilidad,
  las reglas de focalización y las pruebas importan de `src/simulacion/`.
  `discontinuidad_difusa` pasa a `simulacion/estimadores.py`.
- Las reglas de focalización ya no descartan filas con faltantes en las
  columnas canónicas: el contrato las rechaza (en la base real no hay).

### Corregido
- Códigos de celda `int8`/`int16` (de `cat.codes`) desbordaban los grados
  de libertad de `regresion_efectos_fijos`; con las 993 celdas reales,
  por encima de 32.767 hogares en la encuesta. No afectó las corridas
  publicadas (30.000 hogares).
- `tablas_markdown` no se llamaba en `main`.

### Comprobado
- Con los datos reales, tabla de trabajo y repetición 0 idénticas a la
  versión anterior; la repetición 0 de la sensibilidad y de las reglas
  coincide con los CSV publicados (1e-16 con un hilo de BLAS). Las
  cifras publicadas no cambian.

## 2026-11-04 (20) — Prioridad 2 de la guía: diseño del módulo de simulación

### Nuevo
- `docs/metodologia/DISENO_MODULO_SIMULACION.md`: diseño de
  `src/simulacion/` antes del código. Modo simulado (población sintética
  desde parámetros agregados, casillas de menos de 30 hogares fusionadas)
  y modo de datos propios; contrato de columnas canónicas por tabla con
  dominios verificados contra la armonización; asterisco en las salidas
  simuladas; migración desde `src/validacion/simulacion_semisintetica.py`
  con equivalencia en 3 repeticiones; pruebas nuevas.

### Decisión
- No se solicitarán más datos: la réplica usa solo las fuentes del banco
  de datos. La prioridad 8 (enviar la solicitud del puntaje continuo) se
  descarta y la falta del puntaje queda como limitación. Se borra el
  borrador `docs/institucional/SOLICITUD_PUNTAJE_CONTINUO_SISBEN.md`, y
  los 9 departamentos sin clasificación oficial de pobreza monetaria
  quedan como limitación (`RESULTADOS_POBREZA_MONETARIA.md`).

### Decisiones abiertas
- Umbral de protección de los parámetros (30 hogares).
- Versionar P(T | celda) del Sisbén como agregado.
- Estimación real del modo de datos propios limitada a la de
  `5_estimacion.py`.

## 2026-11-04 (19) — Prioridad 1 de la guía: variabilidad de la imputación del Hot-Deck

### Nuevo
- `src/validacion/variabilidad_hotdeck.py`: el `hotdeck()` del pipeline
  con 100 semillas (la 42 reproduce el grupo guardado en el 100 %).
  Concordancia por hogar (empírica y teórica), CV y error relativo por
  celda, agregados nacional y por departamento, contraste placebo con
  reglas de Rubin.
- `docs/resultados/RESULTADOS_VARIABILIDAD_HOTDECK.md`.
- `tests/test_variabilidad_hotdeck.py` (7 pruebas) y 2 mutaciones: 145
  pruebas, 26 de 26 mutaciones detectadas.

### Hallazgos
- Por hogar: 34,4 % de concordancia de grupo entre dos sorteos y 62,7 %
  en A/B, iguales a lo teórico de la celda.
- Por celda: CV mediano 0,091 (0,049 ponderado), error relativo mediano
  0,072 (0,039 ponderado); en celdas de hasta 30 hogares, CV 0,17.
- Nacional: desviación de 0,10 a 0,15 puntos por grupo.
- El −0,0026 del DML en `POBRE_GEIH`, el único IC sin el cero, depende de
  la semilla: con 100 sorteos el contraste es −0,00003 y solo 3 %
  excluye el cero. La imputación aporta 49-55 % de la varianza total.

### Commits de esta serie (sin autor agregado)
- `e4c0f57` pytest del proyecto con poetry y sin filtros de advertencias
  en la simulación (prioridad 7).

## 2026-11-04 (18) — Prioridad 7 de la guía: pytest del proyecto y filtros de advertencias

- `pyproject.toml`: `[tool.pytest.ini_options]` con `pythonpath = ["."]`.
  `poetry run pytest` (ejecutable de pytest) no ponía la raíz en el path
  y 5 archivos no cargaban `src.*`; ahora pasan las 138.
- Quitado `warnings.filterwarnings("ignore")` de
  `simulacion_semisintetica.py`, `reglas_focalizacion.py` y
  `sensibilidad_semisintetica.py`. Sin el filtro, una repetición completa
  de cada uno da 0 advertencias. Queda el de `prueba_ate_att_cate.py`
  (exploratorio, fuera del pipeline) para la depuración.
- Guía de la tesis: `docs/seguimiento/SEGUIMIENTO_TESIS_2026-11-04.md`
  (commit `e415181`), con las reglas del tutor en `CLAUDE.md`.

## 2026-11-04 (17) — Sensibilidad de la simulación y solicitud del puntaje continuo

### Nuevo
- `src/validacion/sensibilidad_semisintetica.py`: tamaño del efecto
  (× 0,5, × 1, × 2), regla de corte difusa (80 % / 20 % de participación)
  con RD difusa por dos etapas local, y LinearDML con y sin
  regularización. 228 repeticiones hasta MCSE ≤ 0,003 (RD ≤ 0,008).
- `docs/institucional/SOLICITUD_PUNTAJE_CONTINUO_SISBEN.md`: borrador
  (sin enviar) de la solicitud del puntaje continuo, con variante para la
  SDP (registros repetidos del mismo hogar en Bogotá) y para el DNP.
- `tests/test_sensibilidad_semisintetica.py` (4 pruebas) y 2 mutaciones:
  138 pruebas, 24 de 24 mutaciones detectadas.

### Hallazgos
- La pérdida por integración es proporcional: Hot-Deck ≈ 0 y vínculo del
  50 % ≈ 44-49 % del efecto, con efectos de 0,047 a 0,190.
- RD difusa con vínculo: 0,086 frente a 0,090 en el corte (cobertura
  0,96); con Hot-Deck, 0,007.
- Sesgo de LinearDML con efecto nulo: −0,006 (z −3,7 a −4,5) con la
  regularización del proyecto, −0,002 (z −1,1 a −1,9) casi sin ella.
  Decisión pendiente: bajar la regularización en `5_estimacion.py`.

### Corregido en las pruebas
- La primera prueba de la RD difusa exigía que una sola semilla cubriera
  el valor verdadero con un IC al 95 %, lo que falla 1 de cada 20 veces
  por diseño (falló con la semilla 0). Se reemplazó por sesgo y cobertura
  sobre 100 semillas (medido en 200: media 0,1004, cobertura 0,96).

### Commits de esta serie (sin autor agregado)
- `09de1cb` Cotas de Fréchet-Manski con supuestos de monotonía (las dos
  corridas de GitHub Actions pasaron).
- `ca02d57` Sensibilidad de la simulación semisintética y borrador de
  solicitud del puntaje continuo (esta entrada; GitHub Actions pasó en
  las dos ramas).

## 2026-11-04 (16) — Cotas con supuestos de monotonía

### Nuevo
- `cotas_con_supuestos` en `cotas_frechet_manski.py` (Manski y Pepper,
  2000): contraste, contraste con dependencia positiva y ATE sin
  supuestos, con MTS, con MTR, con los dos y con los tres. Salida
  `docs/reports/cotas_frechet_manski_monotonia.csv`.
- Aclarado en `RESULTADOS_FRECHET_MANSKI.md`: las cotas anteriores acotan
  el contraste E[Y|T=1] − E[Y|T=0] (problema de combinación de datos);
  el ATE causal tiene una cota más ancha sin supuestos.
- 28 pruebas nuevas (134 en total), entre ellas una que genera
  poblaciones al azar que cumplen cada supuesto y comprueba que el ATE
  verdadero cae dentro de su cota; 2 mutaciones nuevas (22 de 22).

### Cifras (pobreza monetaria, 921 celdas)
- ATE sin supuestos [−0,571; +0,829]; con MTR [−0,571; 0]; con MTS, MTR y
  dependencia positiva **[−0,405; 0]**. `POBRE_GEIH`: [−0,469; +0,765] →
  [−0,367; 0]. Oficial (712 celdas): [−0,405; 0].
- El MTS no agrega nada sobre el MTR; solo la dependencia positiva sube
  la cota inferior. Las cotas previas no cambian.

### Commits de esta serie (sin autor agregado)
- `6c4c364` Reglas de focalización (OE3) sobre el mundo semisintético
  (las dos corridas de GitHub Actions pasaron).

## 2026-11-04 (15) — Reglas de focalización (P3/OE3)

### Nuevo
- `src/validacion/reglas_focalizacion.py`: siete reglas con el mismo
  presupuesto (los hogares A/B vigentes) en el mundo semisintético, con
  dos modelos del efecto (proporcional, el de P2, y monto fijo en pesos),
  hasta 300 repeticiones con error Monte Carlo. Usa el generador y los
  estimadores de `simulacion_semisintetica.py`.
- `docs/resultados/RESULTADOS_REGLAS_FOCALIZACION.md`.
- `tests/test_reglas_focalizacion.py` (7 pruebas) y 4 mutaciones nuevas:
  20 de 20 detectadas; 106 pruebas.

### Corregido antes de la corrida
- La primera versión suponía un error normal del proxy de medios: los
  hogares sin ingreso inflaban la desviación y la regla por brecha
  esperada quedaba peor que la de ingreso predicho (62 % frente a 81 % del
  ideal). Ahora promedia sobre los cuantiles empíricos del residuo.

### Cifras
- % de la reducción ideal de FGT1 (proporcional / monto fijo): vigente
  imputada 60 / 61, aleatoria 47 / 47, proxy de medios 82 / 85, proxy +
  CATE con vínculo 73 / 72, proxy + CATE con Hot-Deck 45 / 44.
- Error de exclusión: vigente 43,5 %, proxy 18,6 %, CATE con Hot-Deck
  55,5 %.

### Commits de esta serie (sin autor agregado)
- `4c93400` Integración continua: pruebas y prueba de mutación en GitHub
  Actions (las dos corridas de GitHub, en `main` y en
  `ediciones-hotdeck-sdp`, pasaron todos los pasos).

## 2026-11-04 (14) — Integración continua

### Nuevo
- `.github/workflows/pruebas.yml`: GitHub Actions corre `pytest` y
  `tests/mutaciones.py` en cada push a `main`/`ediciones-hotdeck-sdp` y en
  cada PR.
- `requirements-pruebas.txt`: las 11 dependencias de las pruebas,
  fijadas a las versiones del `.venv` con el que pasan (no depende de que
  `poetry.lock` esté al día).
- `tests/mutaciones.py` usa el intérprete que lo ejecuta (antes, la ruta
  de Windows del `.venv`).

### Verificado antes de subir
- Entorno limpio con solo `requirements-pruebas.txt`, sobre un clon del
  repositorio sin datos (como en GitHub): 92 pasan, 7 se saltan (leen
  enero real de GEIH), 16 de 16 mutaciones detectadas.

### Commits de esta serie (sin autor agregado)
- `6181c8b` Pruebas de prioridad alta, reglas compartidas entre fuentes y
  prueba de mutación.
- `db1727d` Verifica la armonización de Bogotá contra el crudo del SDP.

## 2026-11-04 (13) — Pruebas de prioridad alta y reglas compartidas entre fuentes

### Nuevo
- `src/utils/variables_canonicas.py`: `normalizar_llave`, `es_jefe` y
  `edad_a_ciclo`, en un solo lugar. Reemplaza seis copias de la
  normalización de llaves (`3_preprocesamiento.py`, `3b_…`,
  `armonizar_geih_hogar_2024.py`, `pobreza_monetaria_geih.py`,
  `preparar_outcome_prueba_empleo.py`, `comparar_pobreza_monetaria_oficial.py`)
  y los tramos de edad duplicados del Hot-Deck y del SDP.
- `cotas_frechet_manski.py`: la fórmula de las cotas (`cotas_frechet`) y
  la agregación del ATE (`ate_agregado`) separadas para poder probarlas.
- 61 pruebas nuevas (38 → 99): `test_armonizacion.py` (códigos contra los
  diccionarios oficiales, vivienda, jefe, vigencia del SDP, OE1 sin
  `I1`-`I15`/`H_5`), `test_estimacion_dml.py` (propensión con
  indicadoras, LinearDML), `test_cotas_frechet_manski.py`,
  `test_variables_canonicas.py` y `test_ingesta_y_validacion.py` (12
  meses de GEIH con sus variantes, contraste oficial, DAG).
- `tests/mutaciones.py`: reintroduce los 16 errores documentados; los 16
  hacen fallar alguna prueba. `tests/README.md`: qué cubre cada archivo.

### Verificado sin cambios en cifras
- Salidas idénticas (`assert_frame_equal`) de `3_preprocesamiento.py`,
  pobreza monetaria, contraste oficial y `3b`; celda del Hot-Deck igual en
  los 290.899 hogares en celda exacta; llaves y jefes iguales en las
  2.489.049 filas de los 12 meses; cotas de Fréchet-Manski byte a byte.
- Suite estable: 5 de 5 corridas, cada archivo por separado y en orden
  inverso.

- Bogotá reconstruida desde el crudo del SDP (Azure,
  `sisben/bogota/Sisben_03082026_bog.zip`, CSV de 587 MB) con el código
  nuevo: idéntica columna por columna a la versión en uso, por vigencia
  (1.274.578 hogares) y por año exacto (75.488).

### Pendiente
- Integración continua y cobertura medida.

## 2026-11-03 (12) — Evaluación semisintética hasta la convergencia

### Nuevo
- `simulacion_semisintetica.py` corre en lotes paralelos hasta que el
  error estándar Monte Carlo de cada celda queda bajo el umbral (Morris,
  White y Crowther, 2019), guarda cada lote y reanuda si se interrumpe.
- Outcome de pobreza monetaria (línea del dominio), escenarios de efecto
  nulo, confusión no observada media (gamma 0,5) y regla de corte con RD
  local lineal; Causal Forest hasta 200 repeticiones.
- Figura `docs/resultados/simulacion_semisintetica_convergencia.png` y
  tablas generadas del resumen (`docs/reports/simulacion_semisintetica_tablas.md`).

### Cifras
- 432 repeticiones (Causal Forest 216); 150 de 150 celdas convergieron,
  10 de 16 de Causal Forest.
- Hot-Deck: ≈0 en los ocho escenarios, los dos outcomes y los cinco
  estimadores. Vínculo 50 %: la mitad del efecto.
- Confusión no observada (oráculo): −0,29 / −0,53 / −0,78 en log-ingreso;
  +0,021 / +0,066 / +0,138 en pobreza (signo invertido).
- RD en la regla de corte, oráculo: +0,086 frente a +0,090 (cobertura
  0,94); con Hot-Deck, ≈0.
- LinearDML: sesgo de −0,004 a −0,008 en log-ingreso; cobertura 0,91-0,92
  con efecto nulo (regresión con efectos fijos: 0,94-0,97).

## 2026-11-02 (11) — Pobreza monetaria oficial como robustez y evaluación semisintética

### Decidido
- Outcome monetario principal: la reconstrucción (33 departamentos).
  `POBRE_MONETARIO_OFICIAL` (clasificación DANE, 24 departamentos y
  Bogotá) como prueba de robustez en el DML y las cotas. Los 9
  departamentos no están en la base oficial con otro código ni
  identificador (0 de sus 15.911 hogares por `directorio`).

### Nuevo
- `3b_preprocesamiento_monetario.py` pega `POBRE_MONETARIO_OFICIAL` y
  `POBRE_EXTREMO_OFICIAL` (275.057 hogares). Ahora corre después de
  `comparar_pobreza_monetaria_oficial`. Primera corrida pegó solo el 23 %:
  `mes` era "01" en la muestra y "1" en la oficial; se normalizan las
  llaves (prueba en `tests/test_preprocesamiento_monetario.py`).
- `src/validacion/simulacion_semisintetica.py`, `tests/test_simulacion_semisintetica.py`
  y `docs/resultados/SIMULACION_SEMISINTETICA.md`.

### Cifras nuevas
- DML con la oficial: ATE −0,0005 [−0,0041; +0,0030] (celda exacta).
  Cotas: [−0,407; +0,620] frente a [−0,418; +0,649] de la reconstrucción
  en las mismas 712 celdas. Las demás cifras no cambian.
- Semisintética (ATE verdadero 0,095): con Hot-Deck, ≈0 en los cinco
  escenarios y los cuatro estimadores que controlan la celda; con
  vínculo del 50 %, ≈0,044; con oráculo y confusión observable, 0,085-0,094.

## 2026-11-02 (10) — Celda del Hot-Deck con pisos y base oficial de pobreza monetaria

### Decidido
- **La celda oficial del Hot-Deck incluye el nivel de pisos** homologado
  (acabado / cemento o madera burda / tierra). Respaldo: celda sin pisos,
  luego depto + edad, depto, nacional. La celda anterior queda como
  sensibilidad (`incluir_pisos=False`). `viv_pisos` sale de `X` en
  `5_estimacion.py` y el nivel de pisos entra a `W_PROXY`.
- `hotdeck()` falla si falta `viv_pisos`: sin la columna todo caía al
  respaldo sin pisos sin dar error (le pasó a `comparar_filtros_sdp.py`
  en la primera corrida, corregido).

### Nuevo
- Base oficial de pobreza monetaria 2024 (catálogo 874) y marca de
  víctimas MPMD en `data/0_raw/` y Azure (solo CSV).
- `src/validacion/comparar_pobreza_monetaria_oficial.py`: reconstrucción
  frente a la oficial, hogar por hogar. Guarda la base oficial limpia en
  `data/1_processed/pobreza_monetaria/hogares_oficial_2024.parquet`.
- `tests/test_hotdeck_celda.py`.

### Cambios en cifras
- Hot-Deck: 376 → 993 celdas, 100 → 99,98 % en celda exacta; grupos
  A/B/C/D 22,0/33,8/28,7/15,6 → 14,2/29,4/34,4/22,0 %.
- ATE con celda exacta: `ipm_geih_score` +0,0011 → −0,0021, `POBRE_GEIH`
  +0,0004 → −0,0026 (IC [−0,0049; −0,0002]), `log_ingreso_percapita`
  −0,0132 → +0,0006, `POBRE_MONETARIO` +0,0025 → −0,0002. Siguen siendo
  siete de ocho IC con el 0.
- Fréchet-Manski: `POBRE_GEIH` [−0,411; +0,323] → [−0,261; +0,380];
  `POBRE_MONETARIO` [−0,538; +0,503] → [−0,418; +0,648]. 921 celdas,
  ninguna excluye el 0.
- Base oficial: 275.057 hogares (24 departamentos y Bogotá; no trae 81,
  85, 86, 88, 91, 94, 95, 97, 99), tasa 31,83 %. Sobre esos hogares la
  reconstrucción da 33,24 % y clasifica igual al 93,9 %; con las líneas
  oficiales por área y semestre, 32,62 %.

## 2026-11-02 (9) — Saneamiento: modelos auxiliares del DML, pobreza monetaria definitiva, celdas con vivienda y documentación consolidada

### Corregido
- `src/5_estimacion.py`: la celda del Hot-Deck (0..375) y el departamento
  (0..32) entraban como números a la `LogisticRegression` de propensión.
  La propensión con "celda exacta" salía 0,633-0,642 para todos (real
  P(T | celda): 0,36-0,87). Ahora las categóricas sin orden entran como
  indicadoras (`model_t` logística, `model_y` regresión con efectos fijos
  más splines). La propensión estimada reproduce la empírica
  (correlación 0,998).
- Auditoría monetaria: `P6430` = 7 es jornalero, no "sin remuneración".

### Nuevo
- `src/indicadores/pobreza_monetaria_geih.py`: pobreza monetaria
  reconstruida con D1-D7 cerradas (unidad de gasto, tres líneas de
  dominio, hot-deck de no respuesta laboral, arriendo imputado, tasas por
  persona, 8 escenarios de sensibilidad). `3b` ahora solo pega el
  resultado a la muestra de estimación. Diccionario y decisiones:
  `docs/metodologia/pobreza_monetaria/01_diccionario_ingreso.md`.
- `src/validacion/comparar_celdas_hotdeck_vivienda.py`: celdas actual,
  + pisos y + pisos + paredes.
- `seleccion_variables_lasso_shap.py`: métricas por grupo, matrices de
  confusión, calibración y partición por municipio.
- Pruebas de la reconstrucción monetaria (`tests/test_preprocesamiento_monetario.py`, reescrito).

### Cambios en cifras
- Pobreza monetaria (personas): FGT0 37,6 → **33,2 %** (oficial 31,8),
  FGT1 18,3 → 13,5 % (12,6), extrema 17,6 → 12,5 % (11,7), Gini 0,565
  (0,551). Rural 41,3 % (42,5).
- ATE con celda exacta: `ipm_geih_score` +0,0098 → +0,0011,
  `POBRE_GEIH` +0,0058 → +0,0004, `log_ingreso_percapita` −0,0467 →
  −0,0132, `POBRE_MONETARIO` +0,0158 → +0,0025. Siete de ocho IC
  incluyen el 0.
- Fréchet-Manski `POBRE_MONETARIO`: [−0,5817; +0,6877] → [−0,5382; +0,5030].

### Conclusiones que se retiran
- "Los efectos monetarios con la celda exacta son la evidencia de
  robustez más fuerte del proyecto" y "el residuo no colapsa a 0": eran
  producto del error de codificación.
- Los patrones de heterogeneidad del CATE (zona, sexo del jefe, vivienda
  como pista del residuo).

### Documentación consolidada
- Reescritos: `RESUMEN_AVANCES.md`, `docs/resultados/README.md`,
  `DIAGNOSTICO_W_CELDA_EXACTA.md`, `RESULTADOS_DML_ATE_ATT_ATU.md`,
  `RESULTADOS_CAUSALFOREST_CATE.md`, `RESULTADOS_POBREZA_MONETARIA.md`.
  Actualizados: `README.md` (enfoque semisintético vigente),
  `RESULTADOS_FRECHET_MANSKI.md`, `RESULTADOS_HOTDECK.md`,
  `RESULTADOS_SELECCION_VARIABLES_OE1.md`, `CLAUDE.md`.

## 2026-11-02 (8) — Corrección del bug de agosto y pipeline regenerado

### Corregido
- `src/ingesta/local_csv_parser.py` (`parse_stata_a_parquet`): los meses
  cargados desde `.DTA` quedan con el mismo formato que los del CSV
  (enteros sin `".0"`, faltantes como `""`). Prueba nueva en
  `tests/test_local_csv_parser.py`.
- `src/ingesta/geih_loader.py`: la instrucción de uso del docstring estaba
  mal (`-m src.ingesta...` falla por el import `ingesta.*`).

### Regenerado
- Carga de GEIH, armonización, Hot-Deck, filtros SDP, `3_preprocesamiento`,
  `3b_preprocesamiento_monetario`, `5_estimacion`, cotas de Fréchet-Manski,
  representatividad, inventarios y matriz de homologación.
- El Hot-Deck asigna el mismo grupo al 100 % de los hogares; los
  resultados de representatividad tampoco cambian.

### Cambios en cifras
- Privaciones: alcantarillado 18,1 → 19,8 %, acueducto 8,1 → 8,9 %,
  pensión del jefe 75,4 → 73,2 %. `POBRE_GEIH` 16,3 → 17,1 %.
- Pobreza monetaria: FGT0 38,7 → 37,6 %, FGT1 19,5 → 18,3 %, extrema
  18,8 → 17,6 % y 10,7 → 9,5 %. Sobreestimación de 5-6 pp (antes 6-7).
- ATE con `W` proxy / celda exacta: `ipm_geih_score` +0,0235 / +0,0098
  (-58 %); `POBRE_GEIH` +0,0056 / +0,0058; `log_ingreso_percapita`
  -0,0294 / -0,0467; `POBRE_MONETARIO` +0,0141 / +0,0158.
- Fréchet-Manski: `POBRE_GEIH` [-0,4114; +0,3230]; `POBRE_MONETARIO`
  [-0,5817; +0,6877].
- Única conclusión que cambia: el ATU de `ipm_geih_score` con celda
  exacta ahora excluye 0 por un margen mínimo ([+0,0004; +0,0137]).
- `01_matriz_homologacion.md` (comparación de proxies): sus filtros
  `OCI=1`/`DSI=1` excluían agosto. Universos corregidos: `P6920` 321.444
  → 351.164 personas, `P7250` 43.598 → 47.395; las reglas de
  homologación no cambian.

## 2026-11-02 (7) — Homologación de paredes y pisos con la ficha del Sisbén IV; bug de agosto

### Añadido
- `docs/insumos/FICHA_SISBEN_IV_FCS_2017.pdf`: ficha de caracterización
  socioeconómica del Sisbén IV (DNP), con los códigos de respuesta.
- `docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`: escala común de
  paredes (7 categorías) y pisos (5), verificada contra `I13`/`I14` del
  DNP (patrón 0 %/100 % idéntico a la regla oficial del IPM).

### Resuelto
- `viv_paredes`/`viv_pisos` homologadas entre GEIH y Sisbén nacional. Los
  códigos crudos no son comparables (pisos en orden inverso). Bogotá
  (SDP) coherente pero sin verificar con privaciones.
- `geo_zona`: 1 = urbano en las dos fuentes.

### Bug encontrado (sin corregir)
- Agosto de GEIH viene de `.DTA` y sus códigos quedaron como `"1.0"`/`"2.0"`.
  Las comparaciones de texto fallan en ese mes: `sin_alcantarillado` y
  `sin_acueducto` = 0 %, `POBRE_GEIH` = 6,9 % (≈17 % el resto del año),
  `POBRE_MONETARIO` = 53,3 % (≈39 %). Afecta el 8,4 % de la muestra y
  todos los resultados que usan esos outcomes.

## 2026-11-02 (6) — Pobreza monetaria: auditoría de variables y metodología (Fase 1)

### Añadido
- `src/indicadores/inventario_ingresos_geih.py` →
  `docs/reports/inventario_ingresos_geih.csv`: 46 variables de ingreso con
  componente, periodicidad, relación con `INGLABO`, tratamiento propuesto
  y cobertura en los 12 meses.
- `docs/metodologia/pobreza_monetaria/00_auditoria_y_metodologia.md`:
  auditoría y metodología propuesta, en espera de revisión.

### Hallazgos
- La cifra oficial cruza GEIH con registros administrativos (ayudas
  institucionales, PILA): no es reproducible con microdatos públicos.
- `INGLABO` no está imputado; corrige afirmaciones previas del proyecto.
- `P7510S7A1` (ocasionales) se debe excluir; primas anuales, auxilios y
  extras no incluidos faltan en el outcome actual.
- Unidad de gasto: `P6050` = 10 es servicio doméstico; pensionista es el
  11 o el 12 (sin resolver, 0,04 % de la muestra).
- Factor anual `FEX_C18/12`; sin duplicados entre meses; FGT oficial
  sobre personas.

### Pendiente (requiere revisión)
- Decisiones D1-D7 de la auditoría; no se construyó el agregado.

## 2026-11-02 (5) — Pobreza monetaria conectada a DML/Causal Forest

### Cambiado
- `src/5_estimacion.py`: lee `muestra_estimacion_monetaria_2024.parquet`
  (superset de la muestra anterior) y agrega dos outcomes —
  `log_ingreso_percapita` (`log1p`) y `POBRE_MONETARIO` — a los dos de
  IPM-GEIH. Corre 4 outcomes × 2 especificaciones de `W` (proxy continuo
  vs. celda exacta del Hot-Deck).

### Resultado
- Con la celda exacta, el ATE de `log_ingreso_percapita` pasa de -0,0317
  a -0,0468 y el de `POBRE_MONETARIO` de +0,0136 a +0,0152: se amplían en
  vez de encogerse, al contrario de `ipm_geih_score` (-63 %). Los números
  de IPM-GEIH no cambian frente a la corrida anterior. Ver
  `docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md`.

### Revisado
- `viv_paredes`/`viv_pisos` frente a la auditoría de la entrada (4): la
  matriz homologa los códigos GEIH contra la regla oficial del IPM, no
  contra las categorías del Sisbén. Siguen sin homologar con Sisbén.

### Cotas de Fréchet-Manski
- `src/estimacion/cotas_frechet_manski.py` recorre `POBRE_GEIH` y
  `POBRE_MONETARIO` (lee la muestra monetaria). `POBRE_GEIH` reproduce la
  cota anterior; `POBRE_MONETARIO` da [-0,5886; +0,7035], ancho 1,29.
  Ninguna celda excluye el 0 de forma informativa (las 6 que marca un
  filtro numérico tienen `P(Y=1|X)=1` y cota [0; 0]).

### Pendiente
- Angostar las cotas con supuestos MTS/MTR.

## 2026-11-02 (4) — Comparación de proxies del IPM: auditoría y matriz de homologación (rama `comparacion-proxies-ipm`)

### Añadido
- `src/indicadores/inventario_variables_geih.py`: inventario de las
  columnas GEIH 2024 frente al diccionario oficial y al código del
  proyecto (`docs/reports/inventario_variables_geih.csv`).
- `src/indicadores/homologacion_ipm.py`: matriz GEIH ↔ Sisbén de las 15
  privaciones con la regla oficial del DANE (met-IPM, pp. 15-26) y
  diagnóstico de insumos por población de referencia. Genera
  `docs/metodologia/comparacion_proxies/01_matriz_homologacion.{md,csv}`
  y `docs/reports/diagnostico_insumos_homologacion.csv`. Resultado: 12
  homologables, 1 parcial (trabajo infantil, solo 15-17), 2 no
  disponibles (primera infancia, barreras de salud).
- `docs/metodologia/comparacion_proxies/00_auditoria_variables.md`:
  inventario, diferencias de `IPM_GEIH_BASE` frente a la regla oficial,
  hallazgos y decisiones pendientes de revisión.
- `tests/test_homologacion_ipm.py`: todo código GEIH/Sisbén de la matriz
  debe existir en su diccionario oficial.

### Corregido
- `poetry.lock` regenerado: estaba desactualizado frente a
  `pyproject.toml` (faltaba `openpyxl`); sin cambios en las demás versiones.

### Pendiente (requiere revisión antes de la Fase 3)
- Ver §6 de `00_auditoria_variables.md`. No se construyó ningún indicador
  nuevo ni se corrió ningún modelo.

## 2026-11-02 (3) — Pobreza monetaria: ingreso per cápita y FGT0/FGT1

### Añadido
- **`src/3b_preprocesamiento_monetario.py`**: nuevo outcome principal
  según el giro propuesto por el tutor el 2026-10-27 — pobreza monetaria
  en vez de (o además de) el IPM-GEIH. Construye `ingreso_hogar_mensual`
  (ingreso laboral desde `INGLABO` + no laboral desde `otros_ingresos`/
  `no_ocupados`, agregado a TODOS los miembros del hogar),
  `ingreso_percapita`, `POBRE_MONETARIO`/`POBRE_EXTREMO_MONETARIO` y las
  brechas FGT1, comparando contra las líneas de pobreza oficiales del
  DANE 2024 por zona urbano/rural.
- **`docs/insumos/DANE_boletin_PM_2024.pdf`**: boletín técnico oficial
  *Pobreza Monetaria en Colombia 2024* del DANE, descargado y guardado
  como referencia permanente — fuente de las líneas de pobreza
  ($460.198 nacional, $510.161 cabeceras, $291.998 resto; extrema
  $227.220/$242.389/$176.154) y de las cifras FGT0/FGT1 oficiales
  (31,8%/12,6% pobreza; 11,7%/4,5% extrema) usadas para validar por
  plausibilidad.
- **`docs/resultados/RESULTADOS_POBREZA_MONETARIA.md`** y
  **`tests/test_preprocesamiento_monetario.py`** (6 pruebas: una fila
  por hogar, ingreso no negativo/sin faltantes, casos de borde de
  clasificación de pobreza con datos sintéticos, brecha entre 0 y 1,
  `ingreso_percapita` NaN sin personas).

### Corregido durante la construcción (documentado, no solo el número final)
- **Primer intento descartado**: reconstruir el ingreso laboral sumando
  `P6500` (empleo principal) + horas extra/primas/bonificaciones (según
  sus sub-preguntas de doble conteo) + subsidios + pago en especie — tal
  como sugiere el cuestionario, sin usar ninguna variable derivada. Dio
  FGT0=53,6%/FGT1=39,0%, muy por encima de lo oficial (31,8%/12,6%) — no
  el margen esperable de una aproximación sin imputación, un orden de
  magnitud distinto.
- **Causa**: `P6500` por sí solo tiene **47,7% de no respuesta** entre
  personas ocupadas (13.751 de 28.815 en enero) — el script trataba esos
  vacíos como ingreso $0 en vez de "no informa", inflando el conteo de
  hogares con ingreso 0 (21,4%, implausible) y sobre todo FGT1 (un hogar
  con ingreso real alto pero `P6500` vacío contribuía brecha de pobreza
  100% en vez de 0%).
- **Corrección**: el módulo `ocupados` trae `INGLABO`, la variable de
  ingreso laboral que el DANE ya imputa internamente (reduce la no
  respuesta de 47,7% a 4,3%). Usarla en vez de reconstruir a mano bajó el
  % de hogares con ingreso 0 de 21,4% a 4,1%, y las cuatro FGT pasaron de
  estar 1,5-3 veces por encima de lo oficial a estar 6-7 puntos
  porcentuales por encima — una sobreestimación sistemática consistente
  con no replicar la imputación de subreporte no laboral ni el ajuste
  por vivienda propia de la metodología oficial del DANE, no un error de
  construcción.

### Documentación actualizada
`docs/resultados/README.md` (nueva fila §3b y sección), `docs/README.md`,
`docs/seguimiento/RESUMEN_AVANCES.md` (§3g, tabla de pipeline,
pendientes, referencias), `src/README.md`, `CLAUDE.md` (bloque de
validación).

### Pendiente (no hecho en esta corrida)
Conectar `muestra_estimacion_monetaria_2024.parquet` a
`src/5_estimacion.py` como outcome causal (DML/Causal Forest), y repetir
el diagnóstico `W` proxy vs. celda exacta
(`DIAGNOSTICO_W_CELDA_EXACTA.md`) sobre este outcome.

## 2026-11-02 (2) — OE1: selección de variables con LASSO, Ridge y SHAP

### Añadido
- **`src/estimacion/seleccion_variables_lasso_shap.py`**: responde al
  OE1 ("determinar grupos y subgrupos de variables para LASSO, Ridge y
  SHAP") por separado del pipeline causal — no estima ningún efecto,
  solo qué variables del hogar predicen mejor el `Grupo` (A-D) del
  Sisbén. Predictores: `hog_num_personas`/`viv_cuartos`/`jefe_edad`
  (numéricas, orden establecido) y `viv_paredes`/`viv_pisos`/`viv_
  alcantarillado`/`viv_acueducto`/`jefe_sexo`/`geo_zona` (one-hot,
  dirección sin verificar, mismo criterio que evitó el bug de
  `LinearDRLearner` con categóricas sin orden); `geo_depto` como control
  geográfico aparte. Nunca usa `I1`-`I15`/`H_5` como predictor — serían
  circulares con el propio `Grupo` que se calcula a partir de ellas.
  150.000 hogares (submuestra estratificada de 3,09 millones).
- **`docs/resultados/RESULTADOS_SELECCION_VARIABLES_OE1.md`**:
  resultado completo. `viv_pisos` es la variable individual más
  importante en los tres métodos (LASSO, Ridge, SHAP sobre un
  `RandomForestClassifier`). LASSO y Ridge casi no difieren (Spearman
  0,988); SHAP reordena el tercio medio de la tabla (sube `hog_num_
  personas` y `viv_alcantarillado`) — evidencia de interacciones no
  lineales. Ninguna variable eliminada por LASSO. Exactitud ~53 % en las
  tres (línea base de predecir siempre la clase mayoritaria: ~30 %).

### Corregido (de paso, API de sklearn)
- `LogisticRegressionCV` en sklearn 1.9 deprecó `multi_class` y está
  deprecando `penalty` en favor de `l1_ratios` (se eliminará en 1.10) —
  el script usa ya la API nueva (`l1_ratios=[1.0]`/`[0.0]`,
  `use_legacy_attributes=False`), confirmado con `-W error::FutureWarning`
  que no queda ningún warning pendiente.
- `scipy` se declara explícito en `pyproject.toml` (antes solo llegaba
  como dependencia transitiva de scikit-learn; el script lo importa
  directo para `spearmanr`).

### Documentación actualizada
`docs/resultados/README.md` (nueva fila §7 y sección "Resumen por
paso"), `docs/seguimiento/RESUMEN_AVANCES.md` (§3f, tabla de pipeline,
pendientes, referencias), `src/estimacion/README.md`, `CLAUDE.md`
(bloque de validación).

## 2026-11-02 — Diagnóstico W proxy vs. celda exacta, rotulado ATT/ATU, higiene

### Añadido
- `src/5_estimacion.py`: segunda especificación de `W` (`W_COLS_CELDA`),
  el código categórico de `_hotdeck_celda` — la celda EXACTA que usa el
  propio Hot-Deck para sortear el donante (confirmado: sorteo uniforme
  random, `rng.integers` sin ponderar nada del receptor,
  `emparejamiento_hotdeck_geih_sisben.py`). La especificación anterior
  (`W_COLS_PROXY`, con `jefe_edad`/`viv_cuartos` continuos) queda como
  proxy documentado, no se elimina. El script corre ambas para los dos
  outcomes y las imprime una tras otra para comparar directamente.
- `docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md`: resultado completo y
  su lectura. Hallazgo principal — **el proxy continuo SÍ inflaba el
  efecto para `ipm_geih_score`** (ATE +0,0206→+0,0076, -63 %, el ATU deja
  de excluir 0) **pero NO para `POBRE_GEIH`** (ATE +0,0052→+0,0049, casi
  sin cambio, los tres efectos siguen excluyendo 0). La heterogeneidad
  por sexo del jefe cambia de signo otra vez (tercer patrón distinto en
  tres corridas: jefa-mujer-domina → zona-domina-sexo-positivo →
  zona-domina-sexo-negativo) — no citar ninguna versión como robusta. La
  heterogeneidad por zona se mantiene y se acentúa (2,8x → 10x).

### Corregido
- **Rotulado ATT/ATU**: se venían describiendo como "error de
  inclusión"/"error de exclusión" (concepto de focalización, no
  calculado aquí) — etiqueta engañosa, sin error de cómputo. Corregido en
  `src/5_estimacion.py` y `docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md`
  a "efecto en tratados"/"efecto en no tratados".
- `docs/seguimiento/RESUMEN_AVANCES.md`: §5 "Higiene del repositorio"
  describía un problema ya resuelto (carpetas `NACIONAL`/`DEPARTAMENTAL`
  versionadas) — confirmado con `git ls-files` que ya no están en el
  repo. Encabezado de rama actualizado (`hotdeck-azure-avances` ya está
  fusionada a `main`, confirmado con `git merge-base --is-ancestor`).

- Se quitó `warnings.filterwarnings("ignore")` de `src/5_estimacion.py`
  (otro pendiente de la Tabla 4 del paper de avance). Probado con
  `-W always`, incluido un `CausalForestDML` completo a 80.000 filas: no
  generó ningún warning en este entorno — el filtro no ocultaba nada
  real, era código muerto.

### Hallazgo adicional (sin cambio de código)
- Las ramas `corrige-controles-celda` y `simulacion-identificacion`
  (Tabla 5 del paper de avance, prioridad 1) se bifurcaron de `main`
  ANTES de la corrección del diccionario GEIH del 2026-10-28 — no tienen
  `DICCIONARIO_GEIH_2024.xlsx`, tienen el outcome de 4 privaciones, y la
  vivienda sin corregir. Fusionarlas tal cual revertiría las
  correcciones de esta semana — necesitan rehacerse sobre `main` actual,
  no fusionarse directo. `simulacion-identificacion` sí trae código
  nuevo valioso (`src/validacion/simulacion_identificacion.py`,
  `docs/resultados/SIMULACION_IDENTIFICACION.md`) que no existe en
  `main` y que sustenta el diagnóstico de este changelog.

## 2026-10-28 (2) — Retira 2 privaciones tautológicas con las covariables de heterogeneidad

Mismo día que la entrada anterior. Al revisar la validez del Causal
Forest/DML con el outcome recién ampliado a 10 privaciones, se encontró
que `material_pisos_inadecuado` y `material_paredes_inadecuado` se
calculaban con `P4020`/`P4010` — los MISMOS códigos GEIH que
`viv_pisos`/`viv_paredes`, usadas como covariable de heterogeneidad (`X`)
en `5_estimacion.py`. Eso creaba una tautología parcial: un hogar con
piso de tierra sumaba un punto al outcome por definición, independiente
del tratamiento, y la importancia reportada de `viv_pisos`/`viv_paredes`
en el Causal Forest podía ser en parte mecánica.

### Corregido
- `src/3_preprocesamiento.py`: se retiraron `material_pisos_inadecuado` y
  `material_paredes_inadecuado` de `PRIVACIONES` (y su cómputo). El
  índice queda en **8 de 15** privaciones. `K_POBRE` se mantiene en 3
  (sigue siendo el corte más cercano a la tasa oficial de IPM: 16,3 % vs.
  13,0 %, antes 17,2 %).
- `src/5_estimacion.py`: docstring y etiquetas actualizadas (8 en vez de
  10 privaciones); sin cambios de lógica — `X`/`W` no se tocaron.

### Verificado — la importancia de vivienda no era tautológica
Se repitió `5_estimacion.py` y `cotas_frechet_manski.py` con el outcome
de 8 privaciones. Si la importancia de `viv_paredes`/`viv_pisos` hubiera
sido mecánica, debía CAER al quitar el vínculo directo con `Y`. No cayó
— subió levemente (0,600→0,617 sumadas en `ipm_geih_score`; 0,481→0,558
en `POBRE_GEIH`). Evidencia de que la señal de vivienda en el CATE es
real, no un artefacto de la definición del score.

### Recalculado
- ATE (`ipm_geih_score`): +0,0218 → +0,0206. ATE (`POBRE_GEIH`): +0,0050
  → +0,0052 (cambios menores, 2 de 10 componentes poco prevalentes).
- CATE medio: +0,0249 → +0,0237 (`ipm_geih_score`), +0,0041 → +0,0041
  (`POBRE_GEIH`, sin cambio relevante).
- Fréchet-Manski: [-0,4061;+0,3205] → [-0,4083;+0,3080], ancho
  0,7267→0,7163, 365 celdas (sin cambio de cobertura).

### Documentación actualizada
`docs/resultados/README.md`, `RESULTADOS_DML_ATE_ATT_ATU.md`,
`RESULTADOS_CAUSALFOREST_CATE.md` (nueva sección "Chequeo de
tautología"), `RESULTADOS_FRECHET_MANSKI.md`,
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` (nueva sección §1.1),
`docs/seguimiento/RESUMEN_AVANCES.md`, `src/README.md`.

## 2026-10-28 — Diccionario oficial de GEIH: corrección de vivienda y ampliación del indicador a 10 privaciones

Resuelve el bloqueo documentado el 2026-10-27 (no había diccionario
oficial de variables de GEIH). Se obtuvo
`docs/insumos/DICCIONARIO_GEIH_2024.xlsx` (761 filas, portal de
microdatos DANE) y `docs/insumos/DICCIONARIO_SISBEN_2024.xlsx` (3 hojas:
Viv/Pers/Hog).

### Corregido (bug de mapeo, no de adivinanza)
- **`src/armonizacion/armonizar_geih_hogar_2024.py`**: `viv_paredes`,
  `viv_pisos` y `viv_cuartos` apuntaban a columnas GEIH equivocadas desde
  el inicio del proyecto. `viv_paredes` leía en realidad material de
  PISOS (`P4020`), `viv_pisos` leía "¿tiene energía eléctrica? Sí/No"
  (`P4030S1`), y `viv_cuartos` leía "cuartos para dormir" (`P5010`) en
  vez de cuartos en total (`P5000`). Corregido: `viv_paredes`=`P4010`,
  `viv_pisos`=`P4020`, `viv_cuartos`=`P5000`, con `viv_cuartos_dormir`
  (`P5010`) separado como insumo de hacinamiento. También se agregaron
  `viv_alcantarillado` (`P4030S3`), `viv_acueducto` (`P4030S5`) y
  `hog_num_personas` (`P6008`), ubicando los equivalentes de
  `HOG027`/`VIV005`/`VIV008` del Sisbén que estaban pendientes.
- **`src/3_preprocesamiento.py`**: `hacinamiento` usaba `P5020` (tipo de
  servicio sanitario, categórico 1-6) en vez de cuartos para dormir — el
  resultado (23,3 %) parecía plausible por coincidencia de escalas, no
  por estar bien calculado. Corregido con `P5010`/`P6008`: hacinamiento
  real 3,1 %.
- El lado Sisbén (`armonizar_sisben_hogar_2024.py`, `VIV002`/`VIV003`/
  `VIV009`/`VIV005`/`VIV008`/`HOG027`) ya estaba correcto — el bug era
  exclusivamente del lado GEIH.

### Añadido — indicador de pobreza ampliado de 4 a 10 privaciones
- Los candidatos que se habían descartado el 2026-10-27 por no calzar
  con lo esperado (`P3038`/`P3039`, `P5100`-`P5140`) eran, al verificar
  contra el diccionario, preguntas de orientación sexual/identidad de
  género y de valor monetario de arriendo/compra — no los códigos
  correctos de educación/servicios. Con los códigos verificados se
  agregaron: `bajo_logro_educativo_jefe` (`P3042`, nivel < secundaria,
  29,9 %), `inasistencia_escolar_menores` (`P6170`, 6-16 años, cualquier
  miembro del hogar, 2,1 %), `material_pisos_inadecuado` (`P4020`,
  3,5 %), `material_paredes_inadecuado` (`P4010`, 0,9 %),
  `sin_alcantarillado` (`P4030S3`, 18,1 %), `sin_acueducto` (`P4030S5`,
  8,1 %). El indicador pasa de 4 a 10 de las 15 privaciones oficiales del
  IPM, cubriendo ya las 5 dimensiones (antes solo 2). `K_POBRE` se ajustó
  de 2 a 3 (nueva escala 0-10); `POBRE_GEIH` pasa de 23,5 % a 17,2 %.
  Quedan 5 dimensiones sin construir — ver
  `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` §2.

### Recalculado (consecuencia de la corrección, no cambios de método)
- Hot-Deck: Grupo D sube de 10,3 % a 15,6 % nacional (de 31,3 % a 19,0 %
  en Bogotá con año exacto) al corregir `viv_cuartos` — mayor que el
  cambio de haber sumado vivienda a la celda en primer lugar.
- ATE (`ipm_geih_score`): +0,0137 → +0,0218. ATE (`POBRE_GEIH`): +0,0074
  → +0,0050. Los IC95% siguen excluyendo 0 en ambos — el residuo no
  colapsó al corregir el código, lo que ahora es evidencia más confiable
  de que la vivienda sigue colándose fuera de la celda (antes era
  ambiguo: podía ser el bug).
- **CATE: el patrón de heterogeneidad cambió de foco**, no solo de
  magnitud. Antes (código equivocado): dominado por sexo del jefe (jefa
  mujer 36 veces jefe hombre). Ahora (código corregido): dominado por
  zona (rural 2,8-16 veces urbana), con el patrón de sexo invertido y
  mucho más chico. El hallazgo anterior sobre jefatura femenina ya no se
  puede citar — ver `docs/resultados/RESULTADOS_CAUSALFOREST_CATE.md`,
  "Qué cambió y por qué".
- Fréchet-Manski: cota pasa de [-0,627;+0,360] (342 celdas) a
  [-0,4061;+0,3205] (365 celdas) — la celda corregida angosta la cota sin
  cambiar la conclusión (ninguna celda individual excluye 0).

### Documentación actualizada
`docs/resultados/README.md`, `RESULTADOS_HOTDECK.md`,
`COMPARACION_FILTROS_SDP.md`, `RESULTADOS_DML_ATE_ATT_ATU.md`,
`RESULTADOS_CAUSALFOREST_CATE.md`, `RESULTADOS_FRECHET_MANSKI.md`,
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`,
`docs/insumos/DICCIONARIO_HOTDECK.md`,
`docs/seguimiento/RESUMEN_AVANCES.md` — todas con nota explícita de qué
número reemplaza a cuál y por qué, para no perder la trazabilidad de la
corrección.

## 2026-10-27 (2) — Sensibilidad del indicador, representatividad del Sisbén y pruebas automatizadas

### Añadido
- `src/3_preprocesamiento.py`: variantes de umbral (`POBRE_GEIH_K1`...`K4`)
  y función `_validar()` con las validaciones obligatorias (una fila por
  hogar-mes, faltantes tratados explícitamente, cobertura por privación,
  distribución del score, sensibilidad al umbral comparada contra la tasa
  oficial de IPM). Reporte: `docs/reports/reporte_sensibilidad_ipm_geih.csv`.
- `tests/test_preprocesamiento.py`: 6 pruebas con `pytest` sobre datos
  reales (enero 2024) — unicidad de hogar, privaciones binarias sin
  faltantes, umbrales monótonos, consistencia del score.
- `src/validacion/verificar_representatividad_sisben.py`: compara la
  población de GEIH contra los hogares registrados en el Sisbén por
  departamento. Hallazgo: la razón de cobertura varía **32,3 veces** entre
  departamentos (0,4% Valle del Cauca a 12,8% Putumayo) — el registro del
  Sisbén no es una muestra uniforme de GEIH. Detalle en
  `docs/resultados/RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`.
- `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`: documenta la
  construcción de las 4 privaciones, la familia de umbrales, las
  validaciones, y el intento (bloqueado) de ampliar el indicador.

### Bloqueo documentado (no resuelto con una suposición)
- Se auditaron candidatos de GEIH 2024 reales para ampliar el indicador
  de pobreza (asistencia/logro educativo: `P6170`, `P3038`, `P3039`,
  `P3041`-`P3043`; servicios de vivienda: `P5070`, `P5080`, `P5090`,
  `P5100`, `P5110`, `P5130`, `P5140`) — ninguno calza con el concepto
  esperado (varios traen valores monetarios o de tenencia, no acceso a
  servicio binario). Causa: el repositorio no tiene el diccionario oficial
  de variables de GEIH. No se adivinaron los códigos — el indicador se
  queda en 4 privaciones hasta conseguir la ficha técnica.

## 2026-10-27 — Cotas de Fréchet-Manski + reproducción completa del pipeline + índice de resultados

### Añadido
- **`src/estimacion/cotas_frechet_manski.py`**: implementa el ítem "por
  explorar" de la Tabla 1 del documento de pipeline. Calcula `P(Y|X)`
  directamente en GEIH y `P(T|X)` directamente en Sisbén (sin pasar por el
  Hot-Deck) y aplica Fréchet-Hoeffding para acotar el ATE sin suponer
  independencia condicional (CIA). Resultado sobre `POBRE_GEIH`: cota
  **[-0,627; +0,360]** (342 celdas, 100 % de cobertura poblacional GEIH)
  vs. el punto del DML +0,0074 [IC95% +0,004;+0,011] — la cota sin CIA es
  **145 veces más ancha**, y ninguna de las 342 celdas individuales logra
  excluir el cero por su cuenta. Confirma que toda la precisión del DML
  depende de confiar en la suposición del Hot-Deck, no de los datos
  crudos. Detalle en `docs/resultados/RESULTADOS_FRECHET_MANSKI.md`, con
  una propuesta concreta (supuestos de monotonía MTS/MTR) para angostar la
  cota sin llegar a la CIA completa.
- **`docs/resultados/README.md`**: índice y resumen ejecutivo de los 6
  documentos de la carpeta (antes dispersos sin un hilo conductor único).
- Se reprodujo el pipeline completo de punta a punta (Hot-Deck, filtros
  SDP, DAG, preprocesamiento, estimación) y se confirmó que los números
  son idénticos a los del 2026-10-21 — el pipeline es reproducible con
  semillas fijas. Salidas crudas en `docs/reports/resultado_*.txt`
  (corregido el problema de codificación de consola — ahora UTF-8 real,
  no mojibake).

## 2026-10-21 (4) — Primera corrida REAL de ATE/ATT/ATU/CATE

Implementa lo que quedó pendiente en la entrada (3): sumar vivienda a la
celda del Hot-Deck y construir el outcome oficial, luego correr
`3_preprocesamiento.py` y `5_estimacion.py` de verdad (ya no son stubs).

### Añadido
- **Hot-Deck con vivienda en la celda** (`src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py`):
  la celda pasa de `depto+edad` a `depto+edad+viv_cuartos` (tramos 1/2/3+
  cuartos), con degradación de 4 niveles (celda_exacta →
  solo_depto_edad → solo_depto → pool_nacional). Se dejó fuera
  `viv_paredes`/`viv_pisos` — categóricas sin verificar entre fuentes, ver
  abajo. Efecto en la distribución nacional de Grupo: A 28,0%→**31,2%**,
  B 34,4%→35,2%, C 24,9%→23,2%, D 12,7%→**10,3%** — sigue en 100% celda
  exacta.
- **`src/3_preprocesamiento.py` implementado** (antes vacío). Construye
  `ipm_geih_score`/`POBRE_GEIH`, un IPM-GEIH **reducido a 4 de 15
  privaciones**: analfabetismo (`P6160`) y sin aseguramiento de salud
  (`P6090`) — códigos compartidos con IPM, confianza alta —, hacinamiento
  (`P5020` + conteo de personas, umbral >3/cuarto no verificado), y
  `sin_cotizacion_pension_jefe` (`P6920`, tasa de no cotización 56,3%
  calza con la informalidad nacional ~55-58%, pero el indicador mezcla
  informalidad con desempleo/inactividad — limitación explícita en el
  docstring). Se excluyeron `viv_paredes`/`viv_pisos` del outcome (sus
  categorías no están verificadas — ver `DICCIONARIO_HOTDECK.md` §8;
  incluirlas habría significado adivinar qué categoría es "privación").
  Resultado: 23,5% `POBRE_GEIH`, score medio 1,07/4.
- **`src/5_estimacion.py` implementado** (antes vacío). `LinearDML` para
  ATE (toda la muestra) y ATT/ATU (el mismo modelo evaluado sobre T=1 y
  T=0 por separado); `CausalForestDML` para CATE. `W` = celda completa del
  Hot-Deck (`geo_depto+jefe_edad+viv_cuartos`); `X` = covariables no
  usadas en la celda (`geo_zona`, `jefe_sexo`, `viv_paredes`, `viv_pisos`).
  Resultados: ATE≈ATT≈ATU ≈ +0,014 (score 0-4) / +0,007 (`POBRE_GEIH`),
  IC95% excluye 0 en ambos. CATE medio +0,015, concentrado en jefatura
  femenina (+0,029 mujer vs. +0,001 hombre) — `viv_paredes` es la segunda
  variable más importante del forest en ambos outcomes, señal de que
  sigue colándose información de vivienda fuera de la celda. Detalle
  interpretado en `docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md` y
  `docs/resultados/RESULTADOS_CAUSALFOREST_CATE.md`.

### Corregido (bug real, documentado para no repetirlo)
- Primer intento de ATT/ATU con `LinearDRLearner` dio valores absurdos
  (+56, -191 en una escala 0-4) — inestabilidad del estimador doblemente
  robusto por poca superposición de propensión en algunas celdas
  puntuales. Se descartó y se reutilizó el `LinearDML` ya estable,
  evaluado sobre cada subpoblación (T=1, T=0) — ver docstring de
  `_ate_att_atu` en `src/5_estimacion.py`.

### Pendiente (nuevo)
- [ ] Verificar `viv_paredes`/`viv_pisos` contra la ficha oficial de GEIH y, si corresponde, sumarlas a la celda del Hot-Deck y/o al outcome — es la explicación más probable del residuo que no colapsa en ATE/ATT/ATU/CATE.
- [ ] Investigar la heterogeneidad por sexo del jefe en el CATE — ¿real o vivienda/geografía colándose por esa covariable?
- [ ] Refinar `sin_cotizacion_pension_jefe` para separar informalidad de inactividad/desempleo, si aparece una fuente confiable para hacerlo.
- [ ] Completar las 11 privaciones restantes del IPM-GEIH si se consigue el diccionario oficial de GEIH.

## 2026-10-21 (3) — DAG de identificación, filtro dual del SDP y documentación de modelos

A partir de la revisión de *Pipeline de datos y modelos para estimar el
efecto causal del Sisbén IV...* (Roncancio y Fonseca, 2026, PDF del
seminario de grado).

### Añadido
- **`src/4_dag_identificacion.py` implementado** (antes vacío). Construye con
  `networkx` los dos diseños del documento (Figuras 2 y 3) y corre un
  chequeo FORMAL de d-separación (`networkx.is_d_separator`), no solo
  narrado. Hallazgo: **el grafo tal como lo describe la Figura 2 literal
  (un solo nodo "elegibilidad real") NO queda d-separado condicionando
  solo en X** — hay un camino sin bloquear
  `grupo_hotdeck <- elegibilidad_real -> participacion_dps -> resultado_y`
  que el texto no menciona. Separando "elegibilidad del hogar receptor" de
  "elegibilidad del hogar donante" (que es lo que el Hot-Deck real copia —
  nunca la del receptor, que no conoce) el grafo refinado sí queda
  d-separado condicionando solo en X, sosteniendo formalmente la
  afirmación del documento. Salida: `docs/resultados/IDENTIFICACION_CAUSAL.md`,
  `docs/resultados/dag_diseno_principal.png`,
  `docs/resultados/dag_diseno_principal_refinado.png`,
  `docs/resultados/dag_una_tabla.png`. Esto también explica, con teoría de
  grafos, el residuo de -2,3 % en ingreso de la prueba de ATE/CATE de abajo:
  el X de la Figura 2 incluye vivienda, pero la celda del Hot-Deck
  implementada hoy no.
- **Filtro dual del SDP regenerado y comparado lado a lado**
  (`src/armonizacion/armonizar_sisben_bogota_sdp.py` ahora acepta
  `--modo vigencia|anio_exacto`; `src/validacion/comparar_filtros_sdp.py`
  corre el Hot-Deck con ambos donantes). Resultado completo en
  `docs/resultados/COMPARACION_FILTROS_SDP.md` y
  `docs/reports/comparacion_filtros_sdp.csv` — confirma que a nivel
  nacional el filtro casi no cambia el resultado, pero dentro de Bogotá
  el Grupo D pasa de 27,8 % (vigencia) a 17,6 % (año exacto), 10 p.p. de
  diferencia. Se mantiene vigencia como filtro adoptado.
- **`src/estimacion/README.md`**: documenta la carpeta de pruebas
  exploratorias de ATE/ATT/CATE (qué es, qué no es, resultados, limitaciones).
  Referenciado desde `src/README.md`.

### Corregido
- La entrada anterior (2026-10-21 (2)) decía "falta DAG/identificación
  (`4_dag_identificacion.py`, sin implementar)" — ya no aplica, ver arriba.

## 2026-10-21 (2) — Prueba exploratoria de ATE/ATT/CATE + fix de entorno (numpy 2 / econml)

### Corregido (entorno)
- `econml 0.15.0` no era compatible con `numpy 2.x` (los `.pyx` de `econml.tree`/`econml.grf` estaban compilados contra el ABI de numpy 1.x: `ValueError: numpy.dtype size changed`) y `shap<0.44` (dependencia interna de econml) tampoco (`np.obj2sctype` fue removido en numpy 2.0). Se subió a **`econml 0.17.0`** (que a su vez forzó `scikit-learn` de 1.4.2 a **1.9.1**) y **`shap 0.51.0`**. Actualizado en `pyproject.toml`. **`poetry.lock` queda desactualizado** — correr `poetry lock` cuando se tenga Poetry disponible; mientras tanto el entorno funciona vía `pip install` directo sobre el `.venv`.

### Añadido — prueba exploratoria (no es la Fase 4 / `5_estimacion.py`, que sigue sin implementar)
- `src/estimacion/preparar_outcome_prueba_empleo.py`: construye un outcome **provisional** (empleo e ingreso laboral del jefe de hogar, cruzando `caracteristicas_generales` + `ocupados` de GEIH por mes) porque el dataset fusionado del Hot-Deck no tiene ningún outcome todavía (`3_preprocesamiento.py` sigue sin implementar). Resultado: 290.968 hogares, 0 % sin cruce, 62,6 % de jefes ocupados, ingreso laboral mediano $1.300.000 (jefes ocupados, n=181.657) — cifras plausibles para 2024.
- `src/estimacion/prueba_ate_att_cate.py`: corre LinearDML (ATE), LinearDRLearner (ATT) y CausalForestDML (CATE) con `T = 1{Grupo_hotdeck ∈ {A,B}}`, dos veces cada uno — (a) controlando solo por zona/sexo/vivienda, (b) agregando `geo_depto + jefe_edad` (la celda misma del Hot-Deck) — como chequeo de validez: si el "efecto" de (a) no colapsa en (b), es señal de que geografía/edad se está colando por una puerta de atrás, no de que el Hot-Deck tenga información real más allá de su celda. Salida completa en `docs/reports/prueba_ate_att_cate_salida.txt`.
  - **Y1 = jefe ocupado (0/1):** ATE (a) +0,41 p.p. [IC95% +0,03;+0,78] → (b) +0,02 p.p. [IC95% -0,31;+0,35] — **colapsa a 0 como se esperaba**. Mismo patrón en ATT. CATE medio baja de +0,95 a +0,47 p.p. al agregar el control (no colapsa del todo).
  - **Y2 = log(ingreso laboral), jefes ocupados:** ATE (a) -6,56 % → (b) **-2,30 %** [IC95% -3,89;-0,71] — se reduce ~65 % pero **no colapsa a 0**: queda un efecto residual estadísticamente distinto de cero.
  - Lectura: el chequeo de validez pasa para empleo (el Hot-Deck no inventa heterogeneidad en esa variable) pero no del todo para ingreso — el residuo de -2,3 % sugiere que vivienda (`viv_cuartos`, `viv_paredes`, las de mayor importancia en el forest) correlaciona con el grupo Sisbén por una vía distinta a depto+edad (p. ej. submunicipio/estrato dentro del mismo departamento). No se puede concluir que sea un efecto causal del Sisbén — falta DAG/identificación (`4_dag_identificacion.py`, sin implementar) y el tratamiento sigue siendo imputado por Hot-Deck, no observado.

### Pendiente (nuevo)
- [ ] Investigar por qué el residuo de ingreso (-2,3 %) no colapsa con depto+edad — ¿variable de vivienda genuinamente confundida, o matching demasiado grueso a nivel geográfico?
- [x] Re-generar `poetry.lock` con el bump de `econml`/`scikit-learn`/`shap` — hecho.

## 2026-10-21 — Orden de la documentación y acceso a los datos

### Reorganizado
La carpeta `docs/` se agrupa por para qué sirve cada documento (ver [`docs/README.md`](../README.md)):

| Antes | Ahora |
|---|---|
| `docs/DICCIONARIO_DATOS.md`, `docs/DICCIONARIO_HOTDECK.md`, `docs/CODIGOS_LOCALIDAD_BOGOTA.md`, `docs/referencias_teoricas.md` | `docs/insumos/` |
| `data/diccionario_ipm_2025.md` | `docs/insumos/DICCIONARIO_IPM_2025.md` |
| `docs/RESUMEN_AVANCES.md`, `docs/CHANGELOG_PENDIENTES.md` | `docs/seguimiento/` |
| `docs/Anteproyecto_Sisben_IV.docx` | `docs/institucional/` |

`docs/reports/` no cambia: los scripts de calidad de datos escriben allí.

### Añadido
- `docs/insumos/DESCRIPCION_TABLAS.md`: qué es una fila, llave, filas y script de cada tabla de `data/2_models/`.
- `docs/resultados/RESULTADOS_HOTDECK.md`: resultado del emparejamiento y verificación empírica de los códigos de `PER002`.

## 2026-10-10 — Re-corrida del Hot-Deck y verificación de `PER002`

### Confirmado
- **Re-corrida del Hot-Deck** (`src.emparejamiento.emparejamiento_hotdeck_geih_sisben`) sobre el estado actual de datos: mismo resultado que el 2026-10-09 — 290.968 hogares GEIH, 3.290.379 donantes, **100 % celda exacta**, Grupo ponderado A 28,0 % · B 34,4 % · C 25,0 % · D 12,5 %.
- **Hipótesis del ciclo de vida de `PER002` corroborada indirectamente** (`src.validacion.verificar_codigos_edad_sisben`, usa el archivo completo de Personas en Azure, 4.715.226 filas): cruzado contra escolaridad (`PER016`), estado civil (`PER004`) y cotización a pensión (`PER018`), las proporciones por código son coherentes con 3=12–17, 4=18–28, 5=29–59, 6=60+. Además, **0 de 1.820.148 jefes de hogar** tienen `PER002` en {1,2} (códigos de infancia/niñez) — confirma que el hot-deck no pierde ningún jefe al no mapear esos dos códigos. Sigue faltando la ficha oficial de ANDA para una confirmación definitiva. Detalle en `docs/insumos/DICCIONARIO_HOTDECK.md` sección 5.

### Ambigüedades de fondo que persisten (no resueltas por esta corrida)
- El **100 % de celda exacta es un artefacto de una celda muy gruesa** (33 departamentos × 4 ciclos de vida = máx. 130 celdas) combinado con un donante ~11 veces más grande que el receptor — no es evidencia de que el emparejamiento sea preciso. Falta la celda con variables de vivienda para medir sensibilidad.
- `geo_zona`, `jefe_sexo`, `viv_paredes`, `viv_pisos`: sin verificar contra la ficha oficial de cada fuente — no se sabe si el mismo código significa lo mismo en GEIH y en Sisbén.
- Sesgo de selección: el Sisbén solo contiene hogares inscritos — su distribución de grupos no es la de toda la población GEIH.

## 2026-10-10 (2) — Corregido: el SDP no era un corte único, era un registro continuo 2019-2026

### Corregido
- **El archivo del SDP (`sisben/bogota/Sisben_03082026_bog.zip`, 587 MB sin comprimir) trae `fec_fin_encuesta` por hogar, con fechas entre 2019-03-22 y 2026-07-29 — no es un corte único de agosto 2026 como se asumía.** Verificado que cada hogar aparece una sola vez en el archivo (no hay filas duplicadas repitiendo el mismo valor en años distintos): su fecha es la de su único registro, vigente hasta que se actualice.
- **Primer intento — año exacto 2024 — descartado tras revisarlo con el usuario:** solo 75.488 de 1.458.474 jefes (5,2 %) tienen `fec_fin_encuesta` en 2024 exacto. Ese filtro confunde "vigente en 2024" con "re-encuestado en 2024" (el Sisbén no revisita a todos los hogares cada año) y sesga la muestra hacia actualizaciones recientes.
- **Filtro adoptado — vigencia hasta corte (`fec_fin_encuesta <= 2024-12-31`):** consistente con el nacional, cuyo `CORTE` tampoco tiene fecha real por hogar (literal fijo `"SIV_2024"`) — se trata a ambas fuentes como "stock vigente a una fecha". `src/armonizacion/armonizar_sisben_bogota_sdp.py` ahora usa `FECHA_CORTE` (antes `ANIO_CORTE`) y guarda la fecha real de cada hogar en `CORTE`.
- Re-corridas con el donante corregido (filtro de vigencia):
  - **Armonización:** `sisben_bogota_estandarizado.parquet` = **1.274.578** hogares (87,4 % de los 1.458.468; se descartan 183.890 posteriores a 2024). Fusión con nacional: **3.106.489** donantes totales (antes 3.290.379 sin filtrar, 1.907.399 con el año exacto descartado).
  - **Hot-Deck:** 100 % celda exacta. Grupo nacional ponderado: **A 28,0 · B 34,4 · C 24,9 · D 12,7** — prácticamente igual al original sin filtrar (A 28,0/B 34,4/C 25,0/D 12,5), confirma que la distorsión venía del filtro de año exacto, no de excluir los 183.890 hogares 2025-2026.
  - **Dentro de Bogotá (depto 11, 10.016 hogares GEIH) el filtro sí cambia el resultado:** año exacto daba D=17,6 %; vigencia da **D=27,8 %** (10 p.p. de diferencia) — la muestra de "solo recién actualizados" no representa al Sisbén vigente de Bogotá.

### Pendiente (nuevo)
- [ ] Publicar en Azure los parquets corregidos (`sisben_bogota_estandarizado.parquet`, `sisben_estandarizado_2024_con_bogota.parquet`, `geih_sisben_fusionado_2024.parquet`) — pendiente de confirmación antes de sobrescribir el banco de datos compartido.
- [ ] El nacional no expone fecha real por hogar (`CORTE` es un literal fijo) — no se puede verificar si tiene la misma mezcla de antigüedad que Bogotá; queda como limitación no resuelta.

## 2026-10-09 — Armonización, Hot-Deck con Bogotá y reorganización del código

### Corregido
- **Llave de hogar del GEIH (agosto):** los 24.402 hogares de agosto quedaban sin jefe (sexo y edad nulos) porque los identificadores de `hogar_vivienda` y `caracteristicas_generales` no cruzaban por formato. Ahora `DIRECTORIO`, `SECUENCIA_P` y `HOGAR` se normalizan a texto de entero en ambas tablas, y el script avisa si un mes queda con más del 2 % de hogares sin jefe.
- **Edad del jefe en Sisbén:** `PER002` no está en años: el extracto trae códigos 3–6 (ver `DICCIONARIO_HOTDECK.md`). La celda de matching usaba tramos de años contra códigos, y por eso el 89 % caía a `solo_depto`. Ahora se compara por ciclo de vida.
- **Llave completa del Sisbén en la salida:** el parquet armonizado conserva `cod_mpio`, `geo_zona`, `llave`, `CORTE` y `HOGAR` y crea `llave_hogar_sisben` (única, verificada: 1.833.166 filas = 1.833.166 llaves).
- **Viviendas:** se une por `HOGAR` si el archivo lo trae, y se verifica una fila por hogar.
- **Fusión con Bogotá:** columnas de tipo mixto (texto + entero) rompían la escritura a parquet; se convierten a texto.

### Añadido
- **Sisbén Bogotá (SDP, corte 03/08/2026):** 1.458.468 hogares armonizados. En la fusión reemplazan al municipio 11001 del extracto nacional (que traía 1.255 hogares). Donantes totales: 3.290.379.
- **Validación de cobertura de celdas** (`src/validacion/`).

### Resultado del Hot-Deck (12 meses GEIH, 290.968 hogares, donante con Bogotá)
- Celda exacta (departamento + ciclo de vida del jefe): **100 %**.
- Grupo asignado ponderado por `fex`: A 28,0 % · B 34,4 % · C 25,0 % · D 12,5 %.
- Historial de la cobertura: 10,8 % (edad mal codificada) → 91,6 % (edad por ciclo de vida; 8,4 % eran los hogares sin jefe de agosto) → 100 %.

### Reorganización de scripts (nombres alineados con las etapas de la tesis)
| Antes | Ahora | Etapa |
|---|---|---|
| `src/preprocesamiento/estandarizar_geih.py` | `src/armonizacion/armonizar_geih_hogar_2024.py` | Armonización de fuentes |
| `src/preprocesamiento/estandarizar_sisben.py` | `src/armonizacion/armonizar_sisben_hogar_2024.py` | Armonización de fuentes |
| `src/preprocesamiento/estandarizar_sisben_bogota.py` | `src/armonizacion/armonizar_sisben_bogota_sdp.py` | Armonización de fuentes |
| `src/hotdeck/hotdeck_estandarizado.py` | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py` | Emparejamiento estadístico |
| `diagnostico_celdas.py` (raíz) | `src/validacion/validar_cobertura_celdas_hotdeck.py` | Validación |
| `verificar_estandarizado.py` (raíz) | `src/validacion/verificar_esquema_armonizado.py` | Validación |
| `revisar_faltantes_geih.py` (raíz) | `src/validacion/revisar_faltantes_modulos_geih.py` | Validación |
| `src/utils/subir_todo_a_azure.py` | `src/utils/publicar_banco_datos_azure.py` | Banco de datos |
| `src/utils/descargar_todo_desde_azure.py` | `src/utils/restaurar_banco_datos_azure.py` | Banco de datos |

Eliminados de la raíz (scripts temporales, ya cubiertos): `hotdeck_geih_sisben_VALIDADO.py` (primera versión, reemplazada), `diagnostico_env*.py` (depuración de la conexión Azure).
Los nombres de los parquets en `data/2_models/` **no cambiaron**, para no volver a subir el banco de datos.

### Documentación unificada
Todos los `.md` (raíz, `data/`, `docs/`, `src/`, `notebooks/`) y `data/catalogo.yaml` se alinearon al mismo momento del proyecto (2026-10-09): objetivos vigentes P1/OE1, P2/OE2, P3/OE3; fuentes obtenidas (GEIH 2024, IPM 2024, Sisbén nacional y Bogotá); Azure como banco de datos; etapas del código `ingesta → armonizacion → emparejamiento → validacion`. Se retiraron referencias a OE4/OE5, al "puntaje continuo" del Sisbén y a fuentes "por solicitar" que ya se obtuvieron.

### Pendiente
- [x] Verificar en ANDA (`PER002`, V926) la tabla de códigos de ciclo de vida: corroborada indirectamente el 2026-10-10 (ver entrada arriba); falta la ficha oficial para confirmación 100 %.
- [ ] Agregar variables de vivienda a la celda y medir sensibilidad de la distribución de grupos.
- [ ] Verificar categorías de `geo_zona`, `jefe_sexo`, `viv_paredes`, `viv_pisos` entre fuentes.
- [ ] Ubicar en el GEIH equivalentes de `HOG027`, `VIV005`, `VIV008`.
- [ ] Unificar la fecha de corte: Bogotá es agosto 2026; el resto de Sisbén, mayo 2024.
- [ ] Retirar del repositorio los microdatos IPM versionados (`NACIONAL/`, `DEPARTAMENTAL/`, ~330 MB) — ver `docs/RESUMEN_AVANCES.md`.
- [ ] Fase 2: DML y Causal Forest; Fase 3: RD en la frontera B/C.

## Sesiones anteriores
- 2026-09-24: estandarización GEIH/Sisbén, Hot-Deck validado, conexión Azure Blob Storage, renombre del repositorio a `sisben-iv-focalizacion-causal`.
- Ingesta IPM, GEIH (12 meses) y Sisbén IV; limpieza IPM; diccionario de datos; IPM corregido al año 2024; `package-mode = false` en `pyproject.toml`.
