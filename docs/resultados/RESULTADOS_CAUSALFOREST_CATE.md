# Resultados — Causal Forest (CATE)

*Actualizado 2026-10-28: outcome ampliado a 10 privaciones y
`viv_cuartos`/`viv_paredes`/`viv_pisos` corregidos — ver
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`.* **El patrón de
heterogeneidad reportado el 2026-10-21 (concentrado en jefatura femenina)
cambió — ver "Qué cambió y por qué" al final, no se puede seguir citando
el hallazgo anterior.**

Generado por `src/5_estimacion.py` (`_cate`). Salida completa:
`docs/reports/estimacion_ate_att_atu_cate.txt`.

## Qué es

Causal Forest (Wager y Athey, 2018): bosque aleatorio que estima el efecto
causal condicional (CATE) como función de las covariables — da un efecto
distinto por tipo de hogar en vez de un solo número. `CausalForestDML` de
`econml` (400 árboles, mínimo 50 hogares por hoja).

## Cómo se usa aquí

Misma especificación que `RESULTADOS_DML_ATE_ATT_ATU.md`: T = elegibilidad
A/B del Sisbén, `W = {geo_depto, jefe_edad, viv_cuartos}` (celda completa
del Hot-Deck, con `viv_cuartos` corregido), `X = {geo_zona, jefe_sexo,
viv_paredes, viv_pisos}` (heterogeneidad, con `viv_paredes`/`viv_pisos`
ahora apuntando a los códigos GEIH correctos). Submuestra de 80.000
hogares por costo computacional.

## Resultado

| Outcome | CATE medio | Desv. estándar | Rango | Por zona (urbana=1) | Por sexo jefe (mujer=1) |
|---|---|---|---|---|---|
| `ipm_geih_score` (0-10) | +0,0249 | 0,0353 | (-0,207; +0,164) | rural 0,0563 · urbana 0,0202 | hombre 0,033 · mujer 0,0166 |
| `POBRE_GEIH` (0/1) | +0,0041 | 0,0136 | (-0,052; +0,082) | rural 0,0222 · urbana 0,0014 | hombre 0,0076 · mujer 0,0005 |

Importancia de variables: `ipm_geih_score` → `viv_pisos` 0,305,
`viv_paredes` 0,295, `geo_zona_urbana` 0,232, `jefe_mujer` 0,168.
`POBRE_GEIH` → `geo_zona_urbana` 0,356, `viv_paredes` 0,268, `viv_pisos`
0,213, `jefe_mujer` 0,163.

## Cómo leerlo

- **La heterogeneidad ahora se concentra en zona, no en sexo del jefe.**
  Los hogares rurales muestran un CATE bastante más grande que los
  urbanos — 2,8 veces en `ipm_geih_score` (0,056 vs. 0,020) y 16 veces en
  `POBRE_GEIH` (0,022 vs. 0,001). `geo_zona_urbana` es ahora la variable
  más o segunda más importante del forest en los dos outcomes.
- La diferencia por sexo del jefe sigue presente pero mucho más chica que
  antes (hombre 2 veces mujer en `ipm_geih_score`, 15 veces en
  `POBRE_GEIH` pero con magnitudes absolutas pequeñas: 0,0076 vs 0,0005)
  y **con el sentido invertido** respecto al reporte anterior (antes:
  mujer 36 veces más grande que hombre; ahora: hombre más grande que
  mujer).
- `viv_pisos`/`viv_paredes` siguen entre las variables más importantes —
  consistente con `RESULTADOS_DML_ATE_ATT_ATU.md`: la vivienda sigue
  siendo la pista más fuerte de por qué el efecto no colapsa a 0, y ahora
  es una pista confiable (código correcto), no un artefacto.
- **No se puede leer como "el Sisbén afecta más a los hogares rurales"**
  sin antes resolver `viv_paredes`/`viv_pisos` contra el Sisbén — mismo
  razonamiento que antes, solo que ahora el patrón que hay que explicar
  es otro.

## Qué cambió y por qué (respecto al reporte del 2026-10-21)

El reporte anterior decía que el CATE se concentraba en jefatura femenina
(+0,029 mujer vs. +0,001 hombre, 36 veces). Ese resultado se calculó con
`viv_paredes` apuntando en realidad a la columna de **material de
pisos**, y `viv_pisos` apuntando a "¿tiene energía eléctrica? Sí/No" — no
a lo que sus nombres decían (ver
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`). El Causal Forest
construyó particiones usando esas dos variables con significado
equivocado, y el patrón de heterogeneidad que salió de ahí no tenía
garantía de reflejar nada real sobre el sexo del jefe — pudo ser el
código mal mapeado generando una correlación espuria con `jefe_mujer`
dentro de esas particiones.

**No se puede concluir que el hallazgo anterior fuera "falso" en el
sentido de que no hubiera ninguna heterogeneidad** — el forest sí
encontró *algo* las dos veces. Lo que cambia es que ya no se puede citar
*cuál* era el patrón (jefatura femenina) con el código que lo produjo, y
el patrón que sale con el código correcto es distinto (zona, no sexo).
Es exactamente el tipo de corrección que vale la pena dejar visible en
vez de simplemente sobrescribir el número viejo sin explicar qué pasó.

## Limitaciones

Las mismas que `RESULTADOS_DML_ATE_ATT_ATU.md` — tratamiento imputado,
outcome con 10 de 15 privaciones, sin diseño muestral, selección del
Sisbén, falta DPS/RUI, `viv_paredes`/`viv_pisos` sin homologar contra
Sisbén. Adicional: submuestra de 80.000 (no el total) por costo
computacional del Causal Forest.
