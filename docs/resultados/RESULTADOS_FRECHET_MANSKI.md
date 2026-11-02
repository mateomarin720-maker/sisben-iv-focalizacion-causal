# Resultados — Cotas de Fréchet-Manski (ATE sin suponer independencia condicional)

Generado 2026-10-27 por `src/estimacion/cotas_frechet_manski.py`, refrescado
el 2026-10-28 tras corregir `viv_cuartos` y, horas después, tras reducir
el outcome de 10 a 8 privaciones (ver
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`). Ampliado el 2026-11-02
a `POBRE_MONETARIO` (ver sección propia abajo). Detalle por celda:
`docs/reports/cotas_frechet_manski.csv` (`POBRE_GEIH`) y
`docs/reports/cotas_frechet_manski_pobre_monetario.csv`; salida de
consola: `docs/reports/cotas_frechet_manski.txt`.

## Qué es

Manski (2003): en vez de imputar el tratamiento (como hace el Hot-Deck) y
asumir que esa imputación es correcta, usa SOLO lo que los datos dicen por
separado — `P(Y|X)` en GEIH, `P(T|X)` en Sisbén — y aplica la desigualdad
de Fréchet-Hoeffding para acotar la distribución conjunta que es
compatible con esas dos marginales, sin suponer nada sobre cómo se
relacionan Y y T más allá de eso. El resultado es un intervalo, no un
punto: el rango de efectos que los datos NO permiten descartar.

## Cómo se usa aquí

Misma celda X que el Hot-Deck (`geo_depto + ciclo de edad del jefe + tramo
de `viv_cuartos``), para que sea directamente comparable con el DML.
`Y = POBRE_GEIH` (binario). `T = 1{Grupo ∈ {A,B}}`, calculado directamente
sobre el archivo estandarizado del Sisbén (nacional + Bogotá), SIN pasar
por el Hot-Deck. Por celda: cota de Fréchet-Hoeffding sobre
`P(Y=1,T=1|X)` y `P(Y=1,T=0|X)`, de ahí cota sobre `E[Y|T=1,X]` y
`E[Y|T=0,X]`, resta para la cota del CATE(X), y agregación ponderada por
el peso poblacional de GEIH (`FEX_C18`) por celda.

## Resultado

| | Estimador | Rango |
|---|---|---|
| **Fréchet-Manski** (sin CIA) | Cota, no punto | **[-0,4083 ; +0,3080]** |
| **DML con Hot-Deck** (con CIA) | Punto + IC95% | ver `docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md` (el número no se hardcodea aquí para que no quede desactualizado si cambia el outcome o la celda) |

- Cobertura: 365 celdas (antes de corregir `viv_cuartos`: 342 — la celda
  correcta tiene más combinaciones distintas de tramo de cuartos), 100 %
  del peso poblacional de GEIH.
- Ancho de la cota Fréchet-Manski: **0,7163** (antes de corregir
  `viv_cuartos`: 0,986 — la celda correcta angosta la cota, pero sigue
  cubriendo la mayor parte del rango posible de una diferencia de
  proporciones, que va de -1 a +1). La reducción del outcome de 10 a 8
  privaciones (mismo día, ver `METODOLOGIA_INDICADOR_IPM_GEIH.md`) movió
  `POBRE_GEIH` de 17,2 % a 16,3 % de hogares pobres y apenas cambió la
  cota (0,7267→0,7163) — la tasa de pobreza binaria es poco sensible a
  quitar 2 de 10 componentes que ya eran poco prevalentes (3,5 % y 0,9 %).
- Ancho del IC95 % del DML (`POBRE_GEIH`, ver
  `RESULTADOS_DML_ATE_ATT_ATU.md`): 0,0046 — **~156 veces más angosto**
  que la cota Fréchet-Manski.
- **Ninguna de las 365 celdas individuales tiene una cota que excluya el
  0** — ni una sola celda, por sí sola, permite descartar que el efecto
  sea cero o incluso de signo contrario.

## Pobreza monetaria (`POBRE_MONETARIO`) — 2026-11-02

Mismo cálculo, misma celda, mismo `T`, con `Y = POBRE_MONETARIO`
(`3b_preprocesamiento_monetario.py`). Se excluyen los hogares sin
`POBRE_MONETARIO` (ingreso per cápita indefinido). Al correr de nuevo,
`POBRE_GEIH` reprodujo exactamente la cota anterior ([-0,4083; +0,3080]).

| Outcome | P(Y=1) | Cota Fréchet-Manski (sin CIA) | Ancho | ATE DML, celda exacta (con CIA) |
|---|---|---|---|---|
| `POBRE_GEIH` | 0,194 | [-0,4083 ; +0,3080] | 0,7163 | +0,0049 [+0,0026 ; +0,0072] |
| `POBRE_MONETARIO` | 0,387 | **[-0,5886 ; +0,7035]** | **1,2920** | +0,0152 [+0,0118 ; +0,0187] |

- Cobertura: las mismas 365 celdas, 100 % del peso de GEIH.
- La cota de `POBRE_MONETARIO` es **más ancha** que la de `POBRE_GEIH`
  (1,29 frente a 0,72, de un máximo posible de 2). No es un defecto del
  outcome: las cotas de Fréchet-Hoeffding son más anchas cuanto más
  cerca de 0,5 están las dos marginales. Aquí `P(T=1)` ≈ 0,56 y
  `P(Y=1)` sube de 0,19 a 0,39 (la sobreestimación de 6-7 pp de pobreza
  monetaria la ensancha un poco más).
- El ATE del DML (+0,0152) cae dentro de la cota y equivale al ~1 % de
  su ancho.
- **Ninguna celda excluye el 0 de forma informativa.** Un filtro
  numérico marca 6 celdas, pero son degeneradas: tienen 1-11 hogares
  GEIH (0,003 % del peso) y `P(Y=1|X) = 1`, es decir, todos pobres. Ahí
  la cota colapsa a [0; 0] y solo aparecen residuos de punto flotante.

**Lectura:** la robustez que mostró `POBRE_MONETARIO` en el diagnóstico de
`W` (`DIAGNOSTICO_W_CELDA_EXACTA.md`) sigue dependiendo por completo de
la CIA del Hot-Deck. Sin ese supuesto, los datos no descartan un efecto
de ningún signo. Las dos piezas no se contradicen: el diagnóstico de `W`
descarta que el efecto sea un artefacto del proxy *dado* el supuesto, y
las cotas muestran cuánto pesa el supuesto.

## Cómo leerlo

**Esto no contradice al DML — lo contextualiza.** El DML da un número
preciso porque **asume** que, dentro de la celda, el grupo Sisbén
funciona como-si-fuera-aleatorio (la CIA del Hot-Deck). Las cotas de
Fréchet-Manski muestran qué tan fuerte es esa suposición: **sin ella, los
datos por sí solos son compatibles con casi cualquier efecto**, desde una
mejora grande hasta un empeoramiento grande. Toda la precisión del punto
que reporta el DML viene de la suposición, no de los datos crudos.

Esto es exactamente lo que predice la teoría de cotas de partial
identification (Manski, 2003): sin restricciones adicionales, las cotas
"worst-case" suelen ser muy anchas — no es un error del código ni de los
datos, es la honestidad matemática de no asumir lo que no se puede
verificar. La pregunta útil no es "¿por qué la cota es tan ancha?" sino
"¿qué tan dispuestos estamos a confiar en la suposición del Hot-Deck para
poder reportar el número angosto del DML?".

## Qué NO hace este análisis (alcance de esta primera corrida)

- Solo cubre outcomes binarios (`POBRE_GEIH`, `POBRE_MONETARIO`). Las
  cotas de Fréchet-Hoeffding para un outcome continuo (`ipm_geih_score`,
  `log_ingreso_percapita`) requieren acotar la CDF conjunta completa —
  más trabajo, no implementado todavía.
- No incorpora supuestos intermedios que podrían angostar la cota sin
  llegar a la CIA completa — ver "Próximo paso".

## Próximo paso: angostar la cota con supuestos más débiles que la CIA

Las cotas "worst-case" sin ningún supuesto casi siempre son así de anchas
en la literatura de partial identification — eso no significa que no se
pueda hacer nada. Manski (2003) propone supuestos intermedios, más débiles
que la independencia condicional completa pero más fuertes que "nada",
que sí angostan la cota:
- **Monotone Treatment Selection (MTS):** asumir que los hogares con mejor
  `Y` potencial no tienen sistemáticamente MÁS probabilidad de ser
  clasificados A/B — razonable si se cree que el Sisbén no favorece
  activamente a los hogares menos pobres.
- **Monotone Treatment Response (MTR):** asumir que ser clasificado A/B
  (y por tanto elegible a más subsidios) no puede, en promedio, EMPEORAR
  el bienestar — descarta la mitad "negativa" del rango.
Cualquiera de las dos, combinada con las marginales ya calculadas aquí,
angostaría la cota sin necesitar la CIA completa del Hot-Deck. Queda como
extensión natural de este script.

## Limitaciones

Las mismas de `RESULTADOS_DML_ATE_ATT_ATU.md`: outcome con 8 de 15
privaciones, selección del Sisbén, falta DPS/RUI, `viv_paredes`/
`viv_pisos` con código GEIH confirmado pero categorías sin homologar
contra el Sisbén. Además:
`P(T|X)` del Sisbén se calcula sin ponderar (no es una encuesta con diseño
muestral, es un registro administrativo) — `P(Y|X)` de GEIH sí se pondera
por `FEX_C18`.
