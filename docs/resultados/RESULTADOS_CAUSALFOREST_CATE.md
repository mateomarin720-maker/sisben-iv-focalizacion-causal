# Resultados — Causal Forest (CATE)

Generado por `src/5_estimacion.py` (`_cate`). Salida completa:
`docs/reports/estimacion_ate_att_atu_cate.txt`.

**Regenerado 2026-11-02 con los modelos auxiliares corregidos** (la celda
y el departamento entraban como códigos numéricos; ver
`DIAGNOSTICO_W_CELDA_EXACTA.md`). Los patrones de heterogeneidad
reportados antes (concentración rural, inversión por sexo del jefe,
vivienda como "pista" del residuo) venían de ese error y no se deben
citar.

## Qué es

Causal Forest (Wager y Athey, 2018), `CausalForestDML` de `econml` (400
árboles, mínimo 50 hogares por hoja): estima un efecto condicional (CATE)
por tipo de hogar. Misma especificación que
`RESULTADOS_DML_ATE_ATT_ATU.md`; submuestra de 80.000 hogares.

## Resultado (W = celda exacta)

| Outcome | CATE medio | sd | Rural / urbana | Hombre / mujer |
|---|---|---|---|---|
| `ipm_geih_score` | +0,0024 | 0,031 | +0,0165 / +0,0003 | +0,0115 / −0,0070 |
| `POBRE_GEIH` | −0,0018 | 0,011 | +0,0028 / −0,0025 | +0,0018 / −0,0055 |
| `log_ingreso_percapita` | −0,0206 | 0,063 | −0,0621 / −0,0144 | −0,0098 / −0,0317 |
| `POBRE_MONETARIO` | +0,0023 | 0,012 | −0,0010 / +0,0028 | +0,0029 / +0,0016 |

Con W = proxy los valores son del mismo orden (ver la salida completa).

## Cómo leerlo

- El CATE medio es ≈0 en los cuatro outcomes, igual que el ATE del DML.
  Con un tratamiento sorteado al azar dentro de la celda, eso es lo
  esperado (`SIMULACION_IDENTIFICACION.md`).
- Las diferencias por zona y por sexo son del orden de la desviación
  estándar del propio bosque y cambian de signo entre outcomes: no son
  heterogeneidad interpretable.
- La importancia de variables (paredes y pisos arriba) solo indica qué
  variables usa el bosque para partir un efecto que es ≈0; no es
  evidencia de un mecanismo.

## Historial que se conserva

- 2026-10-21: un patrón concentrado en jefatura femenina, calculado con
  `viv_paredes`/`viv_pisos` apuntando a columnas equivocadas
  (`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`).
- 2026-10-28 a 2026-11-02: un patrón por zona y la vivienda como pista de
  un residuo, calculados con la celda como código numérico.
- Chequeo de tautología del 2026-10-28: se retiraron del IPM-GEIH las
  privaciones de pisos y paredes porque usaban los mismos códigos que
  `X`. Esa decisión sigue vigente.

## Limitaciones

Las de `RESULTADOS_DML_ATE_ATT_ATU.md`, más la submuestra de 80.000
hogares por costo computacional.
