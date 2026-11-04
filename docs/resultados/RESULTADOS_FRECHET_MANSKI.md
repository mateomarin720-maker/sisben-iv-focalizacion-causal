# Resultados — Cotas de Fréchet-Manski (ATE sin suponer independencia condicional)

Generado 2026-10-27 por `src/estimacion/cotas_frechet_manski.py`, refrescado
el 2026-10-28 tras corregir `viv_cuartos` y, horas después, tras reducir
el outcome de 10 a 8 privaciones (ver
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`). Ampliado el 2026-11-02
a `POBRE_MONETARIO` (ver sección propia abajo) y regenerado ese mismo día
tras corregir el bug de agosto (códigos `"1.0"` del `.DTA`, ver
CHANGELOG) y otra vez al sumar el nivel de pisos a la celda. Detalle por celda:
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
de `viv_cuartos` + nivel de pisos`), para que sea directamente comparable con el DML.
`Y = POBRE_GEIH` (binario). `T = 1{Grupo ∈ {A,B}}`, calculado directamente
sobre el archivo estandarizado del Sisbén (nacional + Bogotá), SIN pasar
por el Hot-Deck. Por celda: cota de Fréchet-Hoeffding sobre
`P(Y=1,T=1|X)` y `P(Y=1,T=0|X)`, de ahí cota sobre `E[Y|T=1,X]` y
`E[Y|T=0,X]`, resta para la cota del CATE(X), y agregación ponderada por
el peso poblacional de GEIH (`FEX_C18`) por celda.

## Resultado

| | Estimador | Rango |
|---|---|---|
| **Fréchet-Manski** (sin CIA) | Cota, no punto | **[−0,2607 ; +0,3801]** |
| **DML con Hot-Deck** (con CIA) | Punto + IC95% | ver `docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md` (el número no se hardcodea aquí para que no quede desactualizado si cambia el outcome o la celda) |

- Cobertura: 921 celdas con información de las dos fuentes (365 con la
  celda sin pisos), 100 % del peso poblacional de GEIH.
- Ancho de la cota Fréchet-Manski: **0,6409**. Historia: 0,986 antes de
  corregir `viv_cuartos`; 0,7267 con la celda correcta y 10 privaciones;
  0,7163 con 8 privaciones; 0,7344 tras corregir el bug de agosto; 0,6409
  con pisos en la celda (la celda más fina separa mejor hogares con y sin
  privaciones). Sigue cubriendo buena parte del rango posible de una
  diferencia de proporciones (de −1 a +1).
- Ancho del IC95 % del DML con celda exacta (`POBRE_GEIH`, ver
  `DIAGNOSTICO_W_CELDA_EXACTA.md`): 0,0047 — **~140 veces más angosto**
  que la cota Fréchet-Manski. Ese punto ≈0 es la prueba placebo del
  emparejamiento, no una estimación del efecto.
- **Ninguna celda tiene una cota que excluya el 0.** Las 130 celdas con
  `P(Y=1|X)` igual a 0 o 1 tienen cota exactamente [0; 0]; en 10 de ellas
  el CSV muestra un límite inferior de 2·10⁻¹⁶ por redondeo, que no es un
  efecto.

## Pobreza monetaria (`POBRE_MONETARIO`) — 2026-11-02

Mismo cálculo, misma celda, mismo `T`, con `Y = POBRE_MONETARIO` de la
reconstrucción de pobreza monetaria (`RESULTADOS_POBREZA_MONETARIA.md`;
regenerado al reemplazar el outcome anterior, que daba [−0,5817; +0,6877]).

| Outcome | P(Y=1) | Cota Fréchet-Manski (sin CIA) | Ancho | ATE DML, celda exacta (con CIA) |
|---|---|---|---|---|
| `POBRE_GEIH` | 0,204 | [−0,2607 ; +0,3801] | 0,6409 | −0,0026 [−0,0049 ; −0,0002] |
| `POBRE_MONETARIO` | 0,270 | **[−0,4179 ; +0,6477]** | **1,0656** | −0,0002 [−0,0036 ; +0,0033] |

- Cobertura: las mismas 921 celdas, 100 % del peso de GEIH.
- La cota de `POBRE_MONETARIO` es más ancha que la de `POBRE_GEIH` (1,07
  frente a 0,64, de un máximo posible de 2): las cotas de
  Fréchet-Hoeffding se ensanchan cuanto más cerca de 0,5 están las dos
  marginales.
- **Ninguna celda excluye el 0.** Las celdas con `P(Y=1|X)` = 1 (46) o = 0
  (54) tienen cota exactamente [0; 0] (16 aparecen con 2·10⁻¹⁶ por
  redondeo).
- Con pisos en la celda, las dos cotas se corren hacia valores positivos
  (antes [−0,41; +0,32] y [−0,54; +0,50]): dentro de cada celda, P(T) y
  P(Y) quedan más alineadas.

**Robustez con la clasificación oficial del DANE
(`POBRE_MONETARIO_OFICIAL`, 2026-11-02).** Solo existe para 24
departamentos y Bogotá (712 celdas, 99,0 % del peso de GEIH). En esas
celdas:

| Outcome | P(Y=1) | Cota Fréchet-Manski |
|---|---|---|
| `POBRE_MONETARIO` (reconstrucción) | 0,270 | [−0,418 ; +0,649] |
| `POBRE_MONETARIO_OFICIAL` | 0,258 | [−0,407 ; +0,620] |

La cota oficial es 0,04 más angosta porque la tasa es algo menor, y
tampoco identifica el signo. Detalle: `docs/reports/cotas_frechet_manski_pobre_monetario_oficial.csv`.

## Cómo leerlo

**Este es el resultado de identificación central del proyecto con los
datos actuales.** Sin suponer que el sorteo del Hot-Deck reproduce la
relación real entre clasificación y pobreza, los datos no fijan ni el
signo del efecto: pasar a A/B puede asociarse con entre 42 puntos menos
y 65 puntos más de pobreza monetaria. No es un fracaso del modelo: es lo
que dos fuentes sin llave común permiten decir.

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
- Los supuestos de monotonía se agregaron el 2026-11-04 (sección
  siguiente).

## Con supuestos de monotonía (2026-11-04)

**Qué acota cada cota.** Hay dos problemas superpuestos:

1. **La conjunta de T e Y no se observa** (las fuentes no tienen llave):
   P(Y=1, T=1) puede estar en cualquier punto entre los límites de
   Fréchet. Las cotas de arriba resuelven solo este problema: acotan el
   **contraste** E[Y|T=1] − E[Y|T=0], que es el ATE solo si no hay
   confusión dentro de la celda.
2. **Los resultados potenciales no se observan.** Sin suponer nada sobre
   ellos (Manski, 1990), el ATE tiene una cota más ancha que el contraste.

Los supuestos de Manski y Pepper (2000), con Y = pobre y T = clasificado
en A/B:

- **MTS (selección monótona):** los hogares A/B son al menos tan pobres
  como el resto en los dos resultados potenciales. Es lo que busca la
  focalización. Recorta la cota superior hasta el contraste.
- **MTR (respuesta monótona):** el programa no aumenta la pobreza de
  nadie. Recorta la cota superior a 0. **Fija el signo por supuesto, no
  por los datos.**
- **Dependencia positiva:** dentro de cada celda, los A/B son al menos
  tan pobres como el resto (P(Y=1, T=1) ≥ P(Y=1)·P(T=1)). Entre celdas
  se cumple: la correlación entre P(T | celda) y la pobreza de la celda es
  0,29 (`RESULTADOS_HOTDECK.md`). Es el único que sube la cota inferior.

Implementación: `cotas_con_supuestos` en `src/estimacion/cotas_frechet_manski.py`;
salida `docs/reports/cotas_frechet_manski_monotonia.csv`. Todas las cotas
son monótonas en P(Y=1, T=1), así que la unión sobre los valores
factibles se alcanza en los extremos de Fréchet.

| Cota del ATE (921 celdas) | `POBRE_GEIH` | Ancho | `POBRE_MONETARIO` | Ancho |
|---|---|---|---|---|
| Contraste (la de arriba) | [−0,261; +0,380] | 0,64 | [−0,418; +0,648] | 1,07 |
| Contraste + dependencia positiva | [0; +0,380] | 0,38 | [0; +0,648] | 0,65 |
| ATE sin supuestos | [−0,469; +0,765] | 1,23 | [−0,571; +0,829] | 1,40 |
| ATE con MTS | [−0,469; +0,380] | 0,85 | [−0,571; +0,648] | 1,22 |
| ATE con MTR | [−0,469; 0] | 0,47 | [−0,571; 0] | 0,57 |
| ATE con MTS y MTR | [−0,469; 0] | 0,47 | [−0,571; 0] | 0,57 |
| ATE con MTS, MTR y dependencia positiva | **[−0,367; 0]** | 0,37 | **[−0,405; 0]** | 0,41 |

Con la clasificación oficial del DANE (712 celdas), la última fila da
[−0,405; 0], igual que la reconstrucción.

**Lectura.**

1. **Con los tres supuestos, la cota se reduce a menos de un tercio**
   (de 1,40 a 0,41 en pobreza monetaria), pero el efecto puede seguir
   siendo cualquier cosa entre 0 y 40 puntos menos de pobreza. Los
   supuestos acotan, no identifican.
2. **El signo lo pone el MTR, no los datos.** Sin MTR, ninguna
   combinación excluye efectos positivos (que el programa aumente la
   pobreza).
3. **El MTS no agrega nada si ya se supone MTR**: solo baja la cota
   superior, y el MTR ya la deja en 0. Ninguno de los dos sube la cota
   inferior.
4. **Solo la dependencia positiva sube la cota inferior** (de −0,571 a
   −0,405), y es el supuesto más fácil de defender con datos: la
   focalización funciona entre celdas.
5. **El contraste con dependencia positiva es [0; +0,648]**: los A/B son
   al menos tan pobres como el resto, y el Hot-Deck (contraste ≈0 dentro
   de la celda) está en el borde de lo que permiten los datos.

**Validez.** `tests/test_cotas_frechet_manski.py` genera poblaciones al
azar que cumplen cada combinación de supuestos (5 semillas, miles de
poblaciones por combinación) y comprueba que el ATE verdadero cae
siempre dentro de su cota, que cada supuesto angosta o deja igual la
cota y que el contraste coincide con las cotas de Fréchet. Dos
mutaciones (dependencia positiva sin efecto y MTS mal aplicado) hacen
fallar las pruebas.

## Limitaciones

Las mismas de `RESULTADOS_DML_ATE_ATT_ATU.md`: outcome con 8 de 15
privaciones, pobreza monetaria reconstruida, selección del Sisbén, falta
DPS/RUI. Además:
`P(T|X)` del Sisbén se calcula sin ponderar (no es una encuesta con diseño
muestral, es un registro administrativo) — `P(Y|X)` de GEIH sí se pondera
por `FEX_C18`.
