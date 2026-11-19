# Imputación fraccional (FHDI) frente al Hot-Deck

Generado el 2026-11-18 por `src/emparejamiento/fhdi/` (reglas en su
`README.md`), con los datos del banco de Azure leídos en memoria. Salidas
en `docs/reports/`: `fhdi.txt` (consola), `fhdi_validacion.csv`,
`fhdi_comparacion.csv` y `fhdi_placebo.csv`. Son datos reales, no
simulados.

**Pregunta.** El Hot-Deck le da a cada hogar de la GEIH el grupo de un
donante sorteado en su celda. ¿Se puede hacer el enlace más exacto, o al
menos quitarle el ruido del sorteo, sin cambiar la celda?

**Cómo.** La misma celda y la misma cadena de respaldos del Hot-Deck; en
vez de un donante, 10 donantes por hogar, estratificados por grupo, con
pesos calibrados a la proporción de cada grupo en la celda (Kim y
Fuller, 2004), y FEFI (todos los donantes de la celda). 290.968 hogares
de la GEIH y 3.093.411 donantes del Sisbén con clasificación; 99,92 % en
celda exacta y 100 % de los hogares calibrados exactamente.

## 1. Cuánto puede acertar el enlace por celda

Validación dentro del Sisbén: se esconde el grupo del 20 % de los hogares
(618.907), se imputa con el resto como donantes y se compara con el grupo
verdadero.

| Método | Acierta A/B | Acierta el grupo A-D | Error cuadrático A/B (Brier) | Descalibración | Error en A/B por departamento (pp) |
|---|---|---|---|---|---|
| Sin celda (todo el registro) | 50,3 % | 26,2 % | 0,249 | 0,001 | 21,0 |
| Sorteo (Hot-Deck) | 73,0 % | 44,0 % | 0,270 | 0,270 | 0,92 |
| **Moda de la celda** | **80,5 %** | **55,2 %** | 0,195 | 0,195 | **13,5** |
| **FHDI (M = 10)** | 73,0 % (esperado) | 44,1 % (esperado) | **0,136** | **0,002** | **0,58** |
| FEFI | 73,0 % (esperado) | 44,1 % (esperado) | 0,136 | 0,002 | 0,58 |

Lectura:

- **El techo del enlace por celda es la moda: 80,5 % en A/B y 55,2 % en
  el grupo.** Ningún método que use solo la celda acierta más hogar por
  hogar. Ponderado por los hogares de la GEIH el techo es 78,4 % y el
  sorteo 70,3 % (la cifra de «dos sorteos coinciden en A/B» de
  `RESULTADOS_VARIABILIDAD_HOTDECK.md`). Agregar zona, paredes o sexo del
  jefe sube el techo entre 0,1 y 0,3 pp: lo que limita el enlace es la
  información común entre las fuentes, no el método.
- **La moda acierta más por hogar pero distorsiona la distribución:**
  le da a todos los hogares de una celda su grupo más frecuente, y la
  proporción de A/B por departamento se aleja 13,5 pp de la verdadera.
  Para la tesis, que estima incidencias y errores de focalización, es el
  peor de los métodos con celda.
- **La FHDI no acierta más que el sorteo, pero dice exactamente cuánto se
  sabe:** su probabilidad está calibrada (cuando dice 60 % de A/B, el 60 %
  lo es; descalibración 0,002), tiene el menor error cuadrático (0,136,
  la mitad del sorteo) y el menor error por departamento (0,58 pp).
- **FHDI y FEFI coinciden** en todas las medidas: con la calibración, 10
  donantes bastan.

## 2. Cantidades sobre la GEIH

| Cantidad | Hot-Deck (semilla 42) | Hot-Deck (media de 100 sorteos) | FHDI = FEFI | Error jackknife | Desviación entre sorteos |
|---|---|---|---|---|---|
| Grupo A | 14,93 % | 14,96 % | 14,95 % | 0,06 | 0,09 |
| Grupo B | 29,71 % | 29,75 % | 29,75 % | 0,05 | 0,14 |
| Grupo C | 33,75 % | 33,86 % | 33,88 % | 0,05 | 0,16 |
| Grupo D | 21,61 % | 21,43 % | 21,43 % | 0,06 | 0,13 |
| A/B | 44,63 % | | 44,70 % | 0,10 | |
| Exclusión (pobreza monetaria) | 33,57 % | | **33,76 %** | 0,17 | |
| Inclusión (pobreza monetaria) | 59,77 % | | **59,94 %** | 0,17 | |
| Exclusión (IPM-GEIH) | 28,49 % | | 28,35 % | 0,21 | |
| Inclusión (IPM-GEIH) | 76,79 % | | 76,78 % | 0,16 | |
| Pobreza monetaria en A/B | 40,23 % | | 40,06 % | 0,17 | |
| Pobreza monetaria en C/D | 16,39 % | | 16,50 % | 0,13 | |

Lectura:

- **La FHDI reproduce la media de los 100 sorteos** (diferencias de 0,02
  pp o menos) en una sola corrida, y su error estándar ya no tiene la
  parte del sorteo: la desviación entre sorteos (0,09 a 0,16 pp en los
  grupos) era mayor que el error muestral de la GEIH (0,05 a 0,06 pp).
- **Por departamento**, el sorteo guardado se aleja hasta 1,8 pp de FEFI
  en la proporción de A/B, y la desviación entre sorteos llega a 1,3 pp;
  la FHDI coincide con FEFI (diferencia máxima 0,00 pp).
- **Los errores de exclusión e inclusión de FEFI son exactamente el valor
  «con independencia» de `errores_focalizacion_frechet.py`** (33,76 % y
  59,94 % en pobreza monetaria), calculado por otro camino: es el punto
  que corresponde a suponer que, dentro de la celda, pobreza y grupo no
  se relacionan. Sigue dentro de las cotas de Fréchet, que no cambian
  (exclusión [2,8 %; 57,7 %], inclusión [41,2 %; 74,4 %]). La FHDI da un
  punto con su error, no estrecha la cota.

## 3. Contraste placebo: cero exacto

| Outcome | FHDI | Hot-Deck: 100 sorteos con Rubin | IC 95 % | Varianza por imputación |
|---|---|---|---|---|
| Pobreza monetaria | 0 | 0,0000 | [−0,0055; 0,0055] | 53 % |
| Pobreza IPM-GEIH | 0 | +0,0001 | [−0,0035; +0,0038] | 47 % |
| Log del ingreso per cápita | 0 | −0,0013 | [−0,0210; +0,0184] | 49 % |

Con los pesos calibrados, todos los hogares de una celda tienen la misma
proporción ponderada de A/B, así que el grupo imputado no varía entre
hogares dentro de la celda y la regresión con efectos fijos da 0 exacto.
Es la Proposición 1 sin ruido: el Hot-Deck llega a lo mismo en promedio
(los IC de Rubin contienen el 0), pero cada sorteo da un número distinto
y la mitad de su varianza es del sorteo.

## 4. Vínculo parcial en la simulación*: la recta de atenuación con las dos imputaciones

`src/simulacion/sensibilidad_semisintetica.py vinculo` (pregunta 5; salidas
`docs/reports/sensibilidad_vinculo_fhdi*.csv` y `.txt`). Hogares reales de
la GEIH con tratamiento y efecto simulados*, encuestas de 30.000 hogares,
288 repeticiones. A una fracción L de los hogares se le da su T verdadero;
al resto, el T de un donante sorteado (Hot-Deck) o la proporción de T = 1
de su celda (FHDI). Confusión observada, τ = 0,095*:

| L | Regresión, Hot-Deck | Regresión, FHDI | L·τ | LinearDML, Hot-Deck | LinearDML, FHDI |
|---|---|---|---|---|---|
| 0 | +0,000* | no identificable | 0 | −0,036* | no identificable |
| 0,25 | +0,023* | **+0,092*** | +0,024 | −0,012* | −0,071* |
| 0,50 | +0,046* | **+0,093*** | +0,047 | +0,014* | +0,005* |
| 0,75 | +0,069* | **+0,093*** | +0,071 | +0,036* | +0,034* |
| 1 | +0,092* | +0,092* | +0,095 | +0,061* | +0,061* |

- **Regresión con efectos fijos:** con Hot-Deck cae a L·τ (la recta de la
  Proposición 2); con FHDI recupera τ en todo L > 0, con cobertura de
  0,95-0,98 y más varianza cuanto menor es L. Con L = 0 no se identifica.
- **LinearDML con FHDI se sesga más que con Hot-Deck** (con efecto nulo,
  −0,161* con L = 0,25 frente a −0,036*). Hipótesis en
  `METODOLOGIA_FHDI.md` (P6): la parte imputada solo varía entre celdas y
  la regularización de LinearDML no quita del todo los efectos de celda
  con ≈8 hogares por celda.
- **Diagnóstico** (`vinculo_diagnostico`, 96 repeticiones). Sesgo con
  efecto nulo y L = 0,25:

| Hogares por celda | LinearDML, FHDI | LinearDML sin regularizar, FHDI | LinearDML, Hot-Deck | Regresión, FHDI |
|---|---|---|---|---|
| ≈8 (30.000 hogares) | −0,161* | −0,105* | −0,038* | +0,004* |
| ≈16 (60.000) | −0,091* | −0,052* | −0,017* | +0,001* |
| ≈32 (120.000) | −0,047* | −0,025* | −0,011* | +0,002* |

  El sesgo se reduce a la mitad cada vez que se duplican los hogares por
  celda; sin regularizar baja un tercio pero no desaparece, y crece como
  1/L. Es la parte de los efectos de celda que el ajuste cruzado no quita,
  concentrada en la poca variación de T que aportan los vinculados. La
  regresión con efectos fijos exactos no se sesga. Con los datos reales
  (78 hogares por celda) sería del orden de −0,016.

### LinearDML dentro de la celda (pregunta 7)

`sensibilidad_semisintetica.py intra_celda` (salidas
`docs/reports/sensibilidad_intra_celda*`): antes de LinearDML se resta la
media de la celda a Y, a T y a los controles, como en la regresión con
efectos fijos. 264 repeticiones, 30.000 hogares por encuesta. Confusión
observada, τ = 0,095*:

| L | Imputación | Regresión con efectos fijos | LinearDML vigente | LinearDML dentro de la celda | L·τ |
|---|---|---|---|---|---|
| 0 | Hot-Deck | +0,001* | −0,034* | +0,001* | 0 |
| 0,25 | Hot-Deck | +0,024* | −0,011* | +0,024* | +0,024 |
| 0,50 | Hot-Deck | +0,046* | +0,013* | +0,047* | +0,047 |
| 0,75 | Hot-Deck | +0,069* | +0,037* | +0,070* | +0,071 |
| 0,25 | FHDI | +0,093* | −0,067* | **+0,094*** | |
| 0,50 | FHDI | +0,093* | +0,007* | **+0,094*** | |
| 0,75 | FHDI | +0,091* | +0,034* | **+0,092*** | |
| 1 | (vínculo exacto) | +0,092* | +0,060* | **+0,094*** | +0,095 |

Con efecto nulo, LinearDML dentro de la celda da entre −0,003* y +0,001*
en todos los L y las dos imputaciones (la regresión, lo mismo); el
vigente, −0,035* a −0,037* con Hot-Deck y −0,160*, −0,088*, −0,063* con
FHDI y L = 0,25; 0,5; 0,75. Cobertura del IC 95 %: 0,93-0,96 dentro de la
celda (como la regresión) frente a 0,06-0,67 del vigente. Con Hot-Deck y
L < 1 la cobertura de τ es baja en los tres estimadores porque estiman
L·τ, no τ (la Proposición 2).

- Quitada la celda exactamente, LinearDML coincide con la regresión con
  efectos fijos: con FHDI recupera τ; con Hot-Deck, L·τ.
- Corrige también el sesgo del LinearDML vigente con vínculo exacto
  (+0,060* frente a τ = 0,095*). Adoptarlo movería las filas de LinearDML
  de la Tabla 6; por ahora no se cambió nada de lo vigente (decisión de la
  fase 2b, `METODOLOGIA_FHDI.md` P7).

## Conclusión

La FHDI es una alternativa al Hot-Deck que **no cambia ninguna conclusión
de la tesis** y quita el ruido de la imputación: reproduce en una
corrida la media de los 100 sorteos, con un error estándar que solo mide
la muestra de la GEIH, y da el contraste placebo como 0 exacto. **No hace
más exacto el enlace hogar por hogar:** el techo con la celda actual es la
moda (80,5 % en A/B dentro del Sisbén; 78,4 % ponderado por la GEIH), y
asignarla distorsiona las incidencias. Subir ese techo exige más
información común entre las fuentes o una llave, no otro método de
imputación.

Supuesto que se mantiene: el mismo del Hot-Deck, que dentro de la celda
el grupo del Sisbén no depende de la pobreza medida en la GEIH. La
validación interna mide lo bien que la celda predice el grupo en el
Sisbén; no mide si la GEIH y el Sisbén registran igual las variables de
la celda (eso lo cubre la homologación, `RESULTADOS_HOTDECK.md`).
