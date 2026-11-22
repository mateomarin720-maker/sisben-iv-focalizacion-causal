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

## Resultado (W = celda exacta; donantes ponderados por `fex`, 2026-11-21)

| Outcome | CATE medio | sd | Rural / urbana | Hombre / mujer |
|---|---|---|---|---|
| `ipm_geih_score` | +0,0132 | 0,032 | +0,0076 / +0,0141 | +0,0283 / −0,0022 |
| `POBRE_GEIH` | +0,0032 | 0,016 | −0,0003 / +0,0037 | +0,0087 / −0,0024 |
| `log_ingreso_percapita` | −0,0194 | 0,044 | −0,0486 / −0,0150 | −0,0147 / −0,0241 |
| `POBRE_MONETARIO` | +0,0039 | 0,012 | +0,0022 / +0,0042 | +0,0010 / +0,0070 |

`X` = zona, sexo del jefe y paredes; pisos salió de `X` al entrar a la
celda. Celda con personas y menores (2026-11-14), IPM-GEIH con la vivienda
corregida por zona (2026-11-12) y donantes del Hot-Deck sorteados según su
`fex` (2026-11-21).

Con W = proxy los valores son del mismo orden (ver la salida completa).

## Cómo leerlo

- El CATE medio es ≈0 en los cuatro outcomes, igual que el ATE del DML.
  Con un tratamiento sorteado al azar dentro de la celda, eso es lo
  esperado (`SIMULACION_IDENTIFICACION.md`).
- Las diferencias por zona y por sexo son del orden de la desviación
  estándar del propio bosque y cambian de signo entre outcomes: no son
  heterogeneidad interpretable.
- La importancia de variables (paredes arriba, ≈0,5) solo indica qué
  variables usa el bosque para partir un efecto que es ≈0; no es
  evidencia de un mecanismo.

**La heterogeneidad no es pequeña: no es identificable con estas
fuentes.** Que el bosque dé diferencias de ±0,01 entre subgrupos no dice
que el efecto varíe poco. Dice que el grupo imputado no lleva
información del hogar. Sin el supuesto del vínculo, la cota de Fréchet
del CATE de cada subgrupo es ancha y contiene el cero en todos los casos
(`RESULTADOS_FRECHET_MANSKI.md`, "Una cota por cada número de los
modelos"):

| Subgrupo | CATE del bosque, `POBRE_MONETARIO` | Cota de Fréchet, `POBRE_MONETARIO` |
|---|---|---|
| Urbana | +0,0042 | [−0,31; +0,71] |
| Rural | +0,0022 | [−0,46; +0,48] |
| Jefe hombre | +0,0010 | [−0,33; +0,65] |
| Jefe mujer | +0,0070 | [−0,36; +0,69] |

Las diferencias del bosque son menos del 1 % del ancho de esas cotas.
Los datos son compatibles tanto con un efecto igual en todos los
subgrupos como con diferencias de decenas de puntos entre ellos.

## Historial que se conserva

- 2026-10-21: un patrón concentrado en jefatura femenina, calculado con
  `viv_paredes`/`viv_pisos` apuntando a columnas equivocadas
  (`docs/metodologia/METODOLOGIA_INDICADOR_IPM_GEIH.md`).
- 2026-10-28 a 2026-11-02: un patrón por zona y la vivienda como pista de
  un residuo, calculados con la celda como código numérico.
- Chequeo de tautología del 2026-10-28: se retiraron del IPM-GEIH las
  privaciones de pisos y paredes porque usaban los mismos códigos que
  `X`. Esa decisión sigue vigente.

## Limitaciones

Las de `RESULTADOS_DML_ATE_ATT_ATU.md`, más la submuestra de 80.000
hogares por costo computacional.
