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

## Variables sin verificar — no asumir su dirección/categorías

- **`viv_paredes` y `viv_pisos`**: código de pregunta y categorías
  DISTINTOS entre GEIH (`P4020`/`P4030S1`), Sisbén (`VIV002`/`VIV003` o
  `tip_mat_paredes`/`tip_mat_pisos` en Bogotá) e IPM (`P4005`/`P4015`).
  **No homologar categorías entre fuentes sin verificar contra la ficha
  oficial** — es la causa más probable del residuo que no colapsa a 0 en
  la estimación causal (ver `docs/resultados/IDENTIFICACION_CAUSAL.md` y
  `RESULTADOS_CAUSALFOREST_CATE.md`). Es seguro usarlas como control
  dentro de UNA sola fuente (no comparar categorías entre fuentes).
- **`PER002`** (edad del jefe en Sisbén) es un código de ciclo de vida, no
  años — la correspondencia a rangos (3=12-17, 4=18-28, 5=29-59, 6=60+)
  está corroborada indirectamente (cruce con escolaridad/estado
  civil/pensión) pero no contra la ficha oficial de ANDA.
- **`geo_zona`**: existe en ambas fuentes pero la dirección (¿1=urbano en
  las dos?) no está confirmada.
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
poetry run python src/5_estimacion.py
poetry run python -m src.estimacion.cotas_frechet_manski
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
