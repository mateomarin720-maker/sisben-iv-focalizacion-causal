# Descripción de las tablas del pipeline

Las tablas de `data/2_models/` son las que consume el emparejamiento y, más adelante, la estimación. No se versionan en GitHub: viven en Azure Blob Storage y se restauran con `src/utils/restaurar_banco_datos_azure.py`.

Conteos de filas: última ejecución registrada en [`RESUMEN_AVANCES.md`](../seguimiento/RESUMEN_AVANCES.md). Columnas: tomadas del código de los scripts que generan cada tabla.

## Resumen

| Tabla | Una fila es | Filas | Llave | Script que la genera |
|---|---|---|---|---|
| `geih_estandarizado_2024.parquet` | un hogar GEIH (con los datos de su jefe), por mes | 290.968 | `llave_directorio` + `llave_secuencia_p` + `llave_hogar` + `mes` | `src/armonizacion/armonizar_geih_hogar_2024.py` |
| `sisben_estandarizado_2024.parquet` | un hogar del Sisbén IV nacional (con los datos de su jefe) | 1.833.166 | `llave_hogar_sisben` | `src/armonizacion/armonizar_sisben_hogar_2024.py` |
| `sisben_bogota_estandarizado.parquet` | un hogar del Sisbén IV de Bogotá (SDP) | 1.458.468 | `llave_hogar_sisben` | `src/armonizacion/armonizar_sisben_bogota_sdp.py` |
| `sisben_estandarizado_2024_con_bogota.parquet` | un hogar del Sisbén: nacional con Bogotá (SDP) en lugar del municipio 11001 | 3.290.379 | `llave_hogar_sisben` | `src/armonizacion/armonizar_sisben_bogota_sdp.py` (fusión) |
| `geih_sisben_fusionado_2024.parquet` | un hogar GEIH con el grupo Sisbén asignado por Hot-Deck | 290.968 | igual que `geih_estandarizado_2024` | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py` |

Todas las tablas tienen una fila por **hogar**, no por persona: el Sisbén y el GEIH traen varias personas por hogar, y se conserva solo al jefe. Los miembros del mismo hogar no son hogares distintos.

## `geih_estandarizado_2024.parquet`

Se arma con los módulos `hogar_vivienda` y `caracteristicas_generales` de GEIH 2024 (12 meses apilados), filtrando al jefe de hogar (`P6050 = 1`).

| Columna | Origen en GEIH | Significado |
|---|---|---|
| `llave_directorio`, `llave_secuencia_p`, `llave_hogar` | `DIRECTORIO`, `SECUENCIA_P`, `HOGAR` | Identificadores normalizados a texto de entero |
| `geo_depto` | `DPTO` | Departamento (código DIVIPOLA de 2 dígitos) |
| `geo_zona` | `CLASE` | Zona (1 cabecera, 2 resto) |
| `viv_paredes` | `P4020` | Material de las paredes |
| `viv_pisos` | `P4030S1` | Material de los pisos |
| `viv_cuartos` | `P5010` | Número de cuartos |
| `fex` | `FEX_C18` | Factor de expansión |
| `jefe_sexo` | `P3271` | Sexo del jefe |
| `jefe_edad` | `P6040` | Edad del jefe, **en años** |
| `mes` | — | Mes de la encuesta (`01` a `12`) |
| `fuente` | — | Siempre `geih` |

## `sisben_estandarizado_2024.parquet`

Se arma con Hogares, Viviendas y Personas del Sisbén IV, filtrando al jefe (`PER003 = 1`). Corte: mayo de 2024.

| Columna | Origen en Sisbén | Significado |
|---|---|---|
| `cod_mpio` | `cod_mpio` | Municipio (código DIVIPOLA de 5 dígitos) |
| `geo_zona` | `ZONA` | Zona |
| `llave`, `CORTE`, `HOGAR` | `llave`, `CORTE`, `HOGAR` | Con `cod_mpio` y `geo_zona` forman la llave completa; `llave` es solo un consecutivo local |
| `llave_hogar_sisben` | construida | `cod_mpio|geo_zona|llave|CORTE|HOGAR`; única por hogar |
| `geo_depto` | `cod_mpio[:2]` | Departamento |
| `hog_num_personas` | `HOG027` | Número de personas del hogar |
| `viv_paredes`, `viv_pisos`, `viv_cuartos` | `VIV002`, `VIV003`, `VIV009` | Vivienda |
| `viv_alcantarillado`, `viv_acueducto` | `VIV005`, `VIV008` | Servicios de la vivienda |
| `jefe_sexo` | `PER001` | Sexo del jefe |
| `jefe_edad` | `PER002` | Edad del jefe **como código de grupo de edad (3 a 6), no en años** |
| `PER003` | `PER003` | Parentesco con el jefe (aquí siempre `1`) |
| `Grupo`, `Nivel`, `Clasificacion` | `Grupo`, `Nivel`, `Clasificacion` | **Tratamiento**: grupo A/B/C/D, nivel y su combinación (por ejemplo `B3`) |
| `fex` | `FEX` | Factor de expansión |
| `fuente` | — | `sisben_iv` |

Las privaciones `I1`–`I15` y `H_5` del Sisbén no se incluyen: las calcula el propio Sisbén y generarían circularidad.

## `sisben_bogota_estandarizado.parquet`

Se arma con la entrega de la Secretaría Distrital de Planeación (corte 3 de agosto de 2026), que trae una fila por persona. El jefe es `tip_parentesco = 1`; el hogar se identifica con `ide_ficha_origen` (vivienda) + `ide_hogar`.

Tiene las mismas columnas que la tabla nacional, con estas diferencias:

| Columna | Valor o cálculo |
|---|---|
| `cod_mpio`, `geo_depto` | `11001` y `11` |
| `geo_localidad` | Localidad (`Cod_comuna`); solo existe en Bogotá. Ver [`CODIGOS_LOCALIDAD_BOGOTA.md`](CODIGOS_LOCALIDAD_BOGOTA.md) |
| `geo_zona` | `Cod_clase` (1 cabecera, 2 centro poblado, 3 rural disperso) |
| `jefe_edad` | Se calcula desde `fec_nacimiento` (referencia 31/12/2024) y se pasa a los mismos códigos 3 a 6 |
| `jefe_sexo` | El valor `4` es inválido y queda nulo |
| `fex` | Fijo en `1.0`: la entrega no trae factor de expansión |
| `CORTE`, `fuente` | `bogota_sdp_2026-08` y `sdp_bogota_2026-08` |

## `sisben_estandarizado_2024_con_bogota.parquet`

Es la tabla nacional sin el municipio 11001 más la tabla de Bogotá. La columna `fuente` distingue el origen (`dnp_nacional_2024-05` o `sdp_bogota_2026-08`). Es la tabla que usa el Hot-Deck como donante. Las columnas de texto mezclado se convierten a `string` para poder escribir el Parquet.

## `geih_sisben_fusionado_2024.parquet`

Es `geih_estandarizado_2024` más lo que agrega el Hot-Deck:

| Columna | Significado |
|---|---|
| `Grupo_hotdeck`, `Nivel_hotdeck`, `Clasificacion_hotdeck` | Tratamiento copiado del hogar donante |
| `_hotdeck_nivel` | Con qué nivel se encontró donante: `celda_exacta`, `solo_depto` o `pool_nacional` |
| `_hotdeck_celda` | Celda del hogar receptor (departamento y ciclo de vida del jefe) |

Esta tabla **no identifica al mismo hogar** en las dos fuentes: el emparejamiento solo es válido a nivel poblacional. Ver [`DICCIONARIO_HOTDECK.md`](DICCIONARIO_HOTDECK.md).
