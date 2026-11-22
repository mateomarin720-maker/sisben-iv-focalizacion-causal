# Resultados — Errores de inclusión y exclusión del Sisbén con datos reales

Generado el 2026-11-10 por `src/diagnostico/errores_focalizacion_frechet.py`;
regenerado el 2026-11-14 con la celda que suma personas del hogar y
menores de 18 años, y el 2026-11-21 con la proporción de elegibles de
cada celda ponderada por el factor de expansión del Sisbén (`fex`; el
archivo nacional de ANDA es una muestra que sobrerrepresenta A y B). Las
cifras anteriores, entre paréntesis donde ayudan a comparar.
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
cuartos, nivel de pisos, personas y menores; 3.721 celdas) se conocen la proporción de pobres
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
| A-B | Monetaria | **[4,4 %; 59,5 %]** | 36,1 % | **[39,0 %; 74,2 %]** | 59,2 % |
| A-B | IPM-GEIH | [2,2 %; 58,2 %] | 30,8 % | [66,6 %; 85,7 %] | 76,4 % |
| A-B | Monetaria oficial (23 deptos. y Bogotá) | [3,8 %; 60,0 %] | 35,6 % | [41,4 %; 75,7 %] | 60,8 % |
| A-B-C | Monetaria | [0,0 %; 26,7 %] | 9,3 % | [65,6 %; 74,8 %] | 68,7 % |
| A-B-C | IPM-GEIH | [0,0 %; 27,4 %] | 8,5 % | [81,5 %; 86,6 %] | 83,1 % |

Sin ponderar el Sisbén por `fex` (hasta el 2026-11-21), A-B y pobreza
monetaria daban exclusión [2,8 %; 57,7 %] (33,8 % con independencia) e
inclusión [41,2 %; 74,4 %] (59,9 %): con el registro bien expandido hay
menos elegibles por celda, y la exclusión sube unos 2 puntos.

Con la celda del 2026-11-02 (993 celdas), A-B y pobreza monetaria daban
exclusión [0,9 %; 75,0 %] e inclusión [38,6 %; 84,5 %]: personas y
menores cierran la exclusión 19 puntos (17 por arriba) y la inclusión 13.

Pobreza monetaria: 27,0 % de los hogares; IPM-GEIH: 14,5 % (20,4 % antes de corregir la vivienda por zona, 2026-11-12); A/B: 42,4 % de los hogares
registrados, con el peso de la GEIH en cada celda (44,7 % sin ponderar el
Sisbén; 43,6 % con la celda anterior). Las 3.721 celdas tienen hogares de las dos fuentes (100 % del
peso de la GEIH).

## Por departamento (pobreza monetaria, A-B)

Detalle completo en el CSV. Los casos que más se apartan:

| Departamento | Pobreza | A/B | Error de exclusión | Error de inclusión |
|---|---|---|---|---|
| 11 Bogotá | 15,2 % | 19,7 % | **[11,5 %; 87,8 %]** | [31,5 %; 90,6 %] |
| 25 Cundinamarca | 18,8 % | 26,5 % | **[10,5 %; 87,5 %]** | [36,2 %; 91,1 %] |
| 27 Chocó | 55,8 % | 76,2 % | [1,2 %; 27,2 %] | [27,6 %; 46,7 %] |
| 44 La Guajira | 61,2 % | 75,2 % | [2,0 %; 26,1 %] | [20,3 %; 39,9 %] |
| 86 Putumayo | 50,8 % | 43,0 % | **[26,8 %; 67,5 %]** | [13,6 %; 61,6 %] |
| 88 San Andrés | 12,8 % | 14,3 % | **[34,5 %; 97,0 %]** | [41,1 %; 97,3 %] |
| 95 Guaviare | 28,0 % | 39,9 % | **[11,2 %; 70,3 %]** | [37,7 %; 79,2 %] |

## Cómo leerlo

1. **El error de inclusión tiene un piso que no depende de ningún
   supuesto dentro de la celda: al menos 39 % de los hogares A/B no son
   pobres monetarios** (al menos 67 % no son pobres por IPM). La razón es
   aritmética: el Sisbén clasifica como A/B a más hogares (42,4 %) de los
   que son pobres (27,0 %), y pasa lo mismo en el 74 % de las celdas (75 %
   del peso de la GEIH). Ninguna forma de acoplar las dos fuentes elimina
   ese exceso.
2. **El error de exclusión no se puede acotar lejos de cero a nivel
   nacional.** Los datos son compatibles con que casi todos los pobres
   estén en A/B (4,4 % excluidos) o con que más de la mitad quede fuera
   (59,5 %). Con la celda más fina el techo bajó de 75,0 % a 57,7 % (59,5 %
   con el `fex`): la
   celda separa mejor a los hogares pobres y a los A/B, y ya no es
   compatible con los datos que tres de cada cuatro pobres queden fuera. Es el mismo problema de identificación de las cotas
   del efecto (`RESULTADOS_FRECHET_MANSKI.md`), aplicado a la
   focalización.
3. **Donde hay menos A/B que pobres, la exclusión sí tiene piso.** En
   Putumayo al menos 26,8 % de los pobres quedan fuera de A/B, en San
   Andrés al menos 34,5 %, en Bogotá al menos 11,5 % y en Cundinamarca y
   Guaviare al menos 10,5 % y 11,2 %. Son los únicos resultados de
   exclusión con datos reales que no dependen del emparejamiento. El piso
   sale de las celdas con más pobres que A/B (765); el 98 % de su peso está
   en celdas con al menos 10 hogares GEIH, así que no es un efecto de
   celdas diminutas.
4. **El Hot-Deck es un punto dentro de la cota, no la respuesta.** Con
   independencia dentro de la celda, la exclusión sería 36,1 % y la
   inclusión 59,2 % (33,8 % y 59,9 % sin ponderar el Sisbén; 44,3 % y
   65,5 % con la celda anterior). Se parece a
   lo que da la regla vigente en la simulación (27,8 %\* y 54,8 %\*,
   sobre personas y no sobre hogares), porque esa regla también sortea el
   grupo en la celda.
5. **Ampliar a A-B-C cambia una tasa por la otra:** la exclusión baja a
   lo sumo a 26,7 % y el piso de inclusión sube a 66 %.

\* Resultado simulado (semisintético).

## Alcance y supuestos

- **e es la proporción de A/B entre los hogares registrados en el
  Sisbén** y se toma como la de toda la celda en la GEIH. Es el mismo
  supuesto del Hot-Deck. La cobertura del registro varía entre
  departamentos (`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`: 68 % nacional
  con el `fex`, 41,5 % en Bogotá) y sube con la pobreza de la celda. Si los
  hogares no registrados se contaran como no elegibles, habría menos
  elegibles en cada celda, y la exclusión sería mayor que en estas cotas:
  el error de exclusión estimado es un piso del real.
- Las tasas son de hogares. Las de las reglas simuladas son de personas,
  así que la comparación del punto 4 es aproximada.
- Las cotas son de las proporciones poblacionales. No incluyen el error
  de muestreo de p y e por celda.
- Pruebas: `tests/test_errores_focalizacion_frechet.py`, que verifica
  que las tasas verdaderas de poblaciones al azar (5 semillas, con
  dependencia arbitraria dentro de la celda) caen dentro de la cota, que
  las cotas se alcanzan y que las definiciones coinciden con las de las
  reglas simuladas. La mutación correspondiente está en `tests/mutaciones.py`.
