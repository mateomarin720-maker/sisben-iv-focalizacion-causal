# Resultados — Causal Forest (CATE)

*Actualizado 2026-10-28 (dos veces el mismo día): outcome ampliado a 10
privaciones y `viv_cuartos`/`viv_paredes`/`viv_pisos` corregidos, y horas
después reducido a **8** privaciones al retirar
`material_pisos_inadecuado`/`material_paredes_inadecuado` del outcome por
ser tautológicas con `viv_pisos`/`viv_paredes` de `X` (ver
"Chequeo de tautología" abajo) — ver
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`.* **El patrón de
heterogeneidad reportado el 2026-10-21 (concentrado en jefatura femenina)
cambió — ver "Qué cambió y por qué" al final, no se puede seguir citando
el hallazgo anterior.**

**Regenerado 2026-11-02 tras corregir el bug de agosto** (códigos
`"1.0"` del `.DTA`, ver CHANGELOG). El patrón cualitativo se mantiene.

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
| `ipm_geih_score` (0-8) | +0,0228 | 0,0359 | (-0,246; +0,216) | rural 0,0448 · urbana 0,0195 | hombre 0,0288 · mujer 0,0167 |
| `POBRE_GEIH` (0/1, K≥3) | +0,0033 | 0,0118 | (-0,050; +0,056) | rural 0,0139 · urbana 0,0017 | hombre 0,0056 · mujer 0,0009 |

Importancia de variables: `ipm_geih_score` → `viv_paredes` 0,320,
`viv_pisos` 0,285, `geo_zona_urbana` 0,222, `jefe_mujer` 0,172.
`POBRE_GEIH` → `viv_paredes` 0,338, `viv_pisos` 0,262, `geo_zona_urbana`
0,249, `jefe_mujer` 0,151.

## Cómo leerlo

- **La heterogeneidad ahora se concentra en zona, no en sexo del jefe.**
  Los hogares rurales muestran un CATE bastante más grande que los
  urbanos — 2,3 veces en `ipm_geih_score` (0,045 vs. 0,020) y 8 veces en
  `POBRE_GEIH` (0,014 vs. 0,002). `geo_zona_urbana` es la tercera
  variable más importante del forest en los dos outcomes, detrás de la
  vivienda.
- La diferencia por sexo del jefe sigue presente pero mucho más chica que
  antes (hombre 1,7 veces mujer en `ipm_geih_score`, 6 veces en
  `POBRE_GEIH` pero con magnitudes absolutas pequeñas: 0,0056 vs 0,0009)
  y **con el sentido invertido** respecto al reporte anterior (antes:
  mujer 36 veces más grande que hombre; ahora: hombre más grande que
  mujer).
- `viv_paredes`/`viv_pisos` siguen siendo las dos variables más
  importantes — consistente con `RESULTADOS_DML_ATE_ATT_ATU.md`: la
  vivienda sigue siendo la pista más fuerte de por qué el efecto no
  colapsa a 0, y ahora es una pista confiable (código correcto, y
  verificada contra tautología — ver abajo), no un artefacto.
- **No se puede leer como "el Sisbén afecta más a los hogares rurales"**
  sin antes probar `viv_paredes`/`viv_pisos` (ya homologadas con el
  Sisbén, `docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`) dentro de
  la celda del Hot-Deck.

**Diagnóstico 2026-11-02:** los números de esta página usan `W` con
`jefe_edad`/`viv_cuartos` CONTINUOS, un proxy de la celda discreta real
del Hot-Deck. Con la celda EXACTA (`W` categórico, igual al sorteo real),
el CATE medio de `ipm_geih_score` cae de +0,0228 a +0,0085 y la
heterogeneidad por sexo del jefe se vuelve negativa para jefa mujer
(-0,0071) — un TERCER patrón distinto a los dos reportados antes en este
documento. La heterogeneidad por zona se mantiene y se acentúa (13x en
vez de 2,3x). Ver `docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md` para el
detalle completo.

## Chequeo de tautología: ¿la importancia de vivienda era mecánica?

Al ampliar el outcome a 10 privaciones (ver docstring de
`3_preprocesamiento.py`), dos de los nuevos componentes
(`material_pisos_inadecuado`, `material_paredes_inadecuado`) se
calculaban con los MISMOS códigos GEIH (`P4020`/`P4010`) que
`viv_pisos`/`viv_paredes` en `X`. Eso significa que, mientras esos dos
componentes estuvieron en el outcome, parte de la "importancia" de
`viv_paredes`/`viv_pisos` podía ser pura tautología: un hogar con piso de
tierra suma un punto al score por definición, tratado o no — el forest
podía estar detectando esa relación mecánica, no heterogeneidad causal
real.

**Se puso a prueba retirando esos dos componentes del outcome** (queda en
8 privaciones) y corriendo todo de nuevo. Si la importancia de
`viv_paredes`/`viv_pisos` hubiera sido mecánica, debía CAER al quitar el
vínculo directo con `Y`. No cayó — subió levemente:

| Importancia (`ipm_geih_score`) | Con 10 privaciones (tautológico) | Con 8 privaciones (sin tautología) |
|---|---|---|
| `viv_paredes` + `viv_pisos` sumadas | 0,600 | 0,617 |
| `geo_zona_urbana` | 0,232 | 0,217 |
| `jefe_mujer` | 0,168 | 0,167 |

El resultado es evidencia (no prueba definitiva — el forest es no lineal
y la muestra cambia por el resampleo de CATE) de que la señal de
vivienda en el CATE **no depende de la tautología** y probablemente
refleja algo real que la celda del Hot-Deck no absorbe — consistente con
el diagnóstico de `IDENTIFICACION_CAUSAL.md`.

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
outcome con 8 de 15 privaciones, sin diseño muestral, selección del
Sisbén, falta DPS/RUI, `viv_paredes`/`viv_pisos` sin homologar contra
Sisbén. Adicional: submuestra de 80.000 (no el total) por costo
computacional del Causal Forest.
