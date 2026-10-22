# Changelog del proyecto

Formato: más reciente primero. Rama de trabajo: `hotdeck-azure-avances`.

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
- [ ] Re-generar `poetry.lock` con Poetry (no disponible en este entorno) para que el bump de `econml`/`scikit-learn`/`shap` quede fijado para todo el equipo.

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
