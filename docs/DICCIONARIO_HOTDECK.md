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

## 5. Edad del jefe: ciclo de vida (⚠️ hipótesis por verificar)

El extracto del Sisbén **no trae la edad en años**. `PER002` toma solo los valores 3, 4, 5 y 6, que corresponden a códigos de ciclo de vida, no a años. Para comparar con GEIH se usa el mismo ciclo en ambas fuentes:

| Código `PER002` | Ciclo (hipótesis) | Hogares Sisbén nacional |
|---|---|---|
| 3 | 12–17 años | 4.105 (0,2 %) |
| 4 | 18–28 años | 323.694 (17,8 %) |
| 5 | 29–59 años | 1.077.118 (59,2 %) |
| 6 | 60 años o más | 415.166 (22,8 %) |

**Estado: sin verificar.** La correspondencia se dedujo de las proporciones y de los ciclos de vida del Sisbén IV; falta confirmarla en la ficha de ANDA (variable `PER002`, V926). En Bogotá y en GEIH la edad se convierte con los cortes 17/28/59.

## 6. Celda de matching actual

`geo_depto` + ciclo de vida del jefe (≈130 celdas). Degradación jerárquica: `celda_exacta` → `solo_depto` → `pool_nacional`. Solo son donantes los hogares con `Clasificacion` observada. Resultado actual: 100 % celda exacta.

## 7. ⚠️ Circularidad confirmada — nunca usar como Outcome

| Variable Sisbén | Motivo |
|---|---|
| `I1`–`I15` (Personas) | Privaciones Alkire-Foster proxy calculadas por el propio Sisbén |
| `H_5` (Personas) | Proxy interno del IPM calculado por Sisbén |
| `aseguramiento_salud` | Excluida por el mismo motivo |

## 8. Limitaciones registradas
- **Corte distinto:** Bogotá es del 03/08/2026; el resto del Sisbén, mayo 2024.
- **Selección:** el Sisbén solo incluye hogares encuestados; asignar su distribución a todo el GEIH sobrerrepresenta A y B.
- **Edad por ciclo de vida**, no en años exactos.
- **Hogares sin jefe:** 13.083 en Sisbén nacional (0,7 %) y 227 en Bogotá con clasificación distinta entre miembros.

## 9. Pendientes de este diccionario
- [ ] Confirmar en ANDA los códigos de `PER002`.
- [ ] Ubicar en GEIH las columnas equivalentes a `HOG027`, `VIV005`, `VIV008`.
- [ ] Verificar `geo_zona`, `jefe_sexo`, `viv_paredes`, `viv_pisos` contra el DDI de cada fuente antes de sumarlas a la celda.
