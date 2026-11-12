# Arquitectura de datos y guía de replicación

Anexo de la tesis. Describe cómo se organizan los datos, qué controla la calidad en cada
etapa y cómo reproducir los resultados, en todo o en parte. Cantidades medidas sobre el
banco de datos el 2026-11-08.

## Capas de datos

Los datos no se versionan en git. Viven en Azure Blob Storage, con la misma estructura que
`data/` en el equipo local. La fuente de cada archivo, su acceso y su estado están en
[`data/catalogo.yaml`](../../data/catalogo.yaml).

| Capa | Carpeta | Contenido | Volumen | Regla |
|---|---|---|---|---|
| **Bronce** | `data/0_raw/` | Archivos tal como los entrega cada fuente | 280 archivos, 43,2 GB | Solo lectura: nadie los modifica |
| **Plata** | `data/1_processed/` | Cada fuente en Parquet, tipada y limpia, sin cruzarla con otra | 102 archivos, 0,18 GB | Una tabla por módulo y periodo |
| **Oro** | `data/2_models/` | Esquema canónico por hogar, Hot-Deck y tablas de estimación | 14 archivos, 0,20 GB | Generada por código, nunca editada a mano |

La correspondencia con bronce, plata y oro no es exacta: `2_models` guarda también las tablas
armonizadas por fuente, que en un esquema estricto serían plata. Se dejaron ahí porque son
la entrada directa del emparejamiento.

### Qué hay en cada capa

| Tabla | Capa | Filas | Unidad |
|---|---|---|---|
| GEIH 2024: 8 módulos × 12 meses (96 Parquet) | Plata | 829.683 en características generales; 290.968 en hogar y vivienda | Persona u hogar |
| Sisbén IV nacional: hogares / personas / viviendas | Plata | 1.833.166 / 4.715.226 / 1.699.927 | Hogar, persona, vivienda |
| IPM, hogares | Plata | 79.125 | Hogar |
| `geih_estandarizado_2024` | Oro | 290.968 | Hogar (jefe) |
| `sisben_estandarizado_2024` | Oro | 1.833.166 | Hogar (jefe) |
| `sisben_bogota_estandarizado` | Oro | 1.274.578 | Hogar vigente al 31-dic-2024 |
| `sisben_estandarizado_2024_con_bogota` | Oro | 3.106.489 | Donante del Hot-Deck |
| `geih_sisben_fusionado_2024` | Oro | 290.968 | Hogar con grupo imputado |
| `muestra_estimacion_2024` y `_monetaria_2024` | Oro | 290.968 | Tabla de estimación |

El número de hogares se conserva en toda la cadena, de la GEIH plata a la tabla final.

### Fuentes y cómo obtenerlas

| Fuente | Entidad | Acceso | Relación con las demás |
|---|---|---|---|
| GEIH 2024 | DANE | Registro en microdatos | Encuesta base |
| Sisbén IV nacional | DNP | Solicitud institucional | Sin llave con la GEIH: Hot-Deck |
| Sisbén IV Bogotá | SDP | Entrega institucional | Reemplaza a Bogotá en el nacional |
| IPM 2024 | DANE | Registro en microdatos | Sin llave de hogar con las demás: nunca se cruza |
| Pobreza monetaria 2024 | DANE (catálogo 874) | Registro en microdatos | Con llave de la GEIH |
| Marca de víctimas | DANE (catálogo 874) | Registro en microdatos | Con llave de la GEIH |

El proyecto no solicitará más datos. DPS y Registro Único de Víctimas figuran en el catálogo
como pendientes y quedan fuera del alcance.

### Factores de expansión

La GEIH trae el factor de expansión `FEX_C18`, que la armonización renombra `fex`
(`src/armonizacion/armonizar_geih_hogar_2024.py`). Cada uno de los 12 meses se expande a toda
la población, así que la suma anual de `fex` es 12 veces el número de hogares (214,9 millones).
Para totales se usa el mes promedio, `fex / 12`, que da 17,9 millones de hogares; las
proporciones y tasas no cambian. El Sisbén es un registro administrativo, sin diseño muestral
ni factor de expansión: sus proporciones por celda van sin ponderar.

| Análisis | Ponderado | Cómo | Código |
|---|---|---|---|
| Distribución del grupo asignado por el Hot-Deck | Sí | `fex` | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py` |
| Pobreza monetaria reconstruida y contraste con el DANE | Sí | Personas: `FEX_C18 / 12` | `src/indicadores/pobreza_monetaria_geih.py`, `src/validacion/comparar_pobreza_monetaria_oficial.py` |
| Cobertura del Sisbén por departamento | Sí | Hogares: `fex / 12` | `src/validacion/verificar_representatividad_sisben.py` |
| Cotas de Fréchet-Manski | En parte | P(Y \| celda) de la GEIH y la agregación nacional con `fex`; P(T \| celda) del Sisbén sin ponderar | `src/diagnostico/cotas_frechet_manski.py` |
| Errores de focalización | Sí | `fex` | `src/diagnostico/errores_focalizacion_frechet.py` |
| Variabilidad del Hot-Deck | Sí | `fex` | `src/diagnostico/variabilidad_hotdeck.py` |
| Variables candidatas y reglas de focalización | Sí | Hogares: `fex`; personas: `fex` × personas de la unidad de gasto | `src/diagnostico/variables_candidatas_pobreza.py`, `src/focalizacion/reglas_focalizacion.py` |
| Incidencia de las transferencias | Sí | `FEX_C18 / 12` | `src/diagnostico/incidencia_transferencias.py` |
| Sorteo de donantes del Hot-Deck | No | Donante al azar dentro de la celda (el Sisbén no tiene factor) | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py` |
| DML y Causal Forest | No | Estimación sobre la muestra, sin `sample_weight` | `src/5_estimacion.py` |

El DML sin ponderar estima el efecto promedio de la muestra, no el de la población. Con el
grupo imputado es un placebo (Proposición 1) y su límite es cero con o sin ponderación.

## Flujo

| Etapa | Código | Entrada → salida | Resultado |
|---|---|---|---|
| 1. Ingesta | `src/1_integracion.py`, `src/ingesta/` | Bronce → plata | |
| 2. Limpieza | `src/2_limpieza.py` | IPM en plata | |
| 3. Armonización | `src/armonizacion/` | Plata → esquema canónico | `src/validacion/verificar_esquema_armonizado.py` |
| 4. Emparejamiento | `src/emparejamiento/` | GEIH ← Sisbén, por celda | `RESULTADOS_HOTDECK.md` |
| 5. Resultados | `src/3_preprocesamiento.py`, `src/indicadores/`, `src/3b_preprocesamiento_monetario.py` | Tabla de estimación | `RESULTADOS_POBREZA_MONETARIA.md` |
| 6. Identificación | `src/4_dag_identificacion.py` | DAG | `IDENTIFICACION_CAUSAL.md` |
| 7. Estimación | `src/5_estimacion.py`, `src/diagnostico/` | Diagnóstico y cotas | `RESULTADOS_DML_ATE_ATT_ATU.md`, `RESULTADOS_FRECHET_MANSKI.md` |
| 8. Simulación | `src/simulacion/`, `src/validacion/` | Evaluación semisintética\* | `SIMULACION_SEMISINTETICA.md`, `RESULTADOS_REGLAS_FOCALIZACION.md` |
| 9. Focalización | `src/diagnostico/variables_candidatas_pobreza.py`, `incidencia_transferencias.py` | Recomendación e incidencia | `RECOMENDACION_VARIABLES_POBREZA.md` |

Los reportes crudos van a `docs/reports/`, y su interpretación, a `docs/resultados/`.

## Reglas compartidas

- **Esquema canónico.** Los nombres estandarizados de GEIH y Sisbén no cambian ni se
  configuran. Quien traiga datos de otra institución debe usarlos:
  `src/simulacion/contrato.py` los exige y valida sus códigos, sin renombrar.
- **Una sola versión de cada regla.** Llaves de hogar, jefe de hogar y ciclo de vida están en
  `src/utils/variables_canonicas.py`. La celda del Hot-Deck y su cadena de respaldos están en
  `claves_por_nivel`, que usan el emparejamiento y la simulación.
- **Sin secretos en git.** Las credenciales van en `.env`, excluido del repositorio.

## Controles de calidad

| Control | Qué detecta | Evidencia |
|---|---|---|
| Etiquetas contra los diccionarios oficiales | Una columna que "suena bien" pero es otra | `tests/test_armonizacion.py`. Hasta octubre, `viv_paredes` leía en realidad material de pisos, sin dar error |
| 12 meses, no uno | Formatos que cambian entre meses | Agosto llegó en otro formato y su pobreza salía en 6,9 % frente a ≈17 %, sin error; hay prueba específica |
| Conservación de hogares | Cruces que pierden filas | 290.968 hogares en toda la cadena; los cruces validan su cardinalidad |
| Cobertura del Hot-Deck | Celdas sin donante | 99,98 % en celda exacta, 993 celdas |
| Contraste con cifras oficiales | Resultado mal reconstruido | Pobreza monetaria 33,2 % frente a 31,8 % oficial; misma clasificación que el DANE en el 93,9 % de los hogares |
| Propensión contra la empírica | Categóricas usadas como número | `5_estimacion.py` la imprime por celda |
| Equivalencia al refactorizar | Que mover código cambie resultados | `tests/test_simulacion_equivalencia.py` |
| Pruebas automáticas | Errores conocidos y nuevos | 263 pruebas y 57 errores reintroducidos por mutación, en GitHub Actions en cada cambio |
| Prueba de mutación | Pruebas que pasan aunque el error vuelva | 43 errores reintroducidos, los 43 detectados (`tests/mutaciones.py`) |
| Convergencia Monte Carlo | Simulaciones con demasiado ruido | Repeticiones hasta que el error estándar Monte Carlo queda bajo el umbral |

## Guía de replicación

Requisitos: Python ≥ 3.11, Poetry y unos 45 GB de disco para la réplica completa.

```bash
git clone <url-del-repositorio>
cd sisben_causal
poetry install
cp .env.example .env
```

### Ruta A: verificar el código, sin datos

No requiere credenciales. Las 7 pruebas que leen la GEIH real se saltan.

```bash
poetry run pytest tests/
python tests/mutaciones.py
```

### Ruta B: reproducir resultados desde las tablas ya construidas

Es la ruta para un jurado o una revisión. Quien administra el banco genera una URL de solo
lectura con vencimiento, y quien la recibe la pone en `.env` como `AZURE_CONTAINER_SAS_URL`.
La URL es un secreto mientras no venza.

```bash
# administrador del banco
poetry run python -m src.utils.generar_acceso_lectura_azure --dias 30
# revisor
poetry run python -m src.utils.restaurar_banco_datos_azure
```

Sin el argumento `--solo` se descargan las tres capas (unos 43 GB). Con `--solo 2_models` se
descargan solo las tablas oro (0,20 GB), que bastan para la estimación, la simulación y las
cotas. La incidencia, las variables candidatas y la pobreza monetaria leen además la plata
(`--solo 1_processed`) y, en el caso de la marca de víctimas, un archivo de bronce.

### Ruta C: desde las fuentes originales

1. Obtener las fuentes según la tabla anterior y depositarlas en `data/0_raw/<fuente>/`.
2. Pasar a plata y armonizar:

```bash
poetry run python src/1_integracion.py
poetry run python -m src.ingesta.sisben_loader
poetry run python src/2_limpieza.py
poetry run python -m src.armonizacion.armonizar_geih_hogar_2024
poetry run python -m src.armonizacion.armonizar_sisben_hogar_2024
poetry run python -m src.armonizacion.armonizar_sisben_bogota_sdp RUTA_CSV
```

3. Correr el resto en este orden. Cada paso debe reproducir lo documentado en `docs/resultados/`.

```bash
poetry run python -m src.emparejamiento.emparejamiento_hotdeck_geih_sisben
poetry run python src/4_dag_identificacion.py
poetry run python src/3_preprocesamiento.py
poetry run python -m src.indicadores.pobreza_monetaria_geih
poetry run python src/3b_preprocesamiento_monetario.py
poetry run python src/5_estimacion.py
poetry run python -m src.diagnostico.cotas_frechet_manski
poetry run python -m src.diagnostico.cotas_frechet_modelos
poetry run python -m src.diagnostico.errores_focalizacion_frechet
poetry run python -m src.diagnostico.seleccion_variables_lasso_shap
poetry run python -m src.diagnostico.variables_candidatas_pobreza 6
poetry run python -m src.diagnostico.incidencia_transferencias
poetry run python -m src.simulacion
poetry run python -m src.focalizacion.reglas_focalizacion
poetry run python -m src.focalizacion.heterogeneidad_ampliada
poetry run python -m src.simulacion.sensibilidad_semisintetica
poetry run python -m src.diagnostico.variabilidad_hotdeck 2
```

Los scripts numerados se ejecutan directamente: un módulo no puede empezar por dígito. En
Windows, para guardar la salida en un archivo, definir `PYTHONIOENCODING=utf-8`.

Tiempos de referencia en el equipo del proyecto (8 núcleos): variables candidatas, unos 50
minutos; reglas de focalización, unos 35; evaluación semisintética, de 1,5 a 4 horas.

## Reutilización por otra institución

| Se puede cambiar | No se puede cambiar |
|---|---|
| Escenarios, vínculos, efecto verdadero y umbrales de convergencia (`src/simulacion/escenarios.py`) | Los nombres canónicos de las columnas |
| Fuentes de entrada, si cumplen el contrato | Los dominios de código de cada columna |

## Limitaciones

- **La ruta C no se ha ejecutado completa en un entorno limpio.** Cada etapa se corrió en el
  equipo del proyecto y GitHub Actions corre las pruebas sin datos, pero no hay una corrida
  de punta a punta desde bronce.
- **Los dos modos del módulo de simulación no se han corrido con datos de otra institución.**
  El modo simulado (`calibrar.py`, `generador.py`) y el de datos propios (`datos_propios.py`)
  están implementados y probados con la GEIH y el Sisbén del proyecto
  (`DISENO_MODULO_SIMULACION.md`); con datos enlazados de otra entidad, que no existen aún,
  solo se ha comprobado que el contrato de columnas canónicas los valida.
- **El acceso al Sisbén es institucional:** la réplica desde fuentes depende de esa entrega.
- **Sin ajuste por diseño muestral** en los estimadores, y el factor de expansión solo pondera
  agregados descriptivos y los modelos de focalización.

\* Resultado simulado.
