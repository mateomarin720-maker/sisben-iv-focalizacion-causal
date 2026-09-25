# Diccionario consolidado — Variables para Hot-Deck (GEIH ↔ Sisbén IV)

*(Actualizado 2026-09-24 — se agregaron variables de filtro de jefe de
hogar y zona, encontradas en la construcción del Hot-Deck pero que no
estaban documentadas aquí, siguiendo la observación del tutor de que
las variables codificadas deben quedar siempre con su nombre en el
catálogo, no solo en comentarios de código.)*

## 1. Variable de tratamiento

| Variable Sisbén | Etiqueta |
|---|---|
| `Grupo` | Grupo (A/B/C/D) |
| `Nivel` | Nivel dentro del grupo |
| `Clasificacion` | Grupo + Nivel concatenado (ej. "B3") |

## 2. Filtro de jefe de hogar (NUEVO — antes solo en comentarios de código)

| Fuente | Variable | Valor filtro | Verificado |
|---|---|---|---|
| GEIH (`caracteristicas_generales`) | `P6050` | `"1"` = jefe de hogar | ✅ 24.247 de 24.247 hogares (100%) |
| Sisbén (`personas`) | `PER003` | `"1"` = jefe de hogar | ✅ 1.820.083 de 1.833.166 hogares (99,3%) — 65 hogares con doble jefe corregidos en `estandarizar_sisben.py` |

## 3. Llave de hogar en cada fuente

| Fuente | Llave |
|---|---|
| Sisbén IV | `cod_mpio + zona + llave + corte` (+`hogar` en Viviendas/Personas) |
| GEIH | `DIRECTORIO + SECUENCIA_P + HOGAR` |
| IPM | `DIRECTORIO + SECUENCIA_ENCUESTA + SECUENCIA_P` |

## 4. Esquema canónico — variables ya homologadas (usado en el Hot-Deck)

| Nombre canónico | GEIH | Sisbén | Estado de verificación |
|---|---|---|---|
| `geo_depto` | `DPTO` | `cod_mpio[:2]` | ✅ Verificado exacto — 33 códigos DIVIPOLA idénticos |
| `geo_zona` (NUEVO, documentado ahora) | `CLASE` (1=cabecera/urbano, 2=resto/rural) | `ZONA` (1/2) | ⚠️ NO verificado — distribución muy distinta entre fuentes (GEIH 87%/13%, Sisbén 46%/54%), puede ser diferencia real de composición poblacional o dirección de código distinta. Excluida de la celda de matching hasta confirmar |
| `viv_paredes` | `P4020` | `VIV002` | ⚠️ Categorías no verificadas oficialmente |
| `viv_pisos` | `P4030S1` | `VIV003` | ⚠️ Categorías no verificadas oficialmente |
| `viv_alcantarillado` | — (pendiente ubicar en GEIH) | `VIV005` | ⚠️ Falta homologar en GEIH |
| `viv_acueducto` | — (pendiente ubicar en GEIH) | `VIV008` | ⚠️ Falta homologar en GEIH |
| `viv_cuartos` | `P5010` | `VIV009` | ⚠️ Categorías no verificadas |
| `hog_num_personas` | — (pendiente ubicar en GEIH) | `HOG027` | ⚠️ Falta homologar en GEIH |
| `jefe_sexo` | `P3271` | `PER001` | ⚠️ Dirección de código (1=hombre/mujer) no verificada oficialmente en ninguna de las dos |
| `jefe_edad` | `P6040` | `PER002` | ✅ Numérica, sin problema de dirección de código |
| `fex` | `FEX_C18` | `FEX` | Factor de expansión, no se usa como variable de matching |

## 5. ⚠️ Circularidad confirmada — nunca usar como Outcome

| Variable Sisbén | Motivo |
|---|---|
| `I1`–`I15` (Personas) | Privaciones Alkire-Foster proxy calculadas por el propio Sisbén |
| `H_5` (Personas) | Proxy interno del IPM calculado por Sisbén |

## 6. Pendientes de este diccionario

- [ ] Ubicar en GEIH las columnas equivalentes a `HOG027`, `VIV005`, `VIV008` de Sisbén (probablemente en `hogar_vivienda.parquet`, no revisado todavía en esta sesión)
- [ ] Verificar oficialmente `geo_zona` y `jefe_sexo` contra el DDI de cada fuente antes de sumarlas a la celda de matching
- [ ] Verificar categorías de `viv_paredes`/`viv_pisos` (¿mismo orden de opciones en ambas encuestas?)
