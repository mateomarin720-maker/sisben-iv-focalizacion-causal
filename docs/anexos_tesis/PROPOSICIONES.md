# Proposiciones del enlace por celdas

Los tres resultados que el borrador muestra con ilustraciones (Hot-Deck con
efecto cero, atenuación con el vínculo parcial y la mitad de la varianza que
viene del sorteo) se pueden enunciar y probar. Las tres proposiciones se
comprueban por Monte Carlo en `src/diagnostico/proposiciones.py` (salida
[`docs/reports/proposiciones.txt`](../reports/proposiciones.txt), pruebas en
`tests/test_proposiciones.py`). La última sección deriva el ancho de la cota
de Fréchet-Manski de la sección 4.4.

## Notación

- C: celda del Hot-Deck (departamento, ciclo de vida del jefe, tramo de
  cuartos, pisos).
- En la celda c, q_c = P(T = 1 | C = c) en la fuente donante (Sisbén).
- T: grupo verdadero del hogar (A/B = 1). T̃: grupo imputado, el de un
  donante sorteado al azar en la celda del hogar.
- Y: resultado medido en la fuente receptora (GEIH).
- θ̂: contraste de Y sobre el tratamiento con efectos fijos de celda,
  θ̂ = Σᵢ (Tᵢ − T̄_c)(Yᵢ − Ȳ_c) / Σᵢ (Tᵢ − T̄_c)².
- El DML con la celda como controles estima el mismo momento,
  E[(T − E[T|C])(Y − E[Y|C])], con modelos auxiliares en lugar de medias
  de celda (Chernozhukov et al., 2018).

## Proposición 1: con T imputado, el efecto estimado es cero

**Enunciado.** Si T̃ se sortea dentro de la celda sin mirar Y (Hot-Deck),
entonces T̃ ⊥ Y | C, y todo estimador que controle por la celda converge a
cero, sea cual sea el efecto verdadero.

**Prueba.** El sorteo solo usa la celda: dado C = c, T̃ es Bernoulli(q_c)
e independiente de (Y, T). Entonces:

    Cov(T̃, Y | C) = E[(T̃ − q_C)(Y − E[Y|C]) | C] = E[T̃ − q_C | C] · E[Y − E[Y|C] | C] = 0

El numerador de θ̂ dividido por n converge a E[Cov(T̃, Y | C)] = 0. El
denominador converge a E[q_C(1 − q_C)] > 0. Por tanto θ̂ → 0. ∎

Es el supuesto de independencia condicional del *statistical matching*
(D'Orazio, Di Zio y Scanu, 2006; Rässler, 2002). El archivo fusionado lo
cumple por construcción, sea o no cierto en la población. Por eso el DML
sobre el grupo imputado es un placebo del emparejamiento y no estima el
efecto del Sisbén.

**Corolario.** Si los controles W son más gruesos que la celda (o la celda
entra como número), Cov(T̃, Y | W) = Cov(q_C, E[Y|C] | W) ≠ 0. El
estimador recoge entonces la correlación entre celdas (ecológica), no un
efecto. Es lo que pasaba con la celda como código numérico antes del
2026-11-02 (ATE +0,02 con IC sin el cero; ver `CLAUDE.md`).

**Comprobación.** Con un efecto verdadero de 0,10:

| | Contraste con T verdadero | Contraste con T imputado (200 sorteos) |
|---|---|---|
| Sin confusión en la celda | 0,115 | −0,0005 (error MC 0,0011) |
| Con confusión en la celda | 0,774 | −0,0005 (error MC 0,0011) |

Con datos reales, el contraste combinado de 100 sorteos es −0,000004 para
`POBRE_GEIH` (IC [−0,0033; +0,0033]).

## Proposición 2: la señal cae en proporción al enlace

**Enunciado.** Sea L la fracción de hogares que se enlazan con su registro
verdadero, elegidos al azar e independientes de (Y, T). El resto recibe T̃
imputado en su celda. Si T es ignorable dada la celda y el efecto es
constante (τ), el contraste con efectos fijos de celda converge a L·τ.

**Prueba.** Sea D ~ Bernoulli(L) la indicadora de enlace, con
T_obs = D·T + (1 − D)·T̃. Dentro de la celda c:

- Cov(T_obs, Y | c) = L·Cov(T, Y | c) + (1 − L)·Cov(T̃, Y | c) = L·Cov(T, Y | c),
  por la Proposición 1.
- Var(T_obs | c) = q_c(1 − q_c), porque T y T̃ tienen la misma
  distribución en la celda: el Hot-Deck preserva la marginal.

La pendiente dentro de la celda es L·Cov(T, Y | c)/Var(T | c) = L·τ. El
promedio ponderado por la varianza de las celdas también es L·τ. Con un
efecto heterogéneo, el límite es L por el promedio de τ ponderado por
q_c(1 − q_c). ∎

**Enlaces falsos.** Si el resto no se imputa en la celda sino que se enlaza
con un hogar cualquiera de la población (un error de enlace), T_obs en la
celda c es Bernoulli(m_c), con m_c = L·q_c + (1 − L)·q̄. El límite es

    τ · Σ_c n_c · L · q_c(1 − q_c) / Σ_c n_c · m_c(1 − m_c)

Es igual a L·τ cuando las celdas tienen la misma q_c, y algo menor cuando
difieren, porque el enlace falso agrega varianza a T sin agregar señal. Es
el sesgo hacia cero de la regresión con archivos enlazados con error
(Scheuren y Winkler, 1993; Lahiri y Larsen, 2005). Corregirlo exige conocer
la tasa de error del enlace; de ahí la petición al DNP sobre las tasas y la
calidad del enlace del Registro Social de Hogares.

**Comprobación** (100 poblaciones; las filas comparten poblaciones, así que
sus errores van juntos):

| Fracción enlazada | 0 | 0,25 | 0,50 | 0,75 | 1 |
|---|---|---|---|---|---|
| Resto imputado en la celda: factor simulado | −0,02 | 0,23 | 0,47 | 0,75 | 1,00 |
| Esperado (L) | 0 | 0,25 | 0,50 | 0,75 | 1 |
| Resto con enlace falso: factor simulado | 0,03 | 0,24 | 0,44 | 0,70 | 1,00 |
| Esperado (fórmula) | 0 | 0,20 | 0,42 | 0,68 | 1 |

Error Monte Carlo de cada factor: 0,013 a 0,018. En la simulación
semisintética\* (confusión observada, LinearDML), el vínculo del 50 % da
+0,040\* frente a +0,089\* del oráculo en log-ingreso (factor 0,45\*) y
−0,014\* frente a −0,031\* en pobreza (0,45\*). Que quede algo por debajo
de 0,5 es coherente con el sesgo de regularización que se ve con efecto
nulo (`SIMULACION_SEMISINTETICA.md`).

## Proposición 3: con imputación total, la mitad de la varianza es del sorteo

**Enunciado.** Con imputación total (ningún hogar enlazado), la varianza
entre sorteos B y la varianza dentro de cada sorteo U son iguales en
esperanza. La fracción de información perdida de Rubin (1987),
(1 + 1/M)·B / (U + (1 + 1/M)·B), tiende a (1 + 1/M)/(2 + 1/M) ≈ 0,5.

**Prueba.** Sean dᵢ = Yᵢ − Ȳ_c y S = Σ_c n_c q_c(1 − q_c). Como Σ_{i∈c} dᵢ = 0,
el numerador de θ̂ es Σᵢ T̃ᵢ dᵢ. Dados Y y las celdas, los T̃ᵢ son
Bernoulli(q_c) independientes, y el denominador se concentra en S. Entonces:

- Entre sorteos: B ≈ Var(Σᵢ T̃ᵢ dᵢ | Y) / S² = Σᵢ q_c(1 − q_c) dᵢ² / S².
- Dentro del sorteo: el error robusto (HC0) es U = Σᵢ (T̃ᵢ − T̄_c)² eᵢ² / S²,
  con eᵢ ≈ dᵢ porque θ̂ ≈ 0. Su esperanza dado Y es Σᵢ q_c(1 − q_c) dᵢ² / S².

Son la misma cantidad. ∎

Con imputación total, el IC de un solo sorteo usa √U cuando la varianza que
importa es U + B ≈ 2U: es demasiado estrecho en un factor √2. Por eso un
sorteo aislado puede dar un IC sin el cero, como el de `POBRE_GEIH` antes
de corregir la vivienda del IPM-GEIH por zona (−0,0026 [−0,0049; −0,0002];
con el indicador corregido, −0,0021 [−0,0045; +0,0004]).

**El rango 49 %-55 % es ruido, no tres resultados.** Con M sorteos, B se
estima con un error relativo de √(2/(M − 1)), unos 14 % con M = 100. La
fracción de una sola corrida varía entonces unos ±3 puntos alrededor de
0,5. En la tesis conviene reportarla por fila:

| Resultado | Fracción de la varianza que viene del sorteo |
|---|---|
| `POBRE_MONETARIO` | 48,9 % |
| `POBRE_GEIH` | 48,8 % |
| `log_ingreso_percapita` | 54,5 % |
| `ipm_geih_score` | no calculada: `variabilidad_hotdeck` combina solo estos tres |

Fuente: `docs/reports/variabilidad_hotdeck_estimacion.csv`.

**Comprobación.** En 20 poblaciones sintéticas con 100 sorteos cada una, la
razón B/U promedio es 1,00 y la fracción va de 0,45 a 0,58 (media 0,50).
Los tres valores reales caen en ese rango.

## La cota del ATE con dos fuentes no enlazadas (sección 4.4)

Manski (1990) acota el ATE de un resultado binario cuando T e Y se observan
en el mismo hogar. Esa cota tiene ancho 1:

    E[Y(1)] ∈ [P₁₁, P₁₁ + P(T=0)]        E[Y(0)] ∈ [P₁₀, P₁₀ + P(T=1)]
    ATE ∈ [2P₁₁ − p − e,  2P₁₁ − p − e + 1]

Aquí P₁₁ = P(Y=1, T=1), P₁₀ = P(Y=1, T=0), p = P(Y=1) y e = P(T=1).

Con las fuentes sin llave, P₁₁ tampoco se observa. Dentro de la celda,
Fréchet (1951) y Hoeffding (1940) la acotan con las dos marginales:

    max(0, p + e − 1) ≤ P₁₁ ≤ min(p, e),   de ancho Δ = min(p, e) − max(0, p + e − 1)

Los dos extremos de la cota de Manski crecen con 2P₁₁. La unión sobre
todos los P₁₁ factibles tiene entonces ancho **1 + 2Δ**, entre 1 y 2. Es
un problema de identificación doble: el de los resultados potenciales
(Manski) y el de la conjunta no observada (Fréchet). Por eso no basta la
cota clásica.

**Con los datos.** Con las 921 celdas de pobreza monetaria
(`cotas_frechet_manski_pobre_monetario.csv`, ponderadas por `fex`), el Δ
medio es 0,200. Entonces 1 + 2 × 0,200 = 1,40, el ancho publicado de
[−0,571; +0,829]. La cota de ancho 1 del marco teórico es la de bases
enlazadas.

La misma acotación de P₁₁ da los errores de focalización por celda sin
supuestos causales (`RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md`). Los
pobres no elegibles están entre max(0, p − e) y min(p, 1 − e). Agregados
con factores de expansión, el error de exclusión de A/B frente a pobreza
monetaria va de 0,9 % a 75,0 %, y el de inclusión de 38,6 % a 84,5 %.

\* Resultado simulado.

## Referencias

Las citas completas, verificadas, están en
[`BIBLIOGRAFIA_VERIFICADA.md`](BIBLIOGRAFIA_VERIFICADA.md): Chernozhukov et
al. (2018), D'Orazio, Di Zio y Scanu (2006), Fréchet (1951), Hoeffding
(1940), Lahiri y Larsen (2005), Manski (1990), Rässler (2002), Rubin (1987)
y Scheuren y Winkler (1993).
