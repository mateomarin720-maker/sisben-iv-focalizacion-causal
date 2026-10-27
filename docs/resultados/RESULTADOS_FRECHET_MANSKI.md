# Resultados — Cotas de Fréchet-Manski (ATE sin suponer independencia condicional)

Generado 2026-10-27 por `src/estimacion/cotas_frechet_manski.py`. Detalle
por celda: `docs/reports/cotas_frechet_manski.csv`.

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
| **Fréchet-Manski** (sin CIA) | Cota, no punto | **[-0,627 ; +0,360]** |
| **DML con Hot-Deck** (con CIA) | Punto + IC95% | +0,0074 [+0,004 ; +0,011] |

- Cobertura: 342 celdas, 100 % del peso poblacional de GEIH.
- Ancho de la cota Fréchet-Manski: **0,986** (casi todo el rango posible
  de una diferencia de proporciones, que va de -1 a +1).
- Ancho del IC95 % del DML: 0,0068 — **145 veces más angosto**.
- **Ninguna de las 342 celdas individuales tiene una cota que excluya el
  0** — ni una sola celda, por sí sola, permite descartar que el efecto
  sea cero o incluso de signo contrario.

## Cómo leerlo

**Esto no contradice al DML — lo contextualiza.** El DML da un número
preciso porque **asume** que, dentro de la celda, el grupo Sisbén
funciona como-si-fuera-aleatorio (la CIA del Hot-Deck). Las cotas de
Fréchet-Manski muestran qué tan fuerte es esa suposición: **sin ella, los
datos por sí solos son compatibles con casi cualquier efecto**, desde una
mejora grande hasta un empeoramiento grande. Toda la precisión del +0,0074
del DML viene de la suposición, no de los datos crudos.

Esto es exactamente lo que predice la teoría de cotas de partial
identification (Manski, 2003): sin restricciones adicionales, las cotas
"worst-case" suelen ser muy anchas — no es un error del código ni de los
datos, es la honestidad matemática de no asumir lo que no se puede
verificar. La pregunta útil no es "¿por qué la cota es tan ancha?" sino
"¿qué tan dispuestos estamos a confiar en la suposición del Hot-Deck para
poder reportar el número angosto del DML?".

## Qué NO hace este análisis (alcance de esta primera corrida)

- Solo cubre `POBRE_GEIH` (binario). Las cotas de Fréchet-Hoeffding para
  un outcome continuo (`ipm_geih_score`) requieren acotar la CDF conjunta
  completa — más trabajo, no implementado todavía.
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

Las mismas de `RESULTADOS_DML_ATE_ATT_ATU.md`: outcome reducido, selección
del Sisbén, falta DPS/RUI, categorías de vivienda sin verificar. Además:
`P(T|X)` del Sisbén se calcula sin ponderar (no es una encuesta con diseño
muestral, es un registro administrativo) — `P(Y|X)` de GEIH sí se pondera
por `FEX_C18`.
