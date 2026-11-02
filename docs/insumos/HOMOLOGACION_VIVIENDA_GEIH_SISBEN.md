# Homologación de paredes y pisos entre GEIH y Sisbén IV

Resuelve el bloqueo abierto desde el inicio del proyecto: las categorías de
`viv_paredes`/`viv_pisos` no se podían comparar entre fuentes porque el
diccionario del Sisbén solo trae Nombre y Etiqueta.

## Fuentes

- **Sisbén:** *Ficha de Caracterización Socioeconómica* del Sisbén IV (DNP,
  versión del 29-oct-2017), preguntas 18 (paredes exteriores) y 19 (pisos):
  `docs/insumos/FICHA_SISBEN_IV_FCS_2017.pdf`. Variables en los
  microdatos: `VIV002` (paredes) y `VIV003` (pisos).
- **GEIH:** diccionario oficial 2024, `P4010` (paredes) y `P4020` (pisos).

## Verificación: ¿los microdatos 2024 usan los códigos de la ficha de 2017?

Sí. Se cruzaron `VIV002`/`VIV003` con las privaciones que el propio DNP
calcula (`I14`/`I13`, del jefe de cada hogar, 1.820.082 hogares). Este
cruce se usa **solo para validar códigos**; esas privaciones nunca se usan
como outcome. El resultado es determinista, 0 % o 100 % en cada celda:

| Variable | Zona 1 | Zona 2 |
|---|---|---|
| `I14` (paredes inadecuadas) | códigos 5, 6, 7 → 100 %; 1-4 → 0 % | códigos 6, 7 → 100 %; 1-5 → 0 % |
| `I13` (pisos inadecuados) | código 5 → 100 %; resto → 0 % | código 5 → 100 %; resto → 0 % |

Leído con la ficha, coincide exactamente con la regla oficial del IPM del
DANE (`met-IPM.pdf`, p. 26):
- paredes: madera burda (5), guadua/caña/vegetal (6) y zinc/desechos (7)
  en lo urbano, sin la madera burda en lo rural;
- pisos: tierra o arena (5) en ambas zonas.

Ninguna otra lectura de los códigos produce ese patrón.

**Efecto colateral:** esto confirma que en el Sisbén `ZONA` = 1 es urbano
(la madera burda solo es privación en zona 1, igual que en la regla
urbana oficial). En GEIH, el diccionario confirma `CLASE` 1 = Urbano,
2 = Rural. `geo_zona` tiene la misma dirección en las dos fuentes.

## Paredes exteriores

| Categoría común | GEIH `P4010` | Sisbén `VIV002` |
|---|---|---|
| H1 Ladrillo, bloque, piedra, prefabricado, madera pulida | 1 (a, ladrillo/bloque/prefabricado/piedra), 2 (b, madera pulida) | 1 (bloque/ladrillo/piedra/madera pulida), 4 (prefabricado) |
| H2 Tapia pisada, adobe | 3 (c) | 2 |
| H3 Bahareque | 4 (d) | 3 |
| H4 Madera burda, tabla, tablón | 5 (e) | 5 |
| H5 Guadua, caña, esterilla, otro vegetal | 6 (f, guadua), 7 (g, caña/esterilla/vegetal) | 6 |
| H6 Zinc, tela, cartón, latas, desechos, plástico | 8 (h) | 7 |
| H7 Sin paredes | 9 (i) | 0 (no aparece en los datos 2024) |

La homologación es exacta en las 7 categorías comunes. Solo se pierde
detalle donde una fuente desagrega más: GEIH separa la madera pulida y la
guadua, y el Sisbén separa el prefabricado.

## Pisos

| Categoría común | GEIH `P4020` | Sisbén `VIV003` |
|---|---|---|
| P1 Alfombra, mármol, parqué, madera pulida | 5 (e, mármol), 6 (f, madera pulida), 7 (g, alfombra) | 1 |
| P2 Baldosa, vinilo, tableta, ladrillo | 4 (d, baldosín/ladrillo/vinisol/sintéticos) | 2 |
| P3 Cemento, gravilla | 2 (b) | 3 |
| P4 Madera burda, tabla, tablón | 3 (c, incluye "otro vegetal") | 4 (incluye "madera en mal estado") |
| P5 Tierra, arena | 1 (a) | 5 |
| — Otro | sin equivalente | 6 (0,14 % de los hogares) |

Dos diferencias menores:
- "Otro vegetal" va en P4 en GEIH; en el Sisbén probablemente cae en
  "otro" (6).
- El código 6 del Sisbén no tiene par en GEIH: se trata como faltante en
  la escala común.

**Ojo con el orden: las dos escalas van en sentido contrario.** En GEIH
el código 1 de pisos es tierra; en el Sisbén, tierra es el 5. Comparar
los códigos crudos entre fuentes, o usarlos como número ordinal, da
resultados invertidos.

## Distribuciones (sanity check)

| | H1 paredes | P5 tierra | P2 baldosa |
|---|---|---|---|
| GEIH 2024 (hogares, sin expandir) | 92,5 % | 3,5 % | 69,9 % |
| Sisbén nacional | 53,7 % | 30,9 % | 13,3 % |
| Sisbén Bogotá (SDP) | 98,6 % | 0,7 % | 81,1 % |

Las diferencias son de población, no de codificación: el Sisbén nacional
registra sobre todo hogares pobres y rurales. Bogotá (`tip_mat_paredes`/
`tip_mat_pisos`) tiene distribuciones coherentes con la ficha, pero **no**
se pudo verificar con privaciones porque la entrega del SDP no trae
`I13`/`I14`.

## Qué cambia en el proyecto

- `viv_paredes`/`viv_pisos` ya se pueden comparar entre fuentes usando la
  escala común (H1-H7, P1-P5). Antes eso no era posible.
- Se pueden sumar a la celda del Hot-Deck (pendiente de decidir: más
  celdas implica menos donantes por celda).
- En `5_estimacion.py` se usan como `X` dentro de una sola fuente (GEIH),
  con los códigos de GEIH, así que el uso actual no cambia.
- La pista de que el residuo causal venía de "vivienda sin homologar"
  (`IDENTIFICACION_CAUSAL.md`, `DIAGNOSTICO_W_CELDA_EXACTA.md`) ya se puede
  probar en vez de suponer.
