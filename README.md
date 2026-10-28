
# Proyecto: Inferencia causal sobre la clasificación en el Sisbén IV
---
![Logo Universidad Santo Tomás](https://usantotomas.edu.co/hs-fs/hubfs/social-suggested-images/usantotomas.edu.cohs-fshubfsLogo%20Santoto%20-%20SP%20Bogota%20Horizontal%20blanco-2.png)

## Consultorio de Estadística y Ciencia de Datos
**Universidad Santo Tomás — Facultad de Ingeniería — Maestría en Ciencia de Datos**

- **Estudiantes**: Juan Sebastián Fonseca Arévalo, José Mateo Roncancio Marín
- **Profesor**: Carlos Isaac Zainea Maya
- **Año**: 2026

### 1. Descripción General

Este repositorio contiene los artefactos y el código del proyecto de grado
**"Efecto causal del Sisbén IV en la identificación de la pobreza y el
bienestar multidimensional en hogares colombianos"**. El proyecto evalúa
el efecto causal de la clasificación del Sisbén IV sobre el bienestar
multidimensional de hogares colombianos, mediante técnicas de **Causal
Forest** y **Double Machine Learning (DML)**, integrando fuentes GEIH,
Sisbén IV (nacional y Bogotá), IPM y, según el escenario de acceso, DPS.
Como no existe una llave común entre GEIH y Sisbén, ambas se vinculan por
**emparejamiento estadístico (Hot-Deck)**.

A diferencia de un enfoque puramente predictivo, el proyecto se centra en
**inferencia causal**: estimar el efecto de la clasificación Sisbén IV
sobre indicadores de bienestar real, bajo supuestos de identificación
explícitos, con el fin de entender las causas estructurales detrás de los
errores de inclusión y exclusión reportados (DNP-BID, 2022).

La estructura sigue la metodología estandarizada del **Consultorio de
Estadística y Ciencia de Datos** de la USTA, garantizando reproducibilidad,
colaboración y calidad en cada fase del ciclo de vida del proyecto.

### 2. Pregunta de investigación y objetivos

**Pregunta general.** ¿Qué tan bien cumple el Sisbén IV su función de
focalización social en Colombia, tanto en su capacidad de identificar
correctamente a los hogares pobres como en el efecto que la elegibilidad
que confiere produce sobre su bienestar?

**Objetivo general:** evaluar el desempeño del Sisbén IV como instrumento
de focalización social en Colombia, estimando tanto su validez de
clasificación frente a mediciones independientes de pobreza como el efecto
causal de la elegibilidad que confiere —a través de la participación
efectiva en programas de transferencias— sobre el bienestar
multidimensional de los hogares, con base en los microdatos del Sisbén IV
y fuentes oficiales del DANE y el DPS.

**Objetivos específicos (versión vigente, replanteada en septiembre de 2026):**
- **P1 / OE1 — Medición.** Caracterizar los determinantes de la
  clasificación Sisbén IV y evaluar su validez frente a la pobreza medida
  con fuentes independientes (IPM del DANE y pobreza monetaria de la GEIH)
  mediante LASSO/Ridge, SHAP y métricas de concordancia (AUC-ROC, matrices
  de error de inclusión y exclusión). Método predictivo-descriptivo.
- **P2 / OE2 — Causalidad.** Estimar el efecto causal de la elegibilidad
  (grupos A/B), con la participación efectiva en programas del DPS como
  tratamiento de primera etapa (cadena elegibilidad → participación →
  bienestar), mediante Double Machine Learning (efecto promedio) y Causal
  Forest (efectos heterogéneos, CATE), complementado según el acceso a
  datos con un diseño de discontinuidad sobre la frontera ordinal B/C.
- **P3 / OE3 — Política.** Cuantificar cuánto se reducirían los errores de
  inclusión/exclusión y la brecha de pobreza (FGT1) con reglas de
  focalización informadas por los efectos heterogéneos, frente a la
  clasificación vigente.

> El anteproyecto (`docs/institucional/Anteproyecto_Sisben_IV.docx`, abril 2026) aún
> contiene la versión anterior (OE1–OE5); su actualización está pendiente
> a cargo del equipo. Esta es la formulación que rige el código y la
> documentación del repositorio.

Detalle completo de marco teórico, metodología y cronograma en
[`docs/institucional/Anteproyecto_Sisben_IV.docx`](docs/institucional/Anteproyecto_Sisben_IV.docx).

### 3. Stack tecnológico

![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)

- **Lenguaje principal**: Python ≥ 3.11
- **Gestor de dependencias**: Poetry
- **Librerías centrales**:
  - Manipulación de datos: `pandas`, `numpy` (2.x), `pyarrow`
  - Banco de datos: Azure Blob Storage (`azure-storage-blob`)
  - Modelado ML base: `scikit-learn` (≥1.9), `xgboost`
  - Inferencia causal: `dowhy`, `econml` (≥0.17), `causal-learn`, `networkx`
  - Interpretabilidad: `shap` (≥0.51)
  - Visualización: `matplotlib`, `seaborn`, `graphviz`
  - Entorno exploratorio: `jupyterlab`

### 4. Cómo empezar

1. **Clona el repositorio**:
    ```bash
    git clone <url-del-repo>
    cd sisben_causal
    ```

2. **Instala las dependencias con Poetry**:
    ```bash
    poetry install
    ```

3. **Activa el entorno virtual**:
    ```bash
    poetry shell
    ```

4. **Configura las credenciales** (nunca se versionan; `.env` está en `.gitignore`):
    ```bash
    cp .env.example .env
    # completar AZURE_STORAGE_CONNECTION_STRING (pedirla al equipo, no por chat)
    # opcional: SOCRATA_APP_TOKEN para fuentes abiertas
    ```

5. **Restaura el banco de datos desde Azure** (los datos no están en git):
    ```bash
    poetry run python -m src.utils.restaurar_banco_datos_azure
    ```

6. **Lanza Jupyter para explorar los notebooks**:
    ```bash
    jupyter lab
    ```

### 5. Estructura del repositorio

- **`/data`**: Datos en sus tres estados (`0_raw`, `1_processed`, `2_models`)
  y el catálogo de fuentes ([`data/catalogo.yaml`](data/catalogo.yaml)).
  **Los datos no se versionan**: el banco de datos principal es Azure Blob
  Storage (contenedor `datos-inferencia-causal`); ver `.gitignore`.
- **`/docs`**: Documentación, agrupada por para qué sirve (ver
  [`docs/README.md`](docs/README.md)) — insumos (diccionarios de datos),
  [resultados](docs/resultados/README.md) (un documento por paso del
  pipeline, con índice y hallazgos consolidados), seguimiento
  ([resumen de avances](docs/seguimiento/RESUMEN_AVANCES.md) y
  [changelog](docs/seguimiento/CHANGELOG_PENDIENTES.md)) e institucional
  (anteproyecto).
- **`/notebooks`**: Cuadernos de exploración y pruebas de identificación.
- **`/src`**: Código fuente por etapa: `ingesta/`, `armonizacion/`,
  `emparejamiento/`, `estimacion/` (DML/Causal Forest/Fréchet-Manski),
  `validacion/`, `utils/` (incluye Azure) y los scripts numerados `1_` a
  `7_` del flujo metodológico.
- **`/tests`**: Pruebas automatizadas (`poetry run pytest tests/`) sobre
  las transformaciones críticas del pipeline, con datos reales.
- **`.gitignore`**, **`pyproject.toml`** (Poetry, `package-mode = false`) y
  este **`README.md`**.

### 6. Flujo metodológico (resumen)

1. **Integración / ingesta** (`1_integracion.py`, `ingesta/`): fuentes
   crudas → Parquet (GEIH 12 meses 2024, IPM 2024, Sisbén IV nacional y
   Bogotá-SDP). ✅
2. **Limpieza** (`2_limpieza.py`): tipado, duplicados y faltantes
   estructurales documentados. ✅
3. **Armonización** (`armonizacion/`): esquema canónico por hogar (jefe de
   hogar) común a GEIH y Sisbén. ✅
4. **Emparejamiento estadístico** (`emparejamiento/`): Hot-Deck GEIH ←
   Sisbén por celdas (departamento + ciclo de vida del jefe + tramo de
   cuartos de la vivienda). Válido solo a nivel poblacional; no identifica
   el mismo hogar. ✅
5. **Preprocesamiento causal** (`3_preprocesamiento.py`): outcome IPM-GEIH
   (reducido a 4 de 15 privaciones — analfabetismo, aseguramiento de
   salud, hacinamiento, cotización a pensión del jefe; nunca las variables
   propias del Sisbén `I1`–`I15`, `H_5`). ✅
6. **Especificación causal** (`4_dag_identificacion.py`): los dos diseños
   del proyecto (principal, y de una sola tabla) como DAG, con chequeo
   formal de d-separación. ✅
7. **Estimación** (`5_estimacion.py`): DML (ATE/ATT/ATU) y Causal Forest
   (CATE); cotas de Fréchet-Manski como robustez sin suponer independencia
   condicional (`src/estimacion/cotas_frechet_manski.py`). ✅ primera
   corrida real — pendiente resolver `viv_paredes`/`viv_pisos` antes de
   leer el resultado como efecto causal.
8. **Refutación** (`6_refutacion.py`) y **reporte** (`7_reporte/`):
   placebo, sensibilidad, comparación FGT1 (OE3). ⏳ pendiente.

Resultados interpretados de cada paso en
[`docs/resultados/`](docs/resultados/README.md) (empezar por su índice).

### 7. Estado del proyecto

| Objetivo | Qué cubre | Estado |
|---|---|---|
| Fuentes de datos | GEIH, IPM, Sisbén nacional y Bogotá | ✅ Las cuatro obtenidas, armonizadas y validadas. DPS y RUI quedan fuera del alcance vigente o pendientes de gestión (ver §8 y `data/README.md`). |
| Emparejamiento (Hot-Deck) | Asignar grupo Sisbén a GEIH | ✅ 100 % en celda exacta, celda con depto+edad+vivienda, código de edad (`PER002`) corroborado indirectamente. |
| P1 / OE1 — Determinantes y validez (LASSO, SHAP) | Validez de clasificación del Sisbén frente a IPM/GEIH | ⏳ No iniciado. |
| P2 / OE2 — Causalidad (DML, Causal Forest) | Efecto de la elegibilidad A/B sobre el bienestar | 🔧 Primera corrida real completa (ATE/ATT/ATU/CATE + cotas de robustez Fréchet-Manski) — el resultado todavía no se puede leer como efecto causal confirmado: falta verificar las categorías de vivienda (`viv_paredes`/`viv_pisos`) que explican el residuo observado. |
| P3 / OE3 — Reglas de focalización (FGT1) | Comparar reglas actuales vs. alternativas | ⏳ No iniciado, depende de P1 y P2. |

Detalle completo, hallazgos y pendientes técnicos en
[`docs/resultados/README.md`](docs/resultados/README.md) (resultados) y
[`docs/seguimiento/RESUMEN_AVANCES.md`](docs/seguimiento/RESUMEN_AVANCES.md) (estado y pendientes).

### 8. Consideraciones éticas y de datos

- Los datos individuales del Sisbén IV son **sensibles**; se trabaja con
  versiones anonimizadas conforme a las políticas del DNP/SDP y la
  normativa de protección de datos (Ley 1581 de 2012). No se intenta
  identificar hogares individuales (el emparejamiento es poblacional).
- Ninguna base de datos ni credencial se sube al repositorio: los datos
  viven en Azure Blob Storage y las claves en `.env` (ignorado por git).
- Los resultados son de naturaleza académica y no constituyen una
  evaluación oficial del Sisbén IV.

### 9. Créditos y referencia metodológica

El patrón de arquitectura de datos (capas de ingesta, catálogo de fuentes
versionado y trazabilidad de transformaciones) se basa en el enfoque
empleado en el proyecto hermano del Consultorio, *Sinergia socioeconómica:
contratación pública, estructura territorial y economía popular*
(repositorio `desarrollo_social_y_economico`), adaptado aquí a fuentes de
registro social (GEIH, Sisbén IV, IPM, DPS).
