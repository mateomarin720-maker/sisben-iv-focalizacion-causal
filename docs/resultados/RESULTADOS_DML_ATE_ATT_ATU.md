# Resultados — Double Machine Learning (ATE, ATT, ATU)

*Actualizado 2026-10-28 (dos veces el mismo día): outcome ampliado a 10
privaciones y `viv_cuartos` corregido, y horas después reducido a **8**
privaciones al retirar `material_pisos_inadecuado`/
`material_paredes_inadecuado` (tautológicas con `viv_pisos`/`viv_paredes`
de `X`, ver abajo) — ver `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`.
Los números de esta página reemplazan la corrida anterior (4 privaciones,
2026-10-21/27).*

Generado por `src/5_estimacion.py` (`_ate_att_atu`). Salida completa:
`docs/reports/estimacion_ate_att_atu_cate.txt`.

## Qué es

Double Machine Learning (Chernozhukov et al., 2018): estima el efecto
causal de un tratamiento binario controlando por covariables con modelos de
aprendizaje automático (no supone una forma funcional lineal para los
modelos de molestia `Y~W` y `T~W`), con validación cruzada (`LinearDML` de
`econml`).

## Cómo se usa aquí

- **Tratamiento (T):** `1` si `Grupo_hotdeck ∈ {A,B}` (elegibilidad A/B
  del Sisbén). Con la corrección de `viv_cuartos`, el 63,7 % de los
  hogares GEIH queda en T=1 (antes de corregir `viv_cuartos`: 74,4 %).
- **Outcomes:** `ipm_geih_score` (continuo, 0-8 privaciones) y
  `POBRE_GEIH` (binario, score ≥ 3) — ver
  `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` para las 8 privaciones
  (`material_pisos_inadecuado`/`material_paredes_inadecuado` se retiraron
  del outcome por tautología con `X`, ver "Cómo leerlo").
- **W (controles de los modelos de molestia):** `geo_depto`, `jefe_edad`,
  `viv_cuartos` — la celda COMPLETA del Hot-Deck, con `viv_cuartos` ya
  corregido (cuartos en total, no "cuartos para dormir").
- **X (heterogeneidad del efecto):** `geo_zona`, `jefe_sexo`,
  `viv_paredes`, `viv_pisos` — covariables NO usadas en la celda, ahora
  con los códigos correctos también (antes `viv_paredes`/`viv_pisos`
  apuntaban a las columnas equivocadas).
- **ATT y ATU** se calculan con el MISMO `LinearDML` ya ajustado,
  evaluando `effect()`/`ate()` solo sobre los hogares tratados (ATT) o no
  tratados (ATU).

## Resultado

| Outcome | ATE | ATT (error de inclusión) | ATU (error de exclusión) |
|---|---|---|---|
| `ipm_geih_score` (0-8) | +0,0206 [+0,0141; +0,0272] | +0,0214 [+0,0146; +0,0281] | +0,0193 [+0,0130; +0,0256] |
| `POBRE_GEIH` (0/1, K≥3, 16,3 % de los hogares) | +0,0052 [+0,0029; +0,0075] | +0,0055 [+0,0032; +0,0079] | +0,0046 [+0,0025; +0,0067] |

Intervalos de confianza al 95 %. Propensión `P(T=1|W)`: p5=0,536,
p95=0,731 (mínimo observado 0,000 en alguna celda puntual — misma
limitación de siempre, ver abajo).

## Cómo leerlo

- Los tres efectos (ATE/ATT/ATU) siguen siendo parecidos entre sí, como
  antes — esperable con pocas covariables de heterogeneidad en `X`.
- Los IC95 % **siguen excluyendo 0** en los dos outcomes, incluso con el
  outcome y la celda corregidos — la asociación entre el grupo asignado
  por Hot-Deck y las privaciones del jefe no desaparece al arreglar el
  error de `viv_cuartos`. Esto es informativo: si el residuo hubiera sido
  puramente un artefacto del código equivocado, debería haber colapsado a
  0 con la corrección. No colapsó.
- **La importancia de variables apunta en la misma dirección que antes,
  ahora con más confianza en el diagnóstico:** `viv_paredes` (0,316) y
  `viv_pisos` (0,301) siguen siendo las covariables más importantes
  para `ipm_geih_score`, y ahora SÍ son las variables correctas (antes de
  2026-10-28 apuntaban a las columnas equivocadas, así que la señal podía
  deberse al error de código). Con el código corregido, la vivienda
  sigue siendo la pista más fuerte de por qué el efecto no colapsa a 0 —
  pero ahora es una pista confiable, no una que dependía de un bug.
- `geo_zona_urbana` también gana peso (0,217 en `ipm_geih_score`, 0,293
  en `POBRE_GEIH`) — con la celda correcta, la geografía fina (urbano/
  rural) parece explicar más del residuo de lo que se pensaba.
- **Chequeo de tautología (2026-10-28, tras retirar 2 privaciones de `Y`):**
  el outcome llegó a tener 2 componentes (`material_pisos_inadecuado`/
  `material_paredes_inadecuado`) calculados con los MISMOS códigos GEIH
  que `viv_pisos`/`viv_paredes` en `X` — eso habría inflado
  mecánicamente su importancia en el Causal Forest. Se retiraron esos dos
  componentes del outcome y se volvió a correr todo: la importancia de
  `viv_paredes`/`viv_pisos` NO bajó (subió levemente, de 0,600 a 0,617
  sumadas en `ipm_geih_score`). Si la señal hubiera sido mecánica,
  debería haber caído al quitar el componente tautológico — no cayó. Esto
  es evidencia de que la vivienda explica heterogeneidad real, no un
  artefacto de la definición del score — ver detalle en
  `docs/resultados/RESULTADOS_CAUSALFOREST_CATE.md`.

## Qué se mantiene igual

El hallazgo metodológico sobre `LinearDRLearner` (descartado para ATT/ATU
por dar valores absurdos con categóricas sin orden en `X`) sigue vigente
— ver docstring de `_ate_att_atu` en `src/5_estimacion.py`. No fue
afectado por la corrección de variables, es un problema del estimador,
no del dato.

## Limitaciones

- Tratamiento imputado por Hot-Deck, no observado.
- `W` usa `jefe_edad` y `viv_cuartos` continuos como proxy de la celda
  real (que es por tramos/ciclo de vida) — no es una réplica exacta de la
  celda discreta.
- Outcome con 8 de 15 privaciones del IPM oficial — ver limitaciones
  específicas (`sin_cotizacion_pension_jefe` mezcla causas distintas) en
  `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`.
- Sin ajuste por diseño muestral de GEIH ni de Sisbén.
- Selección: el Sisbén solo cubre hogares inscritos — ver
  `docs/resultados/RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`.
- Falta DPS/RUI como confusores.
- `viv_paredes`/`viv_pisos` ahora tienen el código GEIH correcto, pero
  sus categorías siguen sin homologar contra el Sisbén — por eso siguen
  en `X`, no en `W` (celda del Hot-Deck).
- Propensión mínima observada = 0,000 en al menos una celda — posible
  violación puntual de superposición (positivity).
