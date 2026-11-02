# Auditoría de variables para los proxies de pobreza multidimensional

*2026-11-02 · Rama `comparacion-proxies-ipm` · Fases 1 y 2 de la comparación de proxies.*

Esta entrega cubre la **auditoría** (Fase 1) y la **matriz de homologación**
(Fase 2), para revisión antes de construir indicadores nuevos. No se
construyó ningún indicador, no se corrió ningún modelo y no se modificó
ningún resultado existente.

| Producto | Archivo |
|---|---|
| Matriz de homologación (documento) | [`01_matriz_homologacion.md`](01_matriz_homologacion.md) |
| Matriz de homologación (tabla) | [`01_matriz_homologacion.csv`](01_matriz_homologacion.csv) |
| Inventario de variables GEIH | [`docs/reports/inventario_variables_geih.csv`](../../reports/inventario_variables_geih.csv) |
| Diagnóstico de insumos por privación | [`docs/reports/diagnostico_insumos_homologacion.csv`](../../reports/diagnostico_insumos_homologacion.csv) |
| Scripts | `src/indicadores/inventario_variables_geih.py`, `src/indicadores/homologacion_ipm.py` |
| Pruebas | `tests/test_homologacion_ipm.py` |

## 1. Fuentes consultadas

- **Regla oficial de las 15 privaciones:** DANE, *Metodología Índice de
  Pobreza Multidimensional (IPM)*,
  [met-IPM.pdf](https://www.dane.gov.co/files/operaciones/PM/met-IPM.pdf),
  §3.2.1 (pp. 15-26) y glosario (pp. 29-31). De ahí salen umbrales, edades,
  reglas urbano/rural y ponderación: cada dimensión pesa 1/5, las variables
  pesan lo mismo dentro de su dimensión, y un hogar es pobre si el índice
  ponderado es ≥ 5/15.
- **Códigos GEIH:** `docs/insumos/DICCIONARIO_GEIH_2024.xlsx` (texto
  completo de cada pregunta y sus categorías).
- **Códigos Sisbén:** `docs/insumos/DICCIONARIO_SISBEN_2024.xlsx`. Solo
  trae Nombre/Etiqueta: permite asociar cada privación a las preguntas de
  la ficha, pero **no** documenta la regla con que el DNP calcula
  `I1`-`I15`. El documento metodológico del DNP no está en el repositorio
  y el enlace que se encontró (Cali, catálogo 110) respondió con error.
- **Datos:** GEIH 2024, 12 meses, `data/1_processed/geih/2024/`
  (restaurado desde Azure el 2026-11-02).
- **Código del proyecto:** `src/armonizacion/armonizar_geih_hogar_2024.py`,
  `src/3_preprocesamiento.py`, `src/emparejamiento/`.

## 2. Inventario (Fase 1)

### 2.1 Variables GEIH originales disponibles

`src/indicadores/inventario_variables_geih.py` cruza las columnas de los
parquet procesados con el diccionario oficial y con el código del proyecto.

| Módulo | Columnas | En el diccionario | En los 12 meses | Ya usadas por el proyecto¹ |
|---|---|---|---|---|
| Características generales | 70 | 67 | 70 | 14 |
| Hogar y vivienda | 52 | 48 | 51 | 13 |
| Fuerza de trabajo | 47 | 43 | 46 | 7 |
| Ocupados | 204 | 200 | 203 | 8 |
| No ocupados | 41 | 37 | 40 | 7 |
| Otras formas de trabajo | 116 | 112 | 115 | 7 |
| Otros ingresos | 63 | 59 | 62 | 7 |
| Migración | 47 | 42 | 46 | 7 |

¹ Incluye las llaves (`DIRECTORIO`, `SECUENCIA_P`, `HOGAR`, `ORDEN`) y
variables de diseño, que se repiten en todos los módulos.

Las únicas columnas sin entrada en el diccionario son `P3375` y 4 columnas
de trazabilidad de la ingesta (`_source`, `_source_file`, ...). Ninguna
se necesita para las privaciones.

### 2.2 Variables armonizadas existentes

`armonizar_geih_hogar_2024.py` (esquema canónico por hogar, usado por el Hot-Deck):

| Canónica | Código GEIH | Verificación |
|---|---|---|
| `geo_depto`, `geo_zona` | `DPTO`, `CLASE` | Confirmadas (CLASE: 1 urbano, 2 rural) |
| `viv_paredes`, `viv_pisos` | `P4010`, `P4020` | Código confirmado; categorías sin homologar con Sisbén |
| `viv_cuartos`, `viv_cuartos_dormir` | `P5000`, `P5010` | Confirmadas |
| `viv_alcantarillado`, `viv_acueducto` | `P4030S3`, `P4030S5` | Confirmadas |
| `hog_num_personas` | `P6008` | Confirmada |
| `jefe_sexo`, `jefe_edad` | `P3271`, `P6040` (jefe) | Confirmadas |
| `fex` | `FEX_C18` | — |

### 2.3 Proxy de pobreza ya construido (`IPM_GEIH_BASE`)

`src/3_preprocesamiento.py` construye 8 privaciones binarias, su suma
`ipm_geih_score` (0-8, sin ponderar), `POBRE_GEIH` (score ≥ 3) y
`POBRE_GEIH_K1`…`K8`. Se conserva tal cual como **`IPM_GEIH_BASE`**.
Frente a la regla oficial difiere así:

| Privación BASE | Privación oficial | Diferencia frente a la regla DANE |
|---|---|---|
| `analfabetismo` | I2 | Solo el jefe; la oficial mira a todas las personas de 15+ |
| `bajo_logro_educativo_jefe` | I1 | Solo el jefe y nivel < secundaria; la oficial es el promedio de años de las personas de 15+ < 9 |
| `inasistencia_escolar_menores` | I3 | **Igual a la oficial** |
| `sin_aseguramiento_salud` | I9 | Solo el jefe, y "no sabe" (9) cuenta como asegurado; la oficial mira a todos los de 6+ y "no sabe" priva |
| `sin_cotizacion_pension_jefe` | I8 | Solo el jefe, y priva a todo jefe no ocupado; la oficial es la regla de la "nueva PEA" del hogar |
| `hacinamiento` | I15 | > 3 en ambas zonas; la oficial es ≥ 3 en urbano |
| `sin_alcantarillado` | I12 | Regla urbana aplicada también a la zona rural |
| `sin_acueducto` | I11 | Regla urbana aplicada también a la zona rural |

Ninguna de las 8 está mal calculada respecto de su propia definición: la
diferencia es de definición, y así está documentado en
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`. Esto confirma que BASE
no debe llamarse "IPM" sin calificativo.

### 2.4 Disponibles, faltantes y pendientes de validación

| Estado | Privaciones |
|---|---|
| **Disponibles** (insumos completos en su población de referencia) | I1, I2, I3, I4, I7, I8, I9, I11, I12, I13, I14, I15 |
| **Faltantes** (sin preguntas en GEIH 2024) | I5 primera infancia (faltan cuidado y alimentación), I10 barreras de acceso a salud |
| **Parciales** | I6 trabajo infantil: GEIH solo cubre de 15 a 17 años; los de 12 a 14 son el 49,0 % de la población de referencia y no se observan |
| **Pendientes de validación** | Conversión de semestres a años en educación superior (I1, I4); códigos `P7250` 998/999 (I7); identificación de pensionados (I7, I8); "u otra fuente" en agua rural (I11); "cuarto" = cuarto para dormir (I15) |

Con insumos completos se quiere decir: 0 % de vacíos en la población de
referencia de cada privación. Los "no sabe" son a lo sumo 1,46 % (`P7250`)
y casi nulos en el resto (ver el diagnóstico de insumos).

## 3. Hallazgos de la auditoría

1. **`P6050` (parentesco) no coincide con el diccionario.** El diccionario
   documenta 9 categorías (a-i), pero los datos traen 13 códigos (1-13).
   Solo el código 1 (jefe) es seguro. Por eso **no** se excluye a
   empleados domésticos, pensionistas ni trabajadores del hogar (práctica
   habitual del DANE en pobreza monetaria): no se sabe con certeza qué
   código corresponde a cada uno. Todas las reglas de esta matriz usan a
   todos los miembros del hogar GEIH.
2. **Códigos no documentados:** `P7250` trae 998/999 (1,46 % de los
   desocupados) y `P1519` trae un valor 3 (2.546 casos en enero) aunque el
   diccionario solo lista 1/2. Se tratan como faltante o no se usan.
3. **`docs/insumos/DICCIONARIO_IPM_2025.md` tiene etiquetas desplazadas.**
   Por ejemplo, `P6920` aparece como "¿estaba disponible para trabajar?" y
   `P3336S1` como "¿cotiza a pensiones?". No sirve para mapear códigos;
   esta matriz usa el diccionario de GEIH y el documento metodológico.
4. **Documentación inconsistente sobre las privaciones faltantes.**
   `docs/resultados/README.md` dice que faltan "trabajo infantil, agua
   mejorada, excretas, combustible para cocinar, desempleo de larga
   duración". Agua y excretas sí están en BASE (en versión urbana), y el
   combustible para cocinar no es una privación del IPM. La lista correcta
   es la de `METODOLOGIA_INDICADOR_IPM_GEIH.md` §2 (rezago, primera
   infancia, trabajo infantil, desempleo de larga duración, barreras de
   salud). `docs/README.md` también describe esa metodología como "4
   privaciones, bloqueado", que ya no es cierto.
5. **`data/2_models/muestra_estimacion_2024.parquet` no está en Azure.**
   Las salidas de BASE no se pueden restaurar: hay que regenerarlas con
   `3_preprocesamiento.py`, que es determinístico.
6. **`poetry.lock` estaba desactualizado** frente a `pyproject.toml`
   (faltaba `openpyxl`). Se regeneró sin cambiar las demás versiones.
7. Menores: el docstring de `3_preprocesamiento.py` cita
   `Diccionario_variables_GEIH_2024.xlsx`, que no existe (el archivo es
   `DICCIONARIO_GEIH_2024.xlsx`); y BASE toma `P5010` = 98/99 (no sabe)
   como número de cuartos (4 hogares de 290.968, sin efecto práctico).

Los hallazgos 4 y 7 no se corrigieron en esta rama, para no tocar
documentos de resultados sin revisión. Se pueden corregir aparte.

## 4. Resultado de la homologación (Fase 2)

De las 15 privaciones oficiales: **12 homologables, 1 parcial (I6) y 2 no
disponibles (I5, I10)**. El detalle de cada una (variable GEIH, variable
armonizada, código Sisbén, regla oficial, regla reproducible, diferencias,
población de referencia, disponibilidad, supuestos) está en
[`01_matriz_homologacion.md`](01_matriz_homologacion.md).

Las 4 privaciones nuevas que la matriz permite construir y que BASE no
tiene son **rezago escolar (I4), desempleo de larga duración (I7),
material de pisos (I13) y material de paredes (I14)**, más la versión
parcial de trabajo infantil (I6). Las 8 de BASE pueden reconstruirse con
la regla oficial (hogar completo y reglas por zona).

## 5. Propuesta para la Fase 3 (no ejecutada)

| Indicador | Contenido propuesto | Nombre |
|---|---|---|
| `IPM_GEIH_BASE` | El actual, sin cambios (8 privaciones, conteo, K = 3) | Proxy reducido, no IPM |
| `IPM_GEIH_15` | Las 12 homologables con la regla oficial, pesos oficiales reponderados dentro de cada dimensión, corte 5/15 | "Proxy GEIH del IPM (12 de 15 privaciones)", nunca "IPM oficial" |
| `IPM_GEIH_ALT` | Variantes para sensibilidad: con I6 parcial, sin I13/I14, conteo sin ponderar, cortes alternativos | Una columna por variante, documentada |

## 6. Decisiones que requieren revisión metodológica

1. **Reponderación por faltantes.** Sin I5 e I10 las dimensiones Niñez y
   Salud quedan incompletas. Opciones: (a) repartir el peso de la
   dimensión entre las privaciones disponibles (Salud quedaría solo con
   I9 = 0,20); (b) conservar los pesos oficiales y dejar el índice con
   máximo 0,85, ajustando el corte. Recomendación: (a) para
   `IPM_GEIH_15` y (b) como variante de `IPM_GEIH_ALT`.
2. **I6 trabajo infantil (15-17).** ¿Entra en `IPM_GEIH_15` con cobertura
   parcial, o solo en ALT? Recomendación: solo en ALT, porque omite la
   mitad de su población de referencia.
3. **I13/I14 y la tautología con X.** `viv_pisos`/`viv_paredes` son
   covariables de heterogeneidad en `5_estimacion.py`; incluirlas en el
   outcome repite el problema que llevó a retirarlas el 2026-10-28. O se
   construye `IPM_GEIH_15` con ellas y los modelos que lo usen las sacan de
   `X`, o se excluyen del índice principal y van solo en ALT.
4. **Conversión de educación superior** (semestres a años) en I1/I4.
5. **Identificación de pensionados** (`P6920` = 3 o `P7500S2` = 1) para
   las reglas especiales de I7 e I8.
6. **Miembros del hogar:** usar a todas las personas del hogar GEIH
   (decisión actual, por el hallazgo 1) o conseguir la tabla de códigos de
   `P6050` y excluir a empleados domésticos y pensionistas.
7. **Agua rural "u otra fuente"** (I11) y **"cuarto" = cuarto para
   dormir** (I15).
8. **Regla Sisbén de `I1`-`I15`:** conseguir el documento metodológico del
   DNP para completar la columna de comparación con el Sisbén.

## 7. Reproducir

```bash
poetry run python -m src.indicadores.inventario_variables_geih
poetry run python -m src.indicadores.homologacion_ipm
poetry run pytest tests/
```

Requiere `data/1_processed/geih/2024/` (restaurar desde Azure). Las pruebas
de la matriz (`tests/test_homologacion_ipm.py`) no necesitan los datos:
verifican que todo código GEIH y Sisbén citado exista en su diccionario
oficial, que los pesos sumen 1 y que cada regla cite su página del
documento del DANE.
