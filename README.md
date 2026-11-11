
# Proyecto: Inferencia causal sobre la clasificación en el Sisbén IV
---
![Logo Universidad Santo Tomás](https://usantotomas.edu.co/hs-fs/hubfs/social-suggested-images/usantotomas.edu.cohs-fshubfsLogo%20Santoto%20-%20SP%20Bogota%20Horizontal%20blanco-2.png)

## Consultorio de Estadística y Ciencia de Datos
**Universidad Santo Tomás — Facultad de Ingeniería — Maestría en Ciencia de Datos**

- **Estudiantes**: Juan Sebastián Fonseca Arévalo, José Mateo Roncancio Marín
- **Profesor**: Carlos Isaac Zainea Maya
- **Año**: 2026

### 1. Descripción general

Este repositorio contiene el código y los resultados del proyecto de
grado **"Efecto causal del Sisbén IV en la identificación de la pobreza y
el bienestar multidimensional en hogares colombianos"**.

La GEIH dice qué hogares son pobres; el Sisbén IV, cuáles quedan en los
grupos A y B. No comparten llave de hogar, así que se vinculan por
emparejamiento estadístico (Hot-Deck) a nivel de celda. El proyecto
muestra qué se puede y qué no se puede concluir con esa vinculación, y
lo convierte en un **framework de ingeniería y simulación para evaluar
subsidios y transferencias** (enfoque acordado en la tutoría del 3 de
noviembre de 2026).

**La tesis en una base y tres componentes**

| Parte | Pregunta | Hallazgo principal | Código | Resultados |
|---|---|---|---|---|
| Base: datos y enlace | ¿Las fuentes están bien medidas y cómo se vinculan? | Pobreza monetaria reconstruida (33,2 % frente a 31,8 % oficial) e IPM-GEIH; el Hot-Deck vincula solo por celda | `src/ingesta/`, `armonizacion/`, `emparejamiento/`, `indicadores/`, `validacion/` | [`1_datos_y_enlace/`](docs/resultados/README.md#base-datos-y-enlace-entre-fuentes) |
| 1. Diagnóstico con datos reales | ¿Qué permiten decir los datos sobre la clasificación, la pobreza y el efecto? | El DML sobre el grupo imputado es un placebo (≈0); sin el supuesto del vínculo, ninguna cota excluye el cero; al menos 39 % de los A/B no son pobres monetarios | `src/4_dag_identificacion.py`, `5_estimacion.py`, `diagnostico/` | [`2_diagnostico_datos_reales/`](docs/resultados/README.md#componente-1-diagnóstico-con-datos-reales) |
| 2. Simulación semisintética | ¿Qué estimador recupera un efecto conocido según el vínculo entre fuentes? | Con el Hot-Deck todo estimador devuelve ≈0\* aunque el efecto sea +0,095\* | `src/simulacion/` | [`3_simulacion/`](docs/resultados/README.md#componente-2-simulación-semisintética) |
| 3. Reglas de focalización | ¿Cómo cambian los errores de focalización con otras reglas? | Un proxy de medios logra 82-85 %\* de la reducción ideal de la brecha frente a 60 %\* de la clasificación imputada; el CATE estimado no ayuda | `src/focalizacion/` | [`4_focalizacion/`](docs/resultados/README.md#componente-3-reglas-de-focalización) |

\* Resultado simulado.

Para revisar el proyecto, empezar por el [índice de resultados](docs/resultados/README.md).

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

> **Enfoque vigente del componente causal (desde la guía del tutor del
> 2026-10-27).** Con GEIH y Sisbén vinculados por Hot-Deck, el grupo
> imputado se sortea al azar dentro de cada celda, así que un DML sobre él
> da ≈0 sea cual sea el efecto verdadero: es una prueba placebo del
> emparejamiento, no el efecto del Sisbén (lo confirman la simulación de
> identificación y la estimación con datos reales; ver
> [`docs/resultados/README.md`](docs/resultados/README.md)). Por eso el
> P2/OE2 se aborda como una **evaluación semisintética**: sobre hogares
> reales se simula un tratamiento con efecto conocido y se mide cuánto se
> degrada su recuperación (sesgo, RMSE, cobertura, error del CATE) cuando
> el tratamiento se reconstruye por Hot-Deck. Con los datos reales se
> reportan las cotas de Fréchet-Manski, que no fijan ni el signo del
> efecto.

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
- **Librerías que usa el código**:
  - Manipulación de datos: `pandas`, `numpy` (2.x), `pyarrow`, `openpyxl`
  - Banco de datos: Azure Blob Storage (`azure-storage-blob`)
  - Modelos: `scikit-learn` (≥1.9), `scipy`
  - Inferencia causal: `econml` (≥0.17), `networkx` (DAG y d-separación)
  - Interpretabilidad: `shap` (≥0.51)
  - Visualización: `matplotlib`
  - Pruebas: `pytest`

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
    Las versiones salen de `poetry.lock`. `requirements-pruebas.txt` es el
    subconjunto que instala la integración continua, con las mismas versiones
    (una prueba lo verifica).

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

### 5. Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `src/` | Código organizado como la tesis: base (`ingesta/`, `armonizacion/`, `emparejamiento/`, `indicadores/`, `validacion/`, `utils/`), `diagnostico/`, `simulacion/` y `focalizacion/`, más los scripts numerados `1_` a `5_`. Mapa en [`src/README.md`](src/README.md) |
| `docs/resultados/` | Un documento por paso, en cuatro carpetas que siguen la misma estructura, con [índice](docs/resultados/README.md) |
| `docs/reports/` | Salidas crudas de cada script (tablas y consola) |
| `docs/metodologia/` | [Arquitectura y replicación](docs/metodologia/ARQUITECTURA_Y_REPLICACION.md), diseño del módulo de simulación y metodología de la pobreza monetaria |
| `docs/insumos/` | Diccionarios oficiales, ficha del Sisbén IV y homologaciones entre fuentes |
| `docs/seguimiento/` | [Guía de la tesis](docs/seguimiento/SEGUIMIENTO_TESIS_2026-11-04.md), [resumen de avances](docs/seguimiento/RESUMEN_AVANCES.md) y [changelog](docs/seguimiento/CHANGELOG_PENDIENTES.md) |
| `data/` | Estructura de las capas (`0_raw`, `1_processed`, `2_models`) y [catálogo de fuentes](data/catalogo.yaml). Los datos no se versionan: viven en Azure Blob Storage |
| `tests/` | 262 pruebas (`poetry run pytest tests/`) y una prueba de mutación que reintroduce 56 errores conocidos y comprueba que alguna prueba falle. Corren en GitHub Actions en cada push. Mapa en [`tests/README.md`](tests/README.md) |

### 6. Orden de ejecución

1. **Base.** Ingesta (`1_integracion.py`), limpieza (`2_limpieza.py`),
   armonización al esquema canónico por hogar, Hot-Deck por celdas,
   outcomes (`3_preprocesamiento.py`, `indicadores/pobreza_monetaria_geih.py`,
   `3b_preprocesamiento_monetario.py`) y chequeos de `validacion/`. Nunca
   se usan como resultado las privaciones del propio Sisbén (`I1`-`I15`,
   `H_5`).
2. **Diagnóstico con datos reales.** DAG y chequeos de identificación
   (`4_dag_identificacion.py`), DML y Causal Forest como placebo
   (`5_estimacion.py`), cotas de Fréchet-Manski, errores de focalización,
   variabilidad del Hot-Deck y selección y recomendación de variables
   (`diagnostico/`).
3. **Simulación semisintética** (`python -m src.simulacion`) y su
   sensibilidad.
4. **Reglas de focalización** (`focalizacion/`).

Comandos completos y orden exacto: `CLAUDE.md` (sección "Validación").
Cada paso debe reproducir las cifras de `docs/resultados/`.

### 7. Estado del proyecto

| Parte | Estado |
|---|---|
| Fuentes | ✅ GEIH 2024 (12 meses), IPM, Sisbén IV nacional y de Bogotá, armonizadas y validadas contra los diccionarios oficiales. No se solicitarán más datos: la réplica usa solo estas fuentes |
| Base: enlace y outcomes | ✅ Hot-Deck con 99,98 % en celda exacta; IPM-GEIH y pobreza monetaria contrastada con la base oficial (93,9 % de coincidencia) |
| 1. Diagnóstico con datos reales | ✅ DML y Causal Forest (placebo), cotas por parámetro, errores de focalización por celda, selección (OE1) y recomendación de variables |
| 2. Simulación semisintética | ✅ Hasta la convergencia (432 repeticiones) y sensibilidad. El módulo `src/simulacion/` tiene hechos los 7 pasos de su diseño, incluidos el modo simulado y el de datos propios |
| 3. Reglas de focalización | ✅ Con el mismo número de hogares, con el mismo dinero y con heterogeneidad ampliada |
| Documento escrito | En revisión del tutor |

Estado detallado y pendientes:
[`docs/seguimiento/RESUMEN_AVANCES.md`](docs/seguimiento/RESUMEN_AVANCES.md)
y la [guía de la tesis](docs/seguimiento/SEGUIMIENTO_TESIS_2026-11-04.md).

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
