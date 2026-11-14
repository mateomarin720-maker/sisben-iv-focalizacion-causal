# Contrato canónico de datos

Qué columnas con nombre fijo comparten las fuentes del proyecto, qué
significa cada una en la GEIH, el Sisbén IV y el IPM, de qué tipo es y qué
valores admite. Reúne en un solo lugar lo que está repartido en el código
(`src/utils/variables_canonicas.py`, `src/simulacion/contrato.py`,
`src/armonizacion/`) y en los diccionarios de `docs/insumos/`.

## 1. Reglas del contrato

- **Los nombres canónicos no se cambian ni se hacen configurables**
  (regla del tutor, 2026-11-03). Quien tenga otros nombres los convierte en
  su propia armonización; el módulo de simulación exige los nombres y valida
  que estén, sin renombrar, completar ni adivinar (`contrato.validar`).
- **Los códigos viajan como texto.** `"1"` es un código válido y `"1.0"` no:
  ese formato dañó agosto de 2024 de la GEIH sin dar error (CLAUDE.md). Los
  conteos y las edades se guardan como enteros escritos en texto y se validan
  con una expresión regular (`\d+`).
- **Una fila por hogar.** El jefe de hogar es la unidad de referencia: sus
  características (`jefe_sexo`, `jefe_edad`) describen al hogar.
- **Las reglas compartidas entre fuentes viven en un solo módulo,**
  `src/utils/variables_canonicas.py`; no se copian en otros (tabla 1).
- **Los dominios salen de los diccionarios oficiales** (GEIH 2024, ficha del
  Sisbén IV) y de las homologaciones verificadas; donde no hay verificación
  oficial, la tabla 5 lo dice.

### Tabla 1. Reglas compartidas (`variables_canonicas.py`)

| Regla | Qué hace | Detalle |
|---|---|---|
| `normalizar_llave` | Lleva identificadores de hogar a texto de entero | `"7893865.0"`, `" 01 "`, `1` pasan a `"7893865"`, `"1"`, `"1"`; lo no numérico queda faltante. Se usa antes de cualquier cruce entre tablas |
| `JEFE` / `es_jefe` | Marca al jefe de hogar según la fuente | GEIH `P6050 == "1"`; Sisbén nacional `PER003 == "1"`; Sisbén Bogotá (SDP) `tip_parentesco == "1"` |
| `CORTES_CICLO`, `CODIGOS_CICLO`, `edad_a_ciclo` | Lleva la edad en años al código de ciclo de vida de `PER002` | Intervalos cerrados a la derecha: hasta 17 años → `"3"`; 18 a 28 → `"4"`; 29 a 59 → `"5"`; 60 o más → `"6"`. Fuera de rango o no numérica → faltante |

## 2. Variables canónicas por fuente

Una fila por variable del esquema armonizado
(`geih_estandarizado_2024.parquet`, `sisben_estandarizado_2024.parquet`).
Un guion (—) indica que la fuente no tiene la variable o que no se cruza.

### Tabla 2. Qué representa cada variable en cada fuente

| Variable canónica | Qué representa | GEIH 2024 | Sisbén IV nacional | Sisbén Bogotá (SDP) | IPM 2024 |
|---|---|---|---|---|---|
| `llave_directorio`, `llave_secuencia_p`, `llave_hogar` | Identificador del hogar | `DIRECTORIO`, `SECUENCIA_P`, `HOGAR` | — (`llave_hogar_sisben` = `cod_mpio｜ZONA｜llave｜CORTE｜HOGAR`) | `ide_ficha_origen`, `ide_hogar` | — (`DIRECTORIO`, `SECUENCIA_ENCUESTA`, `SECUENCIA_P`; no se cruza) |
| `mes` | Mes de la encuesta | mes del archivo (`"01"` a `"12"`) | — | — | — |
| `fuente` | Origen de la fila | `"geih"` | `"sisben_iv"` en el armonizado nacional; `"dnp_nacional_2024-05"` en la base unida con Bogotá | etiqueta del corte (`fuente_tag`) | — |
| `geo_depto` | Departamento (DIVIPOLA, 2 dígitos) | `DPTO` | primeros 2 dígitos de `cod_mpio` | `"11"` fijo | `DEPARTAMENTO` |
| `geo_localidad` | Localidad de Bogotá | — | — | `Cod_comuna` (20 códigos); solo descriptiva | — |
| `geo_zona` | Zona del hogar | `CLASE` (1 urbano, 2 rural) | `ZONA` (1 urbano, 2 rural; inferido de `I14`) | `Cod_clase` (1 cabecera, 2 centro poblado, 3 rural disperso) | `P3` (Clase) |
| `jefe_sexo` | Sexo del jefe | `P3271` (sexo al nacer) | `PER001` | `sexo_persona` (el código `4` es inválido y pasa a faltante) | — |
| `jefe_edad` | Edad del jefe | `P6040`, años cumplidos | `PER002`, **código de ciclo de vida** (no años) | `fec_nacimiento` convertida a ciclo con `edad_a_ciclo` | — |
| `viv_paredes` | Material predominante de las paredes exteriores | `P4010` | `VIV002` | `tip_mat_paredes` | `P4005` |
| `viv_pisos` | Material predominante de los pisos | `P4020` | `VIV003` | `tip_mat_pisos` | `P4015` |
| `viv_cuartos` | Cuartos en total, incluida la sala-comedor | `P5000` | `VIV009` | `num_cuartos_vivienda` | — |
| `viv_cuartos_dormir` | Cuartos usados para dormir (insumo de hacinamiento; no entra a la celda) | `P5010` | — | — | `P5010` |
| `viv_alcantarillado` | ¿Tiene alcantarillado? | `P4030S3` | `VIV005` | `ind_tiene_alcantarillado` | `P8520S3` |
| `viv_acueducto` | ¿Tiene acueducto? | `P4030S5` | `VIV008` | `ind_tiene_acueducto` | `P8520S5` |
| `hog_num_personas` | Personas del hogar | `P6008` | `HOG027` | conteo de personas por hogar | `PERSONAS` |
| `hog_num_menores` | Personas del hogar menores de 18 años (desde el 2026-11-14) | conteo de personas con `P6040` < 18 | conteo de personas con `PER002` en 1, 2 o 3 | conteo por `fec_nacimiento` (< 18 al 31-12-2024) | — |
| `fex` | Factor de expansión del hogar | `FEX_C18` | `FEX` | — (no hay factor; fijo en 1) | `FEX_C` |
| `Grupo` | Grupo del Sisbén IV (tratamiento) | — (se imputa con el Hot-Deck) | `Grupo` | `Grupo` | — |
| `Nivel` | Nivel dentro del grupo | — | `Nivel` | número extraído de `Clasificacion` | — |
| `Clasificacion` | Grupo y nivel juntos (por ejemplo `B3`) | — (se imputa) | `Clasificacion` | `Clasificacion` | — |
| `CORTE` | Corte del registro | — | literal `"SIV_2024"` | `fec_fin_encuesta` (aaaa-mm-dd) | — |

Dos notas sobre la tabla:

- Los códigos de `viv_paredes` y `viv_pisos` **no son comparables entre
  fuentes** sin la escala común de la sección 3.
- Las variables del IPM de esta tabla son solo la correspondencia de nombres.
  El IPM oficial usa la ECV, no comparte llave de hogar con la GEIH ni con el
  Sisbén, y nunca se cruza a nivel hogar.

## 3. Dominios y categorías válidas

### Tabla 3. Variables codificadas

| Variable | Código | Categoría |
|---|---|---|
| `geo_zona` | `1` | Urbano (cabecera, en GEIH y Sisbén nacional) |
| | `2` | Rural |
| `jefe_sexo` | `1`, `2` | Hombre, mujer (ver tabla 5: dirección pendiente de confirmar) |
| `jefe_edad` (Sisbén, `PER002`) | `3` | 12 a 17 años |
| | `4` | 18 a 28 años |
| | `5` | 29 a 59 años |
| | `6` | 60 años o más |
| `Grupo` | `A`, `B`, `C`, `D` | A pobreza extrema, B pobreza moderada, C vulnerabilidad, D ni pobre ni vulnerable |
| `viv_alcantarillado`, `viv_acueducto` | GEIH: `1` / `2` | Sí tiene / no tiene |
| `vinculo` (columna opcional del módulo de simulación) | `llave`, `hotdeck` | Cómo se obtuvo `Grupo`: por llave o por Hot-Deck |
| `dominio_pm` | `13_ciudades`, `otras_cabeceras`, `rural` | Dominio de la línea de pobreza (DANE 2024: 566.228, 434.323 y 291.998 pesos) |

### Tabla 4. Paredes exteriores: códigos por fuente y escala común

| Escala común | GEIH `P4010` | Sisbén `VIV002` |
|---|---|---|
| H1 Ladrillo, bloque, piedra, prefabricado, madera pulida | `1` (ladrillo, bloque, prefabricado, piedra); `2` (madera pulida) | `1` (bloque, ladrillo, piedra, madera pulida); `4` (prefabricado) |
| H2 Tapia pisada, adobe | `3` | `2` |
| H3 Bahareque | `4` | `3` |
| H4 Madera burda, tabla, tablón | `5` | `5` |
| H5 Guadua, caña, esterilla, otro vegetal | `6` (guadua); `7` (caña, esterilla, vegetal) | `6` |
| H6 Zinc, tela, cartón, latas, desechos, plástico | `8` | `7` |
| H7 Sin paredes | `9` | `0` (no aparece en los datos 2024) |

Dominio en el contrato del módulo de simulación: GEIH `1` a `9`.

### Tabla 4b. Pisos: códigos por fuente y escala común (las escalas van en sentido contrario)

| Escala común | GEIH `P4020` | Sisbén `VIV003` |
|---|---|---|
| P1 Alfombra, mármol, parqué, madera pulida | `5` (mármol); `6` (madera pulida); `7` (alfombra) | `1` |
| P2 Baldosa, vinilo, tableta, ladrillo | `4` | `2` |
| P3 Cemento, gravilla | `2` | `3` |
| P4 Madera burda, tabla, tablón | `3` (incluye otro vegetal) | `4` (incluye madera en mal estado) |
| P5 Tierra, arena | **`1`** | **`5`** |
| Otro | — | `6` (0,14 % de los hogares; faltante en la escala común) |

Dominio en el contrato: GEIH `1` a `7`; Sisbén `1` a `6`. Comparar o usar como
número ordinal los códigos crudos entre fuentes da resultados invertidos.

## 4. Tipo de dato y dominio de cada variable

Es la lectura de `src/simulacion/contrato.py` (tablas `hogares` y
`registro`) más las columnas armonizadas que el contrato no valida. "Código
(texto)" significa texto comparado con la lista de códigos válidos.

### Tabla 5. Tipo, dominio y obligatoriedad

| Variable | Tipo | Dominio válido | Tabla del contrato (obligatoria / opcional) |
|---|---|---|---|
| `geo_depto` | código (texto) | 2 dígitos, DIVIPOLA (33 códigos) | hogares y registro (obligatoria) |
| `geo_zona` | código (texto) | `"1"`, `"2"` | hogares (obligatoria) |
| `jefe_sexo` | código (texto) | `"1"`, `"2"` (dirección sin confirmar, ver sección 5) | hogares (obligatoria) |
| `jefe_edad` en `hogares` | entero (texto) | edad en años, 0 a 120 | hogares (obligatoria) |
| `jefe_edad` en `registro` | código (texto) | `"3"`, `"4"`, `"5"`, `"6"` (ciclo de vida de `PER002`) | registro (obligatoria) |
| `viv_cuartos` | entero (texto) | 1 o más | hogares y registro (obligatoria) |
| `viv_pisos` en `hogares` | código (texto) | `"1"` a `"7"` (GEIH) | hogares (obligatoria) |
| `viv_pisos` en `registro` | código (texto) | `"1"` a `"6"` (Sisbén) | registro (obligatoria) |
| `viv_paredes` | código (texto) | `"1"` a `"9"` (GEIH) | hogares (obligatoria) |
| `ingreso_percapita` | real | 0 o más, pesos; ingreso per cápita de la unidad de gasto, reconstruido con la metodología del DANE | hogares (obligatoria) |
| `dominio_pm` | código (texto) | `13_ciudades`, `otras_cabeceras`, `rural` | hogares (obligatoria) |
| `fex` | real | mayor que 0 | hogares (opcional) |
| `Grupo` | código (texto) | `"A"` a `"D"` | hogares (opcional); registro (obligatoria) |
| `vinculo` | código (texto) | `"llave"`, `"hotdeck"` | hogares (opcional) |
| `Clasificacion` | texto | grupo más nivel; **nula** en hogares sin clasificar, que no se validan ni entran a P(T ∣ celda) | registro (obligatoria) |
| `viv_alcantarillado`, `viv_acueducto` | código (texto) | GEIH `"1"`, `"2"`; Sisbén sin tabla de códigos en el repositorio | no validadas por el contrato |
| `hog_num_personas` | entero (texto) | 1 o más | hogares y registro (obligatoria) |
| `hog_num_menores` | entero (texto) | 0 o más | hogares y registro (obligatoria) |

Variables derivadas que el módulo calcula y **no se aceptan como entrada**
(CLAUDE.md): la celda del Hot-Deck (departamento, ciclo de vida del jefe,
`viv_cuartos`, `viv_pisos`, `hog_num_personas` y `hog_num_menores` en
tramos), zona urbana, jefe mujer y P(T ∣ celda).

Variables de resultado de la tabla de estimación
(`muestra_estimacion_monetaria_2024.parquet`):

| Variable | Tipo | Dominio |
|---|---|---|
| `POBRE_MONETARIO`, `POBRE_EXTREMO_MONETARIO` | entero con faltantes (`Int8`) | `0`, `1`; reconstruidos sobre la GEIH |
| `POBRE_MONETARIO_OFICIAL`, `POBRE_EXTREMO_OFICIAL` | entero con faltantes (`Int8`) | `0`, `1`; vacíos en los 9 departamentos que la base oficial no trae (81, 85, 86, 88, 91, 94, 95, 97, 99) |
| `brecha_pobreza_monetaria`, `brecha_pobreza_extrema` | real | brecha de pobreza del hogar |
| `personas_ug` | entero | personas de la unidad de gasto |

## 5. Lo que el contrato todavía no resuelve

Son los puntos donde el repositorio no tiene verificación oficial; no se
completan por suposición.

1. **`jefe_sexo`:** el diccionario de la GEIH confirma la pregunta (`P3271`,
   sexo al nacer) pero no trae la tabla de códigos. El contrato asume `1`
   hombre y `2` mujer; la dirección está sin confirmar.
2. **`PER002`:** los rangos del ciclo de vida están corroborados con cruces
   (estudio, estado civil, pensión), no con la ficha oficial de ANDA.
3. **`VIV005`, `VIV008`, `ind_tiene_*`:** sin tabla de códigos en el
   repositorio; la homologación con la GEIH `1`/`2` no está verificada.
4. **`geo_zona` en Bogotá:** `Cod_clase` tiene tres códigos y el contrato de
   `hogares` solo admite `"1"` y `"2"`; no afecta hoy porque esa validación
   corre sobre tablas del lado GEIH.
5. **`viv_pisos` y `jefe_edad` cambian de dominio entre las tablas
   `hogares` y `registro`** (códigos GEIH frente a Sisbén; años frente a
   ciclo de vida). El módulo lo exige así a propósito; el error típico es
   pasar una tabla con los códigos de la otra.
6. **Documentación que se solapa:** `docs/insumos/DICCIONARIO_HOTDECK.md`
   describe en su sección 6 la celda vigente (departamento, ciclo de
   vida, cuartos, pisos, personas y menores desde el 2026-11-14); las
   secciones anteriores cuentan cómo se llegó a ella.
   `docs/anexos_tesis/CONTRATO_DATOS.md` es la tabla del contrato de
   simulación generada del código; este documento la amplía con las otras
   fuentes y no la reemplaza.

## 6. Fuentes de este documento

`src/utils/variables_canonicas.py`, `src/simulacion/contrato.py`,
`src/armonizacion/armonizar_geih_hogar_2024.py`,
`src/armonizacion/armonizar_sisben_hogar_2024.py`,
`src/armonizacion/armonizar_sisben_bogota_sdp.py`,
`src/3b_preprocesamiento_monetario.py`,
`docs/insumos/DICCIONARIO_HOTDECK.md`,
`docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`,
`docs/insumos/DICCIONARIO_IPM_2025.md`.
