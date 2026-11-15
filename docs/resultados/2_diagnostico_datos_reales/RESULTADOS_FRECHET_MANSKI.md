# Resultados — Cotas de Fréchet-Manski (ATE sin suponer independencia condicional)

Generado 2026-10-27 por `src/diagnostico/cotas_frechet_manski.py`, refrescado
el 2026-10-28 tras corregir `viv_cuartos` y, horas después, tras reducir
el outcome de 10 a 8 privaciones (ver
`docs/metodologia/METODOLOGIA_INDICADOR_IPM_GEIH.md`). Ampliado el 2026-11-02
a `POBRE_MONETARIO` (ver sección propia abajo) y regenerado ese mismo día
tras corregir el bug de agosto (códigos `"1.0"` del `.DTA`, ver
CHANGELOG) y otra vez al sumar el nivel de pisos a la celda; el
2026-11-14, al sumar personas del hogar y menores de 18 años. Detalle por celda:
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
de `viv_cuartos` + nivel de pisos + personas + menores`), para que sea directamente comparable con el DML.
`Y = POBRE_GEIH` (binario). `T = 1{Grupo ∈ {A,B}}`, calculado directamente
sobre el archivo estandarizado del Sisbén (nacional + Bogotá), SIN pasar
por el Hot-Deck. Por celda: cota de Fréchet-Hoeffding sobre
`P(Y=1,T=1|X)` y `P(Y=1,T=0|X)`, de ahí cota sobre `E[Y|T=1,X]` y
`E[Y|T=0,X]`, resta para la cota del CATE(X), y agregación ponderada por
el peso poblacional de GEIH (`FEX_C18`) por celda.

## Resultado

| | Estimador | Rango |
|---|---|---|
| **Fréchet-Manski** (sin CIA) | Cota, no punto | **[−0,2595 ; +0,3082]** |
| **DML con Hot-Deck** (con CIA) | Punto + IC95% | ver `docs/resultados/2_diagnostico_datos_reales/RESULTADOS_DML_ATE_ATT_ATU.md` (el número no se hardcodea aquí para que no quede desactualizado si cambia el outcome o la celda) |

- Cobertura: 3.217 celdas con información de las dos fuentes y P(T | celda)
  distinta de 0 y 1 (921 con la celda del 2026-11-02; 365 sin pisos),
  99,8 % del peso poblacional de GEIH. El 0,2 % restante está en celdas
  donde todos los donantes son A/B o ninguno lo es: ahí el contraste no
  está definido.
- Ancho de la cota Fréchet-Manski: **0,5677**. Historia: 0,986 antes de
  corregir `viv_cuartos`; 0,7267 con la celda correcta y 10 privaciones;
  0,7163 con 8 privaciones; 0,7344 tras corregir el bug de agosto; 0,6409
  con pisos en la celda (la celda más fina separa mejor hogares con y sin
  privaciones); 0,5340 con la vivienda del IPM-GEIH corregida por zona
  (2026-11-12: la tasa de pobres baja de 20,4 % a 14,5 %); 0,5677 con
  personas y menores en la celda (2026-11-14). En `POBRE_GEIH` el
  contraste se abre un poco porque la celda más fina tiene más celdas con
  P(Y) cerca de 0,5 frente a P(T), pero la cota del ATE sin supuestos se
  cierra (1,19 → 1,16; ver la tabla de monotonía). Sigue cubriendo buena
  parte del rango posible de una diferencia de proporciones (de −1 a +1).
- Ancho del IC95 % del DML con celda exacta (`POBRE_GEIH`, ver
  `DIAGNOSTICO_W_CELDA_EXACTA.md`): 0,0055 — **~100 veces más angosto**
  que la cota Fréchet-Manski. Ese punto ≈0 es la prueba placebo del
  emparejamiento, no una estimación del efecto.
- **Ninguna celda tiene una cota que excluya el 0.** Las 907 celdas con
  `P(Y=1|X)` igual a 0 o 1 (en su mayoría celdas con pocos hogares GEIH)
  tienen cota exactamente [0; 0]; en 66 de ellas el CSV muestra un límite
  inferior de 2·10⁻¹⁶ por redondeo, que no es un efecto.

## Pobreza monetaria (`POBRE_MONETARIO`) — 2026-11-02

Mismo cálculo, misma celda, mismo `T`, con `Y = POBRE_MONETARIO` de la
reconstrucción de pobreza monetaria (`RESULTADOS_POBREZA_MONETARIA.md`;
regenerado al reemplazar el outcome anterior, que daba [−0,5817; +0,6877]).

| Outcome | P(Y=1) | Cota Fréchet-Manski (sin CIA) | Ancho | ATE DML, celda exacta (con CIA) |
|---|---|---|---|---|
| `POBRE_GEIH` | 0,144 | [−0,2595 ; +0,3082] | 0,5677 | +0,0009 [−0,0018 ; +0,0037] |
| `POBRE_MONETARIO` | 0,270 | **[−0,3605 ; +0,6365]** | **0,9970** | +0,0017 [−0,0021 ; +0,0055] |

- Cobertura: las mismas 3.217 celdas, 99,8 % del peso de GEIH.
- Con personas y menores la cota de `POBRE_MONETARIO` se cierra de 1,07
  (921 celdas) a 1,00, sobre todo por abajo (−0,418 → −0,361).
- La cota de `POBRE_MONETARIO` es más ancha que la de `POBRE_GEIH` (1,00
  frente a 0,57, de un máximo posible de 2; 0,64 antes de corregir la
  vivienda del IPM-GEIH por zona): las cotas de
  Fréchet-Hoeffding se ensanchan cuanto más cerca de 0,5 están las dos
  marginales.
- **Ninguna celda excluye el 0.** Las 675 celdas con `P(Y=1|X)` igual a
  0 o 1 tienen cota exactamente [0; 0] (84 aparecen con 2·10⁻¹⁶ por
  redondeo).
- Con pisos en la celda, las dos cotas se corren hacia valores positivos
  (antes [−0,41; +0,32] y [−0,54; +0,50]): dentro de cada celda, P(T) y
  P(Y) quedan más alineadas.

**Robustez con la clasificación oficial del DANE
(`POBRE_MONETARIO_OFICIAL`, 2026-11-02).** Solo existe para 24
departamentos y Bogotá (2.666 celdas, 98,9 % del peso de GEIH; 712 con
la celda del 2026-11-02). La cota oficial es [−0,359 ; +0,619] (ancho
0,978), casi la misma que la de la reconstrucción en todo el país
([−0,361 ; +0,637]): tampoco identifica el signo. Detalle: `docs/reports/cotas_frechet_manski_pobre_monetario_oficial.csv`.

## Cómo leerlo

**Este es el resultado de identificación central del proyecto con los
datos actuales.** Sin suponer que el sorteo del Hot-Deck reproduce la
relación real entre clasificación y pobreza, los datos no fijan ni el
signo del efecto: pasar a A/B puede asociarse con entre 36 puntos menos
y 64 puntos más de pobreza monetaria. No es un fracaso del modelo: es lo
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

- Esta primera corrida cubre solo outcomes binarios. Los continuos
  (`ipm_geih_score`, `log_ingreso_percapita`) y los demás parámetros de
  los modelos se agregaron el 2026-11-09 (sección "Una cota por cada
  número de los modelos").
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
  0,41 (0,29 con la celda del 2026-11-02; `RESULTADOS_HOTDECK.md`). Es
  el único que sube la cota inferior.

Implementación: `cotas_con_supuestos` en `src/diagnostico/cotas_frechet_manski.py`;
salida `docs/reports/cotas_frechet_manski_monotonia.csv`. Todas las cotas
son monótonas en P(Y=1, T=1), así que la unión sobre los valores
factibles se alcanza en los extremos de Fréchet.

| Cota del ATE (3.217 celdas) | `POBRE_GEIH` | Ancho | `POBRE_MONETARIO` | Ancho |
|---|---|---|---|---|
| Contraste (la de arriba) | [−0,260; +0,308] | 0,57 | [−0,361; +0,637] | 1,00 |
| Contraste + dependencia positiva | [0; +0,308] | 0,31 | [0; +0,637] | 0,64 |
| ATE sin supuestos | [−0,465; +0,695] | 1,16 | [−0,489; +0,808] | 1,30 |
| ATE con MTS | [−0,465; +0,308] | 0,77 | [−0,489; +0,637] | 1,13 |
| ATE con MTR | [−0,465; 0] | 0,46 | [−0,489; 0] | 0,49 |
| ATE con MTS y MTR | [−0,465; 0] | 0,46 | [−0,489; 0] | 0,49 |
| ATE con MTS, MTR y dependencia positiva | **[−0,384; 0]** | 0,38 | **[−0,359; 0]** | 0,36 |

Con la clasificación oficial del DANE (2.666 celdas), la última fila da
[−0,362; 0], casi igual que la reconstrucción. Con la celda del
2026-11-02 (921 celdas), la cota sin supuestos de `POBRE_MONETARIO` era
[−0,571; +0,829] (ancho 1,40) y la de los tres supuestos [−0,405; 0]:
personas y menores cierran 0,10 la primera y 0,05 la segunda.

**Lectura.**

1. **Con los tres supuestos, la cota se reduce a menos de un tercio**
   (de 1,30 a 0,36 en pobreza monetaria), pero el efecto puede seguir
   siendo cualquier cosa entre 0 y 36 puntos menos de pobreza. Los
   supuestos acotan, no identifican.
2. **El signo lo pone el MTR, no los datos.** Sin MTR, ninguna
   combinación excluye efectos positivos (que el programa aumente la
   pobreza).
3. **El MTS no agrega nada si ya se supone MTR**: solo baja la cota
   superior, y el MTR ya la deja en 0. Ninguno de los dos sube la cota
   inferior.
4. **Solo la dependencia positiva sube la cota inferior** (de −0,489 a
   −0,359), y es el supuesto más fácil de defender con datos: la
   focalización funciona entre celdas.
5. **El contraste con dependencia positiva es [0; +0,637]**: los A/B son
   al menos tan pobres como el resto, y el Hot-Deck (contraste ≈0 dentro
   de la celda) está en el borde de lo que permiten los datos.

**Validez.** `tests/test_cotas_frechet_manski.py` genera poblaciones al
azar que cumplen cada combinación de supuestos (5 semillas, miles de
poblaciones por combinación) y comprueba que el ATE verdadero cae
siempre dentro de su cota, que cada supuesto angosta o deja igual la
cota y que el contraste coincide con las cotas de Fréchet. Dos
mutaciones (dependencia positiva sin efecto y MTS mal aplicado) hacen
fallar las pruebas.

## Una cota por cada número de los modelos (2026-11-09)

Hasta aquí, la cota acompañaba solo al ATE de los resultados binarios.
`src/diagnostico/cotas_frechet_modelos.py` pone una cota al lado de
**cada parámetro que reportan el DML y el Causal Forest**, en los cinco
resultados. Así se ve, número por número, cuánto aportan los datos y
cuánto el supuesto del Hot-Deck. Salida: `docs/reports/cotas_frechet_modelos.csv`.

**Qué se acota.** Lo mismo que estima el DML con la celda: el contraste
E[Y | A/B, celda] − E[Y | resto, celda], agregado como cada parámetro.
Se mantiene el supuesto de que dentro de la celda no hay confusión, y se
quita solo el del vínculo: qué hogares de la GEIH son los A/B.

| Parámetro | Agregación de las cotas por celda |
|---|---|
| ATE | peso de la celda en GEIH |
| ATT | peso × P(A/B \| celda): dónde están los A/B |
| ATU | peso × P(resto \| celda) |
| CATE por subgrupo | celda × subgrupo, con P(A/B) del Sisbén en ese mismo subgrupo |

Los subgrupos son las X del Causal Forest, con el mismo código en las dos
fuentes:
- zona: 1 = urbano en ambas;
- sexo del jefe: 1 = hombre y 2 = mujer, en la ficha del Sisbén IV
  (pregunta 47) y en GEIH (`P3271`);
- paredes: en la escala común de `HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`.

**Resultados continuos.** En cada celda, el acople extremo pone a los A/B
en una cola de la distribución de Y y al resto en la otra (media de la
fracción P(A/B) más alta menos media del resto más bajo, y al revés). Con
Y binaria coincide con la fórmula de Fréchet de arriba (prueba en
`tests/test_cotas_frechet_modelos.py`). Las cotas binarias del ATE
reproducen exactamente las de las secciones anteriores.

### Lado a lado con los modelos (celda exacta)

| Resultado | Parámetro | DML [IC 95 %] | Cota de Fréchet | Ancho de la cota / ancho del IC |
|---|---|---|---|---|
| `ipm_geih_score` (0-8) | ATE | +0,004 [−0,004; +0,012] | [−1,33; +1,48] | ≈180 |
| | ATT | +0,005 | [−1,63; +1,49] | |
| | ATU | +0,003 | [−1,10; +1,47] | |
| `POBRE_GEIH` | ATE | +0,001 [−0,002; +0,004] | [−0,26; +0,31] | ≈100 |
| | ATT | +0,001 | [−0,42; +0,31] | |
| | ATU | +0,001 | [−0,13; +0,31] | |
| `log_ingreso_percapita` | ATE | +0,001 [−0,013; +0,016] | [−2,55; +1,82] | ≈150 |
| | ATT | +0,003 | [−1,58; +1,84] | |
| | ATU | −0,000 | [−3,33; +1,81] | |
| `POBRE_MONETARIO` | ATE | +0,002 [−0,002; +0,006] | [−0,36; +0,64] | ≈130 |
| | ATT | +0,002 | [−0,49; +0,58] | |
| | ATU | +0,001 | [−0,25; +0,69] | |
| `POBRE_MONETARIO_OFICIAL` | ATE | +0,001 [−0,003; +0,005] | [−0,36; +0,62] | ≈130 |

Cifras del DML: `RESULTADOS_DML_ATE_ATT_ATU.md`; sus IC no incluyen la
varianza del sorteo del Hot-Deck (`RESULTADOS_VARIABILIDAD_HOTDECK.md`).

### CATE por subgrupo (las X del Causal Forest)

| Subgrupo | `POBRE_GEIH` | `POBRE_MONETARIO` | `ipm_geih_score` | `log_ingreso_percapita` |
|---|---|---|---|---|
| Urbana | [−0,18; +0,25] | [−0,32; +0,68] | [−1,19; +1,41] | [−2,91; +1,80] |
| Rural | [−0,50; +0,50] | [−0,46; +0,46] | [−1,69; +1,51] | [−1,47; +1,73] |
| Jefe hombre | [−0,24; +0,34] | [−0,34; +0,61] | [−1,28; +1,55] | [−2,54; +1,71] |
| Jefe mujer | [−0,27; +0,28] | [−0,37; +0,66] | [−1,27; +1,36] | [−2,59; +1,88] |
| Paredes de ladrillo | [−0,23; +0,28] | [−0,35; +0,65] | [−1,25; +1,44] | [−2,69; +1,76] |
| Tapia o bahareque | [−0,42; +0,48] | [−0,41; +0,50] | [−1,41; +1,34] | [−1,22; +1,86] |
| Paredes precarias | [−0,37; +0,56] | [−0,42; +0,50] | [−1,68; +1,57] | [−1,36; +2,13] |

El Causal Forest da CATE de ±0,01 en todos estos subgrupos
(`RESULTADOS_CAUSALFOREST_CATE.md`).

**Celdas pequeñas.** Con pocos hogares en una celda, P(Y) sale 0 o 1 y
la cota se cierra en [0; 0] por azar de muestreo. Repetido solo con
celdas de al menos 30 hogares en cada fuente (1.096 de 3.217 celdas,
92,7 % del peso; con la celda del 2026-11-02 eran 547 de 921 y 98,5 %),
las cotas del ATE en pobreza cambian menos de 0,01 (pobreza monetaria
[−0,353; +0,645] frente a [−0,361; +0,637]); en el log-ingreso, el
límite inferior sube 0,09. Las cotas no se angostan de forma artificial:
la celda más fina cierra la cota por información, no por celdas
pequeñas que caen en [0; 0].

### Lectura

1. **Ninguno de los 50 parámetros acotados excluye el cero** (5
   resultados × ATE, ATT, ATU y 7 subgrupos). La conclusión de la
   sección anterior no depende del parámetro, del resultado ni del
   subgrupo.
2. **Toda la precisión de los modelos viene del supuesto del vínculo.**
   Las cotas son entre 100 y 180 veces más anchas que los IC del DML. En
   el IPM, el efecto puede ir de 1,3 privaciones menos a 1,5 más; en el
   ingreso per cápita, de dividirlo por casi 13 a multiplicarlo por 6.
3. **El ATT tiene la cota más ancha en pobreza** porque pesa más las
   celdas con muchos A/B, donde P(A/B) está más cerca de 0,5 y el acople
   es más libre.
4. **Lo urbano es lo menos incierto:** en `POBRE_GEIH` la cota urbana
   mide 0,43 y la rural 1,00. La incertidumbre del vínculo se concentra
   en lo rural.
5. **El CATE del Causal Forest no informa sobre heterogeneidad real.**
   Sus diferencias entre subgrupos (±0,01) son del orden de 1 % del ancho
   de las cotas de cada subgrupo.

## Limitaciones

Las mismas de `RESULTADOS_DML_ATE_ATT_ATU.md`: outcome con 8 de 15
privaciones, pobreza monetaria reconstruida, selección del Sisbén, falta
DPS/RUI. Además:
`P(T|X)` del Sisbén se calcula sin ponderar (no es una encuesta con diseño
muestral, es un registro administrativo) — `P(Y|X)` de GEIH sí se pondera
por `FEX_C18`.
