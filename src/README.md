# Carpeta `src/`: código fuente

El código está organizado como la tesis: una base de ingeniería (llevar
las fuentes a un esquema común y enlazarlas) y tres componentes de
análisis. Los scripts numerados son el recorrido principal; los paquetes
son módulos reutilizables. Los resultados interpretados están en
`docs/resultados/`, con la misma organización.

Comandos de reproducción y orden de ejecución: `CLAUDE.md` (sección
"Validación") y `docs/metodologia/ARQUITECTURA_Y_REPLICACION.md`.

## Base: datos y enlace entre fuentes

| Ruta | Qué hace |
|---|---|
| `1_integracion.py` | Ingesta de las fuentes declaradas en `data/catalogo.yaml` (bronce → plata) |
| `2_limpieza.py` | Limpieza de las tablas del IPM: tipos, duplicados y faltantes |
| `ingesta/` | Lectores de la GEIH (12 meses, CSV o `.DTA`, Latin-1), del Sisbén y de portales Socrata |
| `armonizacion/` | Lleva la GEIH, el Sisbén nacional y el Sisbén de Bogotá (SDP) a un esquema canónico por hogar |
| `emparejamiento/` | Hot-Deck por celdas (departamento, ciclo de vida del jefe, cuartos, nivel de pisos) con cadena de respaldos. Vincula solo a nivel de celda |
| `indicadores/` | Pobreza monetaria reconstruida con la metodología del DANE, homologación del IPM e inventarios de variables de la GEIH |
| `3_preprocesamiento.py` | Outcome IPM-GEIH (8 de 15 privaciones) y muestra de estimación |
| `3b_preprocesamiento_monetario.py` | Pega la pobreza monetaria a la muestra de estimación |
| `validacion/` | Chequeos de calidad de los datos: esquema armonizado, faltantes por módulo, códigos de edad del Sisbén, filtros del SDP, celdas con pisos y paredes, contraste con la pobreza oficial y representatividad del Sisbén |
| `utils/` | Banco de datos en Azure, configuración, validación de la GEIH y `variables_canonicas.py` (reglas compartidas entre fuentes: llaves, jefe de hogar, ciclo de vida) |

## Componente 1: diagnóstico con datos reales

| Ruta | Qué hace |
|---|---|
| `4_dag_identificacion.py` | Los DAG del proyecto y los chequeos formales de d-separación |
| `5_estimacion.py` | DML (ATE, ATT, ATU) y Causal Forest (CATE) sobre el grupo imputado. Es un placebo del emparejamiento, no el efecto del Sisbén |
| `diagnostico/cotas_frechet_manski.py` | Cotas de Fréchet-Manski del ATE, con supuestos de monotonía |
| `diagnostico/cotas_frechet_modelos.py` | Una cota por cada parámetro de los modelos (ATE, ATT, ATU, CATE por subgrupo), con resultados binarios y continuos |
| `diagnostico/errores_focalizacion_frechet.py` | Errores de inclusión y exclusión del Sisbén con datos reales, como cotas por celda |
| `diagnostico/variabilidad_hotdeck.py` | Cuánto cambia un resultado al repetir el sorteo del Hot-Deck (reglas de Rubin) |
| `diagnostico/seleccion_variables_lasso_shap.py` | Qué variables predicen el grupo del Sisbén (OE1) |
| `diagnostico/variables_candidatas_pobreza.py`, `incidencia_transferencias.py` | Qué variables, fuera del Sisbén, ayudan a identificar la pobreza; incidencia de las ayudas declaradas |

Detalle de esta carpeta: `diagnostico/README.md`.

## Componente 2: simulación semisintética

| Ruta | Qué hace |
|---|---|
| `simulacion/` | Módulo del framework: hogares reales de la GEIH, tratamiento y efecto simulados, y qué estimador recupera el efecto según el vínculo entre fuentes. Exige las columnas canónicas (`contrato.py`). `python -m src.simulacion [n_jobs]` |
| `simulacion/calibrar.py`, `simulacion/generador.py` | Modo simulado: parámetros agregados de la GEIH y el Sisbén (sin grupos de menos de 30 hogares) y población sintética con las columnas canónicas |
| `simulacion/datos_propios.py` | Modo de datos propios: con el grupo observado, DML con la celda exacta y cota de Fréchet; con Hot-Deck, rotulado como placebo |
| `simulacion/sensibilidad_semisintetica.py` | Sensibilidad de la evaluación a la confusión no observada y al solapamiento |
| `simulacion/simulacion_identificacion.py` | Simulación sintética previa: por qué el Hot-Deck da un placebo |

Diseño del módulo: `docs/metodologia/DISENO_MODULO_SIMULACION.md`.

## Componente 3: reglas de focalización

| Ruta | Qué hace |
|---|---|
| `focalizacion/reglas_focalizacion.py` | Compara reglas (vigente, proxy de medios, CATE, ideal) con el mismo número de hogares y con el mismo dinero |
| `focalizacion/heterogeneidad_ampliada.py` | Las mismas reglas con un efecto más heterogéneo (niveles ampliado y complejo) |

## Pruebas

`tests/` en la raíz: `poetry run pytest tests/`. El mapa de qué cubre cada
archivo y la prueba de mutación están en `tests/README.md`.

## Estándares de código

- Funciones pequeñas con una sola responsabilidad y docstrings.
- Los nombres de las variables canónicas de la GEIH y del Sisbén no se
  cambian ni se hacen configurables.
- Las categóricas sin orden entran a los modelos como indicadoras, nunca
  como códigos numéricos.
- Semillas fijas y dependencias en `poetry.lock`.
