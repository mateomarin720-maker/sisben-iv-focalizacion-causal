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

| Nombre canónico | GEIH | Sisbén nacional | Sisbén Bogotá (SDP) | Estado |
|---|---|---|---|---|
| `geo_depto` | `DPTO` | `cod_mpio[:2]` | `"11"` | ✅ 33 códigos DIVIPOLA idénticos |
| `geo_localidad` | — | — | `Cod_comuna` (localidad, 20 códigos) | Solo descriptiva; GEIH no la desagrega |
| `geo_zona` | `CLASE` (1 cabecera, 2 resto) | `ZONA` (1/2) | `Cod_clase` (1 cabecera, 2 centro poblado, 3 rural disperso) | ⚠️ No verificada; excluida de la celda |
| `jefe_edad` | `P6040` (**años**) | `PER002` (**código de ciclo de vida**) | `fec_nacimiento` → ciclo | ⚠️ Ver sección 5 |
| `jefe_sexo` | `P3271` | `PER001` | `sexo_persona` (valor `4` inválido → nulo) | ⚠️ Dirección de código no verificada oficialmente |
| `viv_paredes` | `P4020` | `VIV002` | `tip_mat_paredes` | ⚠️ Categorías sin verificar |
| `viv_pisos` | `P4030S1` | `VIV003` | `tip_mat_pisos` | ⚠️ Categorías sin verificar |
| `viv_cuartos` | `P5010` | `VIV009` | `num_cuartos_vivienda` | ⚠️ Sin verificar |
| `viv_alcantarillado` | — (por ubicar) | `VIV005` | `ind_tiene_alcantarillado` | ⚠️ Falta homologar en GEIH |
| `viv_acueducto` | — (por ubicar) | `VIV008` | `ind_tiene_acueducto` | ⚠️ Falta homologar en GEIH |
| `hog_num_personas` | — (por ubicar) | `HOG027` | conteo de personas por hogar | ⚠️ Falta homologar en GEIH |
| `fex` | `FEX_C18` | `FEX` | — (fijo en 1: no hay factor de expansión) | Ponderación, no entra a la celda |

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
  - Efecto en el Hot-Deck con el filtro adoptado: donante total 3.106.489 hogares (vs. 3.290.379 sin filtrar y 1.907.399 con año exacto). Grupo nacional ponderado: **A 28,0 · B 34,4 · C 24,9 · D 12,7** — casi idéntico al original sin filtrar (A 28,0/B 34,4/C 25,0/D 12,5), confirma que el filtro de año exacto era el que distorsionaba, no el de vigencia. Celda exacta: 100 % (también dentro de Bogotá).
  - **Dentro de Bogotá (depto 11, 10.016 hogares GEIH) el filtro sí importa mucho:** año exacto dio A 6,0/B 28,0/C 48,5/**D 17,6**; vigencia dio A 4,0/B 20,9/C 47,3/**D 27,8** — una diferencia de 10 p.p. en D. La muestra de "solo recién actualizados" no es representativa del Sisbén vigente de Bogotá.
  - Limitación que persiste: no se puede verificar si el nacional (`CORTE="SIV_2024"` fijo) tiene la misma mezcla de antigüedad por hogar que Bogotá — el extracto no expone una fecha real por hogar como sí lo hace el SDP.
- **Selección:** el Sisbén solo incluye hogares encuestados; asignar su distribución a todo el GEIH sobrerrepresenta A y B.
- **Edad por ciclo de vida**, no en años exactos.
- **Hogares sin jefe:** 13.083 en Sisbén nacional (0,7 %) y 227 en Bogotá con clasificación distinta entre miembros.

## 9. Pendientes de este diccionario
- [x] Confirmar los códigos de `PER002` — corroborado indirectamente (sección 5, 2026-10-10); sigue faltando la ficha ANDA oficial para confirmación 100 %.
- [ ] Ubicar en GEIH las columnas equivalentes a `HOG027`, `VIV005`, `VIV008`.
- [ ] Verificar `geo_zona`, `jefe_sexo`, `viv_paredes`, `viv_pisos` contra el DDI de cada fuente antes de sumarlas a la celda.
