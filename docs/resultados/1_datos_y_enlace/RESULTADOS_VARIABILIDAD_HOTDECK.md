# Variabilidad de la imputación del Hot-Deck

Generado 2026-11-04 por `src/diagnostico/variabilidad_hotdeck.py`
(prioridad 1 de `docs/seguimiento/SEGUIMIENTO_TESIS_2026-11-04.md`,
pregunta del tutor del 2026-11-03). Salidas en `docs/reports/`:
`variabilidad_hotdeck.txt` (consola), `_celdas.csv` (por celda),
`_agregados.csv` (nacional y por departamento) y `_estimacion.csv`
(contraste placebo con reglas de Rubin). Regenerado el 2026-11-15 con
la celda que suma personas y menores de 18 años (3.721 celdas); las
cifras con la celda del 2026-11-02 (993 celdas) van entre paréntesis
donde ayudan a comparar.

**Pregunta.** El Hot-Deck sortea, para cada hogar de la GEIH, un donante
del Sisbén de su misma celda. ¿Cuánto cambia el resultado si el sorteo se
repite con otra semilla?

**Cómo.** La misma función `hotdeck()` del pipeline, sobre los mismos
290.968 hogares GEIH y 3.106.489 donantes, con **100 semillas**. La
semilla 42 es la del pipeline y reproduce el grupo guardado en el 100 %
de los hogares. Son datos reales: la variabilidad medida es la de la
imputación que usa el proyecto, no una simulación.

## 1. Por hogar: el grupo imputado no es estable

| Medida (ponderada por `fex`) | Resultado | Teórico de la celda |
|---|---|---|
| Probabilidad de que dos sorteos den el mismo grupo | **41,2 %** (34,4 %) | 41,2 % |
| Probabilidad de que dos sorteos coincidan en A/B | **70,3 %** (62,7 %) | 70,3 % |
| Hogares con el mismo grupo en los 100 sorteos | 0,07 % | |
| Hogares con el mismo estado A/B en los 100 sorteos | 0,85 % | |
| Hogares con P(A/B) ≤ 0,1 o ≥ 0,9 (casi seguro) | 31,6 % (7,8 %) | |
| Hogares con P(A/B) entre 0,3 y 0,7 (incierto) | 28,9 % (39,1 %) | |

La concordancia teórica de un hogar es Σ_g π_g², con π_g la proporción de
donantes de su celda en el grupo g: la probabilidad de que dos donantes
sorteados al azar compartan grupo. La empírica (estimador insesgado con
los 100 sorteos) la reproduce en el agregado y hogar por hogar
(correlación 0,93). **El grupo de cada hogar es un sorteo**: lo que el
Hot-Deck fija es la probabilidad, no el grupo. Con personas y menores en
la celda, los donantes de cada celda son más parecidos entre sí: el
grupo se repite más y cuatro veces más hogares tienen un estado A/B casi
seguro.

## 2. Por celda: proporciones estables, salvo en celdas pequeñas

Proporción de hogares GEIH en A/B dentro de cada celda (3.623 celdas con
receptores; 985 con la celda anterior), en cada sorteo, frente a la
proporción A/B de los donantes de la celda:

| Medida | Mediana entre celdas | Ponderada por población | Percentil 90 |
|---|---|---|---|
| Coeficiente de variación (sd / media entre sorteos) | 0,149 (0,091) | 0,106 (0,049) | 0,484 |
| Error relativo medio, \|p_sorteo − π\| / π | 0,114 (0,072) | 0,085 (0,039) | |

| Hogares GEIH en la celda | Celdas | CV mediano | Error relativo mediano |
|---|---|---|---|
| Menos de 30 | 2.473 | 0,200 | 0,147 |
| 30-99 | 567 | 0,109 | 0,087 |
| 100-299 | 354 | 0,082 | 0,065 |
| 300-999 | 169 | 0,073 | 0,059 |
| 1.000 o más | 60 | 0,068 | 0,053 |

- La variación cae con el tamaño de la celda, como en un muestreo
  binomial (CV ≈ √((1 − π) / (n π))).
- 2.330 celdas tienen CV > 0,1 y suman el **41,9 %** de la población
  (6,7 % con la celda anterior); las 1.423 con CV > 0,2, el 10,7 %. Dos de
  cada tres celdas tienen menos de 30 hogares GEIH: ahí cualquier
  proporción por celda es ruidosa. Es el costo de la celda más fina: más
  información por hogar, menos hogares por celda.
- Ponderado por población, el error relativo frente a los donantes es
  de 8,5 % (3,9 % con la celda anterior). Las proporciones por celda
  sirven para agregar, no para leerlas una por una.

## 3. Agregados: las cifras publicadas apenas se mueven

| Grupo (nacional, % ponderado) | Media | Desviación | CV | Mínimo-máximo | Semilla 42 (publicada) |
|---|---|---|---|---|---|
| A | 14,96 | 0,10 | 0,006 | 14,67-15,22 | 14,93 |
| B | 29,75 | 0,14 | 0,005 | 29,48-30,07 | 29,71 |
| C | 33,86 | 0,16 | 0,005 | 33,43-34,16 | 33,75 |
| D | 21,44 | 0,13 | 0,006 | 21,17-21,80 | 21,62 |

Por departamento, la proporción A/B tiene CV de 0,006 (Caquetá) a 0,041
(San Andrés). Los rangos más amplios entre sorteos están en los
departamentos con menos hogares en la GEIH: Vichada 6,0 puntos (1.123
hogares), Amazonas 5,8, Guaviare 5,2, Casanare 5,2. En los grandes es de
2 puntos o menos (Bogotá 1,7). Los agregados se mueven igual que con la
celda anterior: la celda más fina no los vuelve inestables.

## 4. Consecuencia para la estimación: el único resultado "significativo" es suerte del sorteo

Contraste placebo (regresión de la pobreza sobre A/B con efectos fijos de
celda) en cada sorteo, combinado con las reglas de Rubin (1987) para
imputación múltiple: varianza total = varianza dentro + (1 + 1/m) ×
varianza entre sorteos.

| Outcome | Semilla 42 [error] | Media de 100 sorteos | IC 95 % con Rubin | Varianza de la imputación / total | Sorteos con IC sin el 0 |
|---|---|---|---|---|---|
| `POBRE_MONETARIO` | −0,0002 [0,0019] | +0,0000 | [−0,0055; +0,0055] | 53 % | 4 % |
| `POBRE_GEIH` | −0,0003 [0,0014] | +0,0001 | [−0,0035; +0,0038] | 47 % | 4 % |
| log-ingreso per cápita | +0,0029 [0,0073] | −0,0013 | [−0,0210; +0,0184] | 49 % | 7 % |

- Con la celda anterior y la semilla 42, `POBRE_GEIH` daba −0,0024 con un
  IC al borde del cero (antes de corregir la vivienda del IPM-GEIH por
  zona, −0,0030, y lo excluía, igual que el DML con la celda exacta). En
  los 100 sorteos la media era −0,000004 y solo el 4 % excluía el cero.
  Con la celda nueva la semilla 42 da −0,0003, la media +0,0001 y de nuevo
  el 4 % de los sorteos excluye el cero, lo que el azar produce por sí
  solo con un 5 % de error. **Un resultado al borde con una semilla es
  suerte del sorteo, no señal.**
- **Cerca de la mitad de la varianza total viene de la imputación** (47-53
  %). Los intervalos que se calculan con un solo sorteo, como los del DML
  de `5_estimacion.py`, no la incluyen: en `POBRE_GEIH` el error que
  corresponde es 0,0019 y el de un solo sorteo 0,0014 (un 27 % más
  angosto; el correcto es un 36 % mayor).
  Por resultado: `POBRE_MONETARIO` 53,2 %, `POBRE_GEIH` 46,7 % y
  `log_ingreso_percapita` 48,6 %. Que sea cerca de la mitad no es
  casualidad: con imputación total, la varianza entre sorteos iguala a la
  de dentro del sorteo (Proposición 3, `docs/anexos_tesis/PROPOSICIONES.md`).
  Con 100 sorteos, la fracción estimada varía unos ±3 puntos alrededor de
  0,5, así que las tres cifras son el mismo resultado.

## Respuesta a la pregunta del tutor

- **A nivel de hogar, la imputación es inestable por diseño:** dos
  sorteos coinciden en el grupo de un hogar solo el 41 % de las veces, y
  en A/B el 70 % (34 % y 63 % con la celda anterior). Esa es exactamente la probabilidad que implica la
  composición de los donantes de cada celda; no es un error del código.
- **A nivel de departamento y país, es estable:** CV del 0,5 % al 0,6 %
  en la distribución nacional. Por celda, el error relativo ponderado
  sube a 8,5 % porque la celda nueva tiene menos hogares por celda. El
  Hot-Deck reproduce distribuciones, no hogares.
- **Para cualquier estimación con el grupo imputado** hay que repetir el
  sorteo y combinar con Rubin: con un solo sorteo, los intervalos son
  demasiado angostos y aparecen "efectos" que dependen de la semilla.

## Limitaciones

- La variabilidad medida es solo la del sorteo dentro de la celda; no
  incluye la incertidumbre de la elección de la celda ni el error de
  muestreo de la GEIH.
- El contraste placebo usa una regresión con efectos fijos, no el DML
  completo (más costoso de repetir 100 veces); con la semilla 42 dan lo
  mismo dentro de su error (−0,0003 frente a +0,0009; ver también
  `comparar_estimadores_celda.py`).
- El 0,02 % de los hogares que cae a una celda de respaldo se cuenta en
  su celda exacta, que no tiene donantes (sin concordancia teórica).

## Para reproducir

```bash
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.diagnostico.variabilidad_hotdeck 2 > docs/reports/variabilidad_hotdeck.txt 2>&1
poetry run pytest tests/test_variabilidad_hotdeck.py
```

El argumento es el número de procesos (cada uno carga los 3,1 millones
de donantes: con 2 caben en ~5 GB de RAM libre). Tarda ≈23 minutos
(≈20 s por sorteo).
