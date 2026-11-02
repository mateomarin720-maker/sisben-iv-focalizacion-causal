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

- Llave de hogar: normalizar con `pd.to_numeric(...).astype("Int64").astype("string")`
  antes de cualquier cruce entre tablas — los mismos IDs llegan como texto
  con formato distinto según el módulo/mes (ver `_norm_llave` en
  `armonizar_geih_hogar_2024.py`).
- Jefe de hogar: GEIH `P6050=="1"`; Sisbén nacional `PER003=="1"`; Sisbén
  Bogotá (SDP) `tip_parentesco=="1"`.
- El SDP (Sisbén Bogotá) es un **registro administrativo continuo**
  (`fec_fin_encuesta` 2019-2026), no un corte único — filtrar por
  vigencia (`<=` fecha de corte), no por año exacto de encuesta (sesga
  hacia actualizaciones recientes). Ver
  `docs/resultados/COMPARACION_FILTROS_SDP.md`.
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
poetry run python src/3b_preprocesamiento_monetario.py
poetry run python src/5_estimacion.py
poetry run python -m src.estimacion.cotas_frechet_manski
poetry run python -m src.validacion.verificar_representatividad_sisben
poetry run python -m src.estimacion.seleccion_variables_lasso_shap
poetry run pytest tests/
```

Cada uno debe reproducir los números ya documentados en
`docs/resultados/` (comparar antes de confiar en un cambio — si algo se
modifica en armonización o emparejamiento, estos números deberían moverse
de forma explicable, no silenciosa). Reportes crudos van a
`docs/reports/`; la interpretación de cada uno vive en `docs/resultados/`
(un documento por paso, con un `README.md` índice).

## Git

- Ramas: `main` (la que se mira por defecto en GitHub) y
  `ediciones-hotdeck-sdp` (trabajo en curso) — mantenerlas sincronizadas
  (fast-forward) después de cada cambio importante, no dejarlas divergir.
- **No agregar `Co-Authored-By` ni narrar el proceso en los mensajes de
  commit** — mensajes cortos y directos, como si describieran el trabajo
  del equipo, no un registro de lo que hizo un asistente.
- Siempre `git pull --rebase` antes de `git push` — el repositorio tiene
  más de un colaborador activo.
