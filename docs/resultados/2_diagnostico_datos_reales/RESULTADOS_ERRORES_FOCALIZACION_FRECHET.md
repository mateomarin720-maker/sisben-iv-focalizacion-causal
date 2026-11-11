# Resultados — Errores de inclusión y exclusión del Sisbén con datos reales

Generado el 2026-11-10 por `src/diagnostico/errores_focalizacion_frechet.py`.
Detalle nacional y por departamento: `docs/reports/errores_focalizacion_frechet.csv`;
salida de consola: `docs/reports/errores_focalizacion_frechet.txt`.

## La pregunta

¿Qué parte de los hogares pobres queda fuera de los grupos A y B del
Sisbén (error de exclusión), y qué parte de los A/B no es pobre (error de
inclusión)? Hasta ahora estas tasas solo se habían reportado en el mundo
simulado (`RESULTADOS_REGLAS_FOCALIZACION.md`). Con datos reales no se
pueden contar, porque ningún hogar está a la vez en la GEIH (que dice
quién es pobre) y en el Sisbén (que dice quién es A/B).

## Método (propuesto por el director)

En cada celda c del Hot-Deck (departamento, ciclo de vida del jefe,
cuartos y nivel de pisos; 993 celdas) se conocen la proporción de pobres
p (GEIH, con factor de expansión) y la proporción de elegibles e
(Sisbén). Sin suponer nada sobre cómo se relacionan dentro de la celda,
las cotas de Fréchet dan:

$$\max(0,\,p-e) \le P(\text{pobre}=1,\ \text{elegible}=0 \mid c) \le \min(p,\,1-e)$$

$$\max(0,\,e-p) \le P(\text{pobre}=0,\ \text{elegible}=1 \mid c) \le \min(1-p,\,e)$$

Sumando con los factores de expansión de la GEIH salen las tasas
nacionales y departamentales, con las mismas definiciones de las reglas
simuladas:

- error de exclusión = pobres no elegibles / pobres;
- error de inclusión = elegibles no pobres / elegibles.

Los denominadores se conocen (Σ w·p y Σ w·e), así que la cota de cada
tasa es la de su numerador dividida por él. Como referencia se da el
valor con independencia dentro de la celda, p·(1 − e), que es el que
produce el Hot-Deck al sortear el grupo al azar en la celda.

Elegible = grupos A y B (el tratamiento del resto del proyecto); como
robustez, A, B y C. Unidad: hogares.

## Resultado nacional

| Elegible | Pobreza | Error de exclusión | Con independencia | Error de inclusión | Con independencia |
|---|---|---|---|---|---|
| A-B | Monetaria | **[0,9 %; 75,0 %]** | 44,3 % | **[38,6 %; 84,5 %]** | 65,5 % |
| A-B | IPM-GEIH | [0,8 %; 58,0 %] | 33,2 % | [53,5 %; 80,3 %] | 68,7 % |
| A-B | Monetaria oficial (24 deptos.) | [0,7 %; 75,0 %] | 43,9 % | [41,2 %; 85,2 %] | 66,8 % |
| A-B-C | Monetaria | [0,0 %; 50,0 %] | 16,0 % | [65,3 %; 82,7 %] | 70,9 % |
| A-B-C | IPM-GEIH | [0,0 %; 32,8 %] | 11,1 % | [73,8 %; 82,4 %] | 76,7 % |

Pobreza monetaria: 27,0 % de los hogares; A/B: 43,6 % de los hogares
registrados. Las 993 celdas tienen hogares de las dos fuentes (100 % del
peso de la GEIH).

## Por departamento (pobreza monetaria, A-B)

Detalle completo en el CSV. Los casos que más se apartan:

| Departamento | Pobreza | A/B | Error de exclusión | Error de inclusión |
|---|---|---|---|---|
| 11 Bogotá | 15,2 % | 20,5 % | [5,2 %; 99,4 %] | [29,8 %; 99,6 %] |
| 27 Chocó | 55,8 % | 75,6 % | [0,2 %; 37,9 %] | [26,4 %; 54,2 %] |
| 44 La Guajira | 61,2 % | 72,5 % | [1,0 %; 36,5 %] | [16,4 %; 46,4 %] |
| 86 Putumayo | 50,8 % | 42,0 % | **[19,5 %; 78,9 %]** | [2,7 %; 74,4 %] |
| 88 San Andrés | 12,8 % | 13,6 % | **[24,9 %; 100 %]** | [29,3 %; 100 %] |

## Cómo leerlo

1. **El error de inclusión tiene un piso que no depende de ningún
   supuesto dentro de la celda: al menos 39 % de los hogares A/B no son
   pobres monetarios** (al menos 54 % no son pobres por IPM). La razón es
   aritmética: el Sisbén clasifica como A/B a más hogares (43,6 %) de los
   que son pobres (27,0 %), y pasa lo mismo en el 87 % de las celdas (93 %
   del peso de la GEIH). Ninguna forma de acoplar las dos fuentes elimina
   ese exceso.
2. **El error de exclusión no se puede acotar lejos de cero a nivel
   nacional.** Los datos son compatibles con que casi todos los pobres
   estén en A/B (0,9 % excluidos) o con que lo estén solo uno de cada
   cuatro (75,0 %). Es el mismo problema de identificación de las cotas
   del efecto (`RESULTADOS_FRECHET_MANSKI.md`), aplicado a la
   focalización.
3. **Donde hay menos A/B que pobres, la exclusión sí tiene piso.** En
   Putumayo al menos 19,5 % de los pobres quedan fuera de A/B, en San
   Andrés al menos 24,9 % y en Bogotá al menos 5,2 %. Son los únicos
   resultados de exclusión con datos reales que no dependen del
   emparejamiento.
4. **El Hot-Deck es un punto dentro de la cota, no la respuesta.** Con
   independencia dentro de la celda, la exclusión sería 44,3 % y la
   inclusión 65,5 %. Coincide con lo que da la regla vigente en la
   simulación (43,5 %\* y 58,1 %\*, sobre personas), porque esa regla
   también sortea el grupo en la celda.
5. **Ampliar a A-B-C cambia una tasa por la otra:** la exclusión baja a
   lo sumo a 50 % y el piso de inclusión sube a 65 %.

\* Resultado simulado (semisintético).

## Alcance y supuestos

- **e es la proporción de A/B entre los hogares registrados en el
  Sisbén** y se toma como la de toda la celda en la GEIH. Es el mismo
  supuesto del Hot-Deck. La cobertura del registro varía entre
  departamentos (`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`). Si los
  hogares no registrados se contaran como no elegibles, habría menos
  elegibles en cada celda, y la exclusión sería mayor y la inclusión
  menor que en estas cotas.
- Las tasas son de hogares. Las de las reglas simuladas son de personas,
  así que la comparación del punto 4 es aproximada.
- Las cotas son de las proporciones poblacionales. No incluyen el error
  de muestreo de p y e por celda.
- Pruebas: `tests/test_errores_focalizacion_frechet.py`, que verifica
  que las tasas verdaderas de poblaciones al azar (5 semillas, con
  dependencia arbitraria dentro de la celda) caen dentro de la cota, que
  las cotas se alcanzan y que las definiciones coinciden con las de las
  reglas simuladas. La mutación correspondiente está en `tests/mutaciones.py`.
