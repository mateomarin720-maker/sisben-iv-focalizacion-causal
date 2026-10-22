# Resultados — Causal Forest (CATE)

Generado 2026-10-21 por `src/5_estimacion.py` (`_cate`), primera corrida
real sobre el outcome y el Hot-Deck con vivienda sumada a la celda. Salida
completa: `docs/reports/estimacion_ate_att_atu_cate.txt`.

## Qué es

Causal Forest (Wager y Athey, 2018): bosque aleatorio que estima el efecto
causal condicional (CATE) como función de las covariables — en vez de un
solo número (ATE), da un efecto distinto por tipo de hogar. Implementado
con `CausalForestDML` de `econml` (400 árboles, mínimo 50 hogares por
hoja).

## Cómo se usa aquí

Misma especificación que en `RESULTADOS_DML_ATE_ATT_ATU.md`: T = elegibilidad
A/B del Sisbén, `W = {geo_depto, jefe_edad, viv_cuartos}` (celda completa
del Hot-Deck), `X = {geo_zona, jefe_sexo, viv_paredes, viv_pisos}`
(heterogeneidad). Submuestra de 80.000 hogares (de 290.968) por costo
computacional.

## Resultado

| Outcome | CATE medio | Desv. estándar | Rango | Por zona (urbana=1) | Por sexo jefe (mujer=1) |
|---|---|---|---|---|---|
| `ipm_geih_score` (0-4) | +0,0149 | 0,0211 | (-0,053; +0,087) | rural 0,0097 · urbana 0,0157 | hombre 0,0008 · mujer 0,0293 |
| `POBRE_GEIH` (0/1) | +0,0031 | 0,0156 | (-0,047; +0,065) | rural -0,0077 · urbana 0,0047 | hombre -0,0071 · mujer 0,0136 |

Importancia de variables (ambos outcomes, consistente): `jefe_mujer`
(~0,42-0,45) y `viv_paredes` (~0,38) dominan; `geo_zona_urbana` aporta
~0,17-0,19; `viv_pisos` es casi irrelevante (<0,01).

## Cómo leerlo

- **El efecto heterogéneo se concentra en hogares con jefa mujer:** el CATE
  para `ipm_geih_score` es prácticamente 0 cuando el jefe es hombre (+0,0008)
  y sube a +0,0293 cuando es mujer — 36 veces más grande. Para `POBRE_GEIH`
  el patrón es el mismo signo: negativo/cercano a 0 en hogares con jefe
  hombre, positivo en jefatura femenina.
- **`viv_paredes` es la segunda variable más importante en ambos
  outcomes** — confirma lo que ya señalaba la prueba exploratoria de
  empleo/ingreso (2026-10-21): la vivienda sigue cargando información que
  el Hot-Deck no está capturando en su celda, incluso después de sumarle
  `viv_cuartos`.
- **No se puede leer como "el Sisbén afecta más a los hogares con jefa
  mujer"** sin antes resolver el punto anterior — el patrón por sexo podría
  reflejar que la jefatura femenina correlaciona con composición de
  vivienda o con departamentos específicos de forma que `W` no absorbe del
  todo (mismo tipo de fuga que explica el residuo del ATE/ATT/ATU).
- La magnitud sigue siendo pequeña en términos absolutos (máximo +0,029 en
  una escala 0-4), pero la heterogeneidad por sexo del jefe es
  consistente entre los dos outcomes (score continuo y binario), lo que le
  da algo más de credibilidad que si solo apareciera en uno.

## Próximo paso sugerido

Repetir esta corrida sumando `viv_paredes` (con sus categorías ya resueltas
contra la ficha oficial de GEIH — pendiente, ver
`docs/insumos/DICCIONARIO_HOTDECK.md` §8) a `W` en vez de a `X`, para ver si
la heterogeneidad por sexo del jefe se mantiene o era la vivienda
colándose por esa covariable.

## Limitaciones

Las mismas que `RESULTADOS_DML_ATE_ATT_ATU.md` — tratamiento imputado,
outcome reducido (4 de 15 privaciones, con la limitación de
`sin_cotizacion_pension_jefe`), sin diseño muestral, selección del Sisbén,
falta DPS/RUI. Adicional: submuestra de 80.000 (no el total) por costo
computacional del Causal Forest.
