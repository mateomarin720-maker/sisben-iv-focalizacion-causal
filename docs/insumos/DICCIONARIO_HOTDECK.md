# Diccionario consolidado — Variables para Hot-Deck (GEIH ↔ Sisbén IV)

*(Actualizado 2026-10-09. Toda variable codificada queda con su nombre y
significado aquí, no solo en comentarios de código — observación del tutor.)*

## 1. Variable de tratamiento

| Variable Sisbén | Etiqueta |
|---|---|
| `Grupo` | Grupo (A/B/C/D) |
| `Nivel` | Nivel dentro del grupo |
| `Clasificacion` | Grupo + Nivel concatenado (ej. "B3") |

## 2. Filtro de jefe de hogar

| Fuente | Variable | Valor filtro | Verificado |
|---|---|---|---|
| GEIH (`caracteristicas_generales`) | `P6050` | `"1"` = jefe de hogar | ✅ 24.402 jefes en agosto = 24.402 hogares (100 %) |
| Sisbén nacional (`personas`) | `PER003` | `"1"` = jefe de hogar | ✅ 1.820.083 de 1.833.166 hogares (99,3 %); 65 con doble jefe (se conserva el primero); 13.083 hogares sin jefe |
| Sisbén Bogotá (SDP) | `tip_parentesco` | `1` = jefe del hogar | ✅ 1.458.474 jefes; 6 hogares con doble jefe |

## 3. Llave de hogar en cada fuente

| Fuente | Llave | Nota |
|---|---|---|
| Sisbén IV nacional | `cod_mpio + ZONA + llave + CORTE + HOGAR` | `llave` es un consecutivo local, **no** identifica al hogar por sí sola. El parquet armonizado crea `llave_hogar_sisben` (única, verificada). Personas trae varias filas por hogar (los miembros); el armonizador conserva solo al jefe. |
| Sisbén Bogotá (SDP) | `ide_ficha_origen + ide_hogar` | `ide_ficha_origen` es la **vivienda**; hay 59.352 viviendas con más de un hogar. Una fila por persona (`ide_persona`). |
| GEIH | `DIRECTORIO + SECUENCIA_P + HOGAR` | Se normalizan a texto de entero antes de cruzar módulos (agosto traía otro formato). |
| IPM | `DIRECTORIO + SECUENCIA_ENCUESTA + SECUENCIA_P` | |

## 4. Esquema canónico (usado en el Hot-Deck)

**Actualizado 2026-10-28** con el diccionario oficial de GEIH
(`docs/insumos/DICCIONARIO_GEIH_2024.xlsx`) y el de Sisbén
(`docs/insumos/DICCIONARIO_SISBEN_2024.xlsx`). Antes de esta fecha,
`viv_paredes`/`viv_pisos`/`viv_cuartos` del lado GEIH usaban códigos
equivocados (ver `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` para el
detalle del error y su efecto en el Hot-Deck).

| Nombre canónico | GEIH | Sisbén nacional | Sisbén Bogotá (SDP) | Estado |
|---|---|---|---|---|
| `geo_depto` | `DPTO` | `cod_mpio[:2]` | `"11"` | ✅ 33 códigos DIVIPOLA idénticos |
| `geo_localidad` | — | — | `Cod_comuna` (localidad, 20 códigos) | Solo descriptiva; GEIH no la desagrega |
| `geo_zona` | `CLASE` — **1=Urbano, 2=Rural** (confirmado) | `ZONA` (1/2) | `Cod_clase` (1 cabecera, 2 centro poblado, 3 rural disperso) | ✅ Lado GEIH confirmado; Sisbén sin confirmar si 1 es el mismo sentido |
| `jefe_edad` | `P6040` (**años**, confirmado: "¿cuántos años cumplidos tiene?") | `PER002` (**código de ciclo de vida**) | `fec_nacimiento` → ciclo | ⚠️ Ver sección 5 |
| `jefe_sexo` | `P3271` — confirmada la pregunta ("¿cuál fue su sexo al nacer?"), el diccionario no trae la tabla 1/2 explícita | `PER001` | `sexo_persona` (valor `4` inválido → nulo) | ⚠️ Pregunta confirmada, dirección del código 1/2 sigue sin confirmar |
| `viv_paredes` | **`P4010`** (corregido, antes `P4020`) | `VIV002` | `tip_mat_paredes` | ✅ Lado GEIH confirmado y con categorías completas (ver METODOLOGIA_INDICADOR_IPM_GEIH.md); Sisbén sin la tabla de categorías explícita todavía |
| `viv_pisos` | **`P4020`** (corregido, antes `P4030S1`) | `VIV003` | `tip_mat_pisos` | ✅ Lado GEIH confirmado y con categorías completas; Sisbén igual que arriba |
| `viv_cuartos` | **`P5000`** (corregido, antes `P5010`) — "cuartos en total, incl. sala-comedor" | `VIV009` — "número de cuartos, incl. sala-comedor" | `num_cuartos_vivienda` | ✅ Mismo concepto confirmado en las dos fuentes (antes GEIH medía sin saberlo "cuartos para dormir", un concepto distinto) |
| `viv_cuartos_dormir` | `P5010` (nuevo, separado de `viv_cuartos`) | — | — | Insumo de `hacinamiento` en `3_preprocesamiento.py`, no entra a la celda del Hot-Deck |
| `viv_alcantarillado` | `P4030S3` (nuevo, ya ubicado) | `VIV005` | `ind_tiene_alcantarillado` | ✅ Homologado en GEIH desde 2026-10-28 |
| `viv_acueducto` | `P4030S5` (nuevo, ya ubicado) | `VIV008` | `ind_tiene_acueducto` | ✅ Homologado en GEIH desde 2026-10-28 |
| `hog_num_personas` | `P6008` (nuevo, ya ubicado — "total de personas en el hogar") | `HOG027` | conteo de personas por hogar | ✅ Homologado en GEIH desde 2026-10-28 |
| `fex` | `FEX_C18` | `FEX` | — (fijo en 1: no hay factor de expansión) | Ponderación, no entra a la celda |

Las categorías de `viv_paredes`/`viv_pisos` SÍ están confirmadas del lado
GEIH, pero **las categorías del lado Sisbén (`VIV002`/`VIV003`) todavía no
tienen el desglose completo en el diccionario disponible** — por eso
siguen sin sumarse a la celda del Hot-Deck ni usarse como privación
directamente comparable entre fuentes. `viv_cuartos` (conteo cardinal) sí
se usa en la celda porque no necesita homologar categorías.

## 5. Edad del jefe: ciclo de vida (✅ hipótesis corroborada indirectamente, 2026-10-10)

El extracto del Sisbén **no trae la edad en años**. Entre jefes de hogar (`PER003=="1"`, archivo completo de Personas, 1.820.148 jefes) `PER002` toma **solo** los valores 3, 4, 5 y 6 — 0 jefes con los códigos 1 o 2 (ver abajo). Para comparar con GEIH se usa el mismo ciclo en ambas fuentes:

| Código `PER002` | Ciclo (hipótesis) | Jefes de hogar Sisbén nacional |
|---|---|---|
| 3 | 12–17 años | 4.105 (0,2 %) |
| 4 | 18–28 años | 323.701 (17,8 %) |
| 5 | 29–59 años | 1.077.158 (59,2 %) |
| 6 | 60 años o más | 415.184 (22,8 %) |

**Estado: corroborado indirectamente, no con la ficha oficial.** Sigue sin confirmarse en la ficha ANDA (variable `PER002`, V926), pero se cruzó `PER002` contra variables de comportamiento conocidas en la base completa de Personas (4.715.226 filas, todas las edades, no solo jefes) y las proporciones son consistentes con la hipótesis del ciclo de vida:

| `PER002` | % estudia (`PER016`) | % soltero (`PER004`) | % cotiza pensión (`PER018`) | Lectura |
|---|---|---|---|---|
| 1 | — (86 % N/A) | 100 % | — (100 % N/A) | Primera infancia (no responde estas preguntas) |
| 2 | 95,8 % | 100 % | — (100 % N/A) | Niñez — casi todos estudian, nadie casado |
| **3** | 86,6 % | 98,9 % | 25,5 % N/A / 74,1 % no cotiza | Coherente con 12–17: aún estudia, soltero |
| **4** | 22,4 % | 74,7 % | 89,9 % no cotiza | Coherente con 18–28: deja de estudiar, mayoría soltero |
| **5** | 2,5 % | 42,7 % casado | 85,0 % no cotiza | Coherente con 29–59: estado civil mixto, edad laboral |
| **6** | 0,8 % | 49,7 % casado | 90,4 % no cotiza | Coherente con 60+: casi nadie estudia |

Los códigos 1 y 2 (infancia/niñez, nunca jefes de hogar) confirman además que el ciclo de vida completo tiene 6 categorías, no 4 — el hot-deck solo necesita 3–6 porque un jefe de hogar nunca cae en 1/2. Detalle de la verificación: `src/validacion/verificar_codigos_edad_sisben.py`. En Bogotá y en GEIH la edad se convierte con los cortes 17/28/59.

## 6. Celda de matching actual

`geo_depto` + ciclo de vida del jefe (≈130 celdas). Degradación jerárquica: `celda_exacta` → `solo_depto` → `pool_nacional`. Solo son donantes los hogares con `Clasificacion` observada. Resultado actual: 100 % celda exacta.

## 7. ⚠️ Circularidad confirmada — nunca usar como Outcome

| Variable Sisbén | Motivo |
|---|---|
| `I1`–`I15` (Personas) | Privaciones Alkire-Foster proxy calculadas por el propio Sisbén |
| `H_5` (Personas) | Proxy interno del IPM calculado por Sisbén |
| `aseguramiento_salud` | Excluida por el mismo motivo |

## 8. Limitaciones registradas
- **Corte distinto (corregido 2026-10-10, dos iteraciones):** el archivo del SDP no es un corte único — es un registro administrativo continuo con `fec_fin_encuesta` entre 2019-03-22 y 2026-07-29 (verificado: cada hogar aparece una sola vez en el archivo, con la fecha de su único registro — no hay copias duplicadas repitiendo el mismo valor año a año). Antes del 2026-10-10 se usaban los 1.458.474 jefes completos bajo la etiqueta fija `"bogota_sdp_2026-08"`, sin filtrar por fecha.
  - **Primer intento (año exacto 2024):** descartado. Solo 75.488 de 1.458.474 jefes (5,2 %) tienen `fec_fin_encuesta` en el año 2024 exacto. Ese filtro confunde "estar registrado en 2024" con "haber sido re-encuestado en 2024" — el Sisbén no re-visita a todos los hogares cada año, así que subestima brutalmente el universo vigente y sesga la muestra hacia hogares con actualización reciente (que no son representativos del resto).
  - **Filtro adoptado (vigencia hasta corte, `fec_fin_encuesta <= 2024-12-31`):** 1.274.578 de 1.458.468 hogares (87,4 %) quedan vigentes; se descartan 183.890 por ser posteriores (registrados/actualizados en 2025-2026, fuera del alcance de "población 2024"). Es consistente con el nacional, cuyo `CORTE` tampoco trae fecha real por hogar (literal fijo `"SIV_2024"` para los 1.833.166 hogares) — ambas fuentes se tratan como "stock vigente a una fecha", no "encuestados ese año exacto".
  - Efecto en el Hot-Deck con el filtro adoptado: donante total 3.106.489 hogares (vs. 3.290.379 sin filtrar y 1.907.399 con año exacto). Celda exacta: 100 % (también dentro de Bogotá). Números de Grupo nacional actualizados el 2026-10-28 tras corregir `viv_cuartos` (ver más abajo) — ver `docs/resultados/RESULTADOS_HOTDECK.md` para la cifra vigente.
  - **Dentro de Bogotá el filtro de fecha sigue importando** (ver `docs/resultados/COMPARACION_FILTROS_SDP.md` para los números vigentes tras la corrección de vivienda) — la muestra de "solo recién actualizados" sigue sin ser representativa del Sisbén vigente de Bogotá.
  - Limitación que persiste: no se puede verificar si el nacional (`CORTE="SIV_2024"` fijo) tiene la misma mezcla de antigüedad por hogar que Bogotá — el extracto no expone una fecha real por hogar como sí lo hace el SDP.
- **Selección:** el Sisbén solo incluye hogares encuestados; asignar su distribución a todo el GEIH sobrerrepresenta A y B.
- **Edad por ciclo de vida**, no en años exactos.
- **Hogares sin jefe:** 13.083 en Sisbén nacional (0,7 %) y 227 en Bogotá con clasificación distinta entre miembros.

## 9. Pendientes de este diccionario
- [x] Confirmar los códigos de `PER002` — corroborado indirectamente (sección 5, 2026-10-10); sigue faltando la ficha ANDA oficial para confirmación 100 %.
- [x] Ubicar en GEIH las columnas equivalentes a `HOG027`, `VIV005`, `VIV008` — hecho 2026-10-28 (`P6008`, `P4030S3`, `P4030S5`), ver sección 4.
- [x] Verificar `geo_zona`, `viv_paredes`, `viv_pisos` contra el diccionario oficial de GEIH — hecho 2026-10-28 (sección 4). Pendiente aún del lado Sisbén (categorías de `VIV002`/`VIV003` sin desglose completo) y `jefe_sexo` (pregunta confirmada, dirección del código 1/2 no).
- [ ] Sumar `viv_paredes`/`viv_pisos` a la celda del Hot-Deck una vez se homologuen las categorías también del lado Sisbén.
