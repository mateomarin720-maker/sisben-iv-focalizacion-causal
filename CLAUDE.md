# CLAUDE.md — contexto persistente del proyecto

Proyecto de grado: efecto causal del Sisbén IV sobre el bienestar
multidimensional de hogares colombianos (GEIH + Sisbén IV + IPM, sin llave
común entre fuentes — vinculadas por Hot-Deck). Antes de asumir nada sobre
el estado del proyecto, leer
[`docs/resultados/README.md`](docs/resultados/README.md) (índice y
hallazgos consolidados) y
[`docs/seguimiento/RESUMEN_AVANCES.md`](docs/seguimiento/RESUMEN_AVANCES.md)
(estado y pendientes) — son la fuente de verdad, más confiable que inferir
del código.

## Enfoque vigente y reglas del tutor (tutoría del 2026-11-03)

Guía de la tesis desde el 2026-11-04:
[`docs/seguimiento/SEGUIMIENTO_TESIS_2026-11-04.md`](docs/seguimiento/SEGUIMIENTO_TESIS_2026-11-04.md)
(enfoque, estado y prioridades). La tesis es un **framework de ingeniería
y simulación para evaluar subsidios y transferencias**, en tres bloques:
arquitectura e ingeniería (enlazar las bases y correr los modelos, de
forma reutilizable), simulación semisintética como módulo independiente
(modo con datos propios ya enlazados y modo simulado) y discusión de
focalización (qué variables podría incorporar el Sisbén, como pregunta
abierta y recomendación, no como conclusión causal). Reglas del tutor:

- **Los nombres de las variables estandarizadas de GEIH y Sisbén no se
  cambian ni se hacen configurables**; lo flexible es el resto del
  framework. Un módulo que reciba datos de otra institución exige los
  nombres canónicos y valida que estén; no los renombra.
- **El DML sobre el grupo imputado no se presenta como efecto causal del
  Sisbén** (es un placebo del emparejamiento). Además, un solo sorteo del
  Hot-Deck subestima la incertidumbre: la mitad de la varianza viene de
  la imputación (`RESULTADOS_VARIABILIDAD_HOTDECK.md`); repetir el sorteo
  y combinar con Rubin antes de leer un IC.
- **Resultados simulados con asterisco (\*)** en toda tabla o cifra que
  los mezcle o los presente cerca de resultados con datos reales.
- **El repositorio es entregable al jurado:** limpio y sin ruido. No dejar
  archivos de prueba, ramas ni salidas sin propósito.

## Entorno

- Python ≥3.11. Dependencias con Poetry (`pyproject.toml` /
  `poetry.lock`), pero si Poetry no está disponible en el entorno, el
  `.venv` ya tiene todo instalado — usar
  `./.venv/Scripts/python.exe` (Windows) directo con `pip install` si hace
  falta agregar algo, y luego reflejarlo en `pyproject.toml`.
- Los datos **no se versionan en git** — banco de datos en Azure Blob
  Storage (`src/utils/publicar_banco_datos_azure.py` /
  `restaurar_banco_datos_azure.py`). `data/0_raw`, `1_processed`,
  `2_models` están en `.gitignore`.
- En Windows/Git Bash, redirigir la salida de un script a un archivo
  **sin** `PYTHONIOENCODING=utf-8` produce mojibake (el consola usa
  Latin-1/cp1252, no UTF-8) — correr así:
  `PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe script.py > salida.txt 2>&1`.
- Los scripts numerados (`3_preprocesamiento.py`, `4_dag_identificacion.py`,
  `5_estimacion.py`...) se ejecutan como **script directo**
  (`poetry run python src/4_dag_identificacion.py`), **no** con `-m` — un
  nombre de módulo no puede empezar con dígito.
- GEIH crudo viene en **Latin-1**, no UTF-8 (`encoding="latin1"` en
  `local_csv_parser`/`geih_loader`).

## Bugs ya encontrados — no repetirlos

- **Variables categóricas sin orden dentro de un modelo lineal de
  `econml`** (`LinearDML`/`LinearDRLearner`) rompen la estimación. Pasar
  `geo_depto_cat` (33 códigos sin orden) como `X` de un `LinearDRLearner`
  dio efectos de +56/-191 en una escala 0-4 — inestabilidad del estimador
  doblemente robusto, no un error visible. Las categóricas sin orden van
  en `W` (controles, con modelos no lineales tipo GradientBoosting/Logistic),
  nunca en `X` de un estimador *lineal*. Para `CausalForestDML` (no
  lineal) sí es seguro pasarlas en `X`.
- **Tampoco como código numérico en los modelos auxiliares
  (`model_t`/`model_y`).** Hasta el 2026-11-02 `5_estimacion.py` pasaba la
  celda del Hot-Deck (0..375) y el departamento (0..32) como números a una
  `LogisticRegression`: la propensión con la "celda exacta" salía
  ≈0,64 para todos, cuando P(T|celda) real va de 0,36 a 0,87, y los ATE
  (+0,02, IC sin el 0) eran un artefacto; con indicadoras dan ≈0. No da
  error. Comprobar siempre la propensión estimada contra la empírica por
  celda (`5_estimacion.py` lo imprime).
- **`econml 0.15` no es compatible con `numpy 2.x`** (ni `shap<0.46`,
  dependencia interna de econml). Versión mínima vigente:
  `econml>=0.17`, `shap>=0.51`, `scikit-learn>=1.9` (`pyproject.toml` ya
  actualizado).
- GEIH trae variantes de nombre de módulo entre meses (ej. "No
  ocupado.CSV" en marzo vs. "No ocupados.CSV" el resto del año) y algunos
  meses solo tienen el CSV incompleto pero el `.DTA` completo — el loader
  ya maneja ambos casos (`geih_loader.py`, fallback a `.DTA` vía
  `parse_stata_a_parquet`), pero si se toca ese código, probar con los 12
  meses, no solo uno.
- **El mapeo GEIH→esquema canónico de vivienda estuvo equivocado desde el
  inicio del proyecto hasta el 2026-10-28** (no por adivinar, por una
  hipótesis sin verificar): `viv_paredes` leía en realidad material de
  PISOS (`P4020`), `viv_pisos` leía "¿tiene energía eléctrica?" (`P4030S1`),
  `viv_cuartos` leía "cuartos para dormir" (`P5010`) en vez de cuartos en
  total (`P5000`). El bug no daba error — los nombres de columna GEIH
  sonaban correctos y los scripts corrían sin fallar; solo se detectó al
  comparar contra el diccionario oficial
  (`docs/insumos/DICCIONARIO_GEIH_2024.xlsx`). Lección: con GEIH, no
  confiar en que un P-code "suena" al concepto esperado — verificar
  contra el diccionario (ya disponible, ver abajo) antes de mapear una
  columna nueva, incluso si el resultado agregado parece razonable (el
  hacinamiento viejo daba 23,3 %, un número plausible, calculado con la
  columna equivocada). Detalle completo:
  `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`.

- **Los códigos numéricos de GEIH no siempre siguen el orden de las
  letras del diccionario.** `P6050` trae 13 códigos para 9 letras, y en
  `P6430` el 7 es jornalero o peón (99 % declara salario), no "sin
  remuneración" como sugiere la letra g; sin remuneración son el 6 y el
  8. Verificar con los datos (cruce con otra variable) antes de usar un
  código por su letra.

- **Agosto 2024 de GEIH se carga desde `.DTA`** (7 de 8 módulos).
  Hasta el 2026-11-02, `parse_stata_a_parquet` dejaba los códigos como
  `"1.0"` y los faltantes como `"nan"`, y toda comparación de texto
  (`== "2"`, `_si()`) fallaba ese mes sin dar error (`POBRE_GEIH` 6,9 % en
  agosto vs. ≈17 % el resto del año). Corregido en el parser, con prueba
  (`tests/test_local_csv_parser.py`), y pipeline regenerado. Si se toca
  la carga, verificar que agosto no tenga `"1.0"` ni `"nan"`.

## Diccionarios oficiales de variables

`docs/insumos/DICCIONARIO_GEIH_2024.xlsx` (761 filas: ID/Nombre/Etiqueta/
Tipo/Formato/Pregunta/Módulo) y `docs/insumos/DICCIONARIO_SISBEN_2024.xlsx`
(3 hojas: Viv/Pers/Hog, columnas Nombre/Etiqueta) — obtenidos 2026-10-28,
resuelven el bloqueo que existía por falta de la ficha técnica oficial de
GEIH (IPM ya tenía la suya en `docs/insumos/DICCIONARIO_IPM_2025.md`).
**Antes de mapear o usar una columna de GEIH que no esté ya en
`armonizar_geih_hogar_2024.py`/`3_preprocesamiento.py`, verificar su
código contra este diccionario** — no asumir por el nombre o la posición
en el cuestionario (ver el bug de vivienda arriba). El diccionario de
Sisbén es solo Nombre/Etiqueta (sin lista de categorías por código), así
que no basta para homologar categorías: para eso está la ficha del Sisbén
IV (`docs/insumos/FICHA_SISBEN_IV_FCS_2017.pdf`), que sí trae los códigos
de respuesta.

## Variables sin verificar — no asumir su dirección/categorías

- **`viv_paredes` y `viv_pisos`: homologadas el 2026-11-02** con la
  ficha del Sisbén IV (`docs/insumos/FICHA_SISBEN_IV_FCS_2017.pdf`) y
  verificadas contra `I13`/`I14` del DNP. Tabla de equivalencias en
  `docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`. **Los códigos
  crudos NO son comparables entre fuentes** (en pisos el orden va al
  revés: tierra es 1 en GEIH y 5 en Sisbén); comparar solo a través de la
  escala común del documento. Bogotá (SDP) es coherente con la ficha pero
  no se pudo verificar con privaciones.
- **`PER002`** (edad del jefe en Sisbén) es un código de ciclo de vida, no
  años — la correspondencia a rangos (3=12-17, 4=18-28, 5=29-59, 6=60+)
  está corroborada indirectamente (cruce con escolaridad/estado
  civil/pensión) pero no contra la ficha oficial de ANDA.
- **`geo_zona`**: 1 = urbano en las dos fuentes. En GEIH lo dice el
  diccionario (`CLASE`); en el Sisbén se infiere de `I14` (2026-11-02,
  ver la homologación de vivienda), no de una ficha de la variable.
- Variables cardinales (conteos: `viv_cuartos`, número de personas) SÍ son
  seguras de comparar/sumar a una celda de matching sin homologar — no
  necesitan tabla de equivalencia de categorías.

## Convenciones de datos

- **Módulo de simulación (`src/simulacion/`):** exige las columnas
  canónicas (`contrato.py`) y las valida; no agregar alias, mapeos ni
  columnas derivadas como entrada (la celda la calcula el módulo).

- **Reglas compartidas entre fuentes en un solo lugar:**
  `src/utils/variables_canonicas.py` (desde 2026-11-04). Usarlo, no
  copiar la regla en otro módulo — hasta esa fecha la normalización de
  llaves estaba copiada en seis módulos y los tramos de edad en dos.
  - Llave de hogar: `normalizar_llave` antes de cualquier cruce entre
    tablas — los mismos IDs llegan como texto con formato distinto según
    el módulo/mes ("01", "1", "1.0").
  - Jefe de hogar: `es_jefe(df, fuente)` — GEIH `P6050=="1"`; Sisbén
    nacional `PER003=="1"`; Sisbén Bogotá (SDP) `tip_parentesco=="1"`.
  - Edad en años → código de ciclo de vida de `PER002`: `edad_a_ciclo`
    (GEIH y Bogotá; el nacional ya trae el código).
- El SDP (Sisbén Bogotá) es un **registro administrativo continuo**
  (`fec_fin_encuesta` 2019-2026), no un corte único — filtrar por
  vigencia (`<=` fecha de corte), no por año exacto de encuesta (sesga
  hacia actualizaciones recientes). Ver
  `docs/resultados/COMPARACION_FILTROS_SDP.md`. El crudo no está en
  `0_raw/` de Azure sino en `sisben/bogota/Sisben_03082026_bog.zip`
  (un CSV de 587 MB, separador `;`).
- IPM no comparte llave de hogar con GEIH/Sisbén — nunca intentar un
  cruce a nivel hogar entre IPM y las otras dos fuentes.
- Nunca usar `I1`-`I15` ni `H_5` del Sisbén como outcome — son privaciones
  calculadas por el propio Sisbén (circularidad).

## Validación — qué correr y en qué orden

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
poetry run python -m src.estimacion.variables_candidatas_pobreza 6
poetry run python -m src.estimacion.variables_candidatas_pobreza 6 poblacion
poetry run python -m src.estimacion.incidencia_transferencias
poetry run python -m src.validacion.comparar_celdas_hotdeck_vivienda
poetry run python -m src.simulacion
poetry run python -m src.validacion.reglas_focalizacion
poetry run python -m src.validacion.sensibilidad_semisintetica
poetry run python -m src.validacion.variabilidad_hotdeck 2
poetry run pytest tests/
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe tests/mutaciones.py
```

Cada uno debe reproducir los números ya documentados en
`docs/resultados/` (comparar antes de confiar en un cambio — si algo se
modifica en armonización o emparejamiento, estos números deberían moverse
de forma explicable, no silenciosa). Reportes crudos van a
`docs/reports/`; la interpretación de cada uno vive en `docs/resultados/`
(un documento por paso, con un `README.md` índice).

Pruebas: mapa de qué cubre cada archivo en `tests/README.md`. Si se
encuentra un error nuevo, agregar la prueba que lo habría detectado y su
mutación en `tests/mutaciones.py` (que comprueba que las pruebas fallan
cuando el error vuelve; 43 de 43 el 2026-11-08). Antes de mapear una
columna nueva de GEIH o del Sisbén, agregar su etiqueta esperada en
`tests/test_armonizacion.py`.

## Git

- Ramas: `main` (la que se mira por defecto en GitHub) y
  `ediciones-hotdeck-sdp` (trabajo en curso) — mantenerlas sincronizadas
  (fast-forward) después de cada cambio importante, no dejarlas divergir.
- **No agregar `Co-Authored-By` ni narrar el proceso en los mensajes de
  commit** — mensajes cortos y directos, como si describieran el trabajo
  del equipo, no un registro de lo que hizo un asistente.
- Siempre `git pull --rebase` antes de `git push` — el repositorio tiene
  más de un colaborador activo.
